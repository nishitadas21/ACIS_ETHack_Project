"""
CLI runner for the multi-agent content pipeline (mirrors POST /generate).

Usage:
    python main.py
    python main.py --prompt "Your enterprise content brief"
"""

from __future__ import annotations

import argparse
import json

from content_pipeline import run_content_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Enterprise content operations multi-agent pipeline")
    parser.add_argument(
        "--prompt",
        type=str,
        default=(
            "Launch blog: AI-assisted content operations platform for regulated industries. "
            "Mention workflow automation, brand governance, and analytics."
        ),
        help="Content brief for the Creative Agent",
    )
    parser.add_argument(
        "--spec-file",
        type=str,
        default=None,
        help="Optional path to JSON file merged as product_spec (knowledge-to-content)",
    )
    parser.add_argument("--json", action="store_true", help="Print full JSON to stdout")
    args = parser.parse_args()

    spec = None
    if args.spec_file:
        import json as _json
        from pathlib import Path as _P

        spec = _json.loads(_P(args.spec_file).read_text(encoding="utf-8"))

    result = run_content_pipeline(args.prompt, product_spec=spec)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    print("\n=== SCENARIO ===")
    print(result["final_decision"])

    print("\n=== BLOG ===")
    print(result["blog"][:1200])
    print("\n=== SOCIAL ===")
    for i, s in enumerate(result["social_posts"], 1):
        print(f"{i}. {s}")
    print("\n=== FAQ ===")
    print(result["faq"][:800])
    print("\n=== HINDI (blog localization) ===")
    print((result["localized_version"] or "")[:800])
    print("\n=== SCORES ===")
    print(result["scores"])
    print("\n=== PUBLISHING (simulated) ===")
    print(json.dumps(result["publishing_output"], indent=2))
    print("\n=== IMPACT ===")
    print(json.dumps(result.get("impact"), indent=2))
    print("\n=== CALENDAR ===")
    print(json.dumps(result.get("content_calendar"), indent=2))
    print("\n=== PIPELINE LOG (last 5) ===")
    for row in (result.get("pipeline_logs") or [])[-5:]:
        print(row["agent"], "-", row["message"])


if __name__ == "__main__":
    main()
