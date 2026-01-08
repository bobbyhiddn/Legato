#!/usr/bin/env python3
"""
Query Legato.Listen for semantic correlation.

This script interfaces with the Listen repository to find related signals
and make recommendations about whether to CREATE, APPEND, or QUEUE new items.

Usage:
    python query_listen.py --query '{"title": "...", "intent": "..."}' --output result.json
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional

# Try to import numpy for local correlation
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


def cosine_similarity(a: list, b: list) -> float:
    """Calculate cosine similarity between two vectors."""
    if not HAS_NUMPY:
        raise RuntimeError("numpy not installed")

    a = np.array(a)
    b = np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def load_listen_index(listen_path: Optional[str] = None) -> dict:
    """Load the Listen index from local path or fetch from repository."""
    if listen_path:
        index_file = Path(listen_path) / "index.json"
    else:
        # Try to fetch from repository
        import subprocess
        result = subprocess.run(
            ["gh", "api", "/repos/Legato/Legato.Listen/contents/index.json"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return {}

        import base64
        data = json.loads(result.stdout)
        content = base64.b64decode(data["content"]).decode()
        return json.loads(content)

    if index_file.exists():
        with open(index_file) as f:
            return json.load(f)

    return {}


def generate_embedding(text: str) -> list[float]:
    """
    Generate embedding for text.

    Uses OpenAI embeddings if available, otherwise falls back to
    sentence-transformers for local generation.
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
        # Fall back to sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            return model.encode(text).tolist()
        except ImportError:
            raise RuntimeError(
                "No embedding method available. Set OPENAI_API_KEY or "
                "install sentence-transformers"
            )


def correlate(query: dict, index: dict, top_k: int = 5) -> dict:
    """
    Find signals correlated with the query.

    Args:
        query: Query signal with title, intent, key_phrases
        index: Listen index mapping signal IDs to metadata
        top_k: Number of top matches to return

    Returns:
        Correlation result with matches and recommendation
    """
    # Build query text for embedding
    query_text = " ".join([
        query.get("title", ""),
        query.get("intent", ""),
        " ".join(query.get("key_phrases", []))
    ])

    if not query_text.strip():
        return {
            "matches": [],
            "top_score": 0.0,
            "recommendation": "CREATE",
            "suggested_target": None
        }

    # Generate query embedding
    query_embedding = generate_embedding(query_text)

    # Compare against all signals in index
    scores = []

    for signal_id, signal in index.items():
        # Generate embedding for signal if not cached
        signal_text = " ".join([
            signal.get("title", ""),
            signal.get("intent", ""),
            " ".join(signal.get("key_phrases", []))
        ])

        if not signal_text.strip():
            continue

        signal_embedding = generate_embedding(signal_text)
        score = cosine_similarity(query_embedding, signal_embedding)

        scores.append({
            "signal_id": signal_id,
            "score": score,
            "title": signal.get("title", ""),
            "path": signal.get("path", "")
        })

    # Sort by score and take top_k
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


def main():
    parser = argparse.ArgumentParser(description="Query Listen for correlation")
    parser.add_argument(
        "--query",
        required=True,
        help="Query JSON string or @filename"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON file"
    )
    parser.add_argument(
        "--listen-path",
        help="Local path to Listen repository (optional)"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of top matches to return"
    )
    args = parser.parse_args()

    # Parse query
    if args.query.startswith("@"):
        with open(args.query[1:]) as f:
            query = json.load(f)
    else:
        query = json.loads(args.query)

    # Load index
    index = load_listen_index(args.listen_path)

    if not index:
        print("Warning: Listen index is empty, recommending CREATE", file=sys.stderr)
        result = {
            "matches": [],
            "top_score": 0.0,
            "recommendation": "CREATE",
            "suggested_target": None
        }
    else:
        try:
            result = correlate(query, index, args.top_k)
        except Exception as e:
            print(f"Correlation error: {e}", file=sys.stderr)
            result = {
                "matches": [],
                "top_score": 0.0,
                "recommendation": "CREATE",
                "suggested_target": None,
                "error": str(e)
            }

    # Write output
    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Correlation complete: {result['recommendation']} (score: {result['top_score']:.2f})")


if __name__ == "__main__":
    main()
