"""
Compliance Agent (auditor) — scans draft text against enterprise policy rules
and knowledge-base phrases (RAG-lite).
"""

from __future__ import annotations

import json
from pathlib import Path

from utils.knowledge_base import knowledge_labels_and_banned_extras

RULES_PATH = Path(__file__).resolve().parent.parent / "data" / "compliance_rules.json"


def check_compliance(content: str, scenario: str = "general") -> list[str]:
    rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    issues: list[str] = []
    lower = content.lower()

    for phrase in rules.get("banned_phrases", []):
        if phrase.lower() in lower:
            issues.append(phrase)

    _, kb_phrases = knowledge_labels_and_banned_extras(scenario)
    for phrase in kb_phrases:
        if phrase.lower() in lower:
            if phrase not in issues:
                issues.append(phrase)

    return issues


def check_compliance_legacy(content: str) -> list[str]:
    """Backward-compatible entry when scenario is unknown."""
    return check_compliance(content, "general")
