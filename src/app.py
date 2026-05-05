"""
Application Workflow: Execute the complete Phase 1, 2 & 3 pipeline
"""

import os
import json
import sys
from pathlib import Path

# Add to path for imports from shared/
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.main_graph import build_graph
from dotenv import load_dotenv

load_dotenv()

def run_workflow(mode: str, prompt_or_script: str, run_dir: str):
    """Executes the pipeline and prints JSON output."""
    workflow = build_graph()
    
    initial_state = {
        "mode": mode,
        "run_dir": run_dir,
        "validation_passed": False,
        "hitl_approved": False,
        "scene_manifest": [],
        "character_profiles": {},
        "audio_manifest": [],
        "audio_files": {},
        "bgm_manifest": {},
        "timing_manifest": {},
        "character_voice_cache": {},
        "audio_output_path": "",
    }
    
    if mode == "auto":
        initial_state["prompt"] = prompt_or_script
    else:
        initial_state["raw_script"] = prompt_or_script
        
    print(f"Starting {mode.upper()} mode execution...", file=__import__('sys').stderr)
    result = workflow.invoke(initial_state)
    
    # Only output validated JSON for Phase 1
    if result.get("validation_passed") and result.get("hitl_approved"):
        output = {
            "story": result.get("story", ""),
            "scenes": _serialize_scenes(result.get("scene_manifest", [])),
            "characters": _serialize_characters(result.get("character_profiles", {}))
        }
        # Final output print
        # print(json.dumps(output, indent=2))
    else:
        print("Validation or HITL approval failed.", file=sys.stderr)

def _serialize_scenes(scenes):
    return [s.model_dump() if hasattr(s, 'model_dump') else s for s in scenes]

def _serialize_characters(profiles):
    return [{"name": name, **profile} for name, profile in profiles.items()]
