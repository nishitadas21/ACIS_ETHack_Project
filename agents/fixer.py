"""
Fixer Agent — applies compliant replacements for detected violations.
"""

import json
from pathlib import Path

RULES_PATH = Path(__file__).resolve().parent.parent / "data" / "compliance_rules.json"


def fix_content(content: str, issues: list[str]) -> str:
    rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    suggestions = rules.get("suggestions", {})
    fixed = content

    for issue in issues:
        replacement = suggestions.get(issue) or "[softened wording per policy]"
        lower = fixed.lower()
        idx = lower.find(issue.lower())
        while idx != -1:
            fixed = fixed[:idx] + replacement + fixed[idx + len(issue) :]
            lower = fixed.lower()
            idx = lower.find(issue.lower())

    return fixed
