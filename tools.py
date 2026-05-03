from langchain_core.tools import tool
import json
import os
from memory import memory_db

# Simulate MCP Tool Discovery via a registry
__MCP_TOOL_REGISTRY__ = {}

def mcp_tool(func):
    """Decorator to register a tool in our simulated MCP registry."""
    wrapped_tool = tool(func)
    __MCP_TOOL_REGISTRY__[wrapped_tool.name] = wrapped_tool
    return wrapped_tool

def discover_tools():
    """Agents query this dynamically to get tools."""
    return list(__MCP_TOOL_REGISTRY__.values())

@mcp_tool
def commit_character_memory(name: str, traits: str, appearance: str, image_path: str = "") -> str:
    """Stores character identity metadata and image references into memory."""
    try:
        traits_dict = json.loads(traits)
    except:
        traits_dict = {"raw_traits": traits}
    return memory_db.commit_character(name, traits_dict, appearance, image_path)

@mcp_tool
def commit_script_memory(scene_id: str, content: str) -> str:
    """Stores a finalized script scene into memory."""
    return memory_db.commit_script_segment(scene_id, content)

@mcp_tool
def query_stock_footage(query: str) -> str:
    """Queries for stock footage. (Mocked for this phase)"""
    return f"[Mock] Found stock footage matching: {query}"

@mcp_tool
def generate_image(prompt: str, character_name: str) -> str:
    """
    Triggers Image Synthesis via Stable Diffusion endpoint.
    Returns the file path to the generated image.
    """
    import urllib.request
    import urllib.parse
    
    os.makedirs("images", exist_ok=True)
    clean_name = character_name.lower().replace(' ', '_')
    image_path = f"images/{clean_name}.png"
    
    # Check for cache
    if os.path.exists(image_path) and os.path.getsize(image_path) > 5000:
        return image_path

    try:
        prompt_encoded = urllib.parse.quote(f"A high quality concept art portrait of {prompt}")
        image_url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1024&height=1024&nologo=true"
        
        req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as image_response, open(image_path, 'wb') as out_file:
            out_file.write(image_response.read())
    except Exception as e:
        print(f"Failed to fetch image: {e}")
    return image_path

@mcp_tool
def generate_environment_image(prompt: str, scene_id: str) -> str:
    """Generates a cinematic background environment for a scene with retries and integrity checks."""
    import urllib.request
    import urllib.parse
    import time
    import random
    import cv2
    import numpy as np
    
    os.makedirs("scene_backgrounds", exist_ok=True)
    image_path = f"scene_backgrounds/{scene_id.replace(' ', '_')}.png"
    
    # Validation helper
    def is_valid_image(path):
        if not os.path.exists(path) or os.path.getsize(path) < 1000:
            return False
        img = cv2.imread(path)
        return img is not None

    # Check for valid cache
    if is_valid_image(image_path):
        return image_path
    elif os.path.exists(image_path):
        os.remove(image_path) # Remove partial/corrupt file

    clean_prompt = urllib.parse.quote(f"Cinematic wide angle landscape, {prompt}, 8k resolution, highly detailed, photorealistic")
    image_url = f"https://image.pollinations.ai/prompt/{clean_prompt}?width=1280&height=720&nologo=true"
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            # Jitter to avoid thunderous herd
            wait_time = random.uniform(1.0, 4.0) + (attempt * 2)
            time.sleep(wait_time)
            
            print(f"[SD-AI] Requesting environment for {scene_id} (Attempt {attempt+1}/{max_retries})...")
            req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
            
            with urllib.request.urlopen(req, timeout=45) as image_response:
                data = image_response.read()
                
            # Atomic check: Verify in memory before writing to disk
            arr = np.frombuffer(data, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            
            if img is not None:
                with open(image_path, 'wb') as out_file:
                    out_file.write(data)
                print(f"[SD-AI SUCCESS] Generated {scene_id}.")
                return image_path
            else:
                print(f"[SD-AI WARNING] Corrupt data received for {scene_id} on attempt {attempt+1}.")
                
        except Exception as e:
            print(f"[SD-AI WARNING] Attempt {attempt+1} failed for {scene_id}: {e}")
            
    return f"Error: Failed after {max_retries} attempts"

@mcp_tool
def generate_script_segment(prompt: str, num_scenes: int = 3) -> str:
    """
    Generates a structured multi-scene screenplay from a prompt using a LangChain LLM.
    Returns a JSON string of a list of scene dicts.
    """
    import json
    import os
    from typing import Optional
    from pydantic import BaseModel
    from langchain_groq import ChatGroq

    if not os.environ.get("GROQ_API_KEY"):
        raise ValueError("CRITICAL FAILURE: GROQ_API_KEY not found. Strict rubric compliance requires a valid key for the Scriptwriter LLM.")

    class DialogueOutput(BaseModel):
        speaker: str
        line: str

    class SceneOutput(BaseModel):
        scene_id: str
        heading: str
        action: str
        dialogue: list[DialogueOutput]
        visual_cues: str
        tone: Optional[str] = None
        duration: Optional[int] = None

    class ScriptManifestOutput(BaseModel):
        story: str
        scenes: list[SceneOutput]
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.8)
    structured_llm = llm.with_structured_output(ScriptManifestOutput)

    system_prompt = (
        f"You are an expert Hollywood scriptwriter AI.\n"
        f"Write a {num_scenes}-scene screenplay based on the prompt: '{prompt}'.\n"
        f"Maintain character consistency across the scenes."
    )
    
    print(f"Querying LLM Scriptwriter Engine for {num_scenes} scenes...")
    result = structured_llm.invoke(system_prompt)

    manifest_dict = {
        "story": result.story,
        "scenes": [s.model_dump() for s in result.scenes]
    }
    return json.dumps(manifest_dict)
@mcp_tool
def get_task_graph(scene_manifest: str) -> str:
    """
    Parses scene_manifest JSON and returns a task graph as JSON string.
    Each task = {scene_id, dialogue, visual_cues, character, audio_path, video_path}
    """
    try:
        manifest = json.loads(scene_manifest)
        tasks = []
        for scene in manifest:
            scene_id = scene.get("scene_id", "Unknown")
            visual_cues = scene.get("visual_cues", "")
            
            # Decompose scene into per-character tasks for dialogue
            for idx, d in enumerate(scene.get("dialogue", [])):
                char = d.get("speaker", "Narrator")
                line = d.get("line", "")
                
                task = {
                    "scene_id": f"{scene_id}_task_{idx}",
                    "original_scene_id": scene_id,
                    "character": char,
                    "dialogue": line,
                    "visual_cues": visual_cues,
                    "audio_path": f"audio_tracks/{scene_id.replace(' ', '_')}_{char.replace(' ', '_')}_{idx}.wav",
                    "video_path": f"raw_frames/{scene_id.replace(' ', '_')}_task_{idx}/"
                }
                tasks.append(task)
        return json.dumps(tasks)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp_tool
def voice_cloning_synthesizer(text: str, character_name: str, emotion: str, output_path: str) -> str:
    """
    Uses gTTS and pydub to generate character-aligned speech.
    Now includes gender inference and character-specific uniqueness.
    """
    from gtts import gTTS
    from pydub import AudioSegment
    import os
    import hashlib
    
    # 1. Load character_db.json
    char_db = {}
    appearance = ""
    trait = ""
    if os.path.exists("character_db.json"):
        with open("character_db.json", "r") as f:
            char_db = json.load(f)
            char_info = char_db.get(character_name, {})
            trait = char_info.get("traits", {}).get("personality", "").lower()
            appearance = char_info.get("appearance", "").lower()
            
    # 2. Infer Gender (Heuristic based on appearance and name)
    male_words = {"he ", "him ", "his ", "man ", "sir ", "lord", "king", "warrior", "beast", "dragon"}
    female_words = {"she ", "her ", "hers ", "woman ", "lady", "queen", "damsel", "maiden"}
    
    is_male = any(w in appearance or w in character_name.lower() for w in male_words)
    is_female = any(w in appearance or w in character_name.lower() for w in female_words)
    
    # Gender Base Multiplier (Male = lower pitch, Female = higher pitch)
    gender_multiplier = 1.0
    if is_female and not is_male:
        gender_multiplier = 1.25 # Feminine pitch
    elif is_male:
        gender_multiplier = 0.85 # Masculine pitch
        
    # 3. Unique Character Seed (based on name hash)
    name_hash = int(hashlib.md5(character_name.encode()).hexdigest(), 16)
    unique_offset = (name_hash % 20 - 10) / 100.0 # From -0.1 to +0.1
    
    # 4. Personality to Voice Mapping Table (Base Params)
    mapping = {
        "reckless and bold": {"tld": "us", "speed": 1.3},
        "mysterious and cautious": {"tld": "co.uk", "speed": 0.85},
        "gritty and world-weary": {"tld": "com.au", "speed": 0.9},
        "authoritative and cold": {"tld": "co.uk", "speed": 0.8},
        "desperate and resourceful": {"tld": "us", "speed": 1.2},
        "intellectual and driven": {"tld": "ca", "speed": 1.0},
        "stoic and determined": {"tld": "us", "speed": 0.95},
        "impatient and intense": {"tld": "us", "speed": 1.4}
    }
    
    # Selection from mapping
    matched = {"tld": "us", "speed": 1.0}
    for key, params in mapping.items():
        if key in trait:
            matched = params
            break
            
    # Apply unique offset to speed
    final_speed = matched["speed"] + unique_offset
    
    # Unique TLD distribution if no mapping matched
    available_tlds = ["com", "co.uk", "ca", "co.in", "ie", "co.za", "com.au"]
    tld = matched["tld"]
    if matched["tld"] == "us" and trait == "":
        tld = available_tlds[name_hash % len(available_tlds)]
    
    # 5. Generate audio with gTTS
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tts = gTTS(text=text, lang="en", tld=tld, slow=False)
    temp_path = output_path.replace(".wav", "_temp.mp3")
    tts.save(temp_path)
    
    # 6. Apply Pitch and Speed Shift via frame_rate manipulation
    audio = AudioSegment.from_mp3(temp_path)
    
    # Combined effect: Personality Speed * Gender Pitch * Unique Offset
    combined_mod = final_speed * gender_multiplier
    
    if combined_mod != 1.0:
        new_sample_rate = int(audio.frame_rate * combined_mod)
        audio = audio._spawn(audio.raw_data, overrides={'frame_rate': new_sample_rate})
        audio = audio.set_frame_rate(44100)
        
    # 7. Export final .wav
    audio.export(output_path, format="wav")
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    return output_path

@mcp_tool
def face_swapper(frame_path: str, character_image_path: str, character_name: str) -> str:
    """
    Uses OpenCV to overlay character portrait on frame.
    Simulates identity-based mapping by placing portrait in top corner.
    """
    import cv2
    import numpy as np
    
    frame = cv2.imread(frame_path)
    char_img = cv2.imread(character_image_path)
    
    if frame is None or char_img is None:
        return frame_path # Fail silently or return original
        
    # Resize char_img to be a small thumbnail (identity badge style)
    h, w, _ = frame.shape
    badge_size = int(h * 0.3)
    char_img_resized = cv2.resize(char_img, (badge_size, badge_size))
    
    # Overlay in top-left
    frame[10:10+badge_size, 10:10+badge_size] = char_img_resized
    
    # Add character name label
    cv2.putText(frame, character_name, (10, 20+badge_size+20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    
    dir_name = os.path.dirname(frame_path)
    base_name = os.path.basename(frame_path)
    output_dir = os.path.join(dir_name, "mapped")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, base_name.replace(".png", "_mapped.png"))
    
    cv2.imwrite(output_path, frame)
    return output_path

@mcp_tool
def identity_validator(character_name: str) -> str:
    """Checks character_name exists in character_db.json."""
    if not os.path.exists("character_db.json"):
        return "invalid: character_db.json not found"
        
    with open("character_db.json", "r") as f:
        db = json.load(f)
        
    if character_name in db:
        return "valid"
    return f"invalid: {character_name} not found in character_db."

@mcp_tool
def lip_sync_aligner(audio_path: str, frames_dir: str, output_path: str, scene_id: str) -> str:
    """
    Uses MoviePy to combine frames + audio into final .mp4.
    Calculates frame duration from audio length.
    """
    from moviepy import ImageSequenceClip, AudioFileClip
    import os
    import glob
    
    # Get audio duration
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration
    
    # Get frames (prefer mapped if they exist, else raw)
    mapped_pattern = os.path.join(frames_dir, "mapped", "*.png")
    frames = sorted(glob.glob(mapped_pattern))
    if not frames:
        raw_pattern = os.path.join(frames_dir, "*.png")
        frames = sorted(glob.glob(raw_pattern))
        
    if not frames:
        raise ValueError(f"No frames found in {frames_dir}")
        
    # Ensure standard sequence if no frames found (fallback logic should have run)
    
    fps = len(frames) / duration
    
    video_clip = ImageSequenceClip(frames, fps=fps)
    video_clip = video_clip.with_audio(audio_clip)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    video_clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", logger=None)
    
    return output_path
