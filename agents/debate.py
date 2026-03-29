"""
Multi-agent debate: Performance output vs Compliance Advocate.

Judge Agent selects a final composite that favors compliance when scores diverge.
"""


def compliance_advocate_agent(content: str) -> dict:
    """
    Compliance Advocate (debate participant) — tightens tone and scrubs risky patterns.
    Distinct from the Compliance Agent (auditor) that runs rule checks in auditor.py.
    """
    risky = ["guaranteed", "100%", "risk-free", "instant profit", "no risk"]
    flagged: list[str] = []
    cleaned = content

    for word in risky:
        if word in cleaned.lower():
            flagged.append(word)
            cleaned = cleaned.replace(word, "[redacted: strong claim]")

    # Soften absolute language slightly in body copy
    replacements = {
        "always": "typically",
        "never fails": "aims to reduce failure modes",
    }
    for a, b in replacements.items():
        if a in cleaned.lower():
            idx = cleaned.lower().find(a)
            if idx != -1:
                cleaned = cleaned[:idx] + b + cleaned[idx + len(a) :]

    score = 92 if not flagged else max(55, 92 - len(flagged) * 12)

    return {
        "agent": "compliance_advocate",
        "feedback": "Debate stance: prioritize safe language and auditable claims."
        + (f" Flagged: {flagged}" if flagged else ""),
        "suggested_content": cleaned,
        "score": score,
    }


def judge_agent(original_content: str, perf: dict, advocate: dict) -> dict:
    """
    Judge Agent — balances engagement (performance) vs conservative stance (advocate).
    """
    perf_score = int(perf.get("score") or 0)
    adv_score = int(advocate.get("score") or 0)

    if adv_score < 70:
        final = advocate.get("suggested_content", original_content)
        winner = "compliance_advocate"
        reason = "Compliance advocate flagged material issues; selecting the safer variant."
    elif perf_score >= adv_score + 5:
        final = perf.get("suggested_content", original_content)
        winner = "performance"
        reason = "Content is within tolerance; prioritizing the engagement-optimized variant."
    else:
        # Blend: take advocate text but keep performance hook if present
        final = advocate.get("suggested_content", original_content)
        perf_text = perf.get("suggested_content", "")
        first_block = perf_text.split("\n\n", 1)[0] if perf_text else ""
        if first_block and len(first_block) < 260:
            body = final.split("\n\n", 1)[-1]
            final = f"{first_block}\n\n{body}"
        winner = "hybrid"
        reason = "Hybrid decision: preserve engagement lead-in with advocate-cleaned body."

    return {
        "final_content": final,
        "reason": reason,
        "winner": winner,
        "original_content": original_content,
    }
