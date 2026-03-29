"""
Post-compliance orchestration: debate -> risk -> strategy -> format -> localize -> publish -> audit.

Separated from content_pipeline.py to support human-in-the-loop resume without duplication.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from agents.creative import generate_content, generate_content_calendar
from agents.auditor import check_compliance
from agents.fixer import fix_content
from agents.performance import performance_agent
from agents.debate import compliance_advocate_agent, judge_agent
from agents.risk import risk_confidence_score
from agents.localizer import localize_content
from agents.publisher import publish_content
from agents.strategy import strategy_agent
from api.formatter import format_structured_output
from memory.audit_store import append_audit_record
from utils.model_router import route_model
from utils.reasoning import trace_block
from utils.impact import compute_impact_metrics

COMPLIANCE_BRANCH_THRESHOLD = 45
ENGAGEMENT_BRANCH_THRESHOLD = 65


def run_orchestration_tail(
    *,
    logs: list[dict],
    _log: Callable[..., None],
    run_uuid: str,
    prompt: str,
    spec_text: str,
    spec_meta: dict,
    enhanced_prompt: str,
    scenario: str,
    video_pivot: bool,
    learning: dict[str, Any],
    content: str,
    issues_history: list,
    alternate_used: bool,
    human_in_loop_escalation: bool,
    feedback_saver: Callable[[str, dict], None],
) -> dict[str, Any]:
    """Run stages from multi-agent debate through publish and return the API bundle."""

    # ----- Debate -----
    tier, route_msg = route_model("debate_resolution")
    _log(logs, "routing", "Model Router", route_msg, {"tier": tier, "display": route_msg})

    perf = performance_agent(content)
    _log(
        logs,
        "debate",
        "Performance Agent",
        "Suggested engagement-oriented rewrite",
        trace_block(
            received_preview=content[:400],
            decision="boost_hook_and_cta",
            rationale=perf.get("feedback", ""),
            extra={"score": perf.get("score")},
        ),
    )

    advocate = compliance_advocate_agent(perf.get("suggested_content", content))
    _log(
        logs,
        "debate",
        "Compliance Advocate",
        "Debate stance recorded",
        trace_block(
            received_preview=(perf.get("suggested_content") or "")[:400],
            decision="tighten_language",
            rationale=advocate.get("feedback", ""),
            extra={"score": advocate.get("score")},
        ),
    )

    decision = judge_agent(content, perf, advocate)
    final_text = decision["final_content"]
    _log(
        logs,
        "debate",
        "Judge Agent",
        decision.get("reason", ""),
        trace_block(
            received_preview=content[:300],
            decision=f"winner:{decision.get('winner')}",
            rationale=decision.get("reason", ""),
            extra={"performance_score": perf.get("score"), "advocate_score": advocate.get("score")},
        ),
    )

    tier, route_msg = route_model("risk_synthesis")
    _log(logs, "routing", "Model Router", route_msg, {"tier": tier, "display": route_msg})
    scores = risk_confidence_score(final_text)
    _log(
        logs,
        "risk",
        "Risk Agent",
        "Composite scoring complete",
        trace_block(
            received_preview=final_text[:400],
            decision="score_card",
            rationale="Blend guideline similarity, residual phrase risk, and engagement heuristics.",
            extra=scores,
        ),
    )

    if scores.get("compliance_risk", 0) > COMPLIANCE_BRANCH_THRESHOLD:
        _log(
            logs,
            "branch",
            "Orchestrator",
            f"Branch: compliance_risk>{COMPLIANCE_BRANCH_THRESHOLD} → compliance-strict regeneration",
            trace_block(
                received_preview=final_text[:400],
                decision="strict_recompose",
                rationale="Residual risk triggers conservative re-generation before customer-facing release.",
                extra={"before_scores": dict(scores)},
            ),
        )
        final_text = generate_content(
            enhanced_prompt + "\nForced branch: minimize residual compliance risk; eliminate intensity terms.",
            scenario="high_compliance",
            strict=True,
            video_pivot=False,
        )
        alt_issues = check_compliance(final_text, scenario)
        if alt_issues:
            final_text = fix_content(final_text, alt_issues)
        scores = risk_confidence_score(final_text)
        _log(logs, "branch", "Risk Agent", "Re-score after strict branch", scores)

    if scores.get("engagement_score", 0) < ENGAGEMENT_BRANCH_THRESHOLD:
        _log(
            logs,
            "branch",
            "Orchestrator",
            f"Branch: engagement<{ENGAGEMENT_BRANCH_THRESHOLD} → performance optimization lane",
            trace_block(
                received_preview=final_text[:400],
                decision="performance_lane",
                rationale="Engagement KPI under target — apply Performance Agent output with advocate validation.",
            ),
        )
        boosted = performance_agent(final_text)
        candidate = boosted.get("suggested_content", final_text)
        advocate2 = compliance_advocate_agent(candidate)
        final_text = advocate2.get("suggested_content", candidate) if advocate2.get("score", 0) < 70 else candidate
        scores = risk_confidence_score(final_text)
        _log(logs, "branch", "Risk Agent", "Re-score after engagement branch", scores)

    if scores.get("brand_alignment", 0) < 60:
        _log(
            logs,
            "heal",
            "Orchestrator",
            "Brand alignment low — regenerating brand-safe skeleton",
            {"before": dict(scores)},
        )
        final_text = generate_content(
            f"Brand-aligned rewrite (professional, trustworthy): {final_text[:800]}",
            scenario=scenario,
            strict=True,
            video_pivot=False,
        )
        bi = check_compliance(final_text, scenario)
        if bi:
            final_text = fix_content(final_text, bi)
        scores = risk_confidence_score(final_text)

    tier, route_msg = route_model("strategy_selection")
    _log(logs, "routing", "Model Router", route_msg, {"tier": tier, "display": route_msg})
    strategy = strategy_agent(scores, scenario, video_pivot)
    _log(
        logs,
        "strategy",
        "Strategy Agent",
        "--- STRATEGY DECISION --- " + strategy["primary_mode"],
        trace_block(
            received_preview=json.dumps(scores),
            decision=strategy["primary_mode"],
            rationale=strategy["rationale"],
            extra={"channel_priority": strategy.get("channel_priority")},
        ),
    )

    calendar = generate_content_calendar((prompt + spec_text)[:120], video_pivot)
    _log(
        logs,
        "calendar",
        "Creative Agent",
        "Generated editorial calendar",
        trace_block(
            received_preview=(prompt + spec_text)[:200],
            decision="three_day_plan",
            rationale="Video pivot requests motion-first sequencing by default.",
            extra={"entries": calendar},
        ),
    )

    tier, route_msg = route_model("format_bundle")
    _log(logs, "routing", "Model Router", route_msg, {"tier": tier, "display": route_msg})
    parsed = format_structured_output(final_text)
    _log(
        logs,
        "parse",
        "Structured Formatter",
        "Normalized blog / social[] / FAQ",
        trace_block(
            received_preview=final_text[:300],
            decision="split_sections",
            rationale="Parser enforces enterprise API contract for channel agents.",
            extra={
                "blog_len": len(parsed.get("blog") or ""),
                "social_count": len(parsed.get("social_posts") or []),
            },
        ),
    )

    loc = localize_content(parsed.get("blog") or final_text, "Hindi")
    _log(
        logs,
        "localize",
        "Localization Agent",
        loc.get("log_message", "complete"),
        trace_block(
            received_preview=(parsed.get("blog") or "")[:400],
            decision="translate_blog_hi",
            rationale="Regional mandate — Hindi blog first; extensible to ta/bn/es via LANG_MAP.",
            extra={
                "used_offline_fallback": loc.get("used_offline_fallback"),
                "language_code": loc.get("language_code"),
            },
        ),
    )

    publishing = publish_content(parsed, run_id=run_uuid)
    pub_notes = publishing.get("publisher_recovery_log") or []
    _log(
        logs,
        "publish",
        "Publisher Agent",
        "Channel simulation finished",
        trace_block(
            received_preview=json.dumps({"channels": list(publishing.get("channels", {}).keys())}),
            decision=publishing.get("status", "unknown"),
            rationale="Retry/recovery trace attached in publishing_output.publisher_recovery_log.",
            extra={"recovery_steps": pub_notes},
        ),
    )

    feedback_saver(final_text, scores)

    impact = compute_impact_metrics(
        scores,
        human_in_loop=human_in_loop_escalation,
        escalation_used=human_in_loop_escalation or alternate_used,
    )
    print(impact["time_savings_summary"])

    collaboration_summary = {
        "performance_agent": perf.get("feedback"),
        "compliance_advocate": advocate.get("feedback"),
        "judge": {
            "winner": decision.get("winner"),
            "reason": decision.get("reason"),
        },
        "narrative": (
            f"Performance agent suggested engagement edits; compliance advocate "
            f"{'accepted tone with tightening' if advocate.get('score', 0) >= 80 else 'pushed safer replacements'}. "
            f"Judge selected {decision.get('winner')} path: {decision.get('reason')}"
        ),
    }

    compliance_risk = int(scores.get("compliance_risk") or 0)
    brand_al = int(scores.get("brand_alignment") or 0)
    if compliance_risk < 22 and brand_al > 74:
        conf_label = "high"
    elif compliance_risk < 45:
        conf_label = "medium"
    else:
        conf_label = "low"

    confidence_explanation = {
        "confidence": conf_label,
        "why_final_output": (
            f"{decision.get('reason', '')} "
            f"Residual compliance risk {compliance_risk}%, brand alignment {brand_al}%, "
            f"engagement {scores.get('engagement_score')}% — "
            f"{'human review recommended' if human_in_loop_escalation else 'auto-publish eligible subject to policy tier'}."
        ),
    }

    final_decision = {
        "reason": decision.get("reason", ""),
        "winner": decision.get("winner"),
        "alternate_strategy_used": alternate_used,
        "human_in_loop_escalation": human_in_loop_escalation,
        "scenario": scenario,
        "video_pivot": video_pivot,
        "strategy": {
            "primary_mode": strategy.get("primary_mode"),
            "rationale": strategy.get("rationale"),
            "channel_priority": strategy.get("channel_priority"),
        },
    }

    append_audit_record(
        {
            "run_uuid": run_uuid,
            "prompt": prompt,
            "product_spec_meta": spec_meta,
            "generated_preview": final_text[:4000],
            "issues_history": issues_history,
            "final_decision": final_decision,
            "scores": scores,
            "human_in_loop": human_in_loop_escalation,
            "strategy": strategy,
            "impact": impact,
        }
    )

    return {
        "blog": parsed.get("blog", ""),
        "social_posts": parsed.get("social_posts", []),
        "faq": parsed.get("faq", ""),
        "localized_version": loc.get("localized_text", ""),
        "localization": {
            "language": loc.get("language"),
            "language_code": loc.get("language_code"),
            "used_offline_fallback": loc.get("used_offline_fallback"),
        },
        "content_calendar": calendar,
        "scores": scores,
        "final_decision": final_decision,
        "confidence_explanation": confidence_explanation,
        "collaboration_summary": collaboration_summary,
        "publishing_output": publishing,
        "impact": impact,
        "learning": learning,
        "pipeline_logs": logs,
        "run_uuid": run_uuid,
        "human_in_loop_required": False,
    }
