import sys
import os
from datetime import datetime
from src.app import run_workflow

def main():
    print("Welcome to The Writer's Room!")
    
    # 1. Select Mode
    mode = input("Enter mode (auto/manual): ").strip().lower()
    if mode not in ["auto", "manual"]:
        mode = "auto"
        
    # 2. Generate timestamped run directory
    # Format: 6MAY-214AM-RUN
    now = datetime.now()
    time_part = now.strftime("%I%M%p").lstrip("0")
    timestamp = f"{now.day}{now.strftime('%b')}-{time_part}".upper()
    run_dir = f"outputs/{timestamp}-RUN"
    os.makedirs(run_dir, exist_ok=True)
    
    print(f"All outputs for this session will be stored in: {run_dir}")
    
    # 3. Get Input
    if mode == "auto":
        prompt = input("Enter story prompt: ").strip()
        run_workflow(mode, prompt, run_dir)
    else:
        # Manual mode expects manual_script.json in root
        if os.path.exists("manual_script.json"):
            with open("manual_script.json", "r") as f:
                script_content = f.read()
            run_workflow(mode, script_content, run_dir)
        else:
            print("Error: manual_script.json not found in root directory.")

if __name__ == "__main__":
    main()
