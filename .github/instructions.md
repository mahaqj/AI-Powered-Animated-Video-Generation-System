do not create unecessary explainer .md files for the task u do, simply report in the chat interface to the user, no wasting of tokens on reporting and explainatory.md files

any testing , reporting / local files not part of the overall pipeline must be in a local/ folder 
no helper,testing,random scripts in the root , keep it clean all the time

ALWAYS USE VENV FOR RUNNIING COMMANDS

What This Phase Does
Phase 3 is the visual heart of the pipeline. It receives structured scene data from Phase 1 (Story & Script JSON) and an audio timing manifest from Phase 2, then:

Generates a still image per scene using Pollinations.ai (via HTTP POST)
Applies Ken Burns animation (zoom/pan) to each still using FFmpeg
Syncs animated clips to the audio timing manifest
Composites all scene clips with transitions into a single final_output.mp4
Optionally burns in subtitles
Exposes all functionality through a FastAPI router that plugs into the shared backend
Tech Stack (Phase 3 Only)
Concern
Tool
Image Generation
Pollinations.ai REST API (POST)
Animation & Compositing
FFmpeg (subprocess calls)
Backend Routing
FastAPI + Pydantic
Async I/O
Python asyncio + httpx
File I/O
pathlib.Path throughout
Testing
pytest + pytest-asyncio

Absolute Rules Copilot Must Follow
Never use MoviePy — FFmpeg subprocesses only.
Never hardcode file paths. Use pathlib.Path and environment variables loaded via python-dotenv.
Every function that touches disk or network must be async where possible.
Every public function must have a docstring with Args, Returns, and Raises sections.
All Pydantic models live in phase3/schemas.py — never inline them.
FFmpeg must be called via asyncio.create_subprocess_exec (not subprocess.run) inside async contexts.
All generated assets go under the OUTPUT_DIR path configured in .env.
Log every major step using Python's logging module (not print).
Unit tests must mock all HTTP calls and FFmpeg subprocesses — no real network or disk I/O in tests.
Follow PEP 8. Max line length: 100 characters.
Shared JSON Schema Contract (from Phase 1)
Phase 3 consumes this structure — do not alter it, only read from it:

{

  "story": { "title": "string", "genre": "string", "tone": "string", "total_duration_seconds": 120 },

  "characters": [

    {

      "id": "char_001",

      "name": "string",

      "role": "string",

      "visual_description": "string",

      "voice_personality": "string"

    }

  ],

  "scenes": [

    {

      "scene_id": "scene_001",

      "sequence": 1,

      "setting": "string",

      "mood": "string",

      "duration_seconds": 15,

      "visual_prompt": "string",

      "dialogue": [

        { "character_id": "char_001", "line": "string", "emotion": "string" }

      ]

    }

  ]

}
Phase 2 Output Contract (timing_manifest.json)
{

  "scenes": [

    {

      "scene_id": "scene_001",

      "audio_file": "outputs/audio/scene_001.mp3",

      "start_ms": 0,

      "end_ms": 15000,

      "dialogue_segments": [

        { "character_id": "char_001", "audio_file": "outputs/audio/scene_001_line_0.mp3", "start_ms": 500, "end_ms": 4200 }

      ]

    }

  ],

  "background_music": { "audio_file": "outputs/audio/bgm.mp3", "volume": 0.3 }

}
Phase 3 Output Contract
Phase 3 produces:

outputs/images/scene_001.png ... per scene
outputs/clips/scene_001_animated.mp4 ... per scene (Ken Burns applied)
outputs/final_output.mp4 — the finished composited video
outputs/phase3_state.json — updated pipeline state handed to Phase 4/5

