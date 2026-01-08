"""
LEGATO CLI module.

Provides the main entry point for the legato command.
"""

import os
import sys
import json
import argparse
from pathlib import Path

from . import __version__
from .classifier import parse_threads, classify_threads, ClassifiedThread
from .correlation import Signal, correlate_signal


def check_environment() -> list[str]:
    """Check required environment variables."""
    issues = []

    if not os.environ.get("ANTHROPIC_API_KEY"):
        issues.append("ANTHROPIC_API_KEY not set (required for classification)")

    if not os.environ.get("GH_TOKEN"):
        issues.append("GH_TOKEN not set (required for GitHub operations)")

    return issues


def cmd_process(args) -> int:
    """Process a transcript."""
    # Get transcript
    if args.transcript.startswith("@"):
        transcript_file = Path(args.transcript[1:])
        if not transcript_file.exists():
            print(f"Error: File not found: {transcript_file}", file=sys.stderr)
            return 1
        transcript = transcript_file.read_text()
    else:
        transcript = args.transcript

    source_id = args.source or "cli-input"

    print(f"Processing transcript (source: {source_id})...")
    print()

    # Parse threads
    print("Step 1: Parsing transcript into threads...")
    threads = parse_threads(transcript, source_id)
    print(f"  Found {len(threads)} threads")

    # Classify threads
    print("Step 2: Classifying threads...")
    classified = classify_threads(threads)

    knowledge_count = sum(1 for t in classified if t.thread_type.value == "KNOWLEDGE")
    project_count = sum(1 for t in classified if t.thread_type.value == "PROJECT")

    print(f"  {knowledge_count} knowledge items")
    print(f"  {project_count} project items")
    print()

    # Output results
    if args.output:
        output = [t.to_dict() for t in classified]
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
        print(f"Results written to {args.output}")
    else:
        print("Classification Results:")
        print("-" * 40)
        for t in classified:
            type_str = t.thread_type.value
            if type_str == "KNOWLEDGE":
                cat = t.knowledge_category.value if t.knowledge_category else "unknown"
                print(f"  [{type_str}/{cat}] {t.knowledge_title or 'Untitled'}")
            else:
                scope = t.project_scope.value if t.project_scope else "note"
                print(f"  [{type_str}/{scope}] {t.project_name or 'unnamed'}")

    return 0


def cmd_classify(args) -> int:
    """Classify threads from a JSON file."""
    with open(args.file) as f:
        threads = json.load(f)

    print(f"Classifying {len(threads)} threads...")

    classified = classify_threads(threads)

    output = [t.to_dict() for t in classified]

    if args.output:
        with open(args.output, "w") as f:
            json.dump(output, f, indent=2)
        print(f"Results written to {args.output}")
    else:
        print(json.dumps(output, indent=2))

    return 0


def cmd_correlate(args) -> int:
    """Check correlation for a query."""
    if args.query.startswith("@"):
        with open(args.query[1:]) as f:
            query_data = json.load(f)
    else:
        query_data = json.loads(args.query)

    signal = Signal.from_dict(query_data)

    print(f"Checking correlation for: {signal.title}")
    print()

    result = correlate_signal(signal)

    print(f"Recommendation: {result['recommendation']}")
    print(f"Top Score: {result['top_score']:.2%}")
    print()

    if result["matches"]:
        print("Top Matches:")
        for match in result["matches"][:3]:
            print(f"  - {match['title']} ({match['score']:.2%})")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2)

    return 0


def cmd_status(args) -> int:
    """Show system status."""
    print("LEGATO System Status")
    print("=" * 40)
    print()

    print(f"Version: {__version__}")
    print()

    # Check environment
    print("Environment:")
    issues = check_environment()
    if issues:
        for issue in issues:
            print(f"  [!] {issue}")
    else:
        print("  [OK] All required variables set")
    print()

    # Check repositories
    print("Repositories:")

    repos = [
        ("Legato.Library", os.environ.get("LIBRARY_REPO", "Legato/Legato.Library")),
        ("Legato.Listen", os.environ.get("LISTEN_REPO", "Legato/Legato.Listen")),
    ]

    import subprocess
    for name, repo in repos:
        result = subprocess.run(
            ["gh", "repo", "view", repo, "--json", "name"],
            capture_output=True,
            text=True
        )
        status = "OK" if result.returncode == 0 else "NOT FOUND"
        print(f"  [{status}] {name}: {repo}")

    return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="LEGATO - Voice transcripts to knowledge and projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"legato {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # process command
    process_parser = subparsers.add_parser("process", help="Process a transcript")
    process_parser.add_argument("transcript", help="Transcript text or @filename")
    process_parser.add_argument("--source", help="Source identifier")
    process_parser.add_argument("--output", "-o", help="Output JSON file")
    process_parser.add_argument("--dry-run", action="store_true", help="Don't commit results")

    # classify command
    classify_parser = subparsers.add_parser("classify", help="Classify threads from file")
    classify_parser.add_argument("file", help="Input JSON file with threads")
    classify_parser.add_argument("--output", "-o", help="Output JSON file")

    # correlate command
    correlate_parser = subparsers.add_parser("correlate", help="Check correlation")
    correlate_parser.add_argument("query", help="Query JSON or @filename")
    correlate_parser.add_argument("--output", "-o", help="Output JSON file")

    # status command
    subparsers.add_parser("status", help="Show system status")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        "process": cmd_process,
        "classify": cmd_classify,
        "correlate": cmd_correlate,
        "status": cmd_status,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
