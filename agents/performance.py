"""
Performance Agent — optimizes for engagement while preserving structure.

Light-touch edits: hook, scannability, CTA. Avoids destructive transforms on FAQ.
"""


def performance_agent(content: str) -> dict:
    text = content.strip()
    lower = text.lower()

    improved = text

    # Opening hook if the draft starts flat
    if not any(word in lower[:120] for word in ("introducing", "today", "ready", "new:", "update")):
        improved = f"Today we’re sharing something worth your attention.\n\n{improved}"

    # Add a single CTA line if none present
    if not any(word in lower for word in ("read the", "see the", "get started", "talk to", "contact")):
        improved = improved.rstrip() + "\n\nNext step: read the full update and pick one workflow to pilot this week."

    # Light emphasis for social section headers
    if "social:" in lower and "**" not in improved:
        improved = improved.replace("SOCIAL:", "SOCIAL (ready to post):")

    score = 72
    if "?" in improved:
        score += 5
    if any(w in improved.lower() for w in ("pilot", "checklist", "this week", "today")):
        score += 8
    score = min(score, 96)

    return {
        "agent": "performance",
        "feedback": "Increased clarity, hook strength, and a single high-intent CTA without rewriting compliance-sensitive claims.",
        "suggested_content": improved,
        "score": score,
    }
