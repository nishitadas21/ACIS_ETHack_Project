"""
Enterprise content pipeline orchestration.

Data flow (high level):
  User prompt (+ optional product_spec)
    → Learning Agent (embeddings) + scenario detection
    → Creative Agent (multi-asset bundle)
    → Compliance Agent + Fixer (retry / alternate regen / escalation)
    → Performance vs. Compliance Advocate debate → Judge Agent
    → Risk Agent → autonomous branches (strict / engagement)
    → Strategy Agent (go-to-market mode)
    → Formatter (blog / social[] / FAQ)
    → Localization Agent (extensible locales)
    → Publisher Agent (timestamped simulation)
    → Impact metrics + audit append

Each stage emits reasoning traces and simulated model-routing notes for judges.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from agents.creative import (
    detect_video_pivot,
    generate_content,
    generate_safest_content,
)
from agents.auditor import check_compliance
from agents.fixer import fix_content
from agents.learning import learning_agent
from memory.audit_store import append_audit_record
from memory.hil_store import load_checkpoint, save_checkpoint
from orchestration_tail import run_orchestration_tail
from utils.knowledge_base import knowledge_labels_and_banned_extras
from utils.model_router import route_model
from utils.reasoning import trace_block

ROOT = Path(__file__).resolve().parent
FEEDBACK_PATH = ROOT / "memory" / "feedback.json"


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log(
    logs: list,
    step: str,
    agent: str,
    message: str,
    detail: dict | None = None,
) -> None:
    payload = {"timestamp": _ts(), "step": step, "agent": agent, "message": message}
    if detail:
        payload["detail"] = detail
    logs.append(payload)


def detect_scenario(prompt: str) -> str:
    """Classify request for stricter compliance or engagement-first tone."""
    p = prompt.lower()
    if any(k in p for k in ("fintech", "finance", "banking", "payments", "lending", "trading")):
        return "high_compliance"
    if any(k in p for k in ("health", "medical", "pharma", "hipaa", "diagnosis")):
        return "strict_regulation"
    if any(k in p for k in ("engagement", "viral", "growth", "campaign", "launch", "product launch")):
        return "engagement_boost"
    return "general"


def save_feedback(content: str, scores: dict) -> None:
    entry = {"content": content, "scores": scores}
    try:
        FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
        if FEEDBACK_PATH.exists():
            existing = json.loads(FEEDBACK_PATH.read_text(encoding="utf-8"))
        else:
            existing = []
    except (json.JSONDecodeError, OSError):
        existing = []
    existing.append(entry)
    FEEDBACK_PATH.write_text(json.dumps(existing, indent=2), encoding="utf-8")


def _format_product_spec(product_spec: str | dict | None) -> tuple[str, dict]:
    """Normalize knowledge payload for prompt injection + audit metadata."""
    if product_spec is None:
        return "", {}
    if isinstance(product_spec, dict):
        text = json.dumps(product_spec, indent=2, ensure_ascii=False)
        meta = {"type": "structured", "keys": list(product_spec.keys())[:24]}
    else:
        text = str(product_spec).strip()
        meta = {"type": "text", "chars": len(text)}
    return text, meta


def run_content_pipeline(
    user_prompt: str,
    product_spec: str | dict | None = None,
    *,
    interactive_hil: bool = False,
) -> dict:
    """
    Execute the multi-agent workflow. Returns JSON-serializable dict (no JSON strings for objects).

    product_spec: optional internal facts sheet injected before generation (knowledge-to-content).
    interactive_hil: if True, pause at severe compliance failure for POST /pipeline/human-decision.
    """
    logs: list = []
    run_uuid = str(uuid.uuid4())[:8]
    prompt = (user_prompt or "").strip() or "Enterprise product update for professional audiences."
    issues_history: list[dict] = []

    _log(
        logs,
        "orchestrator",
        "Orchestrator",
        "Pipeline started",
        {"prompt_preview": prompt[:240], "run_uuid": run_uuid},
    )

    # ----- Knowledge-to-content -----
    spec_text, spec_meta = _format_product_spec(product_spec)
    knowledge_block = ""
    if spec_text:
        knowledge_block = f"\n\n[INTERNAL PRODUCT KNOWLEDGE — CONFIDENTIAL]\n{spec_text}\n"
        _log(
            logs,
            "input",
            "Orchestrator",
            "Using internal product knowledge",
            trace_block(
                received_preview=spec_text[:400],
                decision="inject_spec",
                rationale="Grounding generation in supplied product facts before Creative Agent runs.",
                extra={"product_spec": spec_meta},
            ),
        )

    scenario = detect_scenario(prompt + knowledge_block)
    video_pivot = detect_video_pivot(prompt + knowledge_block)

    _log(
        logs,
        "scenario",
        "Orchestrator",
        f"Scenario={scenario}; video_pivot={video_pivot}",
        trace_block(
            received_preview=prompt[:400],
            decision=f"classify:{scenario}",
            rationale="Keyword routing for regulated vs. growth motions; video pivot from performance brief.",
            extra={"video_pivot": video_pivot},
        ),
    )

    kb_labels, _kb_extra = knowledge_labels_and_banned_extras(scenario)
    if kb_labels:
        _log(
            logs,
            "knowledge",
            "Knowledge Base",
            f"Knowledge retrieved: {', '.join(kb_labels)}",
            trace_block(
                received_preview=prompt[:300],
                decision="kb_load",
                rationale="RAG-lite static KB (data/knowledge.json) merged into governance context.",
                extra={"sections": kb_labels},
            ),
        )
        _log(
            logs,
            "compliance",
            "Compliance Agent",
            "Applied compliance policy from KB (supplemental phrase pack)",
            {"knowledge_sections": kb_labels},
        )

    tier, route_msg = route_model("learning_retrieval")
    _log(logs, "routing", "Model Router", route_msg, {"tier": tier, "display": route_msg})

    # ----- Learning -----
    try:
        learning = learning_agent(prompt + knowledge_block, scenario=scenario)
    except Exception as exc:  # noqa: BLE001
        learning = {"insight": "Learning skipped", "suggestion": "", "error": str(exc)}
        _log(
            logs,
            "learning",
            "Learning Agent",
            "Embedding retrieval failed — cold start",
            {"error": str(exc)},
        )
    else:
        _log(
            logs,
            "learning",
            "Learning Agent",
            f"Insight: {learning.get('insight', '')[:180]}",
            trace_block(
                received_preview=prompt[:400],
                decision="apply_historical_nudge",
                rationale="Similar past outputs inform tone and compliance posture.",
                extra={"suggestion": learning.get("suggestion", "")},
            ),
        )

    enhanced_prompt = prompt + knowledge_block
    if learning.get("suggestion"):
        enhanced_prompt = f"{enhanced_prompt}\nMemory nudge: {learning['suggestion']}"

    if scenario == "high_compliance":
        enhanced_prompt += "\nConstraints: realistic claims only; no guaranteed returns; follow financial promotion norms."
    elif scenario == "strict_regulation":
        enhanced_prompt += "\nConstraints: no medical claims; consult-professional tone; evidence-based wording."
    elif scenario == "engagement_boost":
        enhanced_prompt += "\nConstraints: punchy hooks, clear CTA, scannable format; remain truthful."

    if video_pivot:
        enhanced_prompt += (
            "\nPerformance pivot: stakeholder data shows video outperforms text — bias assets to motion-first calendar."
        )

    # ----- Creative generation -----
    tier, route_msg = route_model("draft_generation")
    _log(logs, "routing", "Model Router", route_msg, {"tier": tier, "display": route_msg})

    _log(
        logs,
        "generate",
        "Creative Agent",
        "Synthesizing blog + 3 social + FAQ from grounded prompt",
        trace_block(
            received_preview=enhanced_prompt[:500],
            decision="multi_asset_bundle",
            rationale="Structured sections preserve downstream parsing and channel routing.",
            extra={"scenario": scenario, "video_pivot": video_pivot},
        ),
    )
    content = generate_content(enhanced_prompt, scenario=scenario, strict=False, video_pivot=video_pivot)

    # ----- Compliance / fix / alternate / escalation -----
    human_in_loop_escalation = False
    alternate_used = False
    compliance_round = 0

    while True:
        issues = check_compliance(content, scenario)
        if not issues:
            msg = "PASS"
        elif len(issues) == 1:
            msg = f"Auditor: detected risky phrase → '{issues[0]}'"
        else:
            msg = f"Auditor: detected risky phrase → '{issues[0]}' (+{len(issues) - 1} more)"
        _log(
            logs,
            "compliance",
            "Compliance Agent",
            f"Auditor: {msg}",
            trace_block(
                received_preview=content[:500],
                decision="flag_issues" if issues else "clear",
                rationale=(
                    "Dictionary scan: compliance_rules.json + knowledge base phrases."
                    if issues
                    else "No banned phrases matched policy + KB pack."
                ),
                extra={"issues": issues},
            ),
        )
        issues_history.append({"round": compliance_round, "issues": list(issues)})

        if not issues:
            break

        if compliance_round >= 2:
            break

        _log(
            logs,
            "fix",
            "Fixer Agent",
            f"Rewrite triggered for tokens: {issues}",
            trace_block(
                received_preview=content[:500],
                decision="replace_with_policy_tokens",
                rationale="Map violations to pre-approved alternatives from compliance_rules.json.",
                extra={"issues": issues},
            ),
        )
        content = fix_content(content, issues)
        compliance_round += 1

    if check_compliance(content, scenario):
        alternate_used = True
        tier, route_msg = route_model("compliance_reasoning")
        _log(logs, "routing", "Model Router", route_msg, {"tier": tier, "display": route_msg})
        _log(
            logs,
            "recovery",
            "Orchestrator",
            "Alternate strategy: regenerate strict bundle",
            trace_block(
                received_preview=content[:400],
                decision="regenerate_strict",
                rationale="Two fix passes insufficient — Creative Agent rerun in high-compliance template.",
            ),
        )
        content = generate_content(
            enhanced_prompt + "\nRegenerate strictly compliant asset bundle.",
            scenario="high_compliance",
            strict=True,
            video_pivot=False,
        )
        issues = check_compliance(content, scenario)
        issues_history.append({"round": "post_alternate", "issues": list(issues)})
        if issues:
            content = fix_content(content, issues)

    if check_compliance(content, scenario):
        human_in_loop_escalation = True
        _log(
            logs,
            "escalation",
            "Orchestrator",
            "Escalated to human — manual approval required due to compliance risk",
            trace_block(
                received_preview=content[:400],
                decision="hil_escalation",
                rationale="Repeated automation failures after fix + strict regen; counsel review gate.",
            ),
        )
        if interactive_hil:
            checkpoint_id = save_checkpoint(
                {
                    "version": 1,
                    "run_uuid": run_uuid,
                    "logs": logs,
                    "prompt": prompt,
                    "spec_meta": spec_meta,
                    "spec_text": spec_text,
                    "enhanced_prompt": enhanced_prompt,
                    "scenario": scenario,
                    "video_pivot": video_pivot,
                    "learning": learning,
                    "issues_history": issues_history,
                    "alternate_used": alternate_used,
                }
            )
            append_audit_record(
                {
                    "run_uuid": run_uuid,
                    "prompt": prompt,
                    "status": "awaiting_human",
                    "checkpoint_id": checkpoint_id,
                    "issues_history": issues_history,
                    "human_in_loop_required": True,
                }
            )
            return {
                "human_in_loop_required": True,
                "human_in_loop_required_reason": "Manual approval required due to compliance risk",
                "checkpoint_id": checkpoint_id,
                "pipeline_status": "awaiting_human",
                "pipeline_logs": logs,
                "run_uuid": run_uuid,
                "blog": "",
                "social_posts": [],
                "faq": "",
                "localized_version": "",
                "localization": {},
                "content_calendar": [],
                "scores": {},
                "final_decision": {"human_in_loop_pending": True, "checkpoint_id": checkpoint_id},
                "confidence_explanation": {},
                "collaboration_summary": {},
                "publishing_output": {},
                "impact": {},
                "learning": learning,
            }

        content = generate_safest_content(enhanced_prompt, topic_hint=prompt[:120])
        issues = check_compliance(content, scenario)
        if issues:
            content = fix_content(content, issues)
        issues_history.append({"round": "hil_template", "issues": list(check_compliance(content, scenario))})

    result = run_orchestration_tail(
        logs=logs,
        _log=_log,
        run_uuid=run_uuid,
        prompt=prompt,
        spec_text=spec_text,
        spec_meta=spec_meta,
        enhanced_prompt=enhanced_prompt,
        scenario=scenario,
        video_pivot=video_pivot,
        learning=learning,
        content=content,
        issues_history=issues_history,
        alternate_used=alternate_used,
        human_in_loop_escalation=human_in_loop_escalation,
        feedback_saver=save_feedback,
    )
    result.setdefault("human_in_loop_required", False)
    return result


def resume_after_human_decision(checkpoint_id: str, decision: str) -> dict:
    """
    Resume pipeline after human review (POST /pipeline/human-decision).

    approve: use safest template path; reject: force Creative Agent regeneration.
    """
    if decision not in ("approve", "reject"):
        raise ValueError("decision must be 'approve' or 'reject'")

    ckpt = load_checkpoint(checkpoint_id)
    logs = ckpt["logs"]
    run_uuid = ckpt["run_uuid"]
    prompt = ckpt["prompt"]
    spec_text = ckpt["spec_text"]
    spec_meta = ckpt["spec_meta"]
    enhanced_prompt = ckpt["enhanced_prompt"]
    scenario = ckpt["scenario"]
    video_pivot = ckpt["video_pivot"]
    learning = ckpt["learning"]
    issues_history = list(ckpt["issues_history"])
    alternate_used = ckpt["alternate_used"]

    if decision == "approve":
        content = generate_safest_content(enhanced_prompt, topic_hint=prompt[:120])
        _log(
            logs,
            "hil",
            "Human Review",
            "Human approved — proceeding with compliance-cleared template",
            trace_block(
                received_preview=content[:400],
                decision="human_approve",
                rationale="Approver accepted escalation; deploy counsel-grade safest bundle.",
            ),
        )
    else:
        content = generate_content(
            enhanced_prompt + "\nHuman reviewer rejected prior bundles. Regenerate a completely new compliant asset set.",
            scenario=scenario,
            strict=True,
            video_pivot=False,
        )
        _log(
            logs,
            "hil",
            "Human Review",
            "Human rejected — regenerating via Creative Agent",
            trace_block(
                received_preview=enhanced_prompt[:400],
                decision="human_reject",
                rationale="Reject path triggers fresh generation with stricter constraints.",
            ),
        )

    issues = check_compliance(content, scenario)
    if issues:
        content = fix_content(content, issues)
    issues_history.append(
        {"round": f"post_human_{decision}", "issues": list(check_compliance(content, scenario))}
    )

    append_audit_record(
        {
            "run_uuid": run_uuid,
            "checkpoint_id": checkpoint_id,
            "human_decision": decision,
            "status": "resumed_from_hil",
        }
    )

    out = run_orchestration_tail(
        logs=logs,
        _log=_log,
        run_uuid=run_uuid,
        prompt=prompt,
        spec_text=spec_text,
        spec_meta=spec_meta,
        enhanced_prompt=enhanced_prompt,
        scenario=scenario,
        video_pivot=video_pivot,
        learning=learning,
        content=content,
        issues_history=issues_history,
        alternate_used=alternate_used,
        human_in_loop_escalation=True,
        feedback_saver=save_feedback,
    )
    out["human_in_loop_required"] = False
    out["final_decision"] = dict(out.get("final_decision") or {})
    out["final_decision"]["human_resolution"] = decision
    return out
