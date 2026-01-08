#!/usr/bin/env python3
"""
Parse voice transcripts into threads for classification.

This script segments raw transcripts into logical threads that can be
individually classified as KNOWLEDGE or PROJECT items.

Usage:
    python parse_transcript.py --input transcript.txt --output threads.json
"""

import os
import sys
import json
import argparse
import re
from pathlib import Path
from typing import Optional
from datetime import datetime

# Import Claude wrapper if available
try:
    from call_claude import call_claude_json
    HAS_CLAUDE = True
except ImportError:
    HAS_CLAUDE = False


def parse_with_claude(transcript: str, source_id: Optional[str] = None) -> list[dict]:
    """
    Use Claude to intelligently parse transcript into threads.

    Args:
        transcript: Raw transcript text
        source_id: Optional source identifier

    Returns:
        List of thread dictionaries
    """
    if not HAS_CLAUDE:
        raise RuntimeError("Claude integration not available")

    prompt = f"""Parse the following voice transcript into logical threads.

Each thread should be a coherent segment that can be classified as either:
- KNOWLEDGE: An insight, concept, reflection, or piece of information
- PROJECT: Something to build or implement

Return a JSON array of threads:
```json
[
  {{
    "id": "thread-001",
    "text": "The actual transcript text for this thread",
    "start_marker": "First few words...",
    "end_marker": "...last few words"
  }}
]
```

Transcript:
{transcript}
"""

    threads = call_claude_json("classifier", prompt)

    # Add metadata
    for i, thread in enumerate(threads):
        thread["id"] = f"thread-{i+1:03d}"
        thread["source_id"] = source_id
        thread["parsed_at"] = datetime.utcnow().isoformat() + "Z"

    return threads


def parse_simple(transcript: str, source_id: Optional[str] = None) -> list[dict]:
    """
    Simple heuristic-based transcript parsing.

    Splits on natural paragraph breaks and topic shifts.

    Args:
        transcript: Raw transcript text
        source_id: Optional source identifier

    Returns:
        List of thread dictionaries
    """
    # Split on double newlines or common topic markers
    segments = re.split(r'\n\n+|(?:^|\n)(?:Also|Anyway|So|Now|Next|Another thing)[,\s]', transcript)

    threads = []
    for i, segment in enumerate(segments):
        segment = segment.strip()
        if not segment or len(segment) < 20:
            continue

        threads.append({
            "id": f"thread-{i+1:03d}",
            "text": segment,
            "start_marker": segment[:50] + "..." if len(segment) > 50 else segment,
            "end_marker": "..." + segment[-50:] if len(segment) > 50 else segment,
            "source_id": source_id,
            "parsed_at": datetime.utcnow().isoformat() + "Z"
        })

    return threads


def parse_transcript(
    transcript: str,
    source_id: Optional[str] = None,
    use_claude: bool = True
) -> list[dict]:
    """
    Parse a transcript into threads.

    Args:
        transcript: Raw transcript text
        source_id: Optional source identifier
        use_claude: Whether to use Claude for intelligent parsing

    Returns:
        List of thread dictionaries
    """
    if use_claude and HAS_CLAUDE and os.environ.get("ANTHROPIC_API_KEY"):
        return parse_with_claude(transcript, source_id)
    else:
        return parse_simple(transcript, source_id)


def main():
    parser = argparse.ArgumentParser(description="Parse transcript into threads")
    parser.add_argument(
        "--input",
        help="Input transcript file or text"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON file"
    )
    parser.add_argument(
        "--source",
        help="Source identifier for the transcript"
    )
    parser.add_argument(
        "--no-claude",
        action="store_true",
        help="Use simple parsing instead of Claude"
    )
    args = parser.parse_args()

    # Get transcript from input file, argument, or environment
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

    # Get source ID
    source_id = args.source or os.environ.get("SOURCE_ID")

    try:
        threads = parse_transcript(
            transcript,
            source_id=source_id,
            use_claude=not args.no_claude
        )

        with open(args.output, "w") as f:
            json.dump(threads, f, indent=2)

        print(f"Parsed {len(threads)} threads to {args.output}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
