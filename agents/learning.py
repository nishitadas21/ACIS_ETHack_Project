"""
Learning Agent — retrieves similar past outputs using embeddings and proposes prompt nudges.
Loads static knowledge.json (RAG-lite) for regulated-domain hints.
"""

import json
from pathlib import Path

from memory.vector_store import get_most_similar
from utils.knowledge_base import knowledge_labels_and_banned_extras, load_knowledge

FEEDBACK_PATH = Path(__file__).resolve().parent.parent / "memory" / "feedback.json"


def load_feedback():
    try:
        return json.loads(FEEDBACK_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def learning_agent(current_prompt: str, scenario: str = "general") -> dict:
    kb = load_knowledge()
    kb_labels, _ = knowledge_labels_and_banned_extras(scenario)
    kb_lines = kb.get("fintech_rules") or []
    kb_snippet = ""
    if kb_labels:
        kb_snippet = " ".join(kb_lines[:2])

    feedback_data = load_feedback()

    if not feedback_data:
        return {
            "insight": "No past data available yet — cold start mode." + (f" {kb_snippet}" if kb_snippet else ""),
            "suggestion": "Emphasize measurable outcomes and documented review steps.",
            "knowledge_retrieved": kb_labels,
        }

    past_contents = [item["content"] for item in feedback_data if item.get("content")]
    similar = get_most_similar(current_prompt, past_contents)

    score: dict = {}
    for item in feedback_data:
        if item.get("content") == similar:
            score = item.get("scores") or {}
            break

    insight = "Similar historical artifact located."
    if score:
        insight = (
            f"Prior similar content scored brand {score.get('brand_alignment', 0)}%, "
            f"compliance risk {score.get('compliance_risk', 0)}, "
            f"engagement {score.get('engagement_score', 0)}%."
        )
    if kb_labels:
        insight += f" Knowledge sections applied: {', '.join(kb_labels)}."

    suggestion_parts: list[str] = []
    if score.get("engagement_score", 70) < 70:
        suggestion_parts.append("Add a crisp CTA and a scannable first paragraph.")
    if score.get("brand_alignment", 70) < 70:
        suggestion_parts.append("Lean into professional tone and brand-safe wording.")
    if score.get("compliance_risk", 0) > 40:
        suggestion_parts.append("Prefer cautious claims and cite review/approval paths.")

    suggestion = " ".join(suggestion_parts) if suggestion_parts else "Maintain balanced tone from prior winning runs."

    return {
        "insight": insight,
        "suggestion": suggestion,
        "similar_content_preview": (similar or "")[:180],
        "knowledge_retrieved": kb_labels,
    }
