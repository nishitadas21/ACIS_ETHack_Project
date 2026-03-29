"""
Publisher Agent — simulates multi-channel distribution with timestamps, UTM, retries, and recovery logs.
"""

from __future__ import annotations

from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _simulate_instagram_post(platform: str, post: str, idx: int, ts: str, rid: str, utm: str) -> tuple[dict, list[dict]]:
    """
    Instagram: fail once, retry once; if still failing -> fallback scheduling message.
    Returns (channel_entry, recovery_trace).
    """
    trace: list[dict] = []
    if platform.lower() != "instagram":
        return (
            {
                "platform": platform,
                "status": "queued",
                "scheduled_at": ts,
                "published_at": None,
                "copy": post,
                "utm": utm,
                "mock_post_url": f"https://social-sim.enterprise.example/{platform.lower()}/post/{rid}-{idx}",
                "ui_hint": "success",
            },
            trace,
        )

    trace.append(
        {
            "platform": "Instagram",
            "phase": "initial_post",
            "outcome": "failed",
            "ui": "failed",
            "message": "Simulated edge error (429 / policy check).",
        }
    )
    trace.append(
        {
            "platform": "Instagram",
            "phase": "retry",
            "outcome": "retrying",
            "ui": "retrying",
            "message": "Retrying publish once with backoff (simulated).",
        }
    )
    trace.append(
        {
            "platform": "Instagram",
            "phase": "retry_attempt",
            "outcome": "failed",
            "ui": "failed",
            "message": "Second attempt still failing (simulated).",
        }
    )
    trace.append(
        {
            "platform": "Instagram",
            "phase": "fallback",
            "outcome": "alternative_scheduling",
            "ui": "failed",
            "message": "Switching to alternative scheduling; marking as failed but logged for retry.",
        }
    )

    return (
        {
            "platform": platform,
            "status": "failed",
            "scheduled_at": ts,
            "published_at": None,
            "copy": post,
            "utm": utm,
            "mock_post_url": f"https://social-sim.enterprise.example/{platform.lower()}/post/{rid}-{idx}",
            "fallback": "queued_for_ops_retry",
            "ui_hint": "failed",
            "operator_note": "Marked as failed but logged for retry — alternate slot T+24h (simulated).",
        },
        trace,
    )


def publish_content(parsed_content: dict, run_id: str | None = None) -> dict:
    """
    Simulate website, social queue, and knowledge base.

    Status values include published | queued | failed. Instagram path demonstrates retry + fallback.
    """
    ts = _now_iso()
    rid = run_id or ts.replace(":", "").replace("+", "")[:16]

    blog = (parsed_content.get("blog") or "").strip()
    social_posts = parsed_content.get("social_posts") or []
    faq = (parsed_content.get("faq") or "").strip()

    channels: dict = {
        "website": None,
        "social_media": [],
        "knowledge_base": None,
    }
    publisher_recovery_log: list[dict] = []

    if blog:
        slug = "-".join(blog.split()[:6]).lower().replace(":", "")[:48]
        utm = f"utm_source=web&utm_medium=owned&utm_campaign=acis_et26&utm_content={rid}"
        channels["website"] = {
            "channel": "website",
            "url": f"https://content-ops.enterprise.example/blog/{slug}?{utm}",
            "status": "published",
            "published_at": ts,
            "utm": utm,
            "excerpt": blog[:220] + ("…" if len(blog) > 220 else ""),
            "ui_hint": "success",
        }

    for i, post in enumerate(social_posts[:5], start=1):
        platforms = ["LinkedIn", "X", "Instagram"]
        platform = platforms[(i - 1) % len(platforms)]
        utm = (
            f"utm_source={platform.lower()}&utm_medium=social&utm_campaign=et_ai_hackathon&utm_content=post{i}_{rid}"
        )

        if platform.lower() == "instagram":
            entry, trace = _simulate_instagram_post(platform, post, i, ts, rid, utm)
            channels["social_media"].append(entry)
            publisher_recovery_log.extend(trace)
            continue

        if i == 1:
            status = "published"
            published_at = ts
            ui_hint = "success"
        else:
            status = "queued"
            published_at = None
            ui_hint = "success"

        channels["social_media"].append(
            {
                "platform": platform,
                "status": status,
                "scheduled_at": ts,
                "published_at": published_at,
                "copy": post,
                "utm": utm,
                "mock_post_url": f"https://social-sim.enterprise.example/{platform.lower()}/post/{rid}-{i}",
                "ui_hint": ui_hint,
            }
        )

    if faq:
        kb_utm = f"utm_source=kb&utm_medium=internal&utm_campaign=enablement_{rid}"
        channels["knowledge_base"] = {
            "system": "internal_kb",
            "doc_id": f"kb-enterprise-content-{rid}",
            "status": "published",
            "indexed_at": ts,
            "utm": kb_utm,
            "preview": faq[:240] + ("…" if len(faq) > 240 else ""),
            "ui_hint": "success",
        }

    return {
        "status": "success",
        "run_correlation_id": rid,
        "generated_at": ts,
        "channels": channels,
        "publisher_recovery_log": publisher_recovery_log,
        "notes": "Simulation only — recovery trace documents retry + fallback decisions.",
    }
