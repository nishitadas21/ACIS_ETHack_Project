"""
RAG-lite: static enterprise knowledge for learning context and compliance alignment.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_PATH = ROOT / "data" / "knowledge.json"


def load_knowledge() -> dict:
    try:
        return json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "fintech_rules": [],
            "additional_banned_phrases": [],
            "auditor_merge_phrases": [],
            "brand_voice": [],
        }


def knowledge_labels_and_banned_extras(scenario: str) -> tuple[list[str], list[str]]:
    """
    Returns (log_labels e.g. ['fintech_rules'], extra phrases for Compliance Agent scan).
    """
    kb = load_knowledge()
    labels: list[str] = []
    extras: list[str] = []
    extras.extend(kb.get("additional_banned_phrases") or [])
    extras.extend(kb.get("auditor_merge_phrases") or [])

    if scenario in ("high_compliance", "strict_regulation"):
        labels.append("fintech_rules")
        extras.extend(["guaranteed returns", "100% safe", "no risk", "risk-free"])

    # Dedupe preserving order
    seen: set[str] = set()
    out: list[str] = []
    for p in extras:
        k = p.strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append(p.strip())
    return labels, out
