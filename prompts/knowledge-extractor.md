# Knowledge Extraction Prompt

You are extracting structured knowledge artifacts from classified transcript threads for the LEGATO system.

## Your Task

Given a classified KNOWLEDGE thread, produce a complete markdown artifact suitable for the Legato.Library.

## Artifact Structure

```markdown
---
id: library.{category}.{slug}
title: "Artifact Title"
category: epiphany|concept|reflection|glimmer|reminder|worklog
created: {ISO timestamp}
source_transcript: {transcript-id}
domain_tags: [{tags}]
key_phrases: [{phrases}]
correlation_score: 0.0
related: []
---

# {Title}

{Main content - well-structured prose derived from transcript}

## Key Points

- {Bullet point summary}
- {Another key point}

## Context

{Any relevant background or context from the transcript}

## Related Thoughts

{Any connections to other ideas mentioned}
```

## Category Guidelines

### EPIPHANY
- Focus on the breakthrough insight itself
- Explain why this is significant
- Connect to broader implications
- Use clear, memorable framing

### CONCEPT
- Define the concept precisely
- Provide examples where relevant
- Explain how it works
- Note any limitations or edge cases

### REFLECTION
- Capture the personal perspective
- Include the reasoning process
- Note any tensions or uncertainties
- Preserve the authentic voice

### GLIMMER
- State the seed idea clearly
- Note what sparked it
- Suggest potential directions
- Keep it brief but actionable

### REMINDER
- Be specific about the action
- Include any deadlines mentioned
- Note the context for why it matters
- Make it actionable

### WORKLOG
- Summarize what was accomplished
- Note any blockers or challenges
- Include relevant details
- Keep it factual

## Slug Generation

Generate slugs that are:
- Lowercase with hyphens
- 2-5 words capturing the essence
- Unique and descriptive
- Example: "oracle-machines-intuition" not "my-thought-about-ai"

## Output

Return the complete markdown artifact ready for commit to the Library.
