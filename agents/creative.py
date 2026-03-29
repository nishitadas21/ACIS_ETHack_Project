"""
Creative Agent — generates structured enterprise content:
blog, social captions, FAQ.

Supports video-forward pivots, strict / safest bundles, and a 3-day content calendar.
Deterministic templates keep the hackathon demo runnable without API keys.
"""

from __future__ import annotations

import re


def _snippet_from_prompt(prompt: str, max_words: int = 28) -> str:
    words = prompt.replace("\n", " ").split()
    return " ".join(words[:max_words]) if words else "our latest platform capabilities"


def detect_video_pivot(prompt: str) -> bool:
    """True when brief signals short-form video outperforming text."""
    p = prompt.lower()
    keys = (
        "video performs",
        "video-first",
        "video first",
        "reels outperform",
        "tiktok",
        "youtube",
        "short-form video",
        "motion creative",
    )
    return any(k in p for k in keys)


def generate_content_calendar(topic: str, video_pivot: bool) -> list[dict]:
    """
    Lightweight editorial calendar for launch programs.

    Returns Day 1–3 plan with asset type and objective (simulated scheduling).
    """
    topic_clean = (topic or "product launch").strip()[:80]
    if video_pivot:
        return [
            {
                "day": 1,
                "asset_type": "Video",
                "title": f"Hero explainer — {topic_clean}",
                "objective": "Awareness + trust via founder narrative (15–45s cut + long cut).",
                "status": "planned",
            },
            {
                "day": 2,
                "asset_type": "Reel",
                "title": f"Proof point montage — {topic_clean}",
                "objective": "Social proof + UGC-style cuts for algorithmic reach.",
                "status": "planned",
            },
            {
                "day": 3,
                "asset_type": "Blog",
                "title": f"Canonical deep dive — {topic_clean}",
                "objective": "SEO + compliance-reviewed source of truth; feed FAQs from this doc.",
                "status": "planned",
            },
        ]
    return [
        {
            "day": 1,
            "asset_type": "Blog",
            "title": f"Launch narrative — {topic_clean}",
            "objective": "Establish positioning and gated CTA.",
            "status": "planned",
        },
        {
            "day": 2,
            "asset_type": "Social carousel",
            "title": f"3-slide story — {topic_clean}",
            "objective": "Atomize blog into LinkedIn / X thread.",
            "status": "planned",
        },
        {
            "day": 3,
            "asset_type": "Webinar invite",
            "title": f"Live Q&A — {topic_clean}",
            "objective": "Move MQLs through expert-led session.",
            "status": "planned",
        },
    ]


def generate_safest_content(prompt: str, topic_hint: str | None = None) -> str:
    """
    Human-in-the-loop escalation path: maximally conservative, review-oriented copy.
    """
    topic = topic_hint or _snippet_from_prompt(prompt)
    blog = f"""BLOG:
This communication is intentionally conservative pending human review. It references {topic} in general terms only.

No performance promises are made. Availability, pricing, and features are subject to change and regional regulation. Please consult your legal and compliance teams before external publication."""

    social = [
        "Pending approval: neutral announcement pointing readers to the official blog and policy pages.",
        "Internal-only suggested copy — replace after compliance sign-off.",
        "Hold for review: do not boost paid media until human approval is recorded.",
    ]

    faq = """FAQ:
Q: Why is this copy so generic?
A: Automated escalation selected the safest template after repeated compliance issues.

Q: What should we do next?
A: Route to a human reviewer, attach product facts, and republish after approval.

Q: Can we mention ROI?
A: Only with substantiation approved by your governance team."""

    return f"{blog.strip()}\n\nSOCIAL:\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(social)) + f"\n\n{faq.strip()}"


def generate_content(
    prompt: str,
    scenario: str = "general",
    strict: bool = False,
    video_pivot: bool = False,
) -> str:
    topic = _snippet_from_prompt(prompt)
    vp_lines = ""
    if video_pivot:
        vp_lines = (
            "\n\n[VIDEO-FORWARD BRIEF] Lead with motion: include a hero video hook, shot list cues, "
            "and social cuts referencing watch time / CTA in captions."
        )

    if strict or scenario == "high_compliance":
        blog = f"""BLOG:
Today we’re sharing an update on {topic}. Our teams built this release to help customers operate with clarity and strong governance.{vp_lines}

Capabilities may vary by plan and region; timelines depend on rollout and internal approvals. We describe features factually and avoid absolute promises. Customers should review official documentation and speak with their account team for specifics."""

        social = [
            "Measured progress: documented update for regulated teams — read the blog and loop in your CSM.",
            "Shipping responsibly: transparency + pragmatic workflows. Details on our site (terms apply).",
            "For practitioners: what changed, what to validate in QA, and where canonical guidance lives.",
        ]
    elif scenario == "strict_regulation":
        blog = f"""BLOG:
This announcement discusses {topic} in general educational terms. It is not medical advice.{vp_lines}

Individual outcomes vary; validate with your own advisors and policies."""

        social = [
            "Educational update (not medical advice): review with your team before acting — see blog.",
            "Clarity first: consult compliance counsel as needed. Link in thread.",
            "Walkthrough of benefits without overpromising — FAQ in article.",
        ]
    elif scenario == "engagement_boost":
        blog = f"""BLOG:
Ready for momentum? {topic.capitalize()} reduces friction for teams that need to publish faster with guardrails.{vp_lines}

Pilot one workflow end-to-end, measure time saved, share wins with stakeholders."""

        social = [
            f"⚡ {topic.capitalize()}: pull the 10-minute pilot checklist in the post.",
            f"Hot take: ops + marketing alignment ships here. {topic.capitalize()} — link below.",
            "Thread starter: what we shipped, why it matters, what to measure next.",
        ]
    else:
        blog = f"""BLOG:
We’re introducing an update centered on {topic}. It improves collaboration, publishing, and measurement.{vp_lines}

Clearer ownership, faster reviews, analytics tied to outcomes — iterate with telemetry."""

        social = [
            f"New: {topic} — guardrailed publishing. Overview in our latest post.",
            "Enterprise content ops tip: one pipeline for brand + compliance + distribution.",
            "Pragmatic rollout plan inside: milestones, risks, success metrics.",
        ]

    if video_pivot:
        social = [
            s + " | Cut: 12s vertical + CTA → full article."
            if "Cut:" not in s
            else s
            for s in social[:3]
        ]

    faq = """FAQ:
Q: Who is this release for?
A: Enterprise content, marketing, and compliance teams.

Q: How do you handle risky claims?
A: Automated checks plus human review by policy tier.

Q: Where is implementation help?
A: Customer success or support ticketing."""

    body = f"{blog.strip()}\n\nSOCIAL:\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(social[:3])) + f"\n\n{faq.strip()}"
    # Demo auto-path: if user literally pastes a banned phrase, keep it so auditor can fix (compliance violation scenario).
    if re.search(r"guaranteed\s+returns", prompt.lower()):
        inject = " Customers value guaranteed returns when outcomes are favorable."
        if "SOCIAL:" in body:
            parts = body.split("SOCIAL:", 1)
            body = parts[0].rstrip() + inject + "\n\nSOCIAL:" + parts[1]
        else:
            body = body.rstrip() + inject
    return body
