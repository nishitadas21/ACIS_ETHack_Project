"""
Structured output formatter — normalizes Creative Agent bundles into API fields.

Consumes raw multi-section text and returns blog, social_posts[], faq as distinct fields.
"""

from __future__ import annotations

from utils.parser import parse_content


def format_structured_output(raw_bundle: str) -> dict:
    """
    Split raw agent output into enterprise-ready structures.

    Returns dict with string/list fields suitable for JSON serialization (not stringified JSON).
    """
    if not raw_bundle or not str(raw_bundle).strip():
        return {
            "blog": "",
            "social_posts": [],
            "faq": "",
            "schema_version": "structured_v2",
        }

    sections = parse_content(str(raw_bundle))
    return {
        "blog": sections.get("blog") or "",
        "social_posts": list(sections.get("social_posts") or []),
        "faq": sections.get("faq") or "",
        "schema_version": "structured_v2",
    }
