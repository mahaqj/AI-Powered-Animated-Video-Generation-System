import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from .config.state import AgenticState, Scene, CharacterModel, FullScript

def scriptwriter_node(state: AgenticState) -> dict:
    """Phase 1: Generates the initial story, scenes, and characters using Groq."""
    print("--- ACT: Scriptwriter ---")
    
    # Mode handling
    mode = state.get("mode", "auto")
    prompt = state.get("prompt", "")
    
    from shared.tools import tool_map
    generate_tool = tool_map.get("generate_script_segment")
    
    if not generate_tool:
        return {"validation_passed": False, "validation_feedback": "Script generation tool not found."}
        
    try:
        raw_json = generate_tool.invoke({"prompt": prompt, "num_scenes": 3})
        parsed = json.loads(raw_json)
        
        story_text = parsed.get("story", "")
        scenes_data = parsed.get("scenes", [])
        
        # Convert to Scene objects
        manifest = [Scene(**item) for item in scenes_data]
        
        return {
            "story": story_text,
            "scene_manifest": manifest,
            "raw_script": raw_json,
            "validation_passed": True
        }
    except Exception as e:
        print(f"[SCRIPT ERROR] {e}")
        return {"validation_passed": False, "validation_feedback": str(e)}

def validator_node(state: AgenticState) -> dict:
    """Validates the generated script manifest against project rubrics."""
    print("--- ACT: Validator ---")
    
    if state.get("mode") == "manual":
        raw_script = state.get("raw_script", "[]")
        try:
            parsed = json.loads(raw_script)
            manifest = [Scene(**item) for item in parsed]
            return {"scene_manifest": manifest, "validation_passed": True, "validation_feedback": ""}
        except Exception as e:
            return {"validation_passed": False, "validation_feedback": f"JSON parse error: {str(e)}"}
            
    # Auto mode validation
    manifest = state.get("scene_manifest", [])
    if not manifest:
        return {"validation_passed": False, "validation_feedback": "Manifest is empty."}
        
    for index, scene in enumerate(manifest):
        if not scene.heading:
            return {"validation_passed": False, "validation_feedback": f"Scene {index} is missing a heading."}
        if not scene.action:
            return {"validation_passed": False, "validation_feedback": f"Scene {index} missing action description."}
        if not scene.dialogue or not scene.dialogue[0].speaker:
            return {"validation_passed": False, "validation_feedback": f"Scene {index} missing dialogue label."}
             
    return {"validation_passed": True, "validation_feedback": "Validation successful."}

def hitl_node(state: AgenticState) -> dict:
    """Checkpoint: pauses execution and waits for real human approval."""
    print("\n--- ACT: Human-in-the-Loop Checkpoint ---")
    
    # If already approved (e.g. via API mode), skip the interactive prompt
    if state.get("hitl_approved"):
        print("Pre-approved via API mode. Skipping interactive prompt.")
        return {"hitl_approved": True}

    print("=" * 50)
    print("SCRIPT PREVIEW FOR REVIEW:")
    manifest = state.get("scene_manifest", [])
    for scene in manifest:
        print(f"  Scene {scene.scene_id}: {scene.heading}")
        print(f"  Action: {scene.action[:80]}...")
        for d in scene.dialogue:
            print(f"  [{d.speaker}]: {d.line}")
        print()
    print("=" * 50)

    while True:
        try:
            user_input = input("Do you approve this script to continue? (yes/no): ").strip().lower()
            if user_input == 'yes':
                print("Script approved. Continuing pipeline...")
                return {"hitl_approved": True}
            elif user_input == 'no':
                print("Script rejected. Terminating.")
                return {"hitl_approved": False}
            else:
                print("Please enter 'yes' or 'no'.")
        except (EOFError, OSError):
            print("No interactive terminal found. Defaulting to rejection unless pre-approved.")
            return {"hitl_approved": False}

def character_designer_node(state: AgenticState) -> dict:
    """Extracts character visual descriptions using Groq."""
    print("--- ACT: Character Designer ---")
    
    from shared.tools import tool_map
    query_tool = tool_map.get("query_stock_footage")
    
    manifest = state.get("scene_manifest", [])
    
    # 1. Compile all dialogue/actions to context
    script_text = ""
    for s in manifest:
        script_text += f"{s.action}\n"
        for d in s.dialogue:
            script_text += f"{d.speaker}: {d.line}\n"

    # 2. Execute via LangChain
    from langchain_groq import ChatGroq
    if not os.environ.get("GROQ_API_KEY"):
        return {"character_profiles": {}, "characters": []}
        
    llm = ChatGroq(model_name="llama-3.3-70b-versatile", temperature=0)
    structured_llm = llm.with_structured_output(FullScript)
    
    print("Querying LLM via Pydantic structured output...")
    try:
        full_script_obj = structured_llm.invoke(f"Extract unique character profiles from this script:\n\n{script_text}")
        
        profiles_dict = {}
        characters_list = []
        
        for char in full_script_obj.characters:
            # Add some stock footage context (mock)
            if query_tool:
                ref = query_tool.invoke({"query": char.name})
                char.traits["stock_reference"] = ref
            
            profiles_dict[char.name] = {
                "appearance": char.appearance,
                "traits": char.traits,
                "role": char.role
            }
            characters_list.append(char.model_dump())
            
        print("Successfully extracted characters using LangChain Pydantic Enforcer!")
        return {"character_profiles": profiles_dict, "characters": characters_list}
    except Exception as e:
        print(f"[CHAR ERROR] {e}")
        return {"character_profiles": {}, "characters": []}

def assemble_fullscript_node(state: AgenticState) -> dict:
    """Bundles everything into a validated FullScript JSON."""
    print("--- ACT: Assembler (FullScript) ---")
    
    story = state.get("story", "")
    scenes = state.get("scene_manifest", [])
    characters = state.get("characters", [])

    char_objs = []
    for c in characters:
        if isinstance(c, dict):
            char_objs.append(CharacterModel(**c))
        else:
            char_objs.append(CharacterModel(**c.model_dump()))

    full = FullScript(story=story, scenes=scenes, characters=char_objs)
    return {"full_script": full.model_dump()}
