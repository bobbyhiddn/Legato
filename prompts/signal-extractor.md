# Signal Extraction Prompt

You are extracting signal metadata from classified threads for the LEGATO correlation system.

## Your Task

Generate a signal object that can be indexed by Legato.Listen for semantic correlation.

## Signal Schema

```json
{
  "id": "{source}.{category}.{slug}",
  "type": "artifact|project",
  "source": "library|lab",
  "category": "{knowledge_category or project_scope}",
  "title": "Human-readable title",
  "domain_tags": ["tag1", "tag2", "tag3"],
  "intent": "One-sentence description of purpose/meaning",
  "key_phrases": ["distinctive phrase 1", "distinctive phrase 2"],
  "path": "relative/path/to/artifact.md",
  "created": "ISO timestamp",
  "updated": "ISO timestamp"
}
```

## Field Guidelines

### id
Format: `{source}.{category}.{slug}`
- source: "library" for knowledge artifacts, "lab" for projects
- category: the knowledge category (epiphany, concept, etc.) or project scope (note, chord)
- slug: lowercase hyphenated identifier

Examples:
- `library.epiphanies.oracle-machines`
- `lab.note.mcp-bedrock-adapter`

### type
- "artifact" for Library knowledge items
- "project" for Lab repositories

### intent
A single sentence capturing the core purpose or meaning.
This is crucial for semantic matching - make it descriptive and unique.

Good: "Exploring the connection between Turing's oracle machines and modern AI as intuition engines"
Bad: "Thoughts about AI"

### domain_tags
2-5 topic tags for coarse filtering.
Use established terms when possible.
Lowercase, no spaces.

### key_phrases
Distinctive terms that identify this specific content.
Include technical terms, proper nouns, unique concepts.
These are used for fine-grained matching.

### path
Relative path where the artifact/project lives.
- Library: `{category}/YYYY-MM-DD-{slug}.md`
- Lab: Points to the repository root

## Examples

### Knowledge Artifact Signal

```json
{
  "id": "library.epiphanies.oracle-machines",
  "type": "artifact",
  "source": "library",
  "category": "epiphany",
  "title": "Oracle Machines and AI Intuition",
  "domain_tags": ["ai", "turing", "theory", "intuition"],
  "intent": "Exploring the connection between Turing's oracle machines and modern AI as intuition engines",
  "key_phrases": ["oracle machine", "intuition engine", "ordinal logic", "computable intuition"],
  "path": "epiphanies/2026-01-07-oracle-machines.md",
  "created": "2026-01-07T15:30:00Z",
  "updated": "2026-01-07T15:30:00Z"
}
```

### Project Signal

```json
{
  "id": "lab.note.mcp-bedrock-adapter",
  "type": "project",
  "source": "lab",
  "category": "note",
  "title": "MCP Adapter for AWS Bedrock",
  "domain_tags": ["mcp", "aws", "bedrock", "classified"],
  "intent": "Build an MCP server wrapping AWS Bedrock API for classified environment deployment",
  "key_phrases": ["mcp server", "bedrock adapter", "jwics", "sts authentication"],
  "path": "Lab.mcp-bedrock-adapter.Note",
  "created": "2026-01-07T16:00:00Z",
  "updated": "2026-01-07T16:00:00Z"
}
```

## Output

Return the complete signal JSON object.
