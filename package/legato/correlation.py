"""
LEGATO Correlation Module.

Provides semantic awareness across artifacts and projects via Legato.Listen.
Prevents duplication by finding related content and making recommendations.
"""

import os
import sys
import json
import argparse
import subprocess
import base64
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# Try numpy for local correlation
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


@dataclass
class Signal:
    """A signal for the Listen index."""

    id: str
    type: str  # "artifact" or "project"
    source: str  # "library" or "lab"
    category: str
    title: str
    domain_tags: list = field(default_factory=list)
    intent: str = ""
    key_phrases: list = field(default_factory=list)
    path: str = ""
    created: Optional[str] = None
    updated: Optional[str] = None
    embedding_ref: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "category": self.category,
            "title": self.title,
            "domain_tags": self.domain_tags,
            "intent": self.intent,
            "key_phrases": self.key_phrases,
            "path": self.path,
            "created": self.created or datetime.utcnow().isoformat() + "Z",
            "updated": self.updated or datetime.utcnow().isoformat() + "Z",
            "embedding_ref": self.embedding_ref,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Signal":
        """Create from dictionary."""
        return cls(
            id=data.get("id", ""),
            type=data.get("type", "artifact"),
            source=data.get("source", "library"),
            category=data.get("category", ""),
            title=data.get("title", ""),
            domain_tags=data.get("domain_tags", []),
            intent=data.get("intent", ""),
            key_phrases=data.get("key_phrases", []),
            path=data.get("path", ""),
            created=data.get("created"),
            updated=data.get("updated"),
            embedding_ref=data.get("embedding_ref"),
        )

    def get_embedding_text(self) -> str:
        """Get text for embedding generation."""
        return " ".join([
            self.title,
            self.intent,
            " ".join(self.key_phrases)
        ])


def generate_embedding(text: str) -> list[float]:
    """
    Generate embedding for text.

    Uses OpenAI embeddings if available, otherwise local model.
    """
    openai_key = os.environ.get("OPENAI_API_KEY")

    if openai_key:
        import requests
        response = requests.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "text-embedding-3-small",
                "input": text
            }
        )
        data = response.json()
        return data["data"][0]["embedding"]

    else:
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            return model.encode(text).tolist()
        except ImportError:
            raise RuntimeError(
                "No embedding method available. Set OPENAI_API_KEY or "
                "install sentence-transformers"
            )


def cosine_similarity(a: list, b: list) -> float:
    """Calculate cosine similarity between two vectors."""
    if not HAS_NUMPY:
        # Simple implementation without numpy
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        return dot / (norm_a * norm_b)

    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def load_listen_index(listen_repo: Optional[str] = None) -> dict:
    """Load the Listen index from repository."""
    listen_repo = listen_repo or os.environ.get("LISTEN_REPO", "Legato/Legato.Listen")

    try:
        result = subprocess.run(
            ["gh", "api", f"/repos/{listen_repo}/contents/index.json"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            content = base64.b64decode(data["content"]).decode()
            return json.loads(content)
    except Exception:
        pass

    return {}


def correlate_signal(signal: Signal, index: Optional[dict] = None, top_k: int = 5) -> dict:
    """
    Find signals correlated with the given signal.

    Args:
        signal: Signal to correlate
        index: Optional pre-loaded index
        top_k: Number of top matches to return

    Returns:
        Correlation result with matches and recommendation
    """
    if index is None:
        index = load_listen_index()

    if not index:
        return {
            "matches": [],
            "top_score": 0.0,
            "recommendation": "CREATE",
            "suggested_target": None
        }

    # Generate query embedding
    query_text = signal.get_embedding_text()
    if not query_text.strip():
        return {
            "matches": [],
            "top_score": 0.0,
            "recommendation": "CREATE",
            "suggested_target": None
        }

    try:
        query_embedding = generate_embedding(query_text)
    except Exception as e:
        print(f"Warning: Could not generate embedding: {e}", file=sys.stderr)
        return {
            "matches": [],
            "top_score": 0.0,
            "recommendation": "CREATE",
            "suggested_target": None,
            "error": str(e)
        }

    # Compare against all signals
    scores = []

    for signal_id, signal_data in index.items():
        other_signal = Signal.from_dict(signal_data)
        other_text = other_signal.get_embedding_text()

        if not other_text.strip():
            continue

        try:
            other_embedding = generate_embedding(other_text)
            score = cosine_similarity(query_embedding, other_embedding)

            scores.append({
                "signal_id": signal_id,
                "score": score,
                "title": other_signal.title,
                "path": other_signal.path
            })
        except Exception:
            continue

    # Sort and take top_k
    scores.sort(key=lambda x: x["score"], reverse=True)
    matches = scores[:top_k]

    # Determine recommendation
    top_score = matches[0]["score"] if matches else 0.0

    if top_score < 0.70:
        recommendation = "CREATE"
    elif top_score < 0.90:
        recommendation = "SUGGEST"
    else:
        recommendation = "AUTO-APPEND"

    return {
        "matches": matches,
        "top_score": top_score,
        "recommendation": recommendation,
        "suggested_target": matches[0]["signal_id"] if matches else None
    }


def register_signal(signal: Signal, listen_repo: Optional[str] = None) -> dict:
    """
    Register a signal in the Listen index.

    Args:
        signal: Signal to register
        listen_repo: Listen repository (default from env)

    Returns:
        Registration result
    """
    listen_repo = listen_repo or os.environ.get("LISTEN_REPO", "Legato/Legato.Listen")
    token = os.environ.get("GH_TOKEN")

    if not token:
        raise RuntimeError("GH_TOKEN environment variable not set")

    # Load current index
    index = load_listen_index(listen_repo)

    # Add/update signal
    signal.updated = datetime.utcnow().isoformat() + "Z"
    if signal.id not in index:
        signal.created = signal.updated

    index[signal.id] = signal.to_dict()

    # Write back to repository
    content = json.dumps(index, indent=2)
    content_b64 = base64.b64encode(content.encode()).decode()

    # Get current SHA
    result = subprocess.run(
        ["gh", "api", f"/repos/{listen_repo}/contents/index.json"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        data = json.loads(result.stdout)
        sha = data.get("sha")

        update_cmd = [
            "gh", "api",
            "--method", "PUT",
            f"/repos/{listen_repo}/contents/index.json",
            "-f", f"message=Register signal: {signal.id}",
            "-f", f"content={content_b64}",
            "-f", f"sha={sha}"
        ]
    else:
        update_cmd = [
            "gh", "api",
            "--method", "PUT",
            f"/repos/{listen_repo}/contents/index.json",
            "-f", f"message=Register signal: {signal.id}",
            "-f", f"content={content_b64}"
        ]

    subprocess.run(update_cmd, check=True)

    return {
        "signal_id": signal.id,
        "registered": True,
        "listen_repo": listen_repo
    }


def main():
    """CLI entry point for correlation module."""
    parser = argparse.ArgumentParser(description="LEGATO Correlation Module")
    parser.add_argument(
        "--register-new",
        action="store_true",
        help="Register new signals from recent commits"
    )
    parser.add_argument(
        "--query",
        help="Query JSON string for correlation"
    )
    parser.add_argument(
        "--output",
        help="Output file"
    )
    args = parser.parse_args()

    if args.query:
        # Correlation query mode
        query_data = json.loads(args.query)
        signal = Signal.from_dict(query_data)
        result = correlate_signal(signal)

        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2)
        else:
            print(json.dumps(result, indent=2))

    elif args.register_new:
        # Registration mode - would typically read from environment
        print("Registration mode not fully implemented in CLI")
        print("Use the Python API: from legato.correlation import register_signal")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
