"""
Phase 5: Intelligent Edit & Undo System — Main Entry Point
Run this standalone for CLI-based testing of the edit agent.

Usage:
    python -m phase5.main --run_dir "outputs/12May-1430PM-RUN" --query "Make the scene darker"
    python -m phase5.main --run_dir "outputs/12May-1430PM-RUN" --history
    python -m phase5.main --run_dir "outputs/12May-1430PM-RUN" --revert 1
"""

import argparse
import json
from pathlib import Path

from phase5.agent.intent_classifier import classify_edit_query
from phase5.agent.edit_executor import EditExecutor
from phase5.state.state_manager import StateManager


def run_interactive(run_dir: str):
    """Interactive CLI loop for testing edits."""
    sm = StateManager(run_dir=run_dir)
    state = _load_state(run_dir, sm)

    print("\n" + "="*60)
    print(" Phase 5 — Intelligent Edit & Undo System")
    print("="*60)
    print(f" Run directory: {run_dir}")
    print(" Commands: 'history', 'revert <N>', 'quit', or type an edit query")
    print("="*60 + "\n")

    executor = EditExecutor(run_dir=run_dir, state_manager=sm)

    while True:
        try:
            user_input = input("Edit> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            break

        elif user_input.lower() == "history":
            history = sm.history()
            if not history:
                print("No versions saved yet.")
            else:
                print(f"\n{'ID':<5} {'Label':<8} {'Description':<40} {'Time'}")
                print("-" * 75)
                for v in history:
                    print(f"{v['id']:<5} {v['version_label']:<8} {v['description'][:38]:<40} {v['created_at'][:19]}")
            print()

        elif user_input.lower().startswith("revert "):
            try:
                version_id = int(user_input.split()[1])
                state = sm.revert(version_id)
                print(f"✓ Reverted to version {version_id}\n")
            except (IndexError, ValueError):
                print("Usage: revert <version_id>  (e.g. revert 2)\n")

        else:
            # Treat as edit query
            print(f"\nClassifying: '{user_input}'...")
            intent = classify_edit_query(user_input)
            print(f"→ Intent: {intent.intent}")
            print(f"→ Target: {intent.target}")
            if intent.scope:
                print(f"→ Scope:  {intent.scope}")
            if intent.parameters:
                print(f"→ Params: {intent.parameters}")
            print(f"→ Confidence: {intent.confidence:.0%}")

            # Snapshot before edit
            sm.snapshot(f"Before: {user_input[:50]}", state)

            # Execute
            result = executor.execute(intent, state)
            print(f"\n{'✓' if result['success'] else '✗'} {result['message']}")

            if result["success"]:
                state = result["updated_state"]
                sm.snapshot(f"After: {user_input[:50]}", state)
            print()


def _load_state(run_dir: str, sm: StateManager) -> dict:
    """Load the most recent state."""
    latest = sm.latest_version_id()
    if latest:
        return sm.get_version_state(latest)
    state_file = Path(run_dir) / "state.json"
    if state_file.exists():
        with open(state_file) as f:
            return json.load(f)
    print("[Warning] No existing state found. Starting with empty state.")
    return {}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 5 Edit Agent CLI")
    parser.add_argument("--run_dir", required=True, help="Path to the pipeline run output directory")
    parser.add_argument("--query", help="Single edit query to execute")
    parser.add_argument("--history", action="store_true", help="Print version history")
    parser.add_argument("--revert", type=int, help="Revert to a specific version ID")
    args = parser.parse_args()

    if args.query:
        # Single-shot mode
        sm = StateManager(run_dir=args.run_dir)
        state = _load_state(args.run_dir, sm)
        intent = classify_edit_query(args.query)
        print(json.dumps(intent.model_dump(), indent=2))
        executor = EditExecutor(run_dir=args.run_dir, state_manager=sm)
        result = executor.execute(intent, state)
        print(result["message"])

    elif args.history:
        sm = StateManager(run_dir=args.run_dir)
        history = sm.history()
        print(json.dumps(history, indent=2))

    elif args.revert:
        sm = StateManager(run_dir=args.run_dir)
        state = sm.revert(args.revert)
        print(f"Reverted to version {args.revert}")
        print(json.dumps(state, indent=2))

    else:
        run_interactive(args.run_dir)
