# LEGATO Specification v0.3

> **Voice transcripts → structured knowledge + executable projects**

This specification defines LEGATO, a GitHub-native framework for processing voice transcripts into knowledge artifacts and executable projects using Claude AI for intelligence and GitHub Copilot Coding Agent for autonomous implementation.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Repository Structures](#2-repository-structures)
3. [Workflow Specifications](#3-workflow-specifications)
4. [Classification Engine](#4-classification-engine)
5. [Correlation Engine](#5-correlation-engine)
6. [Copilot Integration](#6-copilot-integration)
7. [Bootstrapping Guide](#7-bootstrapping-guide)

---

# 1. System Overview

> **"Jarvis in post"** — Voice transcripts → structured knowledge + executable projects, all through GitHub.

## Executive Summary

LEGATO transforms voice captures into two outputs:
1. **Knowledge artifacts** → committed directly to `Legato.Library`
2. **Project tasks** → GitHub Issues assigned to `@copilot` in `Legato.Lab/*`

The entire system runs on GitHub Actions with Claude API for intelligence and GitHub Copilot Coding Agent for code execution.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LEGATO ORGANIZATION                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐      │
│  │  Legato.Conduct  │    │  Legato.Library  │    │  Legato.Listen   │      │
│  │  ═══════════════ │    │  ═══════════════ │    │  ═══════════════ │      │
│  │  • Entry point   │───▶│  • /epiphanies   │◀───│  • /signals      │      │
│  │  • Orchestration │    │  • /concepts     │    │  • /embeddings   │      │
│  │  • Classification│    │  • /reflections  │    │  • Correlation   │      │
│  │  • Routing       │    │  • /glimmers     │    │                  │      │
│  └────────┬─────────┘    │  • /reminders    │    └────────▲─────────┘      │
│           │              │  • /worklog      │             │                 │
│           │              └──────────────────┘             │                 │
│           │                                               │                 │
│           │         ┌────────────────────────────────────┘                 │
│           │         │                                                       │
│           ▼         ▼                                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        Legato.Lab/                                    │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │  │
│  │  │ project-a.Note  │  │ project-b.Chord │  │ project-c.Note  │       │  │
│  │  │ (simple scope)  │  │ (complex scope) │  │ (simple scope)  │       │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Core Repositories

| Repository | Purpose | Key Responsibility |
|------------|---------|-------------------|
| **Legato.Conduct** | Orchestrator | Sole entry point. Receives transcripts, classifies, routes |
| **Legato.Library** | Knowledge Store | Accumulates structured knowledge artifacts |
| **Legato.Listen** | Semantic Brain | Indexes artifacts/projects, provides correlation |
| **Legato.Lab/*** | Project Repos | Spawned repositories for code projects |

## Data Flow

```
┌─────────────────┐
│ Voice Transcript │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Legato.Conduct                           │
│  ┌───────────┐    ┌──────────────┐    ┌─────────────────┐  │
│  │   Parse   │───▶│   Classify   │───▶│ Check Correlation│  │
│  │  Threads  │    │   Threads    │    │   (via Listen)   │  │
│  └───────────┘    └──────────────┘    └────────┬────────┘  │
└────────────────────────────────────────────────┼────────────┘
                                                  │
                    ┌─────────────────────────────┴─────────────────────────────┐
                    │                                                           │
                    ▼                                                           ▼
        ┌───────────────────────┐                             ┌───────────────────────┐
        │ type == "KNOWLEDGE"   │                             │ type == "PROJECT"     │
        └───────────┬───────────┘                             └───────────┬───────────┘
                    │                                                     │
                    ▼                                                     ▼
        ┌───────────────────────┐                             ┌───────────────────────┐
        │  Extract & Format     │                             │  Spawn Lab Repo       │
        │  Artifact             │                             │  from Template        │
        └───────────┬───────────┘                             └───────────┬───────────┘
                    │                                                     │
                    ▼                                                     ▼
        ┌───────────────────────┐                             ┌───────────────────────┐
        │  Commit to Library    │                             │  Create Issue         │
        │  (direct push)        │                             │  with Tasker Body     │
        └───────────┬───────────┘                             └───────────┬───────────┘
                    │                                                     │
                    ▼                                                     ▼
        ┌───────────────────────┐                             ┌───────────────────────┐
        │  Register Signal      │                             │  Assign to @copilot   │
        │  in Listen            │                             │  (via GraphQL)        │
        └───────────────────────┘                             └───────────┬───────────┘
                                                                          │
                                                                          ▼
                                                              ┌───────────────────────┐
                                                              │  Copilot Creates PR   │
                                                              │  (autonomous)         │
                                                              └───────────────────────┘
```

## Key Design Decisions

### GitHub-Native
Everything lives in GitHub. No self-hosted runners for AI. Copilot executes all code tasks.

### Conduct as Entry Point
Users only interact with Conduct. Everything else is orchestrated internally.

### Semantic Awareness
Listen correlates everything before create/append decisions to prevent duplication.

### Differential Processing
- **Knowledge** → Direct commit to Library
- **Projects** → Issue creation + Copilot assignment

### Template-Based Spawning
Lab repos created from templates with pre-configured workflows and instructions.

## API Requirements

| API | Purpose | Authentication |
|-----|---------|----------------|
| GitHub GraphQL | Assign issues to @copilot, create repos, manage PRs | PAT with `repo` scope |
| GitHub REST | Create issues, commit to Library | PAT with `repo` scope |
| Claude API | Transcript parsing/classification | Anthropic API key |
| Embeddings API | Semantic search in Listen | OpenAI or Anthropic key |

## Tagging Convention

| Tag | Meaning |
|-----|---------|
| `legato:note` | Simple project (single PR) |
| `legato:chord` | Complex project (multi-PR) |
| `legato:spawned` | Created by LEGATO system |
| `legato:v{X}` | System version |
| `legato:transcript:{id}` | Source transcript link |

## Success Criteria

| Phase | Milestone |
|-------|-----------|
| **Phase 1 (MVP)** | Clone Conduct → run CLI → paste transcript → knowledge in Library + project issue in Lab → Copilot creates PR |
| **Phase 2 (Correlation)** | Listen indexes all signals, correlation decisions >80% accurate |
| **Phase 3 (Automation)** | `workflow_dispatch` trigger, full hands-off transcript → PR → review |
| **Phase 4 (Webapp)** | Browser intake, status dashboard, authorization queue |

---

# 2. Repository Structures

## 2.1 `Legato.Conduct` — The Orchestrator

**Purpose**: Sole entry point. Receives transcripts, classifies content, routes to appropriate destinations.

```
Legato.Conduct/
├── .github/
│   └── workflows/
│       ├── process-transcript.yml          # Main intake (webhook + dispatch)
│       ├── process-transcript-continue.yml # Comment-triggered continuation
│       ├── spawn-project.yml               # Creates Lab repos from template
│       └── correlate.yml                   # Calls Listen for semantic matching
├── prompts/
│   ├── classifier.md                       # Thread classification instructions
│   ├── knowledge-extractor.md              # Extract knowledge artifacts
│   ├── project-planner.md                  # Generate project specs
│   ├── tasker-template.md                  # Issue body for Copilot
│   └── signal-extractor.md                 # Generate signal metadata
├── templates/
│   ├── note/                               # .Note repo template
│   │   ├── README.md
│   │   ├── SIGNAL.md
│   │   ├── copilot-instructions.md
│   │   └── .github/workflows/
│   └── chord/                              # .Chord repo template
│       ├── README.md
│       ├── SIGNAL.md
│       ├── copilot-instructions.md
│       ├── /init/
│       ├── /plans/
│       ├── /docs/
│       └── .github/workflows/
├── scripts/
│   ├── parse_transcript.py                 # Thread segmentation
│   ├── call_claude.py                      # Claude API wrapper
│   ├── commit_to_library.py                # Push artifacts
│   ├── assign_copilot.py                   # GraphQL for @copilot assignment
│   └── query_listen.py                     # Correlation check
├── legato                                  # CLI entry point
├── package/
│   └── legato/
│       ├── __init__.py
│       ├── classifier.py
│       ├── knowledge.py
│       ├── projects.py
│       └── correlation.py
└── README.md
```

## 2.2 `Legato.Library` — The Knowledge Store

**Purpose**: Accumulates structured knowledge artifacts. Direct commits from Conduct.

```
Legato.Library/
├── .github/
│   └── workflows/
│       └── register-signal.yml             # Triggers Listen on new artifacts
├── epiphanies/                             # Major insights, breakthrough ideas
│   └── YYYY-MM-DD-{slug}.md
├── concepts/                               # Technical concepts, definitions
│   └── YYYY-MM-DD-{slug}.md
├── reflections/                            # Personal thoughts, observations
│   └── YYYY-MM-DD-{slug}.md
├── glimmers/                               # Quick ideas, seeds for future
│   └── YYYY-MM-DD-{slug}.md
├── reminders/                              # Action items, follow-ups
│   └── YYYY-MM-DD-{slug}.md
├── worklog/                                # Daily/session work summaries
│   └── YYYY-MM-DD.md
├── index.json                              # Quick lookup index
└── README.md
```

### Artifact Schema (Frontmatter)

```yaml
---
id: library.{category}.{slug}
title: "Artifact Title"
category: epiphany|concept|reflection|glimmer|reminder|worklog
created: 2026-01-07T15:30:00Z
source_transcript: transcript-2026-01-07-1530
domain_tags: [ai, architecture, claude]
key_phrases: ["oracle machine", "intuition engine"]
correlation_score: 0.0  # Updated by Listen
related: []              # Populated by correlation
---

# Content here...
```

## 2.3 `Legato.Listen` — The Semantic Brain

**Purpose**: Indexes all artifacts and projects. Provides correlation recommendations.

```
Legato.Listen/
├── .github/
│   └── workflows/
│       ├── register-signal.yml             # Index new artifact/project
│       ├── correlate.yml                   # API-style correlation query
│       └── reindex.yml                     # Full reindex (manual trigger)
├── signals/
│   ├── library/                            # Signals from Library artifacts
│   │   └── {artifact-id}.json
│   └── lab/                                # Signals from Lab projects
│       └── {project-id}.json
├── embeddings/
│   └── {signal-id}.vec                     # Vector embeddings
├── scripts/
│   ├── register.py                         # Create/update signal
│   ├── embed.py                            # Generate embeddings
│   ├── correlate.py                        # Find similar signals
│   └── recommend.py                        # CREATE/APPEND/QUEUE decision
├── index.json                              # Signal index for fast lookup
└── README.md
```

### Signal Schema

```json
{
  "id": "library.epiphanies.oracle-machines",
  "type": "artifact",
  "source": "library",
  "category": "epiphany",
  "title": "Oracle Machines and AI Intuition",
  "domain_tags": ["ai", "turing", "theory"],
  "intent": "Exploring the connection between Turing's oracle machines and modern AI as intuition engines",
  "key_phrases": ["oracle machine", "intuition engine", "ordinal logic"],
  "path": "epiphanies/2026-01-07-oracle-machines.md",
  "created": "2026-01-07T15:30:00Z",
  "updated": "2026-01-07T15:30:00Z",
  "embedding_ref": "embeddings/library.epiphanies.oracle-machines.vec"
}
```

## 2.4 `Legato.Lab/{name}.Note` — Simple Project

**Purpose**: Single-PR scope projects. Quick implementations.

```
trading-card-bot.Note/
├── .github/
│   └── workflows/
│       └── on-issue-assigned.yml           # Triggers when Copilot assigned
├── README.md                               # Generated project overview
├── SIGNAL.md                               # Project intent and context
├── copilot-instructions.md                 # Coding guidelines for Copilot
├── plans/
│   └── initial.md                          # Implementation plan
└── src/                                    # Code goes here
```

## 2.5 `Legato.Lab/{name}.Chord` — Complex Project

**Purpose**: Multi-PR scope projects. Larger implementations with phases.

```
hermit-agent.Chord/
├── .github/
│   └── workflows/
│       ├── on-issue-assigned.yml
│       └── phase-complete.yml              # Triggers next phase
├── README.md
├── SIGNAL.md
├── copilot-instructions.md
├── init/                                   # Initial setup, bootstrap
│   └── bootstrap.md
├── plans/
│   ├── phase-01-foundation.md
│   ├── phase-02-core.md
│   └── phase-03-integration.md
├── docs/
│   └── architecture.md
├── src/
└── tests/
```

---

# 3. Workflow Specifications

## 3.1 Primary Workflow: `process-transcript.yml`

This is the main entry point, the orchestrator for transcript processing.

```yaml
name: Process Transcript

on:
  workflow_dispatch:
    inputs:
      transcript:
        description: 'Raw transcript text or file path'
        required: true
        type: string
      source:
        description: 'Source identifier (e.g., voice-memo-2026-01-07)'
        required: false
        type: string
  repository_dispatch:
    types: [transcript-received]

permissions:
  contents: write
  issues: write
  pull-requests: write

jobs:
  parse:
    runs-on: ubuntu-latest
    outputs:
      threads_json: ${{ steps.parse.outputs.threads_json }}
      thread_count: ${{ steps.parse.outputs.thread_count }}
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install deps
        run: pip install -e package/

      - name: Parse transcript into threads
        id: parse
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          TRANSCRIPT: ${{ github.event.inputs.transcript || github.event.client_payload.transcript }}
          SOURCE_ID: ${{ github.event.inputs.source || github.event.client_payload.source }}
        run: |
          python -m legato.classifier --phase parse --output threads.json
          echo "threads_json=$(cat threads.json | jq -c .)" >> $GITHUB_OUTPUT
          echo "thread_count=$(cat threads.json | jq 'length')" >> $GITHUB_OUTPUT

      - name: Upload parsed threads
        uses: actions/upload-artifact@v4
        with:
          name: parsed-threads
          path: threads.json

  classify:
    runs-on: ubuntu-latest
    needs: parse
    outputs:
      routing_json: ${{ steps.classify.outputs.routing_json }}
    steps:
      - uses: actions/checkout@v4

      - name: Download parsed threads
        uses: actions/download-artifact@v4
        with:
          name: parsed-threads

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install deps
        run: pip install -e package/

      - name: Classify threads and check correlation
        id: classify
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          python -m legato.classifier --phase classify --input threads.json --output routing.json
          echo "routing_json=$(cat routing.json | jq -c .)" >> $GITHUB_OUTPUT

      - name: Upload routing decisions
        uses: actions/upload-artifact@v4
        with:
          name: routing-decisions
          path: routing.json

  process-knowledge:
    runs-on: ubuntu-latest
    needs: classify
    if: contains(needs.classify.outputs.routing_json, '"type":"KNOWLEDGE"')
    steps:
      - uses: actions/checkout@v4

      - name: Download routing decisions
        uses: actions/download-artifact@v4
        with:
          name: routing-decisions

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install deps
        run: pip install -e package/

      - name: Extract and commit knowledge artifacts
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GH_TOKEN: ${{ secrets.LIBRARY_PAT }}
        run: |
          python -m legato.knowledge --input routing.json --commit

      - name: Register signals with Listen
        env:
          GH_TOKEN: ${{ secrets.LISTEN_PAT }}
        run: |
          python -m legato.correlation --register-new

  process-projects:
    runs-on: ubuntu-latest
    needs: classify
    if: contains(needs.classify.outputs.routing_json, '"type":"PROJECT"')
    steps:
      - uses: actions/checkout@v4

      - name: Download routing decisions
        uses: actions/download-artifact@v4
        with:
          name: routing-decisions

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install deps
        run: pip install -e package/

      - name: Create projects and assign Copilot
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GH_TOKEN: ${{ secrets.LAB_PAT }}
        run: |
          python -m legato.projects --input routing.json --spawn-and-assign
```

## 3.2 Continuation Workflow: `process-transcript-continue.yml`

For PR-based review and approval via comment triggers.

```yaml
name: Process Transcript (continue)

on:
  issue_comment:
    types: [created]

permissions:
  contents: write
  issues: write
  pull-requests: write

jobs:
  process-comment:
    runs-on: ubuntu-latest
    if: |
      github.event.issue.pull_request &&
      contains(github.event.issue.labels.*.name, 'legato-pending') &&
      (
        github.event.comment.author_association == 'OWNER' ||
        github.event.comment.author_association == 'MEMBER'
      )
    steps:
      - name: Parse comment for action
        id: parse
        env:
          COMMENT_BODY: ${{ github.event.comment.body }}
        run: |
          COMMENT_LOWER="$(echo "${COMMENT_BODY}" | tr '[:upper:]' '[:lower:]' | xargs)"

          if [[ "${COMMENT_LOWER}" =~ ^(approve|lgtm|ship)$ ]]; then
            echo "action=approve" >> $GITHUB_OUTPUT
          elif [[ "${COMMENT_LOWER}" =~ ^(reject|skip)$ ]]; then
            echo "action=reject" >> $GITHUB_OUTPUT
          elif [[ "${COMMENT_LOWER}" =~ ^reclassify ]]; then
            echo "action=reclassify" >> $GITHUB_OUTPUT
          else
            echo "action=revise" >> $GITHUB_OUTPUT
          fi

      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.ref }}

      - name: Handle approval
        if: steps.parse.outputs.action == 'approve'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh pr merge --squash --delete-branch
          gh pr edit --remove-label "legato-pending"

      - name: Handle rejection
        if: steps.parse.outputs.action == 'reject'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          gh pr close
          gh pr edit --remove-label "legato-pending"

      - name: Handle reclassification
        if: steps.parse.outputs.action == 'reclassify'
        run: |
          echo "Triggering reclassification workflow..."

      - name: Handle revision request
        if: steps.parse.outputs.action == 'revise'
        run: |
          echo "Processing revision request: ${COMMENT_BODY}"
```

## 3.3 Spawn Project Workflow: `spawn-project.yml`

Creates new Lab repositories from templates and assigns to Copilot.

```yaml
name: Spawn Project

on:
  workflow_call:
    inputs:
      project_name:
        required: true
        type: string
      project_type:
        required: true
        type: string  # "note" or "chord"
      signal_json:
        required: true
        type: string
      tasker_body:
        required: true
        type: string

jobs:
  spawn:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Create repository from template
        env:
          GH_TOKEN: ${{ secrets.LAB_PAT }}
          PROJECT_NAME: ${{ inputs.project_name }}
          PROJECT_TYPE: ${{ inputs.project_type }}
        run: |
          TEMPLATE_REPO="Legato/Legato.Conduct"
          TEMPLATE_PATH="templates/${PROJECT_TYPE}"
          NEW_REPO="Legato/Lab.${PROJECT_NAME}"

          gh repo create "${NEW_REPO}" \
            --template "${TEMPLATE_REPO}" \
            --public \
            --clone

      - name: Write SIGNAL.md
        env:
          SIGNAL_JSON: ${{ inputs.signal_json }}
        run: |
          echo "${SIGNAL_JSON}" | python -c "
          import json, sys
          signal = json.load(sys.stdin)
          print(f'''# {signal['title']}

          ## Intent
          {signal['intent']}

          ## Domain Tags
          {', '.join(signal['domain_tags'])}

          ## Key Phrases
          {', '.join(signal['key_phrases'])}

          ## Source
          - Transcript: {signal.get('source_transcript', 'N/A')}
          - Created: {signal['created']}
          ''')
          " > SIGNAL.md

      - name: Create initial issue for Copilot
        id: create-issue
        env:
          GH_TOKEN: ${{ secrets.LAB_PAT }}
          TASKER_BODY: ${{ inputs.tasker_body }}
          PROJECT_NAME: ${{ inputs.project_name }}
        run: |
          ISSUE_URL=$(gh issue create \
            --repo "Legato/Lab.${PROJECT_NAME}" \
            --title "Initial Implementation" \
            --body "${TASKER_BODY}" \
            --label "copilot-task,legato:spawned")
          
          ISSUE_NUMBER=$(echo "${ISSUE_URL}" | grep -oE '[0-9]+$')
          echo "issue_number=${ISSUE_NUMBER}" >> $GITHUB_OUTPUT

      - name: Assign issue to Copilot
        env:
          GH_TOKEN: ${{ secrets.LAB_PAT }}
          PROJECT_NAME: ${{ inputs.project_name }}
          ISSUE_NUMBER: ${{ steps.create-issue.outputs.issue_number }}
        run: |
          python scripts/assign_copilot.py \
            --repo "Legato/Lab.${PROJECT_NAME}" \
            --issue "${ISSUE_NUMBER}"
```

## 3.4 Listen Correlation Workflow: `correlate.yml`

API-style workflow for semantic correlation queries.

```yaml
# .github/workflows/correlate.yml (in Legato.Listen)

name: Correlate

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

      - name: Install deps
        run: |
          pip install numpy sentence-transformers

      - name: Run correlation
        id: correlate
        env:
          QUERY_JSON: ${{ github.event.inputs.query_json || github.event.client_payload.query_json }}
        run: |
          python scripts/correlate.py --query "${QUERY_JSON}" --output result.json
          echo "result=$(cat result.json | jq -c .)" >> $GITHUB_OUTPUT
```

## 3.5 Workflow Job Summary

| Job | Purpose | Triggers |
|-----|---------|----------|
| `parse` | Segment transcript into threads | Main workflow start |
| `classify` | Classify threads, check correlation | After parse |
| `process-knowledge` | Extract artifacts, commit to Library | If KNOWLEDGE threads exist |
| `process-projects` | Spawn repos, create issues, assign Copilot | If PROJECT threads exist |
| `process-comment` | Handle PR review commands | Issue comment on legato-pending PRs |
| `spawn` | Create Lab repo, write SIGNAL.md, create issue | Called by process-projects |
| `correlate` | Find similar signals in Listen index | Repository dispatch or manual |

---

# 4. Classification Engine

## Overview

The classification engine transforms raw voice transcripts into structured, actionable items. It operates in two phases: parsing (segmentation) and classification (categorization + routing).

## Thread Types

| Type | Description | Destination |
|------|-------------|-------------|
| `KNOWLEDGE` | Insights, concepts, reflections | Legato.Library |
| `PROJECT` | Things to build/implement | Legato.Lab/* |
| `MIXED` | Contains both elements | Split and route separately |

## Knowledge Categories

| Category | Description | Examples |
|----------|-------------|----------|
| `EPIPHANY` | Major breakthrough or insight | "AI models are oracle machines providing intuition" |
| `CONCEPT` | Technical definition or explanation | "MCP servers work by exposing tools via JSON-RPC" |
| `REFLECTION` | Personal thought or observation | "I've been thinking about how my role has evolved" |
| `GLIMMER` | Quick idea seed for future exploration | "What if we could version prompt templates like code?" |
| `REMINDER` | Action item or follow-up | "Need to follow up with the Pentagon demo prep" |
| `WORKLOG` | Summary of work done | "Today I finished the Espresso MVP integration" |

## Project Scopes

| Scope | Description | Characteristics |
|-------|-------------|-----------------|
| `NOTE` | Simple project | Single PR, quick implementation, minimal architecture |
| `CHORD` | Complex project | Multi-PR, phased implementation, requires planning |

## Classification Schema

```python
# legato/classifier.py

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List

class ThreadType(Enum):
    KNOWLEDGE = "KNOWLEDGE"
    PROJECT = "PROJECT"
    MIXED = "MIXED"

class KnowledgeCategory(Enum):
    EPIPHANY = "epiphany"
    CONCEPT = "concept"
    REFLECTION = "reflection"
    GLIMMER = "glimmer"
    REMINDER = "reminder"
    WORKLOG = "worklog"

class ProjectScope(Enum):
    NOTE = "note"
    CHORD = "chord"

@dataclass
class ClassifiedThread:
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
    correlation_matches: List[dict] = None
    correlation_action: str = "CREATE"  # CREATE, APPEND, QUEUE
    
    # Metadata
    domain_tags: List[str] = None
    key_phrases: List[str] = None
```

## Classification Prompt

```markdown
# prompts/classifier.md

You are classifying segments of a voice transcript for the LEGATO system.

## Your Task

For each thread, determine:

1. **Type**: Is this KNOWLEDGE (an insight, concept, reflection) or PROJECT (something to build/implement)?

2. **If KNOWLEDGE**, categorize as:
   - EPIPHANY: Major breakthrough or insight
   - CONCEPT: Technical definition or explanation
   - REFLECTION: Personal thought or observation
   - GLIMMER: Quick idea seed for future exploration
   - REMINDER: Action item or follow-up
   - WORKLOG: Summary of work done

3. **If PROJECT**, determine:
   - Scope: NOTE (single feature, quick implementation) or CHORD (multi-phase, complex)
   - Name: Suggest a slug-friendly project name

4. **For all**, extract:
   - Domain tags (2-5 relevant topics)
   - Key phrases (distinctive terms that identify this content)
   - Title/summary (one line)

## Classification Signals

### KNOWLEDGE indicators:
- Past tense reflection ("I realized...", "I've been thinking...")
- Conceptual explanation ("The way X works is...")
- Insight framing ("What's interesting is...")
- Action items without implementation scope ("I need to remember...")

### PROJECT indicators:
- Future tense intent ("I want to build...", "We should create...")
- Technical specification ("It should have X, Y, Z features...")
- Implementation details ("Using Python, we could...")
- Scope estimation ("This would take about...")

### Scope determination:
- NOTE: Single feature, <1 day work, no architecture needed
- CHORD: Multiple components, >1 day work, needs design doc

## Output Format

Return JSON array:
```json
[
  {
    "id": "thread-001",
    "type": "KNOWLEDGE",
    "knowledge_category": "epiphany",
    "title": "Oracle Machines as AI Intuition Framework",
    "domain_tags": ["ai", "turing", "theory", "intuition"],
    "key_phrases": ["oracle machine", "intuition engine", "ordinal logic"],
    "description": "Insight connecting Turing's oracle machines to modern AI behavior"
  },
  {
    "id": "thread-002", 
    "type": "PROJECT",
    "project_scope": "note",
    "project_name": "mcp-bedrock-adapter",
    "title": "MCP adapter for AWS Bedrock in classified environments",
    "description": "Build an MCP server that wraps AWS Bedrock API for use in JWICS",
    "domain_tags": ["mcp", "aws", "bedrock", "classified"],
    "key_phrases": ["bedrock adapter", "jwics", "mcp server"]
  }
]
```
```

## Classification Output Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["id", "type", "title", "domain_tags", "key_phrases"],
    "properties": {
      "id": {
        "type": "string",
        "pattern": "^thread-[0-9]{3}$"
      },
      "type": {
        "type": "string",
        "enum": ["KNOWLEDGE", "PROJECT", "MIXED"]
      },
      "title": {
        "type": "string",
        "maxLength": 100
      },
      "description": {
        "type": "string"
      },
      "domain_tags": {
        "type": "array",
        "items": { "type": "string" },
        "minItems": 2,
        "maxItems": 5
      },
      "key_phrases": {
        "type": "array",
        "items": { "type": "string" },
        "minItems": 1
      },
      "knowledge_category": {
        "type": "string",
        "enum": ["epiphany", "concept", "reflection", "glimmer", "reminder", "worklog"]
      },
      "project_scope": {
        "type": "string",
        "enum": ["note", "chord"]
      },
      "project_name": {
        "type": "string",
        "pattern": "^[a-z0-9-]+$"
      }
    }
  }
}
```

## Routing Decision Matrix

| Type | Category/Scope | Correlation | Action |
|------|---------------|-------------|--------|
| KNOWLEDGE | any | <70% | CREATE new artifact in Library |
| KNOWLEDGE | any | 70-90% | SUGGEST append (human review) |
| KNOWLEDGE | any | >90% | AUTO-APPEND to existing |
| PROJECT | note | <70% | CREATE new .Note repo |
| PROJECT | note | >70% | QUEUE for related project |
| PROJECT | chord | <70% | CREATE new .Chord repo |
| PROJECT | chord | 70-90% | SUGGEST as phase (human review) |
| PROJECT | chord | >90% | ADD as phase to existing |
| MIXED | - | - | Split into components, route each |

---

# 5. Correlation Engine

## Overview

The correlation engine (Legato.Listen) provides semantic awareness across all artifacts and projects. It prevents duplication by finding related content and recommending whether to create new items or append to existing ones.

## Correlation Flow

```
New Thread
    │
    ▼
┌─────────────────────────────────────────┐
│ 1. Extract signal metadata              │
│    - domain_tags, key_phrases, intent   │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ 2. Generate embedding                   │
│    - OpenAI text-embedding-3-small      │
│    - Or local sentence-transformers     │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ 3. Query Listen index                   │
│    - Cosine similarity search           │
│    - Return top 5 matches               │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ 4. Make recommendation                  │
│                                         │
│    Score < 70%  → CREATE new            │
│    Score 70-90% → SUGGEST (human review)│
│    Score > 90%  → AUTO-APPEND or QUEUE  │
└─────────────────────────────────────────┘
```

## Signal Schema

Every artifact and project gets a signal registered in Listen.

```json
{
  "id": "library.epiphanies.oracle-machines",
  "type": "artifact",
  "source": "library",
  "category": "epiphany",
  "title": "Oracle Machines and AI Intuition",
  "domain_tags": ["ai", "turing", "theory"],
  "intent": "Exploring the connection between Turing's oracle machines and modern AI as intuition engines",
  "key_phrases": ["oracle machine", "intuition engine", "ordinal logic"],
  "path": "epiphanies/2026-01-07-oracle-machines.md",
  "created": "2026-01-07T15:30:00Z",
  "updated": "2026-01-07T15:30:00Z",
  "embedding_ref": "embeddings/library.epiphanies.oracle-machines.vec"
}
```

### Signal Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (`{source}.{category}.{slug}`) |
| `type` | string | `artifact` or `project` |
| `source` | string | `library` or `lab` |
| `category` | string | Knowledge category or project scope |
| `title` | string | Human-readable title |
| `domain_tags` | array | Topic tags for coarse matching |
| `intent` | string | One-sentence description of purpose |
| `key_phrases` | array | Distinctive terms for fine matching |
| `path` | string | File path relative to source repo |
| `created` | datetime | Creation timestamp |
| `updated` | datetime | Last modification timestamp |
| `embedding_ref` | string | Path to vector embedding file |

## Correlation Query

### Input

```json
{
  "title": "New insight about oracle machines",
  "domain_tags": ["ai", "turing"],
  "key_phrases": ["oracle", "intuition"],
  "intent": "Further thoughts on AI as intuition engine"
}
```

### Output

```json
{
  "query_id": "query-2026-01-07-001",
  "matches": [
    {
      "signal_id": "library.epiphanies.oracle-machines",
      "score": 0.87,
      "title": "Oracle Machines and AI Intuition",
      "path": "epiphanies/2026-01-07-oracle-machines.md"
    },
    {
      "signal_id": "library.concepts.turing-completeness",
      "score": 0.62,
      "title": "Turing Completeness in Modern Systems",
      "path": "concepts/2025-12-15-turing-completeness.md"
    }
  ],
  "top_score": 0.87,
  "recommendation": "SUGGEST",
  "suggested_target": "library.epiphanies.oracle-machines"
}
```

## Recommendation Thresholds

| Score Range | Recommendation | Action |
|-------------|----------------|--------|
| `< 0.70` | `CREATE` | Create new artifact/project |
| `0.70 - 0.90` | `SUGGEST` | Human reviews append decision |
| `> 0.90` | `AUTO-APPEND` | Automatically append to existing |

## Embedding Strategy

### Option 1: OpenAI Embeddings (Cloud)

```python
# scripts/embed.py

import openai

def generate_embedding(text: str) -> list[float]:
    """Generate embedding using OpenAI API."""
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding
```

### Option 2: Local Embeddings (Self-Hosted)

```python
# scripts/embed.py

from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embedding(text: str) -> list[float]:
    """Generate embedding using local model."""
    return model.encode(text).tolist()
```

## Correlation Script

```python
# scripts/correlate.py

import json
import numpy as np
from pathlib import Path
import argparse

def cosine_similarity(a: list, b: list) -> float:
    """Calculate cosine similarity between two vectors."""
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def load_index() -> dict:
    """Load the signal index."""
    with open("index.json") as f:
        return json.load(f)

def load_embedding(ref: str) -> list:
    """Load a stored embedding."""
    with open(ref, "rb") as f:
        return np.load(f).tolist()

def correlate(query: dict, top_k: int = 5) -> dict:
    """Find similar signals to the query."""
    from embed import generate_embedding
    
    # Generate query embedding
    query_text = f"{query['title']} {query['intent']} {' '.join(query['key_phrases'])}"
    query_embedding = generate_embedding(query_text)
    
    # Load index and compute similarities
    index = load_index()
    scores = []
    
    for signal_id, signal in index.items():
        if "embedding_ref" in signal:
            stored_embedding = load_embedding(signal["embedding_ref"])
            score = cosine_similarity(query_embedding, stored_embedding)
            scores.append({
                "signal_id": signal_id,
                "score": score,
                "title": signal["title"],
                "path": signal["path"]
            })
    
    # Sort by score and take top_k
    scores.sort(key=lambda x: x["score"], reverse=True)
    matches = scores[:top_k]
    
    # Determine recommendation
    top_score = matches[0]["score"] if matches else 0
    if top_score < 0.70:
        recommendation = "CREATE"
    elif top_score < 0.90:
        recommendation = "SUGGEST"
    else:
        recommendation = "AUTO-APPEND"
    
    return {
        "matches": matches,
        "top_score": top_score,
        "recommendation": recommendation,
        "suggested_target": matches[0]["signal_id"] if matches else None
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    query = json.loads(args.query)
    result = correlate(query)
    
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)
```

## Signal Registration

When new artifacts or projects are created, they must be registered with Listen.

```python
# scripts/register.py

import json
from datetime import datetime
from pathlib import Path
from embed import generate_embedding

def register_signal(signal: dict) -> None:
    """Register a new signal in the index."""
    
    # Generate embedding
    text = f"{signal['title']} {signal['intent']} {' '.join(signal['key_phrases'])}"
    embedding = generate_embedding(text)
    
    # Save embedding
    embedding_path = f"embeddings/{signal['id']}.vec"
    import numpy as np
    np.save(embedding_path, np.array(embedding))
    
    signal["embedding_ref"] = embedding_path
    signal["created"] = datetime.utcnow().isoformat() + "Z"
    signal["updated"] = signal["created"]
    
    # Update index
    index_path = Path("index.json")
    if index_path.exists():
        with open(index_path) as f:
            index = json.load(f)
    else:
        index = {}
    
    index[signal["id"]] = signal
    
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)
    
    # Save full signal
    signal_dir = Path(f"signals/{signal['source']}")
    signal_dir.mkdir(parents=True, exist_ok=True)
    
    with open(signal_dir / f"{signal['id'].split('.')[-1]}.json", "w") as f:
        json.dump(signal, f, indent=2)
```

## Index Structure

```
Legato.Listen/
├── index.json              # Fast lookup: {signal_id: signal_metadata}
├── signals/
│   ├── library/            # Full signal JSONs from Library
│   │   ├── oracle-machines.json
│   │   └── ...
│   └── lab/                # Full signal JSONs from Lab projects
│       ├── hermit-agent.json
│       └── ...
└── embeddings/
    ├── library.epiphanies.oracle-machines.vec
    └── ...
```

## Reindex Workflow

For rebuilding the entire index (manual trigger).

```yaml
# .github/workflows/reindex.yml

name: Reindex

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

      - name: Install deps
        run: pip install numpy sentence-transformers

      - name: Fetch Library artifacts
        env:
          GH_TOKEN: ${{ secrets.LIBRARY_PAT }}
        run: |
          gh repo clone Legato/Legato.Library library-clone
          python scripts/extract_signals.py --source library-clone --output signals/library/

      - name: Fetch Lab projects
        env:
          GH_TOKEN: ${{ secrets.LAB_PAT }}
        run: |
          for repo in $(gh repo list Legato --json name -q '.[].name | select(startswith("Lab."))'); do
            gh repo clone "Legato/${repo}" "lab-clone/${repo}"
          done
          python scripts/extract_signals.py --source lab-clone --output signals/lab/

      - name: Rebuild embeddings
        run: |
          python scripts/rebuild_embeddings.py

      - name: Commit updated index
        run: |
          git add index.json signals/ embeddings/
          git commit -m "Reindex complete: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
          git push
```

---

# 6. Copilot Integration

## Overview

LEGATO uses GitHub Copilot Coding Agent to autonomously implement projects. When a PROJECT thread is classified, Conduct spawns a Lab repository, creates an issue with detailed instructions, and assigns it to `@copilot` via GraphQL API.

## Assignment Flow

```
┌─────────────────────┐
│  PROJECT classified │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Spawn Lab repo     │
│  from template      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Write SIGNAL.md    │
│  with project intent│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Create Issue       │
│  with Tasker body   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Get Copilot actor  │
│  ID via GraphQL     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Assign issue to    │
│  copilot-swe-agent  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Copilot creates PR │
│  (autonomous)       │
└─────────────────────┘
```

## GraphQL Assignment Script

```python
# scripts/assign_copilot.py

import os
import requests
import argparse

GITHUB_GRAPHQL = "https://api.github.com/graphql"

def get_copilot_actor_id(repo: str, token: str) -> str:
    """Get the copilot-swe-agent actor ID for a repository."""
    owner, name = repo.split("/")
    
    query = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        suggestedActors(capabilities: [CAN_BE_ASSIGNED], first: 20) {
          nodes {
            login
            id
          }
        }
      }
    }
    """
    
    response = requests.post(
        GITHUB_GRAPHQL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={"query": query, "variables": {"owner": owner, "name": name}}
    )
    
    data = response.json()
    actors = data["data"]["repository"]["suggestedActors"]["nodes"]
    
    for actor in actors:
        if "copilot" in actor["login"].lower():
            return actor["id"]
    
    raise RuntimeError("copilot-swe-agent not found in suggested actors")


def get_issue_node_id(repo: str, issue_number: int, token: str) -> str:
    """Get the node ID for an issue."""
    owner, name = repo.split("/")
    
    query = """
    query($owner: String!, $name: String!, $number: Int!) {
      repository(owner: $owner, name: $name) {
        issue(number: $number) {
          id
        }
      }
    }
    """
    
    response = requests.post(
        GITHUB_GRAPHQL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "query": query,
            "variables": {"owner": owner, "name": name, "number": issue_number}
        }
    )
    
    return response.json()["data"]["repository"]["issue"]["id"]


def assign_copilot(repo: str, issue_number: int, token: str) -> None:
    """Assign an issue to the Copilot coding agent."""
    copilot_id = get_copilot_actor_id(repo, token)
    issue_id = get_issue_node_id(repo, issue_number, token)
    
    mutation = """
    mutation($issueId: ID!, $assigneeIds: [ID!]!) {
      addAssigneesToAssignable(input: {
        assignableId: $issueId,
        assigneeIds: $assigneeIds
      }) {
        assignable {
          ... on Issue {
            number
            title
            assignees(first: 5) {
              nodes {
                login
              }
            }
          }
        }
      }
    }
    """
    
    response = requests.post(
        GITHUB_GRAPHQL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "query": mutation,
            "variables": {"issueId": issue_id, "assigneeIds": [copilot_id]}
        }
    )
    
    result = response.json()
    if "errors" in result:
        raise RuntimeError(f"GraphQL errors: {result['errors']}")
    
    assignees = result["data"]["addAssigneesToAssignable"]["assignable"]["assignees"]["nodes"]
    print(f"Issue #{issue_number} assigned to: {[a['login'] for a in assignees]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--issue", required=True, type=int)
    args = parser.parse_args()
    
    token = os.environ.get("GH_TOKEN")
    assign_copilot(args.repo, args.issue, token)
```

## Tasker Template

The issue body that Copilot receives. This is the "contract" between LEGATO and Copilot.

```markdown
# prompts/tasker-template.md

## Tasker: {{ title }}

### Context
{{ context_from_transcript }}

{{ correlation_context }}

### Objective
{{ clear_objective }}

### Acceptance Criteria
- [ ] {{ criterion_1 }}
- [ ] {{ criterion_2 }}
- [ ] {{ criterion_3 }}

### Constraints
- Follow patterns in `copilot-instructions.md`
- Reference `SIGNAL.md` for project intent
- Write tests for new functionality
- Keep PRs focused and reviewable

### References
- Source transcript: `{{ transcript_id }}`
- Related artifacts: {{ related_links }}

---
*Generated by Legato.Conduct | Correlation: {{ correlation_score }}% | Source: {{ source_id }}*
```

### Example Rendered Tasker

```markdown
## Tasker: MCP Bedrock Adapter

### Context
From voice transcript 2026-01-07-1530:
"I need an MCP server that can wrap AWS Bedrock in our JWICS environment. 
It should handle the authentication flow and expose the standard completion 
endpoints as MCP tools."

Related: This builds on the existing FedGenius architecture patterns.

### Objective
Create an MCP server that wraps AWS Bedrock API, suitable for deployment 
in classified environments (JWICS).

### Acceptance Criteria
- [ ] MCP server responds to tool discovery requests
- [ ] Supports `bedrock:complete` tool for text completion
- [ ] Handles AWS STS authentication with assumed roles
- [ ] Includes configuration for different classification levels
- [ ] Unit tests for core functionality

### Constraints
- Follow patterns in `copilot-instructions.md`
- Reference `SIGNAL.md` for project intent
- Write tests for new functionality
- Keep PRs focused and reviewable

### References
- Source transcript: `transcript-2026-01-07-1530`
- Related artifacts: [FedGenius Architecture](../Library/concepts/fedgenius-architecture.md)

---
*Generated by Legato.Conduct | Correlation: 45% | Source: voice-memo-2026-01-07*
```

## copilot-instructions.md Template

Per-repository file that guides Copilot's behavior.

```markdown
# Copilot Instructions for {{ project_name }}

## Project Context
{{ from_signal_md }}

## Architecture
- This is a {{ note|chord }} project
- Primary language: {{ language }}
- Target environment: {{ environment }}

## Code Style
- Use type hints for all functions
- Docstrings for public APIs
- Keep functions focused and small
- Follow PEP 8 for Python, ESLint defaults for TypeScript

## Testing Requirements
- Unit tests in `/tests`
- Use pytest for Python, jest for TypeScript
- Aim for >80% coverage on core logic
- Test edge cases and error paths

## File Organization
```
src/
  {{ module_name }}/
    __init__.py
    main.py
    ...
tests/
  test_main.py
  ...
```

## Off Limits
- Do not modify: `.github/workflows/`, `SIGNAL.md`
- Do not commit: secrets, credentials, `.env`
- Do not add unnecessary dependencies

## PR Guidelines
- Clear title describing the change
- Reference the issue number (e.g., "Fixes #1")
- Keep changes focused on the task
- Include test coverage for new code
```

## SIGNAL.md Template

Project intent document that Copilot should reference.

```markdown
# {{ title }}

## Intent
{{ intent_description }}

## Domain Tags
{{ domain_tags | join(', ') }}

## Key Phrases
{{ key_phrases | join(', ') }}

## Source
- Transcript: {{ source_transcript }}
- Created: {{ created_timestamp }}

## Related
{{ related_artifacts }}
```

## Prerequisites

### Organization Setup

1. Enable Copilot Coding Agent on the GitHub organization
   - Organization Settings → Copilot → Enable Coding Agent

2. Ensure the PAT has sufficient permissions
   - `repo` scope for creating repositories and issues
   - Organization membership for accessing Copilot

### Token Requirements

| Secret | Scope | Purpose |
|--------|-------|---------|
| `LAB_PAT` | `repo`, `workflow` | Create Lab repos, issues, assign Copilot |
| `LIBRARY_PAT` | `repo` | Commit to Library |
| `LISTEN_PAT` | `repo` | Update Listen index |

## Copilot Behavior Expectations

When assigned an issue, Copilot will:

1. Read the issue body (Tasker template)
2. Read `copilot-instructions.md` for guidelines
3. Read `SIGNAL.md` for project context
4. Create a branch
5. Implement the solution
6. Write tests
7. Create a PR with the implementation

### PR Labels

| Label | Meaning |
|-------|---------|
| `copilot-task` | Created from LEGATO tasker |
| `legato:spawned` | Repo created by LEGATO |
| `legato-pending` | Awaiting human review |

## Review Flow

After Copilot creates a PR:

1. PR is labeled `legato-pending`
2. Human reviews the PR
3. Comments trigger continuation workflow:
   - `approve` / `lgtm` / `ship` → Merge PR
   - `reject` / `skip` → Close PR
   - `reclassify` → Re-run classification
   - Other comments → Revision request to Copilot

```
┌─────────────────────┐
│  Copilot creates PR │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Label: legato-     │
│  pending            │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Human reviews      │
└──────────┬──────────┘
           │
     ┌─────┼─────┬─────────┐
     │     │     │         │
     ▼     ▼     ▼         ▼
  approve  reject  reclassify  revise
     │     │     │         │
     ▼     ▼     ▼         ▼
   Merge  Close  Re-run   Request
    PR     PR    classify  changes
```

---

# 7. Bootstrapping Guide

## Phase 1: Foundation

### 1.1 Create GitHub Organization

```bash
# Create the Legato organization
gh org create Legato

# Or use an existing org
export LEGATO_ORG="Legato"
```

### 1.2 Create Conduct Repository

```bash
# Create and clone Conduct
gh repo create ${LEGATO_ORG}/Legato.Conduct --public --clone
cd Legato.Conduct

# Create directory structure
mkdir -p .github/workflows
mkdir -p prompts
mkdir -p templates/note/.github/workflows
mkdir -p templates/chord/.github/workflows
mkdir -p templates/chord/{init,plans,docs,src,tests}
mkdir -p scripts
mkdir -p package/legato

# Create placeholder files
touch .github/workflows/process-transcript.yml
touch .github/workflows/process-transcript-continue.yml
touch .github/workflows/spawn-project.yml
touch .github/workflows/correlate.yml
touch prompts/{classifier,knowledge-extractor,project-planner,tasker-template,signal-extractor}.md
touch scripts/{parse_transcript,call_claude,commit_to_library,assign_copilot,query_listen}.py
touch package/legato/{__init__,classifier,knowledge,projects,correlation}.py
touch legato  # CLI entry point
touch README.md

git add .
git commit -m "Initial structure"
git push
```

### 1.3 Create Library Repository

```bash
gh repo create ${LEGATO_ORG}/Legato.Library --public

# Clone and setup
gh repo clone ${LEGATO_ORG}/Legato.Library
cd Legato.Library

mkdir -p .github/workflows
mkdir -p {epiphanies,concepts,reflections,glimmers,reminders,worklog}

touch .github/workflows/register-signal.yml
touch index.json
touch README.md

# Initialize index
echo '{}' > index.json

git add .
git commit -m "Initial structure"
git push
```

### 1.4 Create Listen Repository

```bash
gh repo create ${LEGATO_ORG}/Legato.Listen --public

# Clone and setup
gh repo clone ${LEGATO_ORG}/Legato.Listen
cd Legato.Listen

mkdir -p .github/workflows
mkdir -p signals/{library,lab}
mkdir -p embeddings
mkdir -p scripts

touch .github/workflows/{register-signal,correlate,reindex}.yml
touch scripts/{register,embed,correlate,recommend}.py
touch index.json
touch README.md

# Initialize index
echo '{}' > index.json

git add .
git commit -m "Initial structure"
git push
```

### 1.5 Enable Copilot Coding Agent

```
Manual steps:
1. Go to Organization Settings
2. Navigate to Copilot section
3. Enable "Coding Agent" feature
4. Verify copilot-swe-agent appears in assignable actors
```

## Phase 2: Secrets Setup

### 2.1 Create Personal Access Tokens

Create PATs with the following scopes:
- `repo` (full control of private repositories)
- `workflow` (update GitHub Action workflows)
- `admin:org` (if creating repos programmatically)

```bash
# Create tokens via GitHub UI or CLI
# Settings → Developer settings → Personal access tokens → Fine-grained tokens

# Recommended: Create separate tokens for each purpose
# - LIBRARY_PAT: Access to Legato.Library
# - LISTEN_PAT: Access to Legato.Listen  
# - LAB_PAT: Access to Legato.Lab/* repos
```

### 2.2 Configure Secrets in Conduct

```bash
cd Legato.Conduct

# API Keys
gh secret set ANTHROPIC_API_KEY --body "sk-ant-..."
gh secret set OPENAI_API_KEY --body "sk-..."  # For embeddings

# Repository Access Tokens
gh secret set LIBRARY_PAT --body "ghp_..."
gh secret set LISTEN_PAT --body "ghp_..."
gh secret set LAB_PAT --body "ghp_..."
```

### 2.3 Verify Secrets

```bash
# List configured secrets
gh secret list

# Expected output:
# ANTHROPIC_API_KEY  Updated 2026-01-07
# OPENAI_API_KEY     Updated 2026-01-07
# LIBRARY_PAT        Updated 2026-01-07
# LISTEN_PAT         Updated 2026-01-07
# LAB_PAT            Updated 2026-01-07
```

## Phase 3: Template Setup

### 3.1 Note Template

```bash
cd Legato.Conduct/templates/note

# README.md
cat > README.md << 'EOF'
# {{ project_name }}

> {{ project_description }}

## Quick Start

See [SIGNAL.md](./SIGNAL.md) for project intent.

## Structure

```
├── src/          # Source code
├── plans/        # Implementation plans
└── tests/        # Test files
```

---
*Created by LEGATO*
EOF

# SIGNAL.md (placeholder)
cat > SIGNAL.md << 'EOF'
# Project Signal

*This file is auto-generated by LEGATO.*

## Intent
[To be filled by spawn workflow]

## Domain Tags
[To be filled]

## Key Phrases
[To be filled]

## Source
- Transcript: [To be filled]
- Created: [To be filled]
EOF

# copilot-instructions.md
cat > copilot-instructions.md << 'EOF'
# Copilot Instructions

## Project Type
This is a **Note** project (single PR, simple scope).

## Guidelines
- Keep implementation focused and minimal
- Write tests for core functionality
- Follow existing patterns if present

## Code Style
- Use type hints (Python) or TypeScript
- Add docstrings/JSDoc for public APIs
- Keep functions small and focused

## Testing
- Tests go in `/tests`
- Use pytest (Python) or jest (TypeScript)

## Off Limits
- Do not modify `.github/workflows/`
- Do not modify `SIGNAL.md`
- Do not commit secrets or credentials

## PR Guidelines
- Reference the issue number
- Clear, descriptive title
- Keep changes focused
EOF

# Workflow
mkdir -p .github/workflows
cat > .github/workflows/on-issue-assigned.yml << 'EOF'
name: Issue Assigned

on:
  issues:
    types: [assigned]

jobs:
  notify:
    runs-on: ubuntu-latest
    if: contains(github.event.issue.assignees.*.login, 'copilot-swe-agent')
    steps:
      - name: Log assignment
        run: |
          echo "Issue #${{ github.event.issue.number }} assigned to Copilot"
          echo "Title: ${{ github.event.issue.title }}"
EOF
```

### 3.2 Chord Template

```bash
cd Legato.Conduct/templates/chord

# README.md
cat > README.md << 'EOF'
# {{ project_name }}

> {{ project_description }}

## Quick Start

See [SIGNAL.md](./SIGNAL.md) for project intent.

## Structure

```
├── init/         # Bootstrap and setup
├── plans/        # Phase implementation plans
├── docs/         # Architecture and documentation
├── src/          # Source code
└── tests/        # Test files
```

## Phases

1. **Foundation** - Core setup and structure
2. **Core** - Main implementation
3. **Integration** - Connect components

---
*Created by LEGATO*
EOF

# SIGNAL.md (same as note)
cp ../note/SIGNAL.md .

# copilot-instructions.md
cat > copilot-instructions.md << 'EOF'
# Copilot Instructions

## Project Type
This is a **Chord** project (multi-PR, complex scope).

## Guidelines
- Follow the phased approach in `/plans`
- Each phase should be a separate PR
- Document architecture decisions in `/docs`

## Code Style
- Use type hints (Python) or TypeScript
- Add docstrings/JSDoc for public APIs
- Keep functions small and focused
- Follow SOLID principles

## Testing
- Tests go in `/tests`
- Use pytest (Python) or jest (TypeScript)
- Aim for >80% coverage

## Architecture
- Check `/docs/architecture.md` for design
- Keep components loosely coupled
- Use dependency injection where appropriate

## Off Limits
- Do not modify `.github/workflows/`
- Do not modify `SIGNAL.md`
- Do not commit secrets or credentials

## PR Guidelines
- Reference the issue number
- Clear, descriptive title
- One phase per PR
- Include tests for new code
EOF

# Directory structure
mkdir -p init plans docs src tests

touch init/bootstrap.md
touch plans/phase-01-foundation.md
touch plans/phase-02-core.md
touch plans/phase-03-integration.md
touch docs/architecture.md

# Workflow
mkdir -p .github/workflows
cat > .github/workflows/on-issue-assigned.yml << 'EOF'
name: Issue Assigned

on:
  issues:
    types: [assigned]

jobs:
  notify:
    runs-on: ubuntu-latest
    if: contains(github.event.issue.assignees.*.login, 'copilot-swe-agent')
    steps:
      - name: Log assignment
        run: |
          echo "Issue #${{ github.event.issue.number }} assigned to Copilot"
          echo "Title: ${{ github.event.issue.title }}"
EOF

cat > .github/workflows/phase-complete.yml << 'EOF'
name: Phase Complete

on:
  pull_request:
    types: [closed]

jobs:
  next-phase:
    runs-on: ubuntu-latest
    if: github.event.pull_request.merged == true
    steps:
      - name: Check for next phase
        run: |
          echo "PR merged: ${{ github.event.pull_request.title }}"
          echo "Check if there's a next phase to trigger"
EOF
```

## Phase 4: End-to-End Test

### 4.1 Create Test Transcript

```bash
# Sample transcript for testing
TEST_TRANSCRIPT="I had an epiphany about how AI could be treated as oracle machines providing intuition rather than reasoning. This connects to Turing's work on ordinal logic. Also, I want to build a simple CLI tool for parsing transcripts into structured data - just a basic note-level project."
```

### 4.2 Trigger via CLI

```bash
cd Legato.Conduct

# Run the CLI (once implemented)
./legato process "${TEST_TRANSCRIPT}"

# Or trigger via workflow dispatch
gh workflow run process-transcript.yml \
  -f transcript="${TEST_TRANSCRIPT}" \
  -f source="test-2026-01-07"
```

### 4.3 Verify Results

```bash
# Check Library for new artifact
cd ../Legato.Library
git pull
ls -la epiphanies/
cat epiphanies/2026-01-07-*.md

# Check Lab for new project
gh repo list ${LEGATO_ORG} --json name -q '.[].name | select(startswith("Lab."))'

# Check if issue was created and assigned
gh issue list --repo ${LEGATO_ORG}/Lab.transcript-parser.Note

# Check if Copilot created a PR
gh pr list --repo ${LEGATO_ORG}/Lab.transcript-parser.Note
```

### 4.4 Expected Outcomes

| Step | Expected Result |
|------|-----------------|
| Parse | Transcript split into 2 threads |
| Classify | Thread 1: KNOWLEDGE/epiphany, Thread 2: PROJECT/note |
| Correlate | Low correlation (<70%), CREATE recommended |
| Library | New file in `epiphanies/` |
| Lab | New repo `Lab.transcript-parser.Note` |
| Issue | Issue #1 created with Tasker body |
| Assignment | Issue assigned to `copilot-swe-agent` |
| Copilot | PR created with implementation |
| Listen | Signals registered for both |

## Phase 5: Future - Webapp

### 5.1 Planned Features

- Web frontend for transcript intake
- OAuth authentication layer
- Real-time status dashboard
- Pending authorization queue
- Mobile-responsive design

### 5.2 Architecture Preview

```
┌─────────────────────────────────────────────────────────────┐
│                      LEGATO Webapp                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Intake    │  │   Status    │  │   Authorization     │ │
│  │   Form      │  │   Dashboard │  │   Queue             │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                │                    │             │
│         └────────────────┼────────────────────┘             │
│                          │                                  │
│                          ▼                                  │
│              ┌───────────────────────┐                      │
│              │  GitHub API / Webhooks│                      │
│              └───────────┬───────────┘                      │
│                          │                                  │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Legato.Conduct  │
                  └─────────────────┘
```

## Checklist

### Phase 1: Foundation
- [ ] Create Legato organization
- [ ] Create Legato.Conduct repository
- [ ] Create Legato.Library repository
- [ ] Create Legato.Listen repository
- [ ] Enable Copilot Coding Agent

### Phase 2: Secrets
- [ ] Create Anthropic API key
- [ ] Create OpenAI API key (optional)
- [ ] Create LIBRARY_PAT
- [ ] Create LISTEN_PAT
- [ ] Create LAB_PAT
- [ ] Configure secrets in Conduct

### Phase 3: Templates
- [ ] Create .Note template
- [ ] Create .Chord template
- [ ] Test template spawning

### Phase 4: End-to-End Test
- [ ] Process test transcript
- [ ] Verify Library artifact created
- [ ] Verify Lab repo spawned
- [ ] Verify issue assigned to Copilot
- [ ] Verify PR created
- [ ] Verify signals registered

### Phase 5: Webapp (Future)
- [ ] Design intake form
- [ ] Implement OAuth flow
- [ ] Build status dashboard
- [ ] Create authorization queue

---

# Quick Reference

## Core Repositories

```
Legato/
├── Legato.Conduct    # Orchestrator (entry point)
├── Legato.Library    # Knowledge store
├── Legato.Listen     # Semantic brain
└── Legato.Lab/       # Project repos
    ├── project.Note  # Simple projects
    └── project.Chord # Complex projects
```

## Data Flow Summary

```
Voice Transcript
       ↓
   [Conduct]
       ↓
  Parse → Classify → Correlate
       ↓                ↓
   KNOWLEDGE         PROJECT
       ↓                ↓
   [Library]         [Lab/*]
       ↓                ↓
    Artifact          Issue
       ↓                ↓
   [Listen]          @copilot
       ↓                ↓
    Signal             PR
```

## Classification Quick Reference

| Type | Categories | Destination |
|------|------------|-------------|
| KNOWLEDGE | epiphany, concept, reflection, glimmer, reminder, worklog | Library |
| PROJECT | note (simple), chord (complex) | Lab/* |

## Correlation Thresholds

| Score | Recommendation |
|-------|----------------|
| < 70% | CREATE new |
| 70-90% | SUGGEST (human review) |
| > 90% | AUTO-APPEND |

---

*LEGATO: Let Every Gesture Align To Output*

*Version 0.3 | 2026-01-07*
