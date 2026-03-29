"""
Helpers for consistent agent reasoning traces (received → decision → why).
"""


def trace_block(*, received_preview: str, decision: str, rationale: str, extra: dict | None = None) -> dict:
    block = {
        "received_preview": (received_preview or "")[:600],
        "decision": decision,
        "rationale": rationale,
    }
    if extra:
        block["extra"] = extra
    return {"reasoning_trace": block}
