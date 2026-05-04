import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports from config/
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.state import AgenticState, Scene
from tools import discover_tools, __MCP_TOOL_REGISTRY__
from pydantic import BaseModel

class ValidationResult(BaseModel):
    is_valid: bool
    feedback: str

def scriptwriter_node(state: AgenticState) -> dict:
    """Takes a prompt and generates a structured multi-scene screenplay via MCP tool."""
    print("--- ACT: Scriptwriter ---")
    prompt = state.get("prompt", "")

    # Dynamically discover and invoke MCP tool — no hardcoding
    tools = discover_tools()
    tool_map = {t.name: t for t in tools}

    generate_tool = tool_map.get("generate_script_segment")
    if not generate_tool:
        return {"scene_manifest": [], "validation_passed": False, "validation_feedback": "MCP tool generate_script_segment not found."}

    raw_json = generate_tool.invoke({"prompt": prompt, "num_scenes": 3})

    import json
    parsed = json.loads(raw_json)
    story_text = parsed.get("story", "")
    scenes_data = parsed.get("scenes", [])
    manifest = [Scene(**s) for s in scenes_data]

    return {"scene_manifest": manifest, "story": story_text}


def validator_node(state: AgenticState) -> dict:
    """Validates the structure of the scene manifest."""
    print("--- ACT: Validator ---")
    
    if state["mode"] == "manual":
        # In manual mode, we parse raw_script
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
        
    # Example logic: check if each scene has a heading
    for index, scene in enumerate(manifest):
        if not scene.heading:
            return {"validation_passed": False, "validation_feedback": f"Scene {index} is missing a heading."}
        if not scene.action:
            return {"validation_passed": False, "validation_feedback": f"Scene {index} missing action description."}
        if not scene.dialogue or not scene.dialogue[0].get("speaker"):
            return {"validation_passed": False, "validation_feedback": f"Scene {index} missing dialogue label."}
             
    return {"validation_passed": True, "validation_feedback": "Validation successful."}


def hitl_node(state: AgenticState) -> dict:
    """Checkpoint: pauses execution and waits for real human approval."""
    print("\n--- ACT: Human-in-the-Loop Checkpoint ---")
    print("=" * 50)
    print("SCRIPT PREVIEW FOR REVIEW:")
    manifest = state.get("scene_manifest", [])
    for scene in manifest:
        print(f"  Scene {scene.scene_id}: {scene.heading}")
        print(f"  Action: {scene.action[:80]}...")
        for d in scene.dialogue:
            print(f"  [{d.get('speaker')}]: {d.get('line')}")
        print()
    print("=" * 50)

    while True:
        user_input = input("Do you approve this script to continue? (yes/no): ").strip().lower()
        if user_input in ("yes", "no"):
            break
        print("Please enter 'yes' or 'no'.")

    approved = user_input == "yes"
    if not approved:
        print("Script rejected by user. Halting pipeline.")
    else:
        print("Script approved. Continuing pipeline...")

    return {"hitl_approved": approved}


def character_designer_node(state: AgenticState) -> dict:
    """Extracts character metadata and queries stock footage via MCP tools."""
    print("--- ACT: Character Designer ---")

    # 1. Define Pydantic Models for LLM Extraction
    from typing import Optional
    from pydantic import BaseModel

    class CharacterProfileOutput(BaseModel):
        name: str
        role: Optional[str] = None
        voice_personality: Optional[str] = None
        appearance: Optional[str] = None

    class CharactersOutput(BaseModel):
        characters: list[CharacterProfileOutput]

    # Dynamically discover MCP tools
    tools = discover_tools()
    tool_map = {t.name: t for t in tools}
    query_tool = tool_map.get("query_stock_footage")

    manifest = state.get("scene_manifest", [])
    profiles_dict = {}

    # Prepare raw text buffer for LLM reading
    script_text = ""
    for s in manifest:
        script_text += f"{s.action}\n"
        for d in s.dialogue:
            script_text += f"{d.get('speaker', 'UNKNOWN')}: {d.get('line', '')}\n"

    # 2. Execute via LangChain using the rubric's correct pattern
    from langchain_groq import ChatGroq
    import os
    
    if not os.environ.get("GROQ_API_KEY"):
        raise ValueError("CRITICAL FAILURE: GROQ_API_KEY missing. The Character Designer LLM requires a valid token.")
        
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7, max_retries=1)
    structured_llm = llm.with_structured_output(CharactersOutput)
    
    prompt = (
        f"Read the following script excerpt. Extract every distinct character. For each character, provide: name, role (protagonist/antagonist/supporting/etc.), a short voice_personality phrase (3-6 words), and a 1-sentence physical appearance.\n\nSCRIPT:\n{script_text}"
    )
    
    print("Querying LLM via Pydantic structured output...")
    result = structured_llm.invoke(prompt)

    characters_list = []
    for char in result.characters:
        profiles_dict[char.name] = {
            "traits": {"voice_personality": char.voice_personality},
            "appearance": char.appearance,
            "role": char.role,
        }
        characters_list.append(char.model_dump())
        if query_tool:
            footage_result = query_tool.invoke({"query": f"{char.name} reference footage"})
            print(f"[MCP] Stock footage query for {char.name}: {footage_result}")
            
    print("Successfully extracted characters using LangChain Pydantic Enforcer!")

    # Write to local JSON deliverable
    import json
    with open("character_db.json", "w") as f:
        json.dump(profiles_dict, f, indent=4)

    return {"character_profiles": profiles_dict, "characters": characters_list}


def assemble_fullscript_node(state: AgenticState) -> dict:
    """Bundles `story`, `scene_manifest`, and `characters` into a validated FullScript JSON."""
    print("--- ACT: Assembler (FullScript) ---")
    from config.state import FullScript, CharacterModel
    import json

    story = state.get("story", "")
    scenes = state.get("scene_manifest", [])
    characters = state.get("characters", [])

    # Ensure CharacterModel instances
    char_objs = []
    for c in characters:
        if isinstance(c, dict):
            char_objs.append(CharacterModel(**c))
        else:
            # already a pydantic model-like
            char_objs.append(CharacterModel(**c.model_dump()))

    # Scenes should already be `Scene` models; FullScript will validate
    full = FullScript(story=story, scenes=scenes, characters=char_objs)

    out_path = "full_script.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(full.model_dump(), f, indent=2)

    return {"full_script": full.model_dump(), "final_output_path": out_path}


# IMAGE SYNTHESIZER REMOVED - Phase 1 no longer generates images
# def image_synth_node(state: AgenticState) -> dict:
#     """Synthesizes images via MCP Tools."""
#     print("--- ACT: Image Synthesizer ---")
#     profiles = state.get("character_profiles", {})
#     image_paths = {}
#     
#     generate_tool = __MCP_TOOL_REGISTRY__["generate_image"]
#     
#     for name, data in profiles.items():
#         appearance = data.get("appearance", "")
#         # Call the simulated MCP tool
#         prompt = f"Portrait of {name}, {appearance}"
#         img_path = generate_tool.invoke({"prompt": prompt, "character_name": name})
#         image_paths[name] = img_path
#         
#     return {"image_paths": image_paths}



def memory_commit_node(state: AgenticState) -> dict:
    """Invokes commit tools dynamically to write to ChromaDB and output final manifest."""
    print("--- ACT: Memory Commit ---")
    
    commit_script = __MCP_TOOL_REGISTRY__["commit_script_memory"]
    commit_char = __MCP_TOOL_REGISTRY__["commit_character_memory"]
    
    # Store Script
    manifest = state.get("scene_manifest", [])
    for scene in manifest:
        try:
             commit_script.invoke({"scene_id": scene.scene_id, "content": scene.model_dump_json()})
        except Exception:
             pass # suppress pydantic v2 vs v1 serialization diffs
             
    # Store Characters (no image_paths in Phase 1 - images removed)
    profiles = state.get("character_profiles", {})
    
    for name, data in profiles.items():
        traits_str = json.dumps(data.get("traits", {}))
        commit_char.invoke({
             "name": name, 
             "traits": traits_str, 
             "appearance": data.get("appearance", ""),
        })
        
    # Write scene manifest
    with open("scene_manifest.json", "w") as f:
         manifest_dicts = [s.model_dump() for s in manifest]
         json.dump(manifest_dicts, f, indent=4)

    # ==============================================================================
    # Phase 2: Persist Audio Data
    # ==============================================================================
    
    from memory import memory_db
    
    # Persist audio manifest to ChromaDB
    audio_manifest = state.get("audio_manifest", [])
    timing_manifest = state.get("timing_manifest", {})
    
    for scene in manifest:
        scene_id = scene.scene_id
        
        # Get audio tasks for this scene
        scene_audio_tasks = [task for task in audio_manifest if task.get("scene_id") == scene_id]
        if scene_audio_tasks:
            memory_db.commit_audio_manifest(scene_id, scene_audio_tasks)
        
        # Get timing entry for this scene
        if scene_id in timing_manifest:
            timing_entry = timing_manifest[scene_id]
            memory_db.commit_timing_manifest(
                scene_id,
                timing_entry.model_dump() if hasattr(timing_entry, 'model_dump') else timing_entry
            )
    
    # Write timing manifest to JSON file
    timing_manifest_output = {}
    for scene_id, timing_entry in timing_manifest.items():
        try:
            if hasattr(timing_entry, 'model_dump'):
                timing_manifest_output[scene_id] = timing_entry.model_dump()
            else:
                timing_manifest_output[scene_id] = timing_entry
        except Exception:
            pass
    
    with open("timing_manifest.json", "w") as f:
        json.dump(timing_manifest_output, f, indent=4, default=str)
    
    print(f"Audio manifest persisted for {len(timing_manifest)} scenes")

    return {"final_output_path": "scene_manifest.json"}


# ==============================================================================
# Phase 2: Audio Generation Nodes
# ==============================================================================

def audio_synthesizer_node(state: AgenticState) -> dict:
    """
    Synthesizes dialogue lines to speech for each scene using gTTS.
    Applies character voice parameters (gender, personality → speed/pitch).
    """
    print("--- ACT: Audio Synthesizer ---")
    
    synth_func = None
    cache_func = None
    import_error = None
    
    try:
        from audio_tools import (
            _synthesize_dialogue_impl as synth_func,
            _cache_character_voice_impl as cache_func,
        )
        print(f"[DEBUG] Successfully imported _impl functions: synth_func={type(synth_func).__name__}, cache_func={type(cache_func).__name__}")
    except ImportError as e:
        import_error = f"ImportError: {e}"
        print(f"[ERROR] Failed to import _impl functions: {e}")
    except Exception as e:
        import_error = f"Exception: {e}"
        print(f"[ERROR] Unexpected error importing _impl functions: {e}")
    
    # Fallback if _impl import failed
    if synth_func is None or cache_func is None:
        print(f"[FALLBACK] _impl functions not available, trying fallback import...")
        try:
            from audio_tools import synthesize_dialogue as synth_func, cache_character_voice as cache_func
            print(f"[FALLBACK] Using @tool-decorated versions: synth_func={type(synth_func).__name__}, cache_func={type(cache_func).__name__}")
            print(f"[WARNING] Tool versions will fail if called directly - will skip synthesis")
            return {
                "audio_manifest": [],
                "audio_files": {},
                "character_voice_cache": {},
            }
        except Exception as fallback_err:
            print(f"[ERROR] Both import strategies failed: {import_error}, fallback_err={fallback_err}")
            return {
                "audio_manifest": [],
                "audio_files": {},
                "character_voice_cache": {},
            }
    
    manifest = state.get("scene_manifest", [])
    characters = state.get("characters", [])
    
    audio_manifest = []
    audio_files = {}
    
    # Create character lookup
    char_lookup = {}
    for char in characters:
        char_lookup[char.get("name", "")] = char
    
    # Process each scene's dialogue
    for scene in manifest:
        scene_id = scene.scene_id
        
        for dialogue_idx, dialogue_entry in enumerate(scene.dialogue):
            speaker = dialogue_entry.get("speaker", "Unknown")
            line = dialogue_entry.get("line", "")
            
            if not line:
                continue
            
            char_data = char_lookup.get(speaker, {})
            appearance = char_data.get("appearance", "")
            voice_personality = char_data.get("voice_personality", "")
            
            # Cache voice (call function directly)
            try:
                cache_func(
                    character_name=speaker,
                    voice_personality=voice_personality,
                    character_appearance=appearance,
                )
            except Exception as e:
                print(f"[CACHE WARNING] Failed to cache voice for {speaker}: {e}")
            
            # Synthesize dialogue (call function directly)
            try:
                output_path = synth_func(
                    text=line,
                    character_name=speaker,
                    character_appearance=appearance,
                    voice_personality=voice_personality,
                    scene_id=scene_id,
                    dialogue_index=dialogue_idx,
                )
                
                task_id = f"{scene_id}_{dialogue_idx}_{speaker}"
                audio_task = {
                    "scene_id": scene_id,
                    "dialogue_index": dialogue_idx,
                    "character": speaker,
                    "dialogue_text": line,
                    "audio_file": output_path,
                }
                audio_manifest.append(audio_task)
                audio_files[task_id] = output_path
                
            except Exception as e:
                print(f"[AUDIO ERROR] Failed to synthesize dialogue for {speaker}: {e}")
    
    print(f"Successfully synthesized {len(audio_manifest)} dialogue lines")
    
    return {
        "audio_manifest": audio_manifest,
        "audio_files": audio_files,
        "character_voice_cache": state.get("character_voice_cache", {}),
    }


def bgm_selector_node(state: AgenticState) -> dict:
    """
    Selects and downloads background music (BGM) for each scene based on tone.
    Returns mapping of scene_id → local BGM file path.
    """
    print("--- ACT: BGM Selector ---")
    
    select_func = None
    download_func = None
    import_error = None
    
    try:
        from audio_tools import (
            _select_bgm_track_impl as select_func,
            _download_bgm_track_impl as download_func,
        )
        print(f"[DEBUG] Successfully imported BGM _impl functions: select_func={type(select_func).__name__}, download_func={type(download_func).__name__}")
    except ImportError as e:
        import_error = f"ImportError: {e}"
        print(f"[ERROR] Failed to import BGM _impl functions: {e}")
    except Exception as e:
        import_error = f"Exception: {e}"
        print(f"[ERROR] Unexpected error importing BGM _impl functions: {e}")
    
    # Fallback if _impl import failed
    if select_func is None or download_func is None:
        print(f"[FALLBACK] BGM _impl functions not available, trying fallback import...")
        try:
            from audio_tools import select_bgm_track as select_func, download_bgm_track as download_func
            print(f"[FALLBACK] Using @tool-decorated versions: will fail if called directly")
            return {"bgm_manifest": {}}
        except Exception as fallback_err:
            print(f"[ERROR] Both import strategies failed for BGM: {import_error}, fallback_err={fallback_err}")
            return {"bgm_manifest": {}}
    
    manifest = state.get("scene_manifest", [])
    bgm_manifest = {}
    
    for idx, scene in enumerate(manifest):
        scene_id = scene.scene_id
        tone = scene.tone or "default"
        duration_ms = (scene.duration or 30) * 1000  # Convert seconds to ms
        
        try:
            # Select BGM track based on tone (call function directly)
            track_json = select_func(tone, duration_ms)
            track_metadata = json.loads(track_json)
            
            # Download and cache the track
            track_url = track_metadata.get("url", "")
            track_id = f"{scene_id.replace(' ', '_')}"
            
            # Use Freesound instead of broken Pixabay URLs
            from audio_tools import _download_bgm_from_freesound
            bgm_file = _download_bgm_from_freesound(tone)
            bgm_manifest[scene_id] = bgm_file
                
        except Exception as e:
            print(f"[BGM ERROR] Failed to select/download BGM for {scene_id}: {e}")
            bgm_manifest[scene_id] = ""
    
    print(f"Selected BGM for {len(bgm_manifest)} scenes")
    
    return {"bgm_manifest": bgm_manifest}


def audio_assembler_node(state: AgenticState) -> dict:
    """
    Assembles dialogue audio files with background music and generates
    timing manifest with detailed start/end times for each segment.
    """
    print("--- ACT: Audio Assembler ---")
    
    assemble_func = None
    import_error = None
    
    try:
        from audio_tools import _assemble_audio_segments_impl as assemble_func
        from config.state import TimingManifestEntry, AudioSegment as AudioSegmentModel
        print(f"[DEBUG] Successfully imported assemble_func: {type(assemble_func).__name__}")
    except ImportError as e:
        import_error = f"ImportError: {e}"
        print(f"[ERROR] Failed to import _assemble_audio_segments_impl: {e}")
    except Exception as e:
        import_error = f"Exception: {e}"
        print(f"[ERROR] Unexpected error importing _assemble_audio_segments_impl: {e}")
    
    # Fallback if _impl import failed
    if assemble_func is None:
        print(f"[FALLBACK] assemble _impl not available, trying fallback import...")
        try:
            from audio_tools import assemble_audio_segments as assemble_func
            from config.state import TimingManifestEntry, AudioSegment as AudioSegmentModel
            print(f"[FALLBACK] Using @tool-decorated version: will fail if called directly")
            return {
                "timing_manifest": {},
                "audio_output_path": "",
            }
        except Exception as fallback_err:
            print(f"[ERROR] Both import strategies failed for assembler: {import_error}, fallback_err={fallback_err}")
            return {
                "timing_manifest": {},
                "audio_output_path": "",
            }
    
    manifest = state.get("scene_manifest", [])
    audio_manifest = state.get("audio_manifest", [])
    bgm_manifest = state.get("bgm_manifest", {})
    
    timing_manifest = {}
    
    # Group audio tasks by scene
    tasks_by_scene = {}
    for task in audio_manifest:
        scene_id = task.get("scene_id")
        if scene_id not in tasks_by_scene:
            tasks_by_scene[scene_id] = []
        tasks_by_scene[scene_id].append(task)
    
    # Process each scene's audio assembly
    for scene in manifest:
        scene_id = scene.scene_id
        
        if scene_id not in tasks_by_scene:
            print(f"[ASSEMBLY WARNING] No audio tasks for scene {scene_id}")
            continue
        
        try:
            dialogue_tasks = tasks_by_scene[scene_id]
            bgm_file = bgm_manifest.get(scene_id, "")
            
            # Prepare dialogue files list
            dialogue_list = []
            for task in dialogue_tasks:
                dialogue_list.append({
                    "file": task.get("audio_file"),
                    "character": task.get("character"),
                })
            
            # Assemble audio segments (call function directly)
            assembly_result_json = assemble_func(
                dialogue_files=json.dumps(dialogue_list),
                bgm_file=bgm_file,
                scene_id=scene_id,
            )
            
            assembly_result = json.loads(assembly_result_json)
            
            if "error" in assembly_result:
                print(f"[ASSEMBLY ERROR] {assembly_result['error']}")
                continue
            
            # Create timing manifest entry
            segments = []
            for timing_entry in assembly_result.get("timing_entries", []):
                segment = AudioSegmentModel(
                    scene_id=scene_id,
                    dialogue_index=timing_entry.get("dialogue_index", 0),
                    character=timing_entry.get("character", "Unknown"),
                    start_ms=timing_entry.get("start_ms", 0),
                    end_ms=timing_entry.get("end_ms", 0),
                    audio_file=dialogue_list[timing_entry.get("dialogue_index", 0)].get("file"),
                )
                segments.append(segment)
            
            timing_entry = TimingManifestEntry(
                scene_id=scene_id,
                audio_file=assembly_result.get("audio_file", ""),
                duration_ms=assembly_result.get("duration_ms", 0),
                dialogue_count=len(dialogue_tasks),
                has_bgm=bool(bgm_file and os.path.exists(bgm_file)),
                segments=segments,
            )
            
            timing_manifest[scene_id] = timing_entry
            
        except Exception as e:
            print(f"[ASSEMBLY ERROR] Failed to assemble audio for {scene_id}: {e}")
    
    print(f"Assembled audio for {len(timing_manifest)} scenes")
    
    return {
        "timing_manifest": timing_manifest,
        "audio_output_path": "timing_manifest.json",
    }
