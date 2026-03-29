"""
FastAPI entrypoint for the ET AI Hackathon enterprise content operations demo.

Run from repository root:
    python -m uvicorn api.app:app --reload

Orchestration lives in content_pipeline.py; this module wires HTTP + static assets.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from content_pipeline import resume_after_human_decision, run_content_pipeline
from memory.audit_store import read_audit_tail

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"

app = FastAPI(
    title="ACIS Enterprise Content Ops",
    description="Multi-agent pipeline: knowledge grounding, generation, compliance, debate, strategy, localization, publishing.",
    version="1.1.0",
)

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class ContentRequest(BaseModel):
    """JSON body for POST /generate — all structured fields (no stringified JSON for nested objects)."""

    prompt: str = Field(..., min_length=1, description="User intent / campaign brief")
    product_spec: str | dict[str, Any] | None = Field(
        default=None,
        description="Structured or free-text internal product facts injected before generation",
    )
    interactive_hil: bool = Field(
        default=False,
        description="If true, pause at severe compliance failure for POST /pipeline/human-decision",
    )


class HumanDecisionRequest(BaseModel):
    checkpoint_id: str = Field(..., min_length=8)
    decision: Literal["approve", "reject"]


@app.get("/", response_class=HTMLResponse)
def home():
    index = FRONTEND_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=500, detail="frontend/index.html missing")
    return HTMLResponse(index.read_text(encoding="utf-8"))


@app.post("/generate")
def generate_pipeline(request: ContentRequest):
    try:
        return run_content_pipeline(
            request.prompt,
            product_spec=request.product_spec,
            interactive_hil=request.interactive_hil,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {exc}") from exc


@app.post("/pipeline/human-decision")
def human_decision(request: HumanDecisionRequest):
    """Resume after human-in-the-loop gate (approve = safest path, reject = regenerate)."""
    try:
        return resume_after_human_decision(request.checkpoint_id, request.decision)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="checkpoint_id not found or expired") from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Resume failed: {exc}") from exc


@app.get("/audit/recent")
def audit_recent(limit: int = 25):
    rows = read_audit_tail(limit)
    return {"records": rows, "count": len(rows)}


@app.get("/run-agent")
def run_agent():
    """
    Canonical demo: regulated fintech scenario + grounded spec (knowledge-to-content).
    """
    demo_prompt = (
        "Product launch: ACIS LedgerSave — digital savings for young professionals. "
        "Emphasize transparency and regulated markets."
    )
    demo_spec = {
        "product_name": "LedgerSave",
        "segment": "B2C fintech",
        "key_features": ["goal-based savings", "bank-grade encryption", "SEBI-aware disclosures"],
        "launch_markets": ["IN", "UAE pilot"],
        "restricted_claims": ["no guaranteed returns", "past performance disclaimer"],
    }
    try:
        body = run_content_pipeline(demo_prompt, product_spec=demo_spec)
        # Full pipeline payload for dashboard + demo metadata (GET /run-agent drives one-click UI)
        result = dict(body)
        result["demo"] = True
        result["prompt_used"] = demo_prompt
        result["product_spec_used"] = demo_spec
        result["blog_preview"] = (body.get("blog") or "")[:280]
        result["log_count"] = len(body.get("pipeline_logs") or [])
        return result
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Demo pipeline failed: {exc}") from exc
