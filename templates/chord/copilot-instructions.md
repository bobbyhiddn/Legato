# Copilot Instructions

## Project Type

This is a **Chord** project (multi-PR, complex scope).

## Guidelines

- Follow the phased approach in `/plans`
- Each phase should be a separate PR
- Document architecture decisions in `/docs`
- Build incrementally, test continuously

## Code Style

### Python
- Use type hints for all functions
- Add docstrings for public APIs
- Keep functions small and focused
- Follow PEP 8
- Use dataclasses for data structures

### TypeScript
- Use strict TypeScript
- Add JSDoc comments for public APIs
- Use functional patterns where appropriate
- Follow ESLint defaults
- Prefer interfaces over types

## Architecture

- Check `/docs/architecture.md` for design
- Keep components loosely coupled
- Use dependency injection where appropriate
- Follow SOLID principles
- Prefer composition over inheritance

## File Organization

```
init/           # Bootstrap scripts and initial setup
plans/          # Phase implementation plans
  phase-01-foundation.md
  phase-02-core.md
  phase-03-integration.md
docs/           # Architecture and documentation
  architecture.md
src/            # Source code
  {module}/
    __init__.py
    ...
tests/          # Test files
  test_{module}.py
  ...
```

## Testing

- Tests go in `/tests`
- Use pytest (Python) or jest (TypeScript)
- Aim for >80% coverage on core logic
- Test edge cases and error paths
- Integration tests for component interactions

## Phase Guidelines

### Phase 1: Foundation
- Set up project structure
- Create base classes/interfaces
- Establish patterns
- Write initial tests

### Phase 2: Core Implementation
- Implement main functionality
- Follow established patterns
- Comprehensive testing
- Performance considerations

### Phase 3: Integration
- Connect components
- End-to-end testing
- Documentation
- Final polish

## Dependencies

- Only add dependencies that are truly necessary
- Prefer standard library when possible
- Pin major versions in requirements
- Document why each dependency is needed

## Off Limits

- Do not modify `.github/workflows/`
- Do not modify `SIGNAL.md`
- Do not commit secrets or credentials
- Do not skip phases without approval

## PR Guidelines

- Reference the issue number (e.g., "Fixes #1")
- Clear, descriptive title
- One phase per PR
- Include tests for new code
- Update architecture docs if design changes

## Common Patterns

### Service Pattern
```python
class Service:
    """Base service class."""

    def __init__(self, config: Config):
        self.config = config

    async def start(self) -> None:
        """Start the service."""
        pass

    async def stop(self) -> None:
        """Stop the service."""
        pass
```

### Repository Pattern
```python
class Repository(ABC):
    """Abstract repository interface."""

    @abstractmethod
    async def get(self, id: str) -> Optional[Entity]:
        pass

    @abstractmethod
    async def save(self, entity: Entity) -> None:
        pass
```

### Error Handling
```python
class ProjectError(Exception):
    """Base exception for this project."""
    pass

class ValidationError(ProjectError):
    """Validation failed."""
    pass

class NotFoundError(ProjectError):
    """Resource not found."""
    pass
```
