from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional


class PhaseStatus(str, Enum):
    IDLE    = "idle"
    RUNNING = "running"
    DONE    = "done"
    ERROR   = "error"
    SKIPPED = "skipped"


class RunPipelineRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=500)
    add_subtitles: bool = False
    seed: Optional[int] = None


class PipelineRunState(BaseModel):
    run_id: str
    prompt: str
    phase1_status: PhaseStatus = PhaseStatus.IDLE
    phase2_status: PhaseStatus = PhaseStatus.IDLE
    phase3_status: PhaseStatus = PhaseStatus.IDLE
    overall_status: PhaseStatus = PhaseStatus.IDLE
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    final_video_url: Optional[str] = None


class RerunPhaseRequest(BaseModel):
    phase: int = Field(..., ge=1, le=3)
    run_id: str


class SSEEvent(BaseModel):
    event: str
    data: dict
