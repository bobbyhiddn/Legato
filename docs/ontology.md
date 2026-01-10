# LEGATO Ontology

## Data Flow Hierarchy

```
Transcript → Threads → Notes → Chords
```

| Level | Description | Storage |
|-------|-------------|---------|
| **Transcript** | Raw voice capture or text input | Conduct (input) |
| **Thread** | Parsed segment of a transcript | Conduct (intermediate) |
| **Note** | Knowledge artifact, always created first | Library |
| **Chord** | Implementation project, escalated from a Note | `{name}` repo (tagged `legato:chord`) |

## Core Principle

**Everything becomes a Note first.**

A Chord is never created in isolation—it is always an escalation of an existing Note. This ensures:
- Every project has documented context in the Library
- The "why" is preserved alongside the "what"
- Knowledge and implementation remain linked

## Notes

Notes are knowledge artifacts stored in `Legato.Library`. They capture:
- Insights and epiphanies
- Technical concepts
- Reflections and observations
- Quick ideas (glimmers)
- Reminders and action items
- Work summaries

### Note Categories

| Category | Description |
|----------|-------------|
| `epiphany` | Major breakthrough or insight |
| `concept` | Technical definition or explanation |
| `reflection` | Personal thought or observation |
| `glimmer` | Quick idea seed for future exploration |
| `reminder` | Action item or follow-up |
| `worklog` | Summary of work done |

### Note Frontmatter

```yaml
---
id: library.concepts.my-idea
title: "My Idea"
category: concept
created: 2026-01-09T12:00:00Z
source_transcript: transcript-2026-01-09
domain_tags: [ai, architecture]
key_phrases: ["key term"]
needs_chord: false       # Set by classifier or manual escalation
chord_name: null         # Suggested name when needs_chord is true
chord_id: null           # Set after escalation is queued
chord_status: null       # pending | active | complete
chord_repo: null         # Set after repo is spawned
---
```

### Chord Escalation Fields

| Field | Set By | Description |
|-------|--------|-------------|
| `needs_chord` | Classifier or user | Flags note for chord escalation |
| `chord_name` | Classifier or user | Suggested repo name |
| `chord_id` | Escalation process | ID like `lab.chord.{name}` |
| `chord_status` | System | `pending` → `active` → `complete` |
| `chord_repo` | Spawn workflow | Full repo path after creation |

## Chords

Chords are multi-phase implementation projects. They are spawned as `{name}` repositories (tagged with `legato:chord`) when a Note is escalated.

### Escalation Triggers

1. **Automatic** - Classifier recognizes the Note describes a complex implementation
2. **Manual** - User clicks "Escalate to Chord" in Pit UI

### Escalation Flow

```
Classifier creates Note with needs_chord: true
       ↓
Note committed to Library with:
  - needs_chord: true
  - chord_name: {suggested-name}
       ↓
Pit syncs Library, sees needs_chord: true
       ↓
Agent queued for user approval
       ↓
User approves in Pit UI
       ↓
Update Note frontmatter:
  - chord_id: lab.chord.{name}
  - chord_status: pending
       ↓
Commit updated Note to Library
       ↓
Spawn {name} repo (tagged legato:chord)
       ↓
Update Note frontmatter:
  - chord_status: active
  - chord_repo: {org}/{name}
  - needs_chord: false (processed)
```

### Manual Escalation

```
User views Note in Pit Library
       ↓
Clicks "Escalate to Chord"
       ↓
Update Note frontmatter:
  - needs_chord: true
  - chord_name: {user-provided or auto}
       ↓
Commit to Library
       ↓
Queue agent (same flow as above)
```

### Chord Frontmatter Reference

When a Note has a Chord:
```yaml
---
id: library.concepts.my-feature
title: "My Feature Concept"
category: concept
chord_id: lab.chord.my-feature
chord_status: active
chord_repo: bobbyhiddn/my-feature
---
```

## Key Distinctions

| Aspect | Note | Chord |
|--------|------|-------|
| **What** | Knowledge artifact | Implementation project |
| **Where** | Library | `{name}` repo (tagged `legato:chord`) |
| **Origin** | From transcript thread | Escalated from Note |
| **Scope** | Single document | Multi-file repository |
| **Agent** | None | Copilot assigned |
| **Lifecycle** | Static (can be edited) | Active (has issues, PRs) |

## The Note-Chord Link

The link between a Note and its Chord is maintained via:

1. **Note frontmatter** - Contains `chord_id`, `chord_status`, `chord_repo`
2. **Chord SIGNAL.md** - References the source Note
3. **Pit agent_queue** - Stores `related_entry_id` pointing to the Note

This bidirectional linking ensures:
- You can find the Chord from any Note
- You can trace any Chord back to its origin Note
- The "why" (Note) is never separated from the "what" (Chord)

## Repository Tagging

Chord repositories are identified by GitHub topic tags, not naming conventions.

| Tag | Meaning |
|-----|---------|
| `legato:chord` | Complex multi-PR project |
| `legato:note` | Simple single-PR project (if spawned) |
| `legato:spawned` | Created by LEGATO system |

This allows natural repository names like `hermit-agent` or `mcp-bedrock-adapter` while maintaining system traceability.

## Anti-Patterns

**DON'T:** Create a Chord directly without a Note
- Loses context and rationale
- Breaks the knowledge chain

**DON'T:** Skip the Note for "obvious" projects
- Even simple ideas benefit from documentation
- Future you will thank present you

**DO:** Let the classifier decide when Notes need Chords
**DO:** Manually escalate when you recognize implementation potential
**DO:** Keep Notes updated as Chords evolve
