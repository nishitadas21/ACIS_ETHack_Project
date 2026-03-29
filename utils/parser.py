"""
Parse structured Creative Agent output into API fields.
"""

import re
from typing import Any


def _default_social_from_blog(blog: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", blog.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 12][:3]
    while len(sentences) < 3:
        sentences.append("Follow the full article for rollout details and guardrails.")
    return sentences[:3]


def parse_content(raw_text: str) -> dict[str, Any]:
    sections: dict[str, Any] = {"blog": "", "social_posts": [], "faq": ""}
    lines = raw_text.split("\n")

    current: str | None = None
    social_buffer: list[str] = []

    for line in lines:
        stripped = line.strip()
        upper = stripped.upper()

        if upper.startswith("BLOG") and ":" in stripped[:8]:
            current = "blog"
            after = stripped.split(":", 1)[-1].strip()
            if after:
                sections["blog"] += after + " "
            continue

        if "SOCIAL" in upper and ":" in stripped[:16]:
            current = "social"
            after = stripped.split(":", 1)[-1].strip()
            if re.match(r"^\d+\.", after):
                social_buffer.append(re.sub(r"^\d+\.\s*", "", after))
            elif after:
                social_buffer.append(after)
            continue

        if upper.startswith("FAQ") and ":" in stripped[:8]:
            current = "faq"
            after = stripped.split(":", 1)[-1].strip()
            if after:
                sections["faq"] += after + " "
            continue

        if current == "blog":
            sections["blog"] += stripped + " "
        elif current == "social":
            if not stripped:
                continue
            if re.match(r"^\d+\.", stripped):
                social_buffer.append(re.sub(r"^\d+\.\s*", "", stripped))
            else:
                social_buffer.append(stripped)
        elif current == "faq":
            sections["faq"] += stripped + " "

    sections["blog"] = (sections["blog"] or "").strip()
    sections["faq"] = (sections["faq"] or "").strip()

    sections["social_posts"] = [s.strip() for s in social_buffer if s.strip()][:3]
    if len(sections["social_posts"]) < 3:
        base = sections["blog"] or raw_text
        defaults = _default_social_from_blog(base if base else raw_text)
        need = 3 - len(sections["social_posts"])
        sections["social_posts"].extend(defaults[:need])

    if not sections["blog"]:
        sections["blog"] = raw_text.strip()

    if not sections["faq"]:
        sections["faq"] = (
            "Q: What is this announcement about?\n"
            "A: A structured enterprise content update with channel-ready assets.\n"
            "Q: Who should review before publish?\n"
            "A: Brand, compliance, and channel owners per your internal tiering."
        )

    return sections
