# Copilot Instructions

## Project Type

This is a **Note** project (single PR, simple scope).

## Guidelines

- Keep implementation focused and minimal
- Write tests for core functionality
- Follow existing patterns if present
- Prefer simple solutions over complex ones

## Code Style

### Python
- Use type hints for all functions
- Add docstrings for public APIs
- Keep functions small and focused
- Follow PEP 8

### TypeScript
- Use strict TypeScript
- Add JSDoc comments for public APIs
- Use functional patterns where appropriate
- Follow ESLint defaults

## File Organization

```
src/
  {module}/
    __init__.py
    main.py
    ...
tests/
  test_main.py
  ...
```

## Testing

- Tests go in `/tests`
- Use pytest (Python) or jest (TypeScript)
- Test both happy path and error cases
- Aim for meaningful coverage, not 100%

## Dependencies

- Only add dependencies that are truly necessary
- Prefer standard library when possible
- Pin major versions in requirements

## Off Limits

- Do not modify `.github/workflows/`
- Do not modify `SIGNAL.md`
- Do not commit secrets or credentials
- Do not add unnecessary configuration files

## PR Guidelines

- Reference the issue number (e.g., "Fixes #1")
- Clear, descriptive title
- Keep changes focused on the task
- Include tests for new code
- Update README if adding new features

## Common Patterns

### Entry Point
```python
def main():
    """Main entry point."""
    pass

if __name__ == "__main__":
    main()
```

### Error Handling
```python
class ProjectError(Exception):
    """Base exception for this project."""
    pass
```

### Configuration
```python
import os

CONFIG = {
    "setting": os.environ.get("SETTING", "default"),
}
```
