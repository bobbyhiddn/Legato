# Bootstrap Guide

This document describes how to bootstrap the project for local development.

## Prerequisites

- Python 3.11+
- pip or poetry

## Setup Steps

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate   # Windows
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Verify installation**
   ```bash
   python -m pytest tests/
   ```

## Development Workflow

1. Create a feature branch from `main`
2. Implement changes following the phase plan
3. Write tests for new functionality
4. Submit PR for review

## Directory Structure After Bootstrap

```
├── init/           # This directory
├── plans/          # Phase plans
├── docs/           # Documentation
├── src/            # Source code (created during Phase 1)
├── tests/          # Tests (created during Phase 1)
├── requirements.txt
└── .env.example
```
