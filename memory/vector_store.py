"""
Embedding helpers for learning retrieval and brand similarity.

Lazily loads the sentence-transformers model to keep API startup responsive.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

_MODEL = None

FEEDBACK_PATH = Path(__file__).resolve().parent.parent / "memory" / "feedback.json"


def _get_model():
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer

        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _MODEL


def get_similarity(text1: str, text2: str) -> float:
    model = _get_model()
    emb1 = model.encode(text1)
    emb2 = model.encode(text2)
    denom = float(np.linalg.norm(emb1) * np.linalg.norm(emb2))
    if denom == 0:
        return 0.0
    return float(np.dot(emb1, emb2) / denom)


def load_past_content():
    try:
        data = json.loads(FEEDBACK_PATH.read_text(encoding="utf-8"))
        return [item["content"] for item in data if item.get("content")]
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def check_brand_similarity(content: str) -> float:
    guidelines_path = Path(__file__).resolve().parent.parent / "data" / "brand_guidelines.txt"
    try:
        guide = guidelines_path.read_text(encoding="utf-8")
    except OSError:
        guide = "Professional, trustworthy, brand-safe enterprise communications."

    guide_sim = get_similarity(content, guide)
    past_contents = load_past_content()

    if not past_contents:
        return max(0.58, min(0.93, guide_sim))

    past_max = max(get_similarity(content, past) for past in past_contents)
    blended = 0.55 * guide_sim + 0.45 * past_max
    return max(0.58, min(0.93, blended))


def get_most_similar(query_text: str, past_contents: list[str]):
    if not past_contents:
        return None

    model = _get_model()
    query_emb = model.encode(query_text)
    best_match = None
    highest = -1.0

    for content in past_contents:
        content_emb = model.encode(content)
        denom = float(np.linalg.norm(query_emb) * np.linalg.norm(content_emb))
        if denom == 0:
            continue
        sim = float(np.dot(query_emb, content_emb) / denom)
        if sim > highest:
            highest = sim
            best_match = content

    return best_match
