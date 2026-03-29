"""
Strategy Agent — chooses channel / governance posture from risk + engagement signals.

Outputs one primary mode: video-first, blog-heavy, or compliance-strict mode.
"""


from __future__ import annotations


def strategy_agent(
    scores: dict,
    scenario: str,
    video_pivot: bool,
) -> dict:
    """
    Decide go-to-market content strategy from scored outputs.

    Prints a visible banner for live demos; same payload is also logged by the orchestrator.
    """
    compliance_risk = int(scores.get("compliance_risk") or 0)
    engagement = int(scores.get("engagement_score") or 0)
    brand = int(scores.get("brand_alignment") or 0)

    print("\n--- STRATEGY DECISION ---")

    if compliance_risk >= 45 or scenario in ("high_compliance", "strict_regulation"):
        mode = "compliance-strict mode"
        rationale = (
            "Residual compliance risk or regulated scenario - prioritize legal review cadence, "
            "conservative claims, and documentation-heavy assets."
        )
        priority = ["legal_review", "blog", "email", "social_proof"]
    elif video_pivot or engagement >= 78:
        mode = "video-first"
        rationale = (
            "Audience signals favor motion formats - lead with short-form video and repurpose "
            "long-form blog as canonical reference."
        )
        priority = ["video", "reels", "blog", "community"]
    else:
        mode = "blog-heavy"
        rationale = (
            "Earned attention via depth - anchor on long-form narrative, then atomize into social snippets."
        )
        priority = ["blog", "linkedin", "newsletter", "video"]

    if brand < 60:
        rationale += " Brand alignment soft - tighten voice guides before scaling spend."

    summary = {
        "primary_mode": mode,
        "rationale": rationale,
        "channel_priority": priority,
        "inputs": {
            "compliance_risk": compliance_risk,
            "engagement_score": engagement,
            "brand_alignment": brand,
            "scenario": scenario,
            "video_pivot": video_pivot,
        },
    }
    print(f"Selected strategy: {mode}")
    print(f"Rationale: {rationale}\n")
    return summary
