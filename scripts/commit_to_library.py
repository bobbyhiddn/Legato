#!/usr/bin/env python3
"""
Commit knowledge artifacts to Legato.Library.

This script handles creating and committing markdown artifacts to the
knowledge store repository.

Usage:
    python commit_to_library.py --artifact artifact.md --category epiphanies
"""

import os
import sys
import json
import argparse
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional


def get_library_path() -> str:
    """Get the Library repository path from environment or default."""
    return os.environ.get("LIBRARY_REPO", "Legato/Legato.Library")


def generate_filename(category: str, slug: str) -> str:
    """Generate a filename for the artifact."""
    date = datetime.utcnow().strftime("%Y-%m-%d")
    return f"{date}-{slug}.md"


def commit_artifact(
    content: str,
    category: str,
    slug: str,
    message: Optional[str] = None
) -> dict:
    """
    Commit an artifact to the Library repository.

    Args:
        content: Markdown content of the artifact
        category: Category directory (epiphanies, concepts, etc.)
        slug: URL-friendly identifier for the artifact
        message: Optional commit message

    Returns:
        Dictionary with commit info
    """
    library_repo = get_library_path()
    token = os.environ.get("GH_TOKEN")

    if not token:
        raise RuntimeError("GH_TOKEN environment variable not set")

    filename = generate_filename(category, slug)
    file_path = f"{category}/{filename}"
    commit_msg = message or f"Add {category}: {slug}"

    # Use GitHub CLI to create the file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Check if file already exists
        check_cmd = [
            "gh", "api",
            f"/repos/{library_repo}/contents/{file_path}",
            "--silent"
        ]
        result = subprocess.run(check_cmd, capture_output=True, text=True)
        file_exists = result.returncode == 0

        if file_exists:
            # Get the SHA for update
            file_info = json.loads(result.stdout)
            sha = file_info.get("sha")

            # Update existing file
            import base64
            content_b64 = base64.b64encode(content.encode()).decode()

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
            # Create new file
            import base64
            content_b64 = base64.b64encode(content.encode()).decode()

            create_cmd = [
                "gh", "api",
                "--method", "PUT",
                f"/repos/{library_repo}/contents/{file_path}",
                "-f", f"message={commit_msg}",
                "-f", f"content={content_b64}"
            ]
            subprocess.run(create_cmd, check=True)

    finally:
        os.unlink(temp_path)

    return {
        "repo": library_repo,
        "path": file_path,
        "message": commit_msg,
        "action": "updated" if file_exists else "created"
    }


def commit_from_routing(routing_file: str) -> list[dict]:
    """
    Commit all knowledge artifacts from a routing decisions file.

    Args:
        routing_file: Path to routing.json file

    Returns:
        List of commit results
    """
    with open(routing_file) as f:
        routing = json.load(f)

    results = []

    for item in routing:
        if item.get("type") != "KNOWLEDGE":
            continue

        category = item.get("knowledge_category", "glimmers")
        slug = item.get("id", "").replace("thread-", "item-")
        title = item.get("title", "Untitled")
        description = item.get("description", "")
        domain_tags = item.get("domain_tags", [])
        key_phrases = item.get("key_phrases", [])

        # Generate artifact content
        content = f"""---
id: library.{category}.{slug}
title: "{title}"
category: {category}
created: {datetime.utcnow().isoformat()}Z
source_transcript: {item.get('source_id', 'unknown')}
domain_tags: {json.dumps(domain_tags)}
key_phrases: {json.dumps(key_phrases)}
correlation_score: 0.0
related: []
---

# {title}

{description}

## Context

This artifact was generated from a voice transcript by LEGATO.

## Key Points

{chr(10).join(f"- {phrase}" for phrase in key_phrases)}

"""

        try:
            result = commit_artifact(content, category, slug)
            results.append(result)
            print(f"Committed: {result['path']}")
        except Exception as e:
            print(f"Error committing {slug}: {e}", file=sys.stderr)
            results.append({"error": str(e), "slug": slug})

    return results


def main():
    parser = argparse.ArgumentParser(description="Commit artifacts to Library")
    parser.add_argument(
        "--artifact",
        help="Path to artifact markdown file"
    )
    parser.add_argument(
        "--category",
        choices=["epiphanies", "concepts", "reflections", "glimmers", "reminders", "worklog"],
        help="Category for the artifact"
    )
    parser.add_argument(
        "--slug",
        help="URL-friendly identifier"
    )
    parser.add_argument(
        "--routing",
        help="Path to routing.json for batch commit"
    )
    parser.add_argument(
        "--message",
        help="Commit message"
    )
    args = parser.parse_args()

    if args.routing:
        # Batch mode from routing file
        results = commit_from_routing(args.routing)
        print(f"Committed {len([r for r in results if 'error' not in r])} artifacts")
    elif args.artifact and args.category and args.slug:
        # Single artifact mode
        content = Path(args.artifact).read_text()
        result = commit_artifact(content, args.category, args.slug, args.message)
        print(f"Committed: {result['path']}")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
