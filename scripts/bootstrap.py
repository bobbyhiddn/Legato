#!/usr/bin/env python3
"""
Bootstrap the complete LEGATO system.

Creates and initializes:
- Legato.Conduct (orchestrator)
- Legato.Library (knowledge store)
- Legato.Listen (semantic correlation index)

Usage:
    python bootstrap.py --org Legato
    python bootstrap.py --org myorg --dry-run

Requires:
    - GH_TOKEN environment variable (GitHub personal access token)
    - PyGithub package
"""

import os
import sys
import argparse
import base64
from pathlib import Path
from datetime import datetime

from github import Github, GithubException, InputGitTreeElement


def get_github_client() -> Github:
    """Get authenticated GitHub client."""
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError(
            "GitHub token not found. Set GH_TOKEN or GITHUB_TOKEN environment variable."
        )
    return Github(token)


def repo_exists(gh: Github, repo_name: str) -> bool:
    """Check if a repository exists."""
    try:
        gh.get_repo(repo_name)
        return True
    except GithubException as e:
        if e.status == 404:
            return False
        raise


def create_repo(gh: Github, repo_name: str, description: str, dry_run: bool = False) -> bool:
    """Create a repository."""
    if dry_run:
        print(f"  [DRY RUN] Would create: {repo_name}")
        return True

    if repo_exists(gh, repo_name):
        print(f"  [EXISTS] {repo_name}")
        return True

    try:
        # Get the user or org
        owner = repo_name.split("/")[0]
        name = repo_name.split("/")[1]

        try:
            # Try as organization first
            org = gh.get_organization(owner)
            org.create_repo(
                name=name,
                description=description,
                private=False,
                auto_init=False,
            )
        except GithubException:
            # Fall back to user repo
            user = gh.get_user()
            user.create_repo(
                name=name,
                description=description,
                private=False,
                auto_init=False,
            )

        print(f"  [CREATED] {repo_name}")
        return True
    except GithubException as e:
        print(f"  [FAILED] {repo_name}: {e.data.get('message', str(e))}")
        return False


def create_file(
    gh: Github, repo_name: str, path: str, content: str, message: str, dry_run: bool = False
) -> bool:
    """Create a file in a repository using the Contents API."""
    if dry_run:
        print(f"  [DRY RUN] Would create: {repo_name}/{path}")
        return True

    try:
        repo = gh.get_repo(repo_name)
        content_bytes = content.encode("utf-8")

        try:
            # Check if file exists
            existing = repo.get_contents(path)
            print(f"  [EXISTS] {path}")
            return True
        except GithubException as e:
            if e.status != 404:
                raise

        # Create the file
        repo.create_file(
            path=path,
            message=message,
            content=content_bytes,
            branch="main",
        )
        print(f"  [CREATED] {path}")
        return True
    except GithubException as e:
        # Handle case where main branch doesn't exist yet
        if "Reference does not exist" in str(e) or e.status == 404:
            try:
                repo = gh.get_repo(repo_name)
                # Create initial commit to establish main branch
                repo.create_file(
                    path=path,
                    message=message,
                    content=content_bytes,
                )
                print(f"  [CREATED] {path}")
                return True
            except GithubException as e2:
                print(f"  [FAILED] {path}: {e2.data.get('message', str(e2))}")
                return False
        print(f"  [FAILED] {path}: {e.data.get('message', str(e))}")
        return False


def get_seed_dir() -> Path:
    """Get the directory containing the seed files (this repo)."""
    # bootstrap.py is in scripts/, so parent.parent is repo root
    return Path(__file__).parent.parent


def push_directory_to_repo(
    gh: Github, repo_name: str, source_dir: Path, commit_message: str, dry_run: bool = False
) -> bool:
    """
    Push an entire directory to a repository using GitHub's Git Data API.

    This creates blobs for all files, builds a tree, and creates a commit,
    avoiding the need for git CLI entirely.
    """
    if dry_run:
        for item in source_dir.rglob("*"):
            if ".git" in item.parts:
                continue
            if item.is_file():
                rel_path = item.relative_to(source_dir)
                print(f"  [DRY RUN] Would copy: {rel_path}")
        return True

    try:
        repo = gh.get_repo(repo_name)

        # Collect all files to push
        files_to_push = []
        for item in source_dir.rglob("*"):
            if ".git" in item.parts:
                continue
            if item.is_file():
                rel_path = str(item.relative_to(source_dir))
                try:
                    content = item.read_text(encoding="utf-8")
                    # Update README if needed
                    if rel_path == "README.md" and content.startswith("# LEGATO Specification"):
                        org = repo_name.split("/")[0]
                        notice = f"""# Legato.Conduct

> **Deployed LEGATO Orchestrator** - Part of the [{org}](https://github.com/{org}) LEGATO system.

---

"""
                        content = notice + content

                    files_to_push.append({
                        "path": rel_path,
                        "content": content,
                        "mode": "100644",  # Regular file
                        "type": "blob",
                    })
                except UnicodeDecodeError:
                    # Binary file - read as base64
                    content_b64 = base64.b64encode(item.read_bytes()).decode("ascii")
                    files_to_push.append({
                        "path": rel_path,
                        "content_b64": content_b64,
                        "mode": "100644",
                        "type": "blob",
                        "encoding": "base64",
                    })

        if not files_to_push:
            print("  [WARNING] No files to push")
            return True

        # Create tree elements
        tree_elements = []
        for file_info in files_to_push:
            if "content_b64" in file_info:
                # Binary file - create blob first
                blob = repo.create_git_blob(file_info["content_b64"], "base64")
                tree_elements.append(
                    InputGitTreeElement(
                        path=file_info["path"],
                        mode=file_info["mode"],
                        type=file_info["type"],
                        sha=blob.sha,
                    )
                )
            else:
                # Text file - can use content directly
                tree_elements.append(
                    InputGitTreeElement(
                        path=file_info["path"],
                        mode=file_info["mode"],
                        type=file_info["type"],
                        content=file_info["content"],
                    )
                )

        # Try to get existing main branch, or create from scratch
        try:
            main_ref = repo.get_git_ref("heads/main")
            base_tree = repo.get_git_commit(main_ref.object.sha).tree
            tree = repo.create_git_tree(tree_elements, base_tree)
            parent_commits = [repo.get_git_commit(main_ref.object.sha)]
        except GithubException:
            # No main branch yet - create tree without base
            tree = repo.create_git_tree(tree_elements)
            parent_commits = []

        # Create commit
        commit = repo.create_git_commit(
            message=commit_message,
            tree=tree,
            parents=parent_commits,
        )

        # Update or create main branch reference
        try:
            main_ref = repo.get_git_ref("heads/main")
            main_ref.edit(sha=commit.sha, force=True)
        except GithubException:
            # Create main branch
            repo.create_git_ref(ref="refs/heads/main", sha=commit.sha)

        print(f"  [DEPLOYED] {len(files_to_push)} files pushed to {repo_name}")
        return True

    except GithubException as e:
        error_msg = e.data.get("message", str(e)) if hasattr(e, "data") else str(e)
        print(f"  [FAILED] Push to {repo_name}: {error_msg}")
        return False


def bootstrap_conduct(gh: Github, org: str, dry_run: bool = False) -> bool:
    """Bootstrap Legato.Conduct repository from seed files."""
    repo_name = f"{org}/Legato.Conduct"
    print(f"\nBootstrapping {repo_name}...")

    if not create_repo(
        gh, repo_name, "LEGATO Orchestrator - Voice transcripts to knowledge and projects", dry_run
    ):
        return False

    seed_dir = get_seed_dir()

    return push_directory_to_repo(
        gh, repo_name, seed_dir, "Initialize Legato.Conduct from seed", dry_run
    )


def bootstrap_library(gh: Github, org: str, dry_run: bool = False) -> bool:
    """Bootstrap Legato.Library repository."""
    repo_name = f"{org}/Legato.Library"
    print(f"\nBootstrapping {repo_name}...")

    if not create_repo(
        gh, repo_name, "LEGATO Knowledge Store - Structured knowledge artifacts", dry_run
    ):
        return False

    # README
    readme = f"""# Legato.Library

> LEGATO Knowledge Store - Structured knowledge artifacts from voice transcripts.

## Structure

```
├── epiphanies/    # Major insights, breakthrough ideas
├── concepts/      # Technical concepts, definitions
├── reflections/   # Personal thoughts, observations
├── glimmers/      # Quick ideas, seeds for future
├── reminders/     # Action items, follow-ups
├── worklog/       # Daily/session work summaries
└── index.json     # Quick lookup index
```

## Artifact Format

Each artifact is a markdown file with YAML frontmatter:

```yaml
---
id: library.{{category}}.{{slug}}
title: "Artifact Title"
category: epiphany|concept|reflection|glimmer|reminder|worklog
created: 2026-01-07T15:30:00Z
source_transcript: transcript-2026-01-07-1530
domain_tags: [ai, architecture]
key_phrases: ["oracle machine", "intuition engine"]
correlation_score: 0.0
related: []
---

# Content here...
```

## Usage

Artifacts are created automatically by [Legato.Conduct](https://github.com/{org}/Legato.Conduct) when processing voice transcripts classified as KNOWLEDGE.

---
*Part of the LEGATO system*
"""

    create_file(gh, repo_name, "README.md", readme, "Initialize Library", dry_run)

    # Index
    create_file(gh, repo_name, "index.json", "{}", "Initialize index", dry_run)

    # Category directories with .gitkeep
    categories = ["epiphanies", "concepts", "reflections", "glimmers", "reminders", "worklog"]
    for cat in categories:
        create_file(
            gh, repo_name, f"{cat}/.gitkeep", f"# {cat.title()}\n", f"Create {cat} directory", dry_run
        )

    # Workflow to register signals
    workflow = f"""name: Register Signal

on:
  push:
    paths:
      - 'epiphanies/**'
      - 'concepts/**'
      - 'reflections/**'
      - 'glimmers/**'
      - 'reminders/**'
      - 'worklog/**'

jobs:
  register:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Get changed files
        id: changes
        run: |
          echo "files=$(git diff --name-only HEAD~1 HEAD | grep -E '\\.(md)$' | tr '\\n' ' ')" >> $GITHUB_OUTPUT

      - name: Notify Listen
        if: steps.changes.outputs.files != ''
        env:
          GH_TOKEN: ${{{{ secrets.LISTEN_PAT }}}}
        run: |
          for file in ${{{{ steps.changes.outputs.files }}}}; do
            echo "Registering signal for: ${{file}}"
            # Trigger Listen to index new artifact
            gh workflow run register-signal.yml \\
              --repo {org}/Legato.Listen \\
              -f artifact_path="${{file}}" \\
              -f source_repo="${{GITHUB_REPOSITORY}}" || true
          done
"""

    create_file(
        gh, repo_name, ".github/workflows/register-signal.yml", workflow,
        "Add signal registration workflow", dry_run
    )

    return True


def bootstrap_listen(gh: Github, org: str, dry_run: bool = False) -> bool:
    """Bootstrap Legato.Listen repository."""
    repo_name = f"{org}/Legato.Listen"
    print(f"\nBootstrapping {repo_name}...")

    if not create_repo(gh, repo_name, "LEGATO Semantic Brain - Correlation and indexing", dry_run):
        return False

    # README
    readme = f"""# Legato.Listen

> LEGATO Semantic Brain - Indexes artifacts and projects for semantic correlation.

## Structure

```
├── signals/
│   ├── library/    # Signals from Library artifacts
│   └── lab/        # Signals from Lab projects
├── embeddings/     # Vector embeddings for similarity search
├── scripts/        # Correlation and indexing scripts
└── index.json      # Master signal index
```

## Signal Format

```json
{{
  "id": "library.epiphanies.oracle-machines",
  "type": "artifact",
  "source": "library",
  "category": "epiphany",
  "title": "Oracle Machines and AI Intuition",
  "domain_tags": ["ai", "turing", "theory"],
  "intent": "Exploring the connection between Turing's oracle machines and modern AI",
  "key_phrases": ["oracle machine", "intuition engine"],
  "path": "epiphanies/2026-01-07-oracle-machines.md",
  "created": "2026-01-07T15:30:00Z",
  "embedding_ref": "embeddings/library.epiphanies.oracle-machines.vec"
}}
```

## Correlation Thresholds

| Score | Recommendation |
|-------|----------------|
| < 70% | CREATE new |
| 70-90% | SUGGEST (human review) |
| > 90% | AUTO-APPEND |

## Usage

Listen is queried by [Legato.Conduct](https://github.com/{org}/Legato.Conduct) during transcript processing to prevent duplication and find related content.

---
*Part of the LEGATO system*
"""

    create_file(gh, repo_name, "README.md", readme, "Initialize Listen", dry_run)

    # Index
    create_file(gh, repo_name, "index.json", "{}", "Initialize index", dry_run)

    # Signal directories
    create_file(
        gh, repo_name, "signals/library/.gitkeep", "# Library signals\n",
        "Create library signals directory", dry_run
    )
    create_file(
        gh, repo_name, "signals/lab/.gitkeep", "# Lab signals\n",
        "Create lab signals directory", dry_run
    )
    create_file(
        gh, repo_name, "embeddings/.gitkeep", "# Vector embeddings\n",
        "Create embeddings directory", dry_run
    )

    # Register signal workflow
    register_workflow = """name: Register Signal

on:
  workflow_dispatch:
    inputs:
      artifact_path:
        description: 'Path to artifact in source repo'
        required: true
        type: string
      source_repo:
        description: 'Source repository'
        required: true
        type: string
  repository_dispatch:
    types: [register-signal]

jobs:
  register:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install requests numpy pyyaml

      - name: Fetch artifact metadata
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ARTIFACT_PATH: ${{ github.event.inputs.artifact_path || github.event.client_payload.artifact_path }}
          SOURCE_REPO: ${{ github.event.inputs.source_repo || github.event.client_payload.source_repo }}
        run: |
          echo "Fetching: ${SOURCE_REPO}/${ARTIFACT_PATH}"
          gh api "/repos/${SOURCE_REPO}/contents/${ARTIFACT_PATH}" --jq '.content' | base64 -d > artifact.md

      - name: Extract and register signal
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python scripts/register.py --input artifact.md

      - name: Commit updated index
        run: |
          git config user.name "LEGATO Bot"
          git config user.email "legato@users.noreply.github.com"
          git add index.json signals/
          git diff --staged --quiet || git commit -m "Register signal: ${{ github.event.inputs.artifact_path }}"
          git push
"""

    create_file(
        gh, repo_name, ".github/workflows/register-signal.yml", register_workflow,
        "Add register signal workflow", dry_run
    )

    # Correlate workflow
    correlate_workflow = """name: Correlate

on:
  workflow_dispatch:
    inputs:
      query_json:
        description: 'Signal metadata to correlate'
        required: true
        type: string
  repository_dispatch:
    types: [correlate-request]

jobs:
  correlate:
    runs-on: ubuntu-latest
    outputs:
      result_json: ${{ steps.correlate.outputs.result }}
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install numpy requests

      - name: Run correlation
        id: correlate
        env:
          QUERY_JSON: ${{ github.event.inputs.query_json || github.event.client_payload.query_json }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python scripts/correlate.py --query "${QUERY_JSON}" --output result.json
          echo "result=$(cat result.json | jq -c .)" >> $GITHUB_OUTPUT
"""

    create_file(
        gh, repo_name, ".github/workflows/correlate.yml", correlate_workflow,
        "Add correlate workflow", dry_run
    )

    # Reindex workflow
    reindex_workflow = """name: Reindex

on:
  workflow_dispatch:

jobs:
  reindex:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install numpy requests

      - name: Rebuild index
        env:
          GH_TOKEN: ${{ secrets.LIBRARY_PAT }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python scripts/reindex.py

      - name: Commit updated index
        run: |
          git config user.name "LEGATO Bot"
          git config user.email "legato@users.noreply.github.com"
          git add index.json signals/ embeddings/
          git diff --staged --quiet || git commit -m "Reindex complete: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
          git push
"""

    create_file(
        gh, repo_name, ".github/workflows/reindex.yml", reindex_workflow,
        "Add reindex workflow", dry_run
    )

    # Scripts
    register_script = '''#!/usr/bin/env python3
"""Register a signal from an artifact."""

import os
import sys
import json
import re
import argparse
from datetime import datetime
from pathlib import Path

def extract_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter from markdown."""
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    import yaml
    try:
        frontmatter = yaml.safe_load(parts[1])
    except:
        frontmatter = {}

    return frontmatter or {}, parts[2].strip()

def generate_embedding(text: str) -> list[float]:
    """Generate embedding using OpenAI API."""
    import requests

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return []

    response = requests.post(
        "https://api.openai.com/v1/embeddings",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "text-embedding-3-small", "input": text}
    )

    if response.status_code == 200:
        return response.json()["data"][0]["embedding"]
    return []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input artifact file")
    args = parser.parse_args()

    content = Path(args.input).read_text()
    frontmatter, body = extract_frontmatter(content)

    signal_id = frontmatter.get("id", f"unknown.{datetime.now().strftime('%Y%m%d%H%M%S')}")

    signal = {
        "id": signal_id,
        "type": "artifact",
        "source": "library",
        "category": frontmatter.get("category", "unknown"),
        "title": frontmatter.get("title", "Untitled"),
        "domain_tags": frontmatter.get("domain_tags", []),
        "intent": body[:200].replace("\\n", " ").strip(),
        "key_phrases": frontmatter.get("key_phrases", []),
        "path": args.input,
        "created": frontmatter.get("created", datetime.utcnow().isoformat() + "Z"),
        "updated": datetime.utcnow().isoformat() + "Z",
    }

    # Generate embedding
    embed_text = f"{signal['title']} {signal['intent']} {' '.join(signal['key_phrases'])}"
    embedding = generate_embedding(embed_text)

    if embedding:
        import numpy as np
        embed_path = f"embeddings/{signal_id.replace('.', '-')}.npy"
        np.save(embed_path, np.array(embedding))
        signal["embedding_ref"] = embed_path

    # Update index
    index_path = Path("index.json")
    index = json.loads(index_path.read_text()) if index_path.exists() else {}
    index[signal_id] = signal
    index_path.write_text(json.dumps(index, indent=2))

    # Save full signal
    signal_path = Path(f"signals/library/{signal_id.split('.')[-1]}.json")
    signal_path.parent.mkdir(parents=True, exist_ok=True)
    signal_path.write_text(json.dumps(signal, indent=2))

    print(f"Registered: {signal_id}")

if __name__ == "__main__":
    main()
'''

    create_file(gh, repo_name, "scripts/register.py", register_script, "Add register script", dry_run)

    correlate_script = '''#!/usr/bin/env python3
"""Find correlated signals."""

import os
import sys
import json
import argparse
from pathlib import Path

import numpy as np

def cosine_similarity(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def generate_embedding(text: str) -> list[float]:
    """Generate embedding using OpenAI API."""
    import requests

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return []

    response = requests.post(
        "https://api.openai.com/v1/embeddings",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "text-embedding-3-small", "input": text}
    )

    if response.status_code == 200:
        return response.json()["data"][0]["embedding"]
    return []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True, help="Query JSON")
    parser.add_argument("--output", required=True, help="Output file")
    args = parser.parse_args()

    query = json.loads(args.query)
    query_text = f"{query.get('title', '')} {query.get('intent', '')} {' '.join(query.get('key_phrases', []))}"

    query_embedding = generate_embedding(query_text)
    if not query_embedding:
        result = {"matches": [], "top_score": 0, "recommendation": "CREATE", "suggested_target": None}
        Path(args.output).write_text(json.dumps(result, indent=2))
        return

    index = json.loads(Path("index.json").read_text()) if Path("index.json").exists() else {}

    scores = []
    for signal_id, signal in index.items():
        if "embedding_ref" not in signal:
            continue
        try:
            stored = np.load(signal["embedding_ref"])
            score = cosine_similarity(query_embedding, stored)
            scores.append({"signal_id": signal_id, "score": score, "title": signal["title"], "path": signal["path"]})
        except:
            continue

    scores.sort(key=lambda x: x["score"], reverse=True)
    matches = scores[:5]
    top_score = matches[0]["score"] if matches else 0

    if top_score < 0.70:
        recommendation = "CREATE"
    elif top_score < 0.90:
        recommendation = "SUGGEST"
    else:
        recommendation = "AUTO-APPEND"

    result = {
        "matches": matches,
        "top_score": top_score,
        "recommendation": recommendation,
        "suggested_target": matches[0]["signal_id"] if matches else None
    }

    Path(args.output).write_text(json.dumps(result, indent=2))
    print(f"Correlation: {recommendation} (score: {top_score:.2f})")

if __name__ == "__main__":
    main()
'''

    create_file(gh, repo_name, "scripts/correlate.py", correlate_script, "Add correlate script", dry_run)

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap the LEGATO system repositories"
    )
    parser.add_argument(
        "--org",
        default="Legato",
        help="GitHub organization or username"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without actually creating"
    )
    parser.add_argument(
        "--conduct-only",
        action="store_true",
        help="Only bootstrap Conduct"
    )
    parser.add_argument(
        "--library-only",
        action="store_true",
        help="Only bootstrap Library"
    )
    parser.add_argument(
        "--listen-only",
        action="store_true",
        help="Only bootstrap Listen"
    )
    parser.add_argument(
        "--skip-conduct",
        action="store_true",
        help="Skip Conduct (only create Library and Listen)"
    )
    args = parser.parse_args()

    # Initialize GitHub client
    gh = None
    if not args.dry_run:
        try:
            gh = get_github_client()
            # Verify authentication
            gh.get_user().login
        except Exception as e:
            print(f"Error: Failed to authenticate with GitHub: {e}", file=sys.stderr)
            print("Set GH_TOKEN or GITHUB_TOKEN environment variable.", file=sys.stderr)
            sys.exit(1)

    print("=" * 50)
    print("LEGATO System Bootstrap")
    print("=" * 50)
    print(f"Organization: {args.org}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print()
    print("Repositories to create:")

    only_one = args.conduct_only or args.library_only or args.listen_only

    will_conduct = (args.conduct_only or not only_one) and not args.skip_conduct
    will_library = args.library_only or (not only_one and not args.conduct_only)
    will_listen = args.listen_only or (not only_one and not args.conduct_only)

    if will_conduct:
        print(f"  - {args.org}/Legato.Conduct (orchestrator)")
    if will_library:
        print(f"  - {args.org}/Legato.Library (knowledge store)")
    if will_listen:
        print(f"  - {args.org}/Legato.Listen (semantic brain)")

    print("=" * 50)

    success = True

    # Bootstrap in order: Conduct first, then Library, then Listen
    if will_conduct:
        if not bootstrap_conduct(gh, args.org, args.dry_run):
            success = False

    if will_library:
        if not bootstrap_library(gh, args.org, args.dry_run):
            success = False

    if will_listen:
        if not bootstrap_listen(gh, args.org, args.dry_run):
            success = False

    print()
    print("=" * 50)
    if success:
        print("Bootstrap complete!")
        if not args.dry_run:
            print()
            print("Your LEGATO system is ready!")
            print()
            print("Repositories created:")
            if will_conduct:
                print(f"  https://github.com/{args.org}/Legato.Conduct")
            if will_library:
                print(f"  https://github.com/{args.org}/Legato.Library")
            if will_listen:
                print(f"  https://github.com/{args.org}/Legato.Listen")
            print()
            print("Next steps:")
            print(f"  1. Configure secrets in {args.org}/Legato.Conduct:")
            print("     - ANTHROPIC_API_KEY (required)")
            print("     - OPENAI_API_KEY (for embeddings, optional)")
            print("     - LIBRARY_PAT, LISTEN_PAT, LAB_PAT (can be same token)")
            print()
            print("  2. Clone and use:")
            print(f"     git clone https://github.com/{args.org}/Legato.Conduct")
            print("     cd Legato.Conduct")
            print("     ./legato process 'Your transcript here'")
    else:
        print("Bootstrap completed with errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
