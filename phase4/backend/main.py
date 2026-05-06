"""
Phase 4 FastAPI Backend — AnimAI Pipeline Orchestration Server
"""
import asyncio
import logging
import shutil
import sys
import os
from pathlib import Path
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from phase3.router import router as phase3_router
from .schemas import RunPipelineRequest, RerunPhaseRequest
from .sse_manager import sse_manager
from .pipeline_runner import run_full_pipeline, rerun_phase, _run_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("phase4.main")

app = FastAPI(title="AnimAI Pipeline", version="1.0.0", description="Agentic AI Video Generation API")

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount Phase Routers ───────────────────────────────────────────────────────
app.include_router(phase3_router, prefix="/api")


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "alive", "app": "AnimAI"}


@app.get("/api/health")
async def health():
    import httpx

    ffmpeg_status = "ok" if shutil.which("ffmpeg") else "missing"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://image.pollinations.ai", timeout=3)
        pollinations_status = "reachable"
    except Exception:
        pollinations_status = "unreachable"

    return {
        "phase1": "ok",
        "phase2": "ok",
        "phase3": "ok",
        "ffmpeg": ffmpeg_status,
        "pollinations": pollinations_status,
    }


# ── SSE Stream ────────────────────────────────────────────────────────────────
@app.get("/api/stream/{run_id}")
async def stream_run(run_id: str):
    channel = sse_manager.get_channel(run_id)
    if not channel:
        raise HTTPException(status_code=404, detail=f"No SSE channel for run_id={run_id}")

    return StreamingResponse(
        channel.stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ── Pipeline Endpoints ────────────────────────────────────────────────────────
@app.post("/api/pipeline/run")
async def start_pipeline(request: RunPipelineRequest):
    run_id = str(uuid4())
    channel = sse_manager.create_channel(run_id)
    asyncio.create_task(run_full_pipeline(run_id, request, channel))
    return {"run_id": run_id, "stream_url": f"/api/stream/{run_id}"}


@app.post("/api/pipeline/rerun")
async def rerun_pipeline_phase(request: RerunPhaseRequest):
    channel = sse_manager.get_channel(request.run_id) or sse_manager.create_channel(request.run_id)
    asyncio.create_task(rerun_phase(request.phase, request.run_id, channel))
    return {"run_id": request.run_id, "stream_url": f"/api/stream/{request.run_id}"}


# ── Video Serve by Run ID ─────────────────────────────────────────────────────
@app.get("/api/video/{run_id}")
async def get_video_for_run(run_id: str):
    """Serve the final video for a specific run."""
    run_info = _run_store.get(run_id, {})
    video_path = run_info.get("final_video_path")

    if video_path and Path(video_path).exists():
        return FileResponse(video_path, media_type="video/mp4", filename="animai_film.mp4")

    raise HTTPException(status_code=404, detail="Video not found for this run.")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
