# """
# Pipeline Runner: Drives Phases 1→2→3 in sequence, publishing SSE events.
# Calls the LangGraph workflow directly (no HTTP round-trip).
# """
# import asyncio
# import logging
# import sys
# import os
# from datetime import datetime
# from pathlib import Path
# from typing import Optional

# from .sse_manager import SSEChannel
# from .schemas import RunPipelineRequest

# logger = logging.getLogger("phase4.pipeline_runner")

# # Simple in-memory store: run_id → { prompt, run_dir, last_phase, final_video_path }
# _run_store: dict[str, dict] = {}


# def _make_run_dir() -> str:
#     """Generate a timestamped run directory name."""
#     return datetime.now().strftime("%-d%b-%-I%M%p").upper() + "-RUN"


# async def run_full_pipeline(
#     run_id: str,
#     request: RunPipelineRequest,
#     channel: SSEChannel,
# ) -> None:
#     """
#     Orchestrate the full Phase 1 → 2 → 3 pipeline, publishing SSE events.
#     The LangGraph graph is invoked in a thread pool so async SSE isn't blocked.
#     """
#     # Add project root to sys.path so shared/ imports work
#     project_root = str(Path(__file__).parent.parent.parent)
#     if project_root not in sys.path:
#         sys.path.insert(0, project_root)

#     from dotenv import load_dotenv
#     load_dotenv()

#     run_dir_name = _make_run_dir()
#     run_dir = f"outputs/{run_dir_name}"
#     os.makedirs(run_dir, exist_ok=True)

#     _run_store[run_id] = {
#         "prompt": request.prompt,
#         "run_dir": run_dir,
#         "add_subtitles": request.add_subtitles,
#         "seed": request.seed,
#         "last_phase": 0
#     }

#     await channel.publish("run_start", {
#         "run_id": run_id,
#         "run_dir": run_dir,
#         "prompt": request.prompt,
#     })

#     try:
#         # ── Phase 1 ────────────────────────────────────────────────────────────
#         _run_store[run_id]["last_phase"] = 1
#         await channel.publish("phase_start", {"phase": 1, "name": "Story & Script"})

#         # Build the initial LangGraph state
#         initial_state = {
#             "mode": "auto",
#             "run_dir": run_dir,
#             "prompt": request.prompt,
#             "validation_passed": False,
#             "hitl_approved": True,   # Auto-approve in API mode — no terminal prompt
#             "scene_manifest": [],
#             "character_profiles": {},
#             "audio_manifest": [],
#             "audio_files": {},
#             "bgm_manifest": {},
#             "timing_manifest": {},
#             "character_voice_cache": {},
#             "audio_output_path": "",
#         }

#         # Import the graph builder here (after sys.path is set)
#         from shared.main_graph import build_graph
#         workflow = build_graph()

#         # Run the entire pipeline graph in a thread pool (it's synchronous internally)
#         result = await asyncio.get_event_loop().run_in_executor(
#             None, lambda: workflow.invoke(initial_state)
#         )

#         # Extract Phase 1 output from result
#         scene_manifest = result.get("scene_manifest", [])
#         character_profiles = result.get("character_profiles", {})

#         if not scene_manifest:
#             raise RuntimeError("Phase 1 produced no scenes. Check your prompt or Groq API key.")

#         await channel.publish("phase_done", {
#             "phase": 1,
#             "data": {
#                 "scene_count": len(scene_manifest),
#                 "story": result.get("story", ""),
#                 "characters": list(character_profiles.keys()),
#             },
#         })

#         # ── Phase 2 ────────────────────────────────────────────────────────────
#         _run_store[run_id]["last_phase"] = 2
#         await channel.publish("phase_start", {"phase": 2, "name": "Audio Generation"})

#         timing_manifest = result.get("timing_manifest", {})
#         if not timing_manifest:
#             # Check if it's a dry run or if audio was skipped
#             if not result.get("audio_output_path"):
#                 raise RuntimeError("Phase 2 produced no audio output.")

#         await channel.publish("phase_done", {
#             "phase": 2,
#             "data": {"scene_count": len(timing_manifest) if timing_manifest else 0},
#         })

#         # ── Phase 3 ────────────────────────────────────────────────────────────
#         _run_store[run_id]["last_phase"] = 3
#         await channel.publish("phase_start", {"phase": 3, "name": "Video Composition"})

#         final_video = result.get("final_video_path")
#         if not final_video:
#             raise RuntimeError("Phase 3 did not produce a final video.")

#         # Store final video path for later retrieval
#         _run_store[run_id]["final_video_path"] = final_video

#         await channel.publish("phase_done", {
#             "phase": 3,
#             "data": {"video_url": f"/api/video/{run_id}"},
#         })

#         # ── Complete ───────────────────────────────────────────────────────────
#         await channel.publish("pipeline_complete", {
#             "video_url": f"/api/video/{run_id}",
#             "run_id": run_id,
#         })

#     except Exception as e:
#         logger.exception(f"[Pipeline:{run_id}] Error: {e}")
#         await channel.publish("phase_error", {
#             "phase": _run_store.get(run_id, {}).get("last_phase", 0),
#             "error": str(e),
#         })
#         await channel.publish("error", {"message": str(e)})
#         return

#     finally:
#         await channel.publish("done", {})


# async def rerun_phase(
#     phase: int,
#     run_id: str,
#     channel: SSEChannel,
# ) -> None:
#     """Re-run a single phase (or cascade) for a previous run."""
#     project_root = str(Path(__file__).parent.parent.parent)
#     if project_root not in sys.path:
#         sys.path.insert(0, project_root)

#     run_info = _run_store.get(run_id)
#     if not run_info:
#         await channel.publish("error", {"message": f"Run {run_id} not found in memory."})
#         await channel.publish("done", {})
#         return

#     # For simplicity: re-run means replay the full pipeline with original prompt
#     from dotenv import load_dotenv
#     load_dotenv()

#     request = RunPipelineRequest(
#         prompt=run_info["prompt"],
#         add_subtitles=run_info.get("add_subtitles", False),
#         seed=run_info.get("seed"),
#     )
#     await run_full_pipeline(run_id, request, channel)
"""
Pipeline Runner: Drives Phases 1→2→3 in sequence, publishing SSE events.
Calls the LangGraph workflow directly (no HTTP round-trip).
"""
import asyncio
import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from .sse_manager import SSEChannel
from .schemas import RunPipelineRequest

logger = logging.getLogger("phase4.pipeline_runner")

# Simple in-memory store: run_id → { prompt, run_dir, last_phase, final_video_path }
_run_store: dict[str, dict] = {}


def _make_run_dir() -> str:
    """Generate a timestamped run directory name."""
    return datetime.now().strftime("%d%b-%I%M%p").upper() + "-RUN"


async def run_full_pipeline(
    run_id: str,
    request: RunPipelineRequest,
    channel: SSEChannel,
) -> None:
    """
    Orchestrate the full Phase 1 → 2 → 3 pipeline, publishing SSE events.
    The LangGraph graph is invoked in a thread pool so async SSE isn't blocked.
    """
    # Add project root to sys.path so shared/ imports work
    project_root = str(Path(__file__).parent.parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from dotenv import load_dotenv
    load_dotenv()

    run_dir_name = _make_run_dir()
    run_dir = f"outputs/{run_dir_name}"
    os.makedirs(run_dir, exist_ok=True)

    _run_store[run_id] = {
        "prompt": request.prompt,
        "run_dir": run_dir,
        "add_subtitles": request.add_subtitles,
        "seed": request.seed,
        "last_phase": 0
    }

    await channel.publish("run_start", {
        "run_id": run_id,
        "run_dir": run_dir,
        "prompt": request.prompt,
    })

    try:
        # ── Phase 1 ────────────────────────────────────────────────────────────
        _run_store[run_id]["last_phase"] = 1
        await channel.publish("phase_start", {"phase": 1, "name": "Story & Script"})

        # Build the initial LangGraph state
        initial_state = {
            "mode": "auto",
            "run_dir": run_dir,
            "prompt": request.prompt,
            "validation_passed": False,
            "hitl_approved": True,   # Auto-approve in API mode — no terminal prompt
            "scene_manifest": [],
            "character_profiles": {},
            "audio_manifest": [],
            "audio_files": {},
            "bgm_manifest": {},
            "timing_manifest": {},
            "character_voice_cache": {},
            "audio_output_path": "",
        }

        # Import the graph builder here (after sys.path is set)
        from shared.main_graph import build_graph
        workflow = build_graph()

        # Run the entire pipeline graph in a thread pool (it's synchronous internally)
        result = await asyncio.get_event_loop().run_in_executor(
            None, lambda: workflow.invoke(initial_state)
        )

        # Extract Phase 1 output from result
        scene_manifest = result.get("scene_manifest", [])
        character_profiles = result.get("character_profiles", {})

        if not scene_manifest:
            raise RuntimeError("Phase 1 produced no scenes. Check your prompt or Groq API key.")

        await channel.publish("phase_done", {
            "phase": 1,
            "data": {
                "scene_count": len(scene_manifest),
                "story": result.get("story", ""),
                "characters": list(character_profiles.keys()),
            },
        })

        # ── Phase 2 ────────────────────────────────────────────────────────────
        _run_store[run_id]["last_phase"] = 2
        await channel.publish("phase_start", {"phase": 2, "name": "Audio Generation"})

        timing_manifest = result.get("timing_manifest", {})
        if not timing_manifest:
            # Check if it's a dry run or if audio was skipped
            if not result.get("audio_output_path"):
                raise RuntimeError("Phase 2 produced no audio output.")

        await channel.publish("phase_done", {
            "phase": 2,
            "data": {"scene_count": len(timing_manifest) if timing_manifest else 0},
        })

        # ── Phase 3 ────────────────────────────────────────────────────────────
        _run_store[run_id]["last_phase"] = 3
        await channel.publish("phase_start", {"phase": 3, "name": "Video Composition"})

        final_video = result.get("final_video_path")
        if not final_video:
            raise RuntimeError("Phase 3 did not produce a final video.")

        # Store final video path for later retrieval
        _run_store[run_id]["final_video_path"] = final_video

        await channel.publish("phase_done", {
            "phase": 3,
            "data": {"video_url": f"/api/video/{run_id}"},
        })

        # ── Complete ───────────────────────────────────────────────────────────
        await channel.publish("pipeline_complete", {
            "video_url": f"/api/video/{run_id}",
            "run_id": run_id,
            "run_dir": run_dir,
        })

    except Exception as e:
        logger.exception(f"[Pipeline:{run_id}] Error: {e}")
        await channel.publish("phase_error", {
            "phase": _run_store.get(run_id, {}).get("last_phase", 0),
            "error": str(e),
        })
        await channel.publish("error", {"message": str(e)})
        return

    finally:
        await channel.publish("done", {})


async def rerun_phase(
    phase: int,
    run_id: str,
    channel: SSEChannel,
) -> None:
    """Re-run a single phase (or cascade) for a previous run."""
    project_root = str(Path(__file__).parent.parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    run_info = _run_store.get(run_id)
    if not run_info:
        await channel.publish("error", {"message": f"Run {run_id} not found in memory."})
        await channel.publish("done", {})
        return

    # For simplicity: re-run means replay the full pipeline with original prompt
    from dotenv import load_dotenv
    load_dotenv()

    request = RunPipelineRequest(
        prompt=run_info["prompt"],
        add_subtitles=run_info.get("add_subtitles", False),
        seed=run_info.get("seed"),
    )
    await run_full_pipeline(run_id, request, channel)