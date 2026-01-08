"""
LEGATO Knowledge Module.

Handles extraction of knowledge artifacts from classified threads
and committing them to the Legato.Library repository.
"""

import os
import sys
import json
import argparse
import subprocess
import base64
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .classifier import ClassifiedThread, ThreadType, KnowledgeCategory


@dataclass
class KnowledgeArtifact:
    """A knowledge artifact ready for the Library."""

    id: str
    title: str
    category: KnowledgeCategory
    content: str
    domain_tags: list = field(default_factory=list)
    key_phrases: list = field(default_factory=list)
    source_transcript: Optional[str] = None
    created: Optional[str] = None
    correlation_score: float = 0.0
    related: list = field(default_factory=list)

    def to_markdown(self) -> str:
        """Convert to markdown format for Library."""
        created = self.created or datetime.utcnow().isoformat() + "Z"

        frontmatter = f"""---
id: {self.id}
title: "{self.title}"
category: {self.category.value}
created: {created}
source_transcript: {self.source_transcript or 'unknown'}
domain_tags: {json.dumps(self.domain_tags)}
key_phrases: {json.dumps(self.key_phrases)}
correlation_score: {self.correlation_score}
related: {json.dumps(self.related)}
---"""

        return f"{frontmatter}\n\n{self.content}"

    def get_path(self) -> str:
        """Get the file path for this artifact."""
        date = datetime.utcnow().strftime("%Y-%m-%d")
        slug = self.id.split(".")[-1]
        return f"{self.category.value}s/{date}-{slug}.md"


def load_prompt(prompt_name: str) -> str:
    """Load a prompt from the prompts directory."""
    prompts_dir = Path(__file__).parent.parent.parent / "prompts"
    prompt_file = prompts_dir / f"{prompt_name}.md"

    if prompt_file.exists():
        return prompt_file.read_text()

    raise FileNotFoundError(f"Prompt not found: {prompt_file}")


def call_claude(system_prompt: str, user_input: str) -> str:
    """Call Claude API with the given prompts."""
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("anthropic package not installed")

    client = anthropic.Anthropic()

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_input}]
    )

    return message.content[0].text


def extract_knowledge(thread: ClassifiedThread) -> KnowledgeArtifact:
    """
    Extract a knowledge artifact from a classified thread.

    Args:
        thread: A classified thread with type KNOWLEDGE

    Returns:
        KnowledgeArtifact ready for commit
    """
    if thread.thread_type != ThreadType.KNOWLEDGE:
        raise ValueError(f"Thread {thread.id} is not a KNOWLEDGE thread")

    extractor_prompt = load_prompt("knowledge-extractor")

    # Prepare input for Claude
    input_data = {
        "thread_id": thread.id,
        "category": thread.knowledge_category.value if thread.knowledge_category else "glimmer",
        "title": thread.knowledge_title or "Untitled",
        "text": thread.raw_text,
        "domain_tags": thread.domain_tags,
        "key_phrases": thread.key_phrases,
        "source_id": thread.source_id,
    }

    response = call_claude(extractor_prompt, json.dumps(input_data, indent=2))

    # Extract markdown content from response
    content = response.strip()

    # Remove any code block markers if present
    if content.startswith("```markdown"):
        content = content[11:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]

    # Generate artifact ID
    category = thread.knowledge_category or KnowledgeCategory.GLIMMER
    slug = (thread.knowledge_title or thread.id).lower()
    slug = "".join(c if c.isalnum() or c == "-" else "-" for c in slug)
    slug = "-".join(filter(None, slug.split("-")))[:50]

    artifact_id = f"library.{category.value}s.{slug}"

    return KnowledgeArtifact(
        id=artifact_id,
        title=thread.knowledge_title or "Untitled",
        category=category,
        content=content,
        domain_tags=thread.domain_tags,
        key_phrases=thread.key_phrases,
        source_transcript=thread.source_id,
        created=datetime.utcnow().isoformat() + "Z",
        correlation_score=thread.correlation_score,
        related=[m.get("signal_id") for m in thread.correlation_matches if m.get("score", 0) > 0.5],
    )


def commit_knowledge(artifact: KnowledgeArtifact, library_repo: Optional[str] = None) -> dict:
    """
    Commit a knowledge artifact to the Library repository.

    Args:
        artifact: The artifact to commit
        library_repo: Repository in owner/repo format (default from env)

    Returns:
        Commit result dictionary
    """
    library_repo = library_repo or os.environ.get("LIBRARY_REPO", "Legato/Legato.Library")
    token = os.environ.get("GH_TOKEN")

    if not token:
        raise RuntimeError("GH_TOKEN environment variable not set")

    content = artifact.to_markdown()
    file_path = artifact.get_path()
    commit_msg = f"Add {artifact.category.value}: {artifact.title}"

    # Encode content
    content_b64 = base64.b64encode(content.encode()).decode()

    # Check if file exists
    check_cmd = [
        "gh", "api",
        f"/repos/{library_repo}/contents/{file_path}",
        "--silent"
    ]

    result = subprocess.run(check_cmd, capture_output=True, text=True)
    file_exists = result.returncode == 0

    if file_exists:
        # Get SHA for update
        file_info = json.loads(result.stdout)
        sha = file_info.get("sha")

        update_cmd = [
            "gh", "api",
            "--method", "PUT",
            f"/repos/{library_repo}/contents/{file_path}",
            "-f", f"message={commit_msg}",
            "-f", f"content={content_b64}",
            "-f", f"sha={sha}"
        ]
        subprocess.run(update_cmd, check=True)
    else:
        create_cmd = [
            "gh", "api",
            "--method", "PUT",
            f"/repos/{library_repo}/contents/{file_path}",
            "-f", f"message={commit_msg}",
            "-f", f"content={content_b64}"
        ]
        subprocess.run(create_cmd, check=True)

    return {
        "repo": library_repo,
        "path": file_path,
        "action": "updated" if file_exists else "created",
        "artifact_id": artifact.id
    }


def process_routing(routing_file: str, commit: bool = False) -> list[dict]:
    """
    Process all KNOWLEDGE items from a routing file.

    Args:
        routing_file: Path to routing.json
        commit: Whether to commit to Library

    Returns:
        List of results
    """
    with open(routing_file) as f:
        routing = json.load(f)

    results = []

    for item in routing:
        if item.get("type") != "KNOWLEDGE":
            continue

        thread = ClassifiedThread.from_dict(item)

        try:
            artifact = extract_knowledge(thread)

            if commit:
                result = commit_knowledge(artifact)
                result["artifact"] = artifact.to_markdown()[:200] + "..."
            else:
                result = {
                    "artifact_id": artifact.id,
                    "path": artifact.get_path(),
                    "action": "would_create"
                }

            results.append(result)
            print(f"Processed: {artifact.id}")

        except Exception as e:
            print(f"Error processing {thread.id}: {e}", file=sys.stderr)
            results.append({"error": str(e), "thread_id": thread.id})

    return results


def main():
    """CLI entry point for knowledge module."""
    parser = argparse.ArgumentParser(description="LEGATO Knowledge Module")
    parser.add_argument(
        "--input",
        required=True,
        help="Input routing.json file"
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Actually commit to Library"
    )
    parser.add_argument(
        "--output",
        help="Output results file"
    )
    args = parser.parse_args()

    results = process_routing(args.input, args.commit)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)

    committed = len([r for r in results if r.get("action") in ("created", "updated")])
    errors = len([r for r in results if "error" in r])

    print(f"Processed {len(results)} items: {committed} committed, {errors} errors")


if __name__ == "__main__":
    main()
