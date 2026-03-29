"""
Risk Agent — composite scoring for brand alignment, residual compliance risk, and engagement.
"""

import json
from pathlib import Path

from memory.vector_store import check_brand_similarity

RULES_PATH = Path(__file__).resolve().parent.parent / "data" / "compliance_rules.json"


def risk_confidence_score(content: str) -> dict:
    score = {
        "brand_alignment": 0,
        "compliance_risk": 0,
        "engagement_score": 0,
    }

    rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    lower = content.lower()

    risk = 8
    for phrase in rules.get("banned_phrases", []):
        if phrase.lower() in lower:
            risk += 28
    score["compliance_risk"] = min(risk, 100)

    similarity = check_brand_similarity(content)
    score["brand_alignment"] = int(round(float(similarity) * 100))
    score["brand_alignment"] = max(45, min(score["brand_alignment"], 98))

    engagement = 52
    if any(word in lower for word in ("read the", "pilot", "today", "update", "workflow")):
        engagement += 12
    if any(word in lower for word in ("discover", "unlock", "new:", "ready")):
        engagement += 10
    if any(word in lower for word in ("join", "start", "explore", "contact")):
        engagement += 8
    if len(content.split()) > 80:
        engagement += 8
    if "?" in content:
        engagement += 5

    score["engagement_score"] = min(engagement, 100)

    return score
