from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
from typing import List, Optional
import os
import json

from .schemas import PipelineInput, TimingManifest, Phase3Output
from .pipeline import get_pipeline
from .config import get_settings
from .state_manager import VersionNotFoundError

settings = get_settings()
router = APIRouter(prefix="/phase3", tags=["Phase 3 — Video Generation"])

# Request/Response models for endpoints
class RunPhase3Request(BaseModel):
    pipeline_input: PipelineInput
    timing_manifest: TimingManifest
    add_subtitles: bool = False
    seed: Optional[int] = None

class RunPhase3Response(BaseModel):
    status: str
    message: str
    final_video_path: str
    phase3_state_path: str
    scene_count: int
    version: int

class RunPartialRequest(BaseModel):
    scene_ids: List[str]
    timing_manifest: TimingManifest
    seed: Optional[int] = None

@router.post("/run", response_model=RunPhase3Response)
async def run_phase3(req: RunPhase3Request):
    try:
        pipeline = get_pipeline()
        output = await pipeline.run(req.pipeline_input, req.timing_manifest, req.add_subtitles, req.seed)
        
        return RunPhase3Response(
            status="success",
            message="Video generation complete",
            final_video_path=str(output.final_video_path),
            phase3_state_path=str(Path(settings.OUTPUT_DIR) / "phase3_state.json"),
            scene_count=len(output.generated_scenes),
            version=output.version
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run-partial", response_model=RunPhase3Response)
async def run_partial_phase3(req: RunPartialRequest):
    state_path = Path(settings.OUTPUT_DIR) / "phase3_state.json"
    if not state_path.exists():
        raise HTTPException(status_code=404, detail="Previous Phase 3 state not found. Run a full generation first.")
        
    try:
        with open(state_path, "r") as f:
            phase3_output = Phase3Output.model_validate_json(f.read())
            
        pipeline = get_pipeline()
        output = await pipeline.run_partial(phase3_output, req.scene_ids, req.timing_manifest, req.seed)
        
        return RunPhase3Response(
            status="success",
            message="Partial re-run complete",
            final_video_path=str(output.final_video_path),
            phase3_state_path=str(state_path),
            scene_count=len(output.generated_scenes),
            version=output.version
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_status():
    state_path = Path(settings.OUTPUT_DIR) / "phase3_state.json"
    if state_path.exists():
        with open(state_path, "r") as f:
            state = json.load(f)
            return {
                "exists": True,
                "version": state.get("version"),
                "created_at": state.get("created_at"),
                "scene_count": len(state.get("generated_scenes", []))
            }
    return {"exists": False}

@router.get("/video")
async def get_video():
    path = Path(settings.OUTPUT_DIR) / "final" / "final_output.mp4"
    # Check for subtitled version first
    subtitled_path = Path(settings.OUTPUT_DIR) / "final" / "final_output_subtitled.mp4"
    if subtitled_path.exists():
        path = subtitled_path
        
    if path.exists():
        return FileResponse(path, media_type="video/mp4", filename="final_output.mp4")
    raise HTTPException(status_code=404, detail="Video not yet generated")

@router.get("/state")
async def get_state():
    state_path = Path(settings.OUTPUT_DIR) / "phase3_state.json"
    if state_path.exists():
        with open(state_path, "r") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Phase 3 state not found")

@router.get("/history")
async def get_history():
    pipeline = get_pipeline()
    return await pipeline.state_manager.history()

@router.post("/revert/{version}")
async def revert_version(version: int):
    try:
        pipeline = get_pipeline()
        reverted_state = await pipeline.state_manager.revert(version)
        
        # Overwrite the current state JSON
        state_path = Path(settings.OUTPUT_DIR) / "phase3_state.json"
        with open(state_path, "w") as f:
            f.write(reverted_state.model_dump_json(indent=2))
            
        return reverted_state
    except VersionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
