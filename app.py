import os
from main_graph import build_graph

def run_workflow(mode: str, prompt_or_script: str):
    """Executes the pipeline."""
    workflow = build_graph()
    
    initial_state = {
        "mode": mode,
        "validation_passed": False,
        "hitl_approved": False,
        "scene_manifest": [],
        "character_profiles": {},
        "image_paths": {}
    }
    
    if mode == "auto":
        initial_state["prompt"] = prompt_or_script
    else:
        initial_state["raw_script"] = prompt_or_script
        
    print(f"Starting {mode.upper()} mode execution...")
    result = workflow.invoke(initial_state)
    
    if result.get("validation_passed") and result.get("hitl_approved"):
        print("\n=== EXECUTION SUCCESS ===")
        print(f"Manifest written to: {result.get('final_output_path')}")
        print("Character database updated.")
        
        image_paths = result.get('image_paths', {})
        if image_paths:
            print("Images generated:")
            for char_name, path in image_paths.items():
                print(f"  - {path} ({char_name})")
        else:
            print("Images generated in images/ directory.")
    else:
        print("\n=== EXECUTION HALTED ===")
        if not result.get("validation_passed"):
            print("Failed Validation:", result.get("validation_feedback"))
        elif not result.get("hitl_approved"):
            print("Stopped at Human-in-the-Loop.")

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
