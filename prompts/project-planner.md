# Project Planning Prompt

You are planning project implementations from classified transcript threads for the LEGATO system.

## Your Task

Given a classified PROJECT thread, produce a structured project plan suitable for GitHub Copilot to implement.

## Project Types

### NOTE Projects (Simple)
Single PR scope, quick implementation, minimal architecture.

Output structure:
```markdown
# Project Plan: {project-name}

## Overview
{One paragraph description}

## Objective
{Clear, specific goal}

## Requirements
- [ ] {Requirement 1}
- [ ] {Requirement 2}
- [ ] {Requirement 3}

## Technical Approach
{Brief description of implementation strategy}

## File Structure
```
{project-name}/
├── src/
│   └── {main files}
├── tests/
│   └── {test files}
└── README.md
```

## Acceptance Criteria
- [ ] {Criterion 1}
- [ ] {Criterion 2}
- [ ] {Criterion 3}

## Out of Scope
- {What this project does NOT include}
```

### CHORD Projects (Complex)
Multi-PR scope, phased implementation, requires architecture.

Output structure:
```markdown
# Project Plan: {project-name}

## Overview
{Detailed description}

## Objective
{Primary goal and secondary goals}

## Architecture
{High-level architecture description}

```
┌─────────────────┐
│  Component A    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Component B    │
└─────────────────┘
```

## Phases

### Phase 1: Foundation
- Goal: {phase goal}
- Deliverables:
  - [ ] {deliverable}
- Acceptance: {how we know it's done}

### Phase 2: Core Implementation
- Goal: {phase goal}
- Deliverables:
  - [ ] {deliverable}
- Dependencies: Phase 1
- Acceptance: {how we know it's done}

### Phase 3: Integration
- Goal: {phase goal}
- Deliverables:
  - [ ] {deliverable}
- Dependencies: Phase 2
- Acceptance: {how we know it's done}

## Technical Stack
- Language: {language}
- Framework: {if applicable}
- Dependencies: {key dependencies}

## File Structure
```
{project-name}/
├── init/
├── plans/
├── docs/
├── src/
└── tests/
```

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| {risk} | {mitigation} |

## Out of Scope
- {What this project does NOT include}
```

## Guidelines

1. **Be Specific**: Vague requirements lead to vague implementations
2. **Scope Appropriately**: Note = single PR, Chord = multiple PRs
3. **Think About Testing**: Include test requirements
4. **Consider Dependencies**: Note what needs to exist first
5. **Define Done**: Clear acceptance criteria

## Output

Return the complete project plan in markdown format.
