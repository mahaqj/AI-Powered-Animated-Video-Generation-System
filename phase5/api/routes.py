"""
Phase 5: FastAPI Routes
Endpoints for edit intent classification, execution, and state management.
These routes should be included in the Phase 4 FastAPI app.
"""

import json
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from phase5.agent.intent_classifier import classify_edit_query
from phase5.agent.edit_executor import EditExecutor
from phase5.state.state_manager import StateManager


router = APIRouter(prefix="/phase5", tags=["Phase 5 - Edit Agent"])


# ─── Request / Response Models ───────────────────────────────────────────────

class EditRequest(BaseModel):
    query: str
    run_dir: str  # Path to current pipeline run output dir
    current_state: Optional[dict] = None  # If not provided, loaded from latest snapshot


class RevertRequest(BaseModel):
    run_dir: str
    version_id: int


class HistoryRequest(BaseModel):
    run_dir: str


# ─── Helper: get or create StateManager ──────────────────────────────────────

def _get_sm(run_dir: str) -> StateManager:
    return StateManager(run_dir=run_dir)


def _load_state(run_dir: str, sm: StateManager, provided_state: Optional[dict]) -> dict:
    """Load state from provided dict, latest snapshot, or pipeline output JSON."""
    if provided_state:
        return provided_state

    # Try loading from latest snapshot
    latest = sm.latest_version_id()
    if latest:
        return sm.get_version_state(latest)

    # Try loading from pipeline state file in run_dir
    state_file = Path(run_dir) / "state.json"
    if state_file.exists():
        with open(state_file, "r") as f:
            return json.load(f)

    return {}


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post("/classify")
async def classify_only(query: str):
    """
    Just classify an edit query without executing it.
    Useful for previewing what the agent will do.
    """
    try:
        intent = classify_edit_query(query)
        return {
            "query": query,
            "intent": intent.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/edit")
async def apply_edit(request: EditRequest):
    """
    Classify and execute an edit command.
    Auto-snapshots state before applying the edit.
    """
    try:
        # 1. Classify intent
        intent = classify_edit_query(request.query)

        # 2. Load state
        sm = _get_sm(request.run_dir)
        state = _load_state(request.run_dir, sm, request.current_state)

        # 3. Snapshot BEFORE edit
        pre_edit_version = sm.snapshot(
            description=f"Before: {request.query}",
            state=state
        )

        # 4. Execute edit
        executor = EditExecutor(run_dir=request.run_dir, state_manager=sm)
        result = executor.execute(intent, state)

        # 5. Snapshot AFTER edit
        if result["success"]:
            post_edit_version = sm.snapshot(
                description=f"After: {request.query}",
                state=result["updated_state"]
            )
        else:
            post_edit_version = None

        return {
            "success": result["success"],
            "message": result["message"],
            "intent": intent.model_dump(),
            "version_before": pre_edit_version,
            "version_after": post_edit_version,
            "updated_state": result["updated_state"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/revert")
async def revert_to_version(request: RevertRequest):
    """
    Revert the pipeline state to a specific version.
    Restores both the state JSON and all asset files.
    """
    try:
        sm = _get_sm(request.run_dir)
        restored_state = sm.revert(request.version_id)
        return {
            "success": True,
            "message": f"Reverted to version {request.version_id}",
            "restored_state": restored_state
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/history")
async def get_version_history(request: HistoryRequest):
    """
    Get the full version history for a run directory.
    """
    try:
        sm = _get_sm(request.run_dir)
        history = sm.history()
        return {
            "run_dir": request.run_dir,
            "version_count": len(history),
            "versions": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/filters")
async def list_available_filters():
    """Return the list of available image filters."""
    from phase5.filters.image_filters import AVAILABLE_FILTERS
    return {"filters": AVAILABLE_FILTERS}


@router.get("/health")
async def health():
    return {"status": "Phase 5 Edit Agent is running"}
