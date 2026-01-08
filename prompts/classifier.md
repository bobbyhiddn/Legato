# Thread Classification Prompt

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

## Important Notes

- If a thread contains both knowledge and project elements, classify it as "MIXED" and provide both sets of fields
- Be conservative with EPIPHANY - reserve for genuinely novel insights
- Prefer GLIMMER for incomplete ideas that need development
- Project names should be lowercase, hyphenated slugs
