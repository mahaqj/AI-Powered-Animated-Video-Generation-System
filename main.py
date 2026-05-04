#!/usr/bin/env python3
"""
AI-Powered Animated Video Generation System

Entry point for the agentic video generation pipeline.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from app import run_workflow

if __name__ == "__main__":
    print("Welcome to The Writer's Room!")
    mode = input("Enter mode (auto/manual): ").strip().lower()
    
    if mode == "auto":
        prompt = input("Enter story prompt: ")
        run_workflow("auto", prompt)
    elif mode == "manual":
        # Load script from manual_script.json
        manual_script_path = Path(__file__).parent / "manual_script.json"
        print(f"For manual mode, we will try to load '{manual_script_path.name}'.")
        if manual_script_path.exists():
            with open(manual_script_path, "r") as f:
                script_data = f.read()
            run_workflow("manual", script_data)
        else:
            print(f"{manual_script_path.name} not found! Creating an example one...")
            import json
            example_script = [
                {
                    "scene_id": "1",
                    "heading": "EXT. CYBERPUNK ALLEY - NIGHT",
                    "action": "A dark figure steps from the shadows.",
                    "dialogue": [{"speaker": "CYBORG", "line": "You're late."}],
                    "visual_cues": "Neon reflections in puddles."
                }
            ]
            with open(manual_script_path, "w") as f:
                json.dump(example_script, f, indent=4)
            print(f"Created example '{manual_script_path.name}'. Please configure it and run again.")
    else:
        print("Invalid mode. Exiting.")
