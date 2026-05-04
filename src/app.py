import os
import json
import sys
from pathlib import Path

# Add parent directory to path for imports from config/
sys.path.insert(0, str(Path(__file__).parent.parent))

from main_graph import build_graph
from dotenv import load_dotenv

load_dotenv()

def run_workflow(mode: str, prompt_or_script: str):
    """Executes the pipeline and prints JSON output."""
    workflow = build_graph()
    
    initial_state = {
        "mode": mode,
        "validation_passed": False,
        "hitl_approved": False,
        "scene_manifest": [],
        "character_profiles": {},
        # Phase 2: Audio State Initialization
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
        print(json.dumps(output, indent=2))
    else:
        # Print error info to stderr, not stdout
        error_output = {
            "error": "Validation or HITL approval failed",
            "validation_passed": result.get("validation_passed", False),
            "hitl_approved": result.get("hitl_approved", False),
        }
        if not result.get("validation_passed"):
            error_output["validation_feedback"] = result.get("validation_feedback", "")
        print(json.dumps(error_output, indent=2), file=__import__('sys').stderr)

def _serialize_scenes(scene_list):
    """Convert scene objects to dictionaries."""
    if not scene_list:
        return []
    
    serialized = []
    for scene in scene_list:
        if hasattr(scene, 'dict'):  # Pydantic model
            serialized.append(scene.dict())
        elif isinstance(scene, dict):
            serialized.append(scene)
        else:
            serialized.append({
                "scene_id": getattr(scene, 'scene_id', ''),
                "heading": getattr(scene, 'heading', ''),
                "action": getattr(scene, 'action', ''),
                "dialogue": getattr(scene, 'dialogue', []),
                "duration": getattr(scene, 'duration', 0),
                "tone": getattr(scene, 'tone', ''),
                "visual_cues": getattr(scene, 'visual_cues', ''),
            })
    return serialized

def _serialize_characters(character_dict):
    """Convert character objects to dictionaries."""
    if not character_dict:
        return []
    
    serialized = []
    for name, char in character_dict.items():
        if hasattr(char, 'dict'):  # Pydantic model
            serialized.append(char.dict())
        elif isinstance(char, dict):
            serialized.append(char)
        else:
            serialized.append({
                "name": getattr(char, 'name', name),
                "role": getattr(char, 'role', ''),
                "appearance": getattr(char, 'appearance', ''),
                "voice_personality": getattr(char, 'voice_personality', ''),
                "visual_description": getattr(char, 'visual_description', ''),
                "emotion_traits": getattr(char, 'emotion_traits', []),
            })
    return serialized

if __name__ == "__main__":
    print("Welcome to The Writer's Room!")
    mode = input("Enter mode (auto/manual): ").strip().lower()
    
    if mode == "auto":
        prompt = input("Enter story prompt: ")
        run_workflow("auto", prompt)
    elif mode == "manual":
        # Load script from some file like manual_script.json
        print("For manual mode, we will try to load 'manual_script.json'.")
        if os.path.exists("manual_script.json"):
            with open("manual_script.json", "r") as f:
                script_data = f.read()
            run_workflow("manual", script_data)
        else:
            print("manual_script.json not found! Creating an example one...")
            example_script = [
                {
                    "scene_id": "1",
                    "heading": "EXT. CYBERPUNK ALLEY - NIGHT",
                    "action": "A dark figure steps from the shadows.",
                    "dialogue": [{"speaker": "CYBORG", "line": "You're late."}],
                    "visual_cues": "Neon reflections in puddles."
                }
            ]
            import json
            with open("manual_script.json", "w") as f:
                json.dump(example_script, f, indent=4)
            print("Created example 'manual_script.json'. Please configure it and run again.")
    else:
        print("Invalid mode. Exiting.")
