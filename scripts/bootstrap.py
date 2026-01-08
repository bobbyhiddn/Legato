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
"""

import os
import sys
import json
import argparse
import subprocess
import base64
import shutil
import tempfile
from pathlib import Path
from datetime import datetime


def run_gh(args: list, check: bool = True) -> subprocess.CompletedProcess:
    """Run a gh CLI command."""
    result = subprocess.run(["gh"] + args, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
    return result


def repo_exists(repo: str) -> bool:
    """Check if a repository exists."""
    result = run_gh(["repo", "view", repo, "--json", "name"], check=False)
    return result.returncode == 0


def create_repo(repo: str, description: str, dry_run: bool = False) -> bool:
    """Create a repository."""
    if dry_run:
        print(f"  [DRY RUN] Would create: {repo}")
        return True

    if repo_exists(repo):
        print(f"  [EXISTS] {repo}")
        return True

    result = run_gh([
        "repo", "create", repo,
        "--public",
        "--description", description
    ])

    if result.returncode == 0:
        print(f"  [CREATED] {repo}")
        return True
    else:
        print(f"  [FAILED] {repo}: {result.stderr}")
        return False


def create_file(repo: str, path: str, content: str, message: str, dry_run: bool = False) -> bool:
    """Create a file in a repository."""
    if dry_run:
        print(f"  [DRY RUN] Would create: {repo}/{path}")
        return True

    content_b64 = base64.b64encode(content.encode()).decode()

    result = run_gh([
        "api", "--method", "PUT",
        f"/repos/{repo}/contents/{path}",
        "-f", f"message={message}",
        "-f", f"content={content_b64}"
    ], check=False)

    if result.returncode == 0:
        print(f"  [CREATED] {path}")
        return True
    elif "sha" in result.stderr:
        print(f"  [EXISTS] {path}")
        return True
    else:
        print(f"  [FAILED] {path}: {result.stderr}")
        return False


def get_seed_dir() -> Path:
    """Get the directory containing the seed files (this repo)."""
    # bootstrap.py is in scripts/, so parent.parent is repo root
    return Path(__file__).parent.parent


def bootstrap_conduct(org: str, dry_run: bool = False) -> bool:
    """Bootstrap Legato.Conduct repository from seed files."""
    repo = f"{org}/Legato.Conduct"
    print(f"\nBootstrapping {repo}...")

    if not create_repo(repo, "LEGATO Orchestrator - Voice transcripts to knowledge and projects", dry_run):
        return False

    if dry_run:
        seed_dir = get_seed_dir()
        # List what would be copied
        for item in seed_dir.rglob("*"):
            if ".git" in item.parts:
                continue
            if item.is_file():
                rel_path = item.relative_to(seed_dir)
                print(f"  [DRY RUN] Would copy: {rel_path}")
        return True

    # Clone the new repo, copy files, push
    seed_dir = get_seed_dir()

    with tempfile.TemporaryDirectory() as tmpdir:
        clone_dir = Path(tmpdir) / "conduct"

        # Clone the empty repo
        result = subprocess.run(
            ["gh", "repo", "clone", repo, str(clone_dir)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            # Repo might be empty, try to initialize it
            clone_dir.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init"], cwd=clone_dir, check=True)
            subprocess.run(
                ["git", "remote", "add", "origin", f"https://github.com/{repo}.git"],
                cwd=clone_dir,
                check=True
            )

        # Copy all files from seed dir (excluding .git)
        for item in seed_dir.iterdir():
            if item.name == ".git":
                continue
            dest = clone_dir / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

        # Update README to reflect it's the deployed version
        readme_path = clone_dir / "README.md"
        if readme_path.exists():
            content = readme_path.read_text()
            # Add deployment notice at the top
            notice = f"""# Legato.Conduct

> **Deployed LEGATO Orchestrator** - Part of the [{org}](https://github.com/{org}) LEGATO system.

---

"""
            # Find where the actual content starts (after the title)
            if content.startswith("# LEGATO Specification"):
                content = notice + content
                readme_path.write_text(content)

        # Commit and push
        subprocess.run(["git", "add", "."], cwd=clone_dir, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initialize Legato.Conduct from seed"],
            cwd=clone_dir,
            capture_output=True
        )

        # Push (handle both main and master)
        result = subprocess.run(
            ["git", "push", "-u", "origin", "main"],
            cwd=clone_dir,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            subprocess.run(
                ["git", "branch", "-M", "main"],
                cwd=clone_dir,
                check=True
            )
            subprocess.run(
                ["git", "push", "-u", "origin", "main"],
                cwd=clone_dir,
                check=True
            )

        print(f"  [DEPLOYED] All files pushed to {repo}")

    return True


def bootstrap_library(org: str, dry_run: bool = False) -> bool:
    """Bootstrap Legato.Library repository."""
    repo = f"{org}/Legato.Library"
    print(f"\nBootstrapping {repo}...")

    if not create_repo(repo, "LEGATO Knowledge Store - Structured knowledge artifacts", dry_run):
        return False

    # README
    readme = """# Legato.Library

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
id: library.{category}.{slug}
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
""".replace("{org}", org)

    create_file(repo, "README.md", readme, "Initialize Library", dry_run)

    # Index
    create_file(repo, "index.json", "{}", "Initialize index", dry_run)

    # Category directories with .gitkeep
    categories = ["epiphanies", "concepts", "reflections", "glimmers", "reminders", "worklog"]
    for cat in categories:
        create_file(repo, f"{cat}/.gitkeep", f"# {cat.title()}\n", f"Create {cat} directory", dry_run)

    # Workflow to register signals
    workflow = """name: Register Signal

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
          GH_TOKEN: ${{ secrets.LISTEN_PAT }}
        run: |
          for file in ${{ steps.changes.outputs.files }}; do
            echo "Registering signal for: ${file}"
            # Trigger Listen to index new artifact
            gh workflow run register-signal.yml \\
              --repo """ + org + """/Legato.Listen \\
              -f artifact_path="${file}" \\
              -f source_repo="${GITHUB_REPOSITORY}" || true
          done
"""

    create_file(repo, ".github/workflows/register-signal.yml", workflow, "Add signal registration workflow", dry_run)

    return True


def bootstrap_listen(org: str, dry_run: bool = False) -> bool:
    """Bootstrap Legato.Listen repository."""
    repo = f"{org}/Legato.Listen"
    print(f"\nBootstrapping {repo}...")

    if not create_repo(repo, "LEGATO Semantic Brain - Correlation and indexing", dry_run):
        return False

    # README
    readme = """# Legato.Listen

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
{
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
}
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
""".replace("{org}", org)

    create_file(repo, "README.md", readme, "Initialize Listen", dry_run)

    # Index
    create_file(repo, "index.json", "{}", "Initialize index", dry_run)

    # Signal directories
    create_file(repo, "signals/library/.gitkeep", "# Library signals\n", "Create library signals directory", dry_run)
    create_file(repo, "signals/lab/.gitkeep", "# Lab signals\n", "Create lab signals directory", dry_run)
    create_file(repo, "embeddings/.gitkeep", "# Vector embeddings\n", "Create embeddings directory", dry_run)

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
        run: pip install requests numpy

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

    create_file(repo, ".github/workflows/register-signal.yml", register_workflow, "Add register signal workflow", dry_run)

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

    create_file(repo, ".github/workflows/correlate.yml", correlate_workflow, "Add correlate workflow", dry_run)

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

    create_file(repo, ".github/workflows/reindex.yml", reindex_workflow, "Add reindex workflow", dry_run)

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

    signal_id = frontmatter.get("id", f"unknown.{datetime.now().strftime(\'%Y%m%d%H%M%S\')}")

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
    embed_text = f"{signal[\'title\']} {signal[\'intent\']} {' '.join(signal[\'key_phrases\'])}"
    embedding = generate_embedding(embed_text)

    if embedding:
        import numpy as np
        embed_path = f"embeddings/{signal_id.replace(\'.\', \'-\')}.npy"
        np.save(embed_path, np.array(embedding))
        signal["embedding_ref"] = embed_path

    # Update index
    index_path = Path("index.json")
    index = json.loads(index_path.read_text()) if index_path.exists() else {}
    index[signal_id] = signal
    index_path.write_text(json.dumps(index, indent=2))

    # Save full signal
    signal_path = Path(f"signals/library/{signal_id.split(\'.\')[-1]}.json")
    signal_path.parent.mkdir(parents=True, exist_ok=True)
    signal_path.write_text(json.dumps(signal, indent=2))

    print(f"Registered: {signal_id}")

if __name__ == "__main__":
    main()
'''

    create_file(repo, "scripts/register.py", register_script, "Add register script", dry_run)

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
    query_text = f"{query.get(\'title\', \'\')} {query.get(\'intent\', \'\')} {' '.join(query.get(\'key_phrases\', []))}"

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

    create_file(repo, "scripts/correlate.py", correlate_script, "Add correlate script", dry_run)

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

    # Check for gh CLI (skip for dry-run to allow previewing)
    if not args.dry_run:
        try:
            result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
            if result.returncode != 0:
                print("Error: Not authenticated with GitHub CLI", file=sys.stderr)
                print("Run: gh auth login", file=sys.stderr)
                sys.exit(1)
        except FileNotFoundError:
            print("Error: GitHub CLI (gh) not found", file=sys.stderr)
            print("Install from: https://cli.github.com/", file=sys.stderr)
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
        if not bootstrap_conduct(args.org, args.dry_run):
            success = False

    if will_library:
        if not bootstrap_library(args.org, args.dry_run):
            success = False

    if will_listen:
        if not bootstrap_listen(args.org, args.dry_run):
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
