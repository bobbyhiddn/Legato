"""
LEGATO Classification Engine.

Transforms raw voice transcripts into structured, actionable items.
Operates in two phases: parsing (segmentation) and classification (categorization + routing).
"""

import os
import sys
import json
import argparse
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime
from pathlib import Path


class ThreadType(Enum):
    """Type of content in a thread."""
    KNOWLEDGE = "KNOWLEDGE"
    PROJECT = "PROJECT"
    MIXED = "MIXED"


class KnowledgeCategory(Enum):
    """Categories for knowledge artifacts."""
    EPIPHANY = "epiphany"      # Major breakthrough or insight
    CONCEPT = "concept"        # Technical definition or explanation
    REFLECTION = "reflection"  # Personal thought or observation
    GLIMMER = "glimmer"        # Quick idea seed for future exploration
    REMINDER = "reminder"      # Action item or follow-up
    WORKLOG = "worklog"        # Summary of work done


class ProjectScope(Enum):
    """Scope for project implementations."""
    NOTE = "note"    # Single PR, quick implementation
    CHORD = "chord"  # Multi-PR, complex implementation


@dataclass
class ClassifiedThread:
    """A classified thread from a transcript."""

    id: str
    raw_text: str
    thread_type: ThreadType

    # If KNOWLEDGE
    knowledge_category: Optional[KnowledgeCategory] = None
    knowledge_title: Optional[str] = None

    # If PROJECT
    project_name: Optional[str] = None
    project_scope: Optional[ProjectScope] = None
    project_description: Optional[str] = None

    # Correlation results
    correlation_score: float = 0.0
    correlation_matches: list = field(default_factory=list)
    correlation_action: str = "CREATE"  # CREATE, APPEND, QUEUE

    # Metadata
    domain_tags: list = field(default_factory=list)
    key_phrases: list = field(default_factory=list)
    source_id: Optional[str] = None
    parsed_at: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "raw_text": self.raw_text,
            "type": self.thread_type.value,
            "knowledge_category": self.knowledge_category.value if self.knowledge_category else None,
            "knowledge_title": self.knowledge_title,
            "project_name": self.project_name,
            "project_scope": self.project_scope.value if self.project_scope else None,
            "project_description": self.project_description,
            "correlation_score": self.correlation_score,
            "correlation_matches": self.correlation_matches,
            "correlation_action": self.correlation_action,
            "domain_tags": self.domain_tags,
            "key_phrases": self.key_phrases,
            "source_id": self.source_id,
            "parsed_at": self.parsed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ClassifiedThread":
        """Create from dictionary."""
        thread_type = ThreadType(data.get("type", "KNOWLEDGE"))

        knowledge_category = None
        if data.get("knowledge_category"):
            # Normalize to lowercase to handle Claude returning EPIPHANY vs epiphany
            category_value = data["knowledge_category"].lower()
            knowledge_category = KnowledgeCategory(category_value)

        project_scope = None
        if data.get("project_scope"):
            # Normalize to lowercase
            scope_value = data["project_scope"].lower()
            project_scope = ProjectScope(scope_value)

        return cls(
            id=data.get("id", ""),
            raw_text=data.get("raw_text", data.get("text", "")),
            thread_type=thread_type,
            knowledge_category=knowledge_category,
            knowledge_title=data.get("knowledge_title", data.get("title")),
            project_name=data.get("project_name"),
            project_scope=project_scope,
            project_description=data.get("project_description", data.get("description")),
            correlation_score=data.get("correlation_score", 0.0),
            correlation_matches=data.get("correlation_matches", []),
            correlation_action=data.get("correlation_action", "CREATE"),
            domain_tags=data.get("domain_tags", []),
            key_phrases=data.get("key_phrases", []),
            source_id=data.get("source_id"),
            parsed_at=data.get("parsed_at"),
        )


def load_prompt(prompt_name: str) -> str:
    """Load a prompt from the prompts directory."""
    prompts_dir = Path(__file__).parent.parent.parent / "prompts"
    prompt_file = prompts_dir / f"{prompt_name}.md"

    if prompt_file.exists():
        return prompt_file.read_text()

    raise FileNotFoundError(f"Prompt not found: {prompt_file}")


def call_claude(system_prompt: str, user_input: str, max_tokens: int = 4096) -> tuple[str, str]:
    """Call Claude API with the given prompts.

    Returns:
        Tuple of (response_text, stop_reason)
    """
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("anthropic package not installed")

    client = anthropic.Anthropic()

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_input}]
    )

    return message.content[0].text, message.stop_reason


def repair_truncated_json(text: str) -> str:
    """Attempt to repair truncated JSON array."""
    text = text.strip()

    # Count open brackets/braces
    open_brackets = text.count('[') - text.count(']')
    open_braces = text.count('{') - text.count('}')

    # Check if we're in a string (odd number of unescaped quotes)
    in_string = False
    i = len(text) - 1
    while i >= 0:
        if text[i] == '"' and (i == 0 or text[i-1] != '\\'):
            in_string = not in_string
            break
        i -= 1

    # If in string, close it
    if in_string:
        text += '"'

    # Close any open braces/brackets
    text += '}' * open_braces
    text += ']' * open_brackets

    return text


def parse_threads(transcript: str, source_id: Optional[str] = None) -> list[dict]:
    """
    Parse transcript into threads using Claude.

    Args:
        transcript: Raw transcript text
        source_id: Optional source identifier

    Returns:
        List of parsed thread dictionaries
    """
    prompt = """Parse this voice transcript into logical threads.
Each thread should be a coherent segment that discusses one topic.
Return a JSON array of threads with id, text, and summary fields.

Return format:
```json
[
  {"id": "thread-001", "text": "...", "summary": "Brief summary"}
]
```"""

    # Use higher token limit for parsing since output includes full transcript text
    response, stop_reason = call_claude(prompt, transcript, max_tokens=16384)

    # Extract JSON from response
    text = response.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]

    # Try to parse JSON, with repair attempt if truncated
    try:
        threads = json.loads(text)
    except json.JSONDecodeError as e:
        if stop_reason == "max_tokens":
            print(f"Warning: Response truncated, attempting JSON repair...", file=sys.stderr)
            repaired = repair_truncated_json(text)
            try:
                threads = json.loads(repaired)
                print(f"JSON repair successful, recovered {len(threads)} threads", file=sys.stderr)
            except json.JSONDecodeError:
                raise ValueError(
                    f"Failed to parse truncated JSON response. "
                    f"Original error: {e}. Consider splitting the transcript into smaller chunks."
                )
        else:
            raise ValueError(f"Failed to parse Claude response as JSON: {e}")

    # Add metadata
    for i, thread in enumerate(threads):
        thread["id"] = f"thread-{i+1:03d}"
        thread["source_id"] = source_id
        thread["parsed_at"] = datetime.utcnow().isoformat() + "Z"

    return threads


def classify_threads(threads: list[dict]) -> list[ClassifiedThread]:
    """
    Classify parsed threads into KNOWLEDGE or PROJECT types.

    Args:
        threads: List of parsed thread dictionaries

    Returns:
        List of ClassifiedThread objects
    """
    classifier_prompt = load_prompt("classifier")

    results = []

    for thread in threads:
        thread_text = thread.get("text", thread.get("raw_text", ""))

        response, _ = call_claude(classifier_prompt, thread_text)

        # Parse classification response
        text = response.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        try:
            classification = json.loads(text)
            if isinstance(classification, list):
                classification = classification[0]
        except json.JSONDecodeError:
            # Default to glimmer if parsing fails
            classification = {
                "type": "KNOWLEDGE",
                "knowledge_category": "glimmer",
                "title": thread.get("summary", "Untitled"),
                "domain_tags": [],
                "key_phrases": []
            }

        # Merge with original thread data
        classification["raw_text"] = thread_text
        classification["id"] = thread.get("id", "")
        classification["source_id"] = thread.get("source_id")
        classification["parsed_at"] = thread.get("parsed_at")

        classified = ClassifiedThread.from_dict(classification)
        results.append(classified)

    return results


def main():
    """CLI entry point for classifier."""
    parser = argparse.ArgumentParser(description="LEGATO Classification Engine")
    parser.add_argument(
        "--phase",
        choices=["parse", "classify", "full"],
        default="full",
        help="Processing phase"
    )
    parser.add_argument(
        "--input",
        help="Input file (transcript or threads.json)"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON file"
    )
    args = parser.parse_args()

    # Get transcript from input or environment
    if args.phase in ("parse", "full"):
        if args.input:
            if Path(args.input).exists():
                transcript = Path(args.input).read_text()
            else:
                transcript = args.input
        elif os.environ.get("TRANSCRIPT"):
            transcript = os.environ["TRANSCRIPT"]
        else:
            print("Error: No transcript provided", file=sys.stderr)
            sys.exit(1)

        source_id = os.environ.get("SOURCE_ID")
        threads = parse_threads(transcript, source_id)

        if args.phase == "parse":
            with open(args.output, "w") as f:
                json.dump(threads, f, indent=2)
            print(f"Parsed {len(threads)} threads")
            return

    if args.phase in ("classify", "full"):
        if args.phase == "classify":
            with open(args.input) as f:
                threads = json.load(f)

        classified = classify_threads(threads)

        output = [t.to_dict() for t in classified]
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)

        knowledge_count = sum(1 for t in classified if t.thread_type == ThreadType.KNOWLEDGE)
        project_count = sum(1 for t in classified if t.thread_type == ThreadType.PROJECT)

        print(f"Classified {len(classified)} threads: {knowledge_count} knowledge, {project_count} projects")


if __name__ == "__main__":
    main()
