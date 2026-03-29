"""
Impact quantification — compares manual content ops effort vs. automated pipeline.
"""

from __future__ import annotations


def compute_impact_metrics(
    scores: dict,
    *,
    human_in_loop: bool,
    escalation_used: bool,
) -> dict:
    manual_hours = 2.0
    base_ai_minutes = 4.5
    if human_in_loop:
        base_ai_minutes += 6.5
    if escalation_used:
        base_ai_minutes += 2.0

    compliance_risk = float(scores.get("compliance_risk") or 0)
    # Higher residual risk => fewer errors "caught" vs fully manual baseline
    compliance_error_reduction_pct = min(
        96.0,
        max(
            38.0,
            72.0 + (45.0 - min(compliance_risk, 85.0)) * 0.35,
        ),
    )

    engagement = float(scores.get("engagement_score") or 0)
    engagement_lift_pct = min(55.0, max(5.0, engagement - 52.0))

    time_savings_summary = (
        f"Manual: {manual_hours:g} hrs -> AI: {base_ai_minutes:.1f} mins "
        f"({manual_hours * 60:.0f} min vs {base_ai_minutes:.1f} min wall time)"
    )
    # Unicode arrow for dashboards / JSON clients (avoid printing this on legacy Windows consoles)
    time_savings_display = (
        f"Manual: {manual_hours:g} hrs \u2192 AI: {base_ai_minutes:.1f} mins"
    )

    return {
        "manual_effort_hours": manual_hours,
        "ai_pipeline_minutes": round(base_ai_minutes, 2),
        "time_savings_summary": time_savings_summary,
        "time_savings_display": time_savings_display,
        "compliance_error_reduction_pct": round(compliance_error_reduction_pct, 1),
        "engagement_lift_pct": round(engagement_lift_pct, 1),
        "assumptions": [
            "Manual estimate assumes writer + compliance + localization handoffs.",
            "AI estimate includes automated checks and simulated routing latency.",
        ],
    }
