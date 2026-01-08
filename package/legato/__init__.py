"""
LEGATO - Voice transcripts to structured knowledge and executable projects.

This package provides the core functionality for the LEGATO system,
which transforms voice transcripts into:
1. Knowledge artifacts (committed to Legato.Library)
2. Project tasks (issues in Legato.Lab/* repos)
"""

__version__ = "0.3.0"

from .classifier import (
    ThreadType,
    KnowledgeCategory,
    ProjectScope,
    ClassifiedThread,
    classify_threads,
)
from .knowledge import (
    KnowledgeArtifact,
    extract_knowledge,
    commit_knowledge,
)
from .projects import (
    ProjectSpec,
    create_project,
    spawn_lab_repo,
)
from .correlation import (
    Signal,
    correlate_signal,
    register_signal,
)

__all__ = [
    # Version
    "__version__",
    # Classifier
    "ThreadType",
    "KnowledgeCategory",
    "ProjectScope",
    "ClassifiedThread",
    "classify_threads",
    # Knowledge
    "KnowledgeArtifact",
    "extract_knowledge",
    "commit_knowledge",
    # Projects
    "ProjectSpec",
    "create_project",
    "spawn_lab_repo",
    # Correlation
    "Signal",
    "correlate_signal",
    "register_signal",
]
