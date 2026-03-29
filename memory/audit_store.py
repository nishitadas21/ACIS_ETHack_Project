"""
Append-only audit trail for enterprise traceability (memory/audit_log.json).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIT_PATH = ROOT / "memory" / "audit_log.json"


def append_audit_record(record: dict) -> None:
    """Persist one pipeline run summary for compliance / ops review."""
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        if AUDIT_PATH.exists():
            existing = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        else:
            existing = []
    except (json.JSONDecodeError, OSError):
        existing = []

    envelope = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        **record,
    }
    existing.append(envelope)
    AUDIT_PATH.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")


def read_audit_tail(limit: int = 30) -> list[dict]:
    """Return the last N audit records (newest last)."""
    try:
        if not AUDIT_PATH.exists():
            return []
        data = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
        return data[-limit:]
    except (OSError, json.JSONDecodeError):
        return []
