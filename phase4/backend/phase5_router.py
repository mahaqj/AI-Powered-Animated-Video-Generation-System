from fastapi import APIRouter, HTTPException
import logging
from pydantic import BaseModel
from pathlib import Path
import json
from typing import Dict

from phase5.edit_intent import EditIntentClassifier
from phase5.executor import EditExecutor
from .pipeline_runner import _run_store
from phase3.pipeline import get_pipeline
from .sse_manager import sse_manager
from phase3.schemas import Phase3Output, TimingManifest

router = APIRouter(prefix="/phase5", tags=["Phase 5 — Editing"])


class EditRequest(BaseModel):
    run_id: str
    edit_text: str


def _load_timing_manifest(run_dir: Path) -> TimingManifest:
    timing_path = run_dir / "timing_manifest.json"
    if not timing_path.exists():
        raise HTTPException(status_code=404, detail="timing_manifest.json not found for this run")

    with open(timing_path, "r") as f:
        timing_data = json.load(f)

    # TimingManifest historically was written as a dict keyed by scene id.
    # Accept both the new format {"scenes": [...]} and the old mapping { "scene1": {...} }.
    if isinstance(timing_data, dict) and "scenes" not in timing_data:
        # Convert mapping to list form
        scenes = []
        for sid, v in timing_data.items():
            # Ensure required fields exist; try to map keys conservatively
            try:
                scene_entry = {
                    "scene_id": v.get("scene_id", sid),
                    "audio_file": v.get("audio_file") or v.get("audio_path") or v.get("file"),
                    "start_ms": int(v.get("start_ms", 0)),
                    "end_ms": int(v.get("end_ms", 0)),
                    "dialogue_segments": v.get("dialogue_segments", []),
                    "bgm_file": v.get("bgm_file") if v.get("bgm_file") else None,
                }
            except Exception:
                raise HTTPException(status_code=500, detail="Malformed timing manifest (legacy mapping)")
            scenes.append(scene_entry)

        timing_data = {"scenes": scenes}

    try:
        return TimingManifest.model_validate(timing_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TimingManifest validation error: {e}")


@router.post("/edit")
async def apply_edit(req: EditRequest):
    logger = logging.getLogger("phase4.phase5_router")
    try:
        run_info = _run_store.get(req.run_id)
        if not run_info:
            raise HTTPException(status_code=404, detail=f"Run {req.run_id} not found")

        run_dir = Path(run_info["run_dir"])
        state_path = run_dir / "phase3_state.json"
        if not state_path.exists():
            raise HTTPException(status_code=404, detail="Phase3 state file not found for this run")

        # Load state
        with open(state_path, "r") as f:
            state_json = f.read()

        pipeline = get_pipeline()
        phase3_output = Phase3Output.model_validate_json(state_json)
        timing_manifest = _load_timing_manifest(run_dir)

        # Classify edit intent
        clf = EditIntentClassifier()
        intent = clf.classify(req.edit_text)

        # Apply edit
        new_state = EditExecutor.apply_edit(phase3_output, intent)

        # Re-run Phase 3 for all scenes so the visible video matches the edit.
        scene_ids = [scene.scene_id for scene in new_state.pipeline_input.scenes]
        rerun_seed = run_info.get("seed")
        updated_state = await pipeline.run_partial(
            new_state,
            scene_ids,
            timing_manifest,
            rerun_seed,
            run_dir=str(run_dir),
        )

        version = updated_state.version
        video_url = f"/api/video/{req.run_id}?v={version}"

        run_info["final_video_path"] = str(updated_state.final_video_path)
        run_info["version"] = version

        # Notify any SSE subscribers for this run
        channel = sse_manager.get_channel(req.run_id)
        if channel:
            await channel.publish(
                "phase5_edit",
                {
                    "run_id": req.run_id,
                    "version": version,
                    "video_url": video_url,
                    "intent": intent.model_dump() if hasattr(intent, "model_dump") else str(intent),
                },
            )

        return {"status": "ok", "version": version, "video_url": video_url, "intent": intent.model_dump()}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unhandled error applying edit")
        # Surface the error to the client for easier debugging
        raise HTTPException(status_code=500, detail=str(e))
