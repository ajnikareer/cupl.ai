"""Live Telemetry & Audit Service for QLOO Taste Intelligence & LLM Synthesis.
Provides 3-stage transparency for hackathon judges and technical inspection:
Stage 1: Input Signals & Context
Stage 2: QLOO Processing & Raw Responses
Stage 3: LLM Synthesis & Grounded Masterplan
"""
import logging
from datetime import datetime, timezone
from ..core.timeutil import now_iso
from ..db import db, list_col, get_doc

log = logging.getLogger("intelligence_audit")


async def record_audit_run(run_data: dict) -> str:
    """Save an audit run to Firestore intelligence_runs collection."""
    try:
        run_id = run_data.get("run_id") or f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        run_data["run_id"] = run_id
        run_data["recorded_at"] = now_iso()
        await db.document(f"intelligence_runs/{run_id}").set(run_data)
        
        # Also link to space if space_id exists
        if run_data.get("space_id"):
            await db.document(f"spaces/{run_data['space_id']}/intelligence/latest").set({"run_id": run_id, "recorded_at": run_data["recorded_at"]})
            
        log.info("Recorded intelligence audit run: %s", run_id)
        return run_id
    except Exception as e:
        log.warning("Failed to record audit run: %s", e)
        return ""


async def list_audit_runs(limit: int = 15) -> list[dict]:
    """List recent intelligence audit runs for the dashboard."""
    try:
        docs = []
        async for doc in db.collection("intelligence_runs").order_by("recorded_at", direction="DESCENDING").limit(limit).stream():
            d = doc.to_dict()
            docs.append({
                "run_id": doc.id,
                "title": d.get("title") or d.get("space_title") or "Masterplan Run",
                "space_type": d.get("space_type", "wedding"),
                "city": d.get("city") or "India",
                "budget": d.get("budget", 0),
                "recorded_at": d.get("recorded_at"),
                "signals_count": len(d.get("stage_1", {}).get("tastes", [])),
                "sections_count": len(d.get("stage_3", {}).get("sections", {})),
                "grounding_pct": d.get("stage_3", {}).get("grounding_pct", 100)
            })
        return docs
    except Exception as e:
        log.warning("list_audit_runs failed: %s", e)
        return []


async def get_audit_run(run_id: str) -> dict | None:
    """Get full 3-stage audit record by run_id."""
    return await get_doc(f"intelligence_runs/{run_id}")


async def get_latest_audit_run() -> dict | None:
    """Get the most recent audit record."""
    runs = await list_audit_runs(limit=1)
    if runs:
        return await get_audit_run(runs[0]["run_id"])
    return None

