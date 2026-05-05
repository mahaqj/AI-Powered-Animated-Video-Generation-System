"""
Phase 1: Story, Script & Character Design - README

## Overview
This phase takes a free-form natural language prompt and generates:
- A complete narrative story
- Scene-by-scene script with dialogue, tone, duration, and visual cues
- Character roster with voice personalities and appearance descriptions

## Input
- **Auto Mode:** User prompt (e.g., "A young astronaut discovers a hidden ocean on Mars")
- **Manual Mode:** Predefined script JSON array

## Output
- `full_script.json` - Main deliverable with { story, scenes[], characters[] }
- `scene_manifest.json` - Parsed scenes
- `character_db.json` - Character profiles with voice parameters

## LangGraph Workflow
```
START
  ↓
[router based on mode]
  ├→ scriptwriter_node (auto mode)
  └→ validator_node (manual mode)
  ↓
validator_node
  ├→ validation_passed? YES
  │   ↓
  │   hitl_node (human approval)
  │     ├→ approved? YES
  │     │   ↓
  │     │   character_designer_node
  │     └→ approved? NO → END
  └→ validation_passed? NO
      ├→ auto mode? → loop to scriptwriter_node
      └→ manual mode? → END
  ↓
assemble_fullscript_node
  ↓
[async] → to Phase 2 (Audio Generation)
  ↓
END
```

## Data Schema
See `config/state.py` for Pydantic models:
- `Scene` - scene_id, heading, action, dialogue[], visual_cues, tone, duration
- `CharacterModel` - name, role, voice_personality, appearance
- `FullScript` - story, scenes[], characters[]

## Implementation Details
- **LLM:** Groq API (llama-3.3-70b-versatile)
- **Structured Output:** LangChain `ChatGroq.with_structured_output()`
- **Character Extraction:** Pydantic BaseModel enforced parsing
- **Stock Footage Queries:** Via MCP tools (currently mocked)

## Dependencies
- langchain-groq
- pydantic >= 2.13.3
- chromadb (shared)

## Running
See root README.md for entry point (main.py)

## Notes
- Image generation removed from Phase 1 (moved to Phase 3)
- Character voice parameters drive Phase 2 TTS synthesis
- All state persisted to ChromaDB for cross-phase continuity
"""
