"""
MCP Tool Registry: Central tool discovery and registration

Simulates Model Context Protocol (MCP) tool discovery.
Agents dynamically query discover_tools() to get available tools.
"""

from langchain_core.tools import tool
import json
import os
from .memory import memory_db

# Simulate MCP Tool Discovery via a registry
__MCP_TOOL_REGISTRY__ = {}

def mcp_tool(func):
    """Decorator to register a tool in our simulated MCP registry."""
    wrapped_tool = tool(func)
    __MCP_TOOL_REGISTRY__[wrapped_tool.name] = wrapped_tool
    return wrapped_tool

def discover_tools():
    """Agents query this dynamically to get available tools."""
    tools = list(__MCP_TOOL_REGISTRY__.values())
    
    # Phase 2: Lazy import to avoid circular dependencies
    try:
        from phase2 import audio_tools as _audio_tools_module
        if _audio_tools_module:
            audio_tools_list = [
                _audio_tools_module.synthesize_dialogue,
                _audio_tools_module.select_bgm_track,
                _audio_tools_module.download_bgm_track,
                _audio_tools_module.assemble_audio_segments,
                _audio_tools_module.cache_character_voice,
                _audio_tools_module.get_cached_voice,
            ]
            tools.extend(audio_tools_list)
    except Exception as e:
        print(f"[WARNING] phase2 tools not loaded: {e}")
        pass
    return tools

# ==============================================================================
# MCP Tools: Phase 1 & 2
# ==============================================================================

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
    """Queries for stock footage. (Mocked for Phase 1)"""
    return f"[Mock] Found stock footage matching: {query}"

@mcp_tool
def generate_image(prompt: str, character_name: str) -> str:
    """
    Generates image via Pollinations API (Phase 3 will handle this properly).
    For now, returns cached path if available.
    """
    import urllib.request
    import urllib.parse
    
    os.makedirs("images", exist_ok=True)
    clean_name = character_name.lower().replace(' ', '_')
    image_path = f"images/{clean_name}.png"
    
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
def generate_script_segment(prompt: str, num_scenes: int = 3) -> str:
    """
    Generate script via Groq LLM.
    Returns JSON with { story, scenes[] }
    """
    from langchain_groq import ChatGroq
    from pydantic import BaseModel
    from typing import List, Optional
    
    class DialogueEntry(BaseModel):
        speaker: str
        line: str
    
    class SceneOutput(BaseModel):
        scene_id: str
        heading: str
        action: str
        dialogue: List[DialogueEntry]
        tone: Optional[str] = None
        duration: Optional[int] = None
        visual_cues: str
    
    class ScriptOutput(BaseModel):
        story: str
        scenes: List[SceneOutput]
    
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)
    structured_llm = llm.with_structured_output(ScriptOutput)
    
    prompt_text = f"""
    Create a {num_scenes}-scene story from this prompt: {prompt}
    
    For each scene, provide:
    - Heading (location and time)
    - Action description
    - Dialogue with speaker names
    - Tone (urgent, mysterious, calm, dramatic, etc.)
    - Duration in seconds
    - Visual cues for animators
    
    Return valid JSON.
    """
    
    result = structured_llm.invoke(prompt_text)
    return json.dumps(result.model_dump())

# Export tool_map for easy discovery in agents
tool_map = __MCP_TOOL_REGISTRY__
