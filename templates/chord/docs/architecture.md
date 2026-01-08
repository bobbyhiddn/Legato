# Architecture

## Overview

This document describes the high-level architecture of the project.

## Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Application                           │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Service   │  │   Service   │  │      Service        │  │
│  │      A      │  │      B      │  │         C           │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                    │              │
│         └────────────────┼────────────────────┘              │
│                          │                                   │
│                          ▼                                   │
│              ┌───────────────────────┐                       │
│              │    Core Domain        │                       │
│              │    (Business Logic)   │                       │
│              └───────────────────────┘                       │
│                          │                                   │
│         ┌────────────────┼────────────────┐                  │
│         │                │                │                  │
│         ▼                ▼                ▼                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Repository  │  │   Client    │  │   Queue     │          │
│  │  (Storage)  │  │  (External) │  │  (Async)    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## Design Principles

### 1. Separation of Concerns

Each component has a single, well-defined responsibility.

### 2. Dependency Inversion

High-level modules don't depend on low-level modules. Both depend on abstractions.

### 3. Interface Segregation

Clients should not be forced to depend on interfaces they don't use.

### 4. Open/Closed

Open for extension, closed for modification.

## Layers

### Presentation Layer

Handles external interfaces (CLI, API, etc.)

### Service Layer

Coordinates business operations and transactions.

### Domain Layer

Contains business logic and rules.

### Infrastructure Layer

Handles external concerns (storage, networking, etc.)

## Data Flow

```
Request → Validation → Service → Domain → Infrastructure → Response
```

## Error Handling

- Domain errors: Business rule violations
- Infrastructure errors: External system failures
- Application errors: Internal failures

All errors include context for debugging.

## Configuration

Configuration flows from environment through the application:

```
Environment Variables
        ↓
   Config Loader
        ↓
  Config Object
        ↓
   Components
```

## Testing Strategy

- Unit tests: Domain logic
- Integration tests: Service + Infrastructure
- E2E tests: Full application

## Deployment

See [deployment.md](./deployment.md) for deployment instructions.
