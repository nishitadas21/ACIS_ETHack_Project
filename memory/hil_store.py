"""
Human-in-the-loop checkpoint persistence (resume after Approve/Reject).
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKPOINT_DIR = ROOT / "memory" / "hil_checkpoints"


def save_checkpoint(payload: dict) -> str:
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    cid = str(uuid.uuid4())
    path = CHECKPOINT_DIR / f"{cid}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return cid


def load_checkpoint(checkpoint_id: str) -> dict:
    path = CHECKPOINT_DIR / f"{checkpoint_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"checkpoint {checkpoint_id} not found")
    return json.loads(path.read_text(encoding="utf-8"))
