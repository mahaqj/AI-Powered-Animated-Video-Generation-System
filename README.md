# AI-Powered-Animated-Video-Generation-System

AI4015-Agentic Artificial Intelligence Course Project

## Overview

A multi-phase agentic AI system for generating complete animated video content from natural language prompts.

### Phase 1: Story, Script & Character Design

**Input:** Free-form natural language prompt (e.g., "A young astronaut discovers a hidden ocean on Mars")

**Output:** Validated JSON object:
```json
{
  "story": "...",
  "scenes": [
    {
      "scene_id": "1",
      "heading": "...",
      "action": "...",
      "dialogue": [...],
      "duration": 30,
      "tone": "...",
      "visual_cues": "..."
    }
  ],
  "characters": [
    {
      "name": "...",
      "role": "...",
      "appearance": "...",
      "voice_personality": "...",
      "visual_description": "...",
      "emotion_traits": [...]
    }
  ]
}
```

**Process:**
1. Script generation via LLM (Groq)
2. Script validation
3. Human-in-the-loop approval
4. Character extraction via LLM
5. Character image generation (Pollinations AI)
6. Persistence to vector database

### Phase 2: Audio Generation & Integration

**Input:** Scene manifest from Phase 1

**Output:** Audio files and timing manifests

**Features:**
- Text-to-Speech synthesis using Google TTS (gTTS)
- Automatic gender/personality-based voice parameter adjustment
- Voice caching for consistent character voices
- Audio assembly with pydub

## Project Structure

```
.
├── src/                          # Source code
│   ├── app.py                   # Entry point and CLI
│   ├── main_graph.py            # LangGraph workflow orchestration
│   ├── agents.py                # All agent node implementations
│   ├── audio_tools.py           # TTS and audio assembly tools
│   ├── tools.py                 # LangChain tool registration
│   └── memory.py                # ChromaDB persistence
├── config/                       # Configuration
│   ├── state.py                 # Pydantic models and state schema
│   └── audio_config.py          # Audio generation settings
├── output/                       # Generated outputs (created at runtime)
│   ├── dialogue_tracks/         # Intermediate TTS files
│   ├── audio/                   # Final mixed audio files
│   └── ...
├── main.py                      # Root entry point
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git ignore rules
├── manual_script.json           # Example manual-mode input
├── full_script.json            # Generated full script (Phase 1)
└── README.md                    # This file
```

## Setup & Installation

### 1. Create Virtual Environment
```powershell
python -m venv agenticproj
.\agenticproj\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Set Environment Variables
```powershell
$env:GROQ_API_KEY = "your-groq-api-key-here"
```

## Running the Application

### Auto Mode (LLM generates script from prompt)
```powershell
python main.py
# Select "auto"
# Enter your story prompt
```

### Manual Mode (Load predefined script)
```powershell
python main.py
# Select "manual"
# System will load/create manual_script.json
```

## Architecture

### LangGraph Workflow (9 Nodes)
```
scriptwriter → validator → hitl → character_designer → image_synth
                                                           ↓
                                         ┌─────────────────┴─────────────────┐
                                         ↓                                   ↓
                                 audio_synthesizer (TTS)         bgm_selector (metadata)
                                         ↓                                   ↓
                                         └─────────────────┬─────────────────┘
                                                           ↓
                                                   audio_assembler
                                                           ↓
                                                   memory_commit
```

### Technology Stack

**LLM & Orchestration:**
- Groq API (llama-3.3-70b-versatile)
- LangChain 0.1.16+ (tool registry, structured output)
- LangGraph 1.1.6 (state machine orchestration)

**Audio Generation:**
- gTTS 2.5.4 (Google Text-to-Speech)
- pydub 0.25.1 (audio mixing and manipulation)
- imageio-ffmpeg (FFmpeg binary, fallback mode)

**Data Management:**
- Pydantic 2.13.3 (schema validation)
- ChromaDB 1.5.8 (vector DB for memory)

**Other:**
- python-dotenv (environment variables)

## Configuration

### Audio Settings (`config/audio_config.py`)
- TTS engine: gTTS (Google Text-to-Speech)
- Output format: MP3, 192k bitrate
- Dialogue volume: -3 dB
- Voice caching: Enabled, 7-day TTL
- Gender detection and pitch adjustment enabled

### Voice Personality Parameters
Personality traits automatically map to voice parameters:
- **bold**: 1.3x speed, +0.1 pitch, intense emotion
- **calm**: 0.85x speed, -0.05 pitch, calm emotion
- **warm**: 1.0x speed, +0.05 pitch, friendly emotion
- And more... (see `config/audio_config.py`)

## Output Format

Phase 1 outputs **ONLY** the JSON object on stdout:
```json
{
  "story": "...",
  "scenes": [...],
  "characters": [...]
}
```

All logging and status messages are printed to stderr for easy output capture.

## Development Notes

- All imports use sys.path manipulation for cross-folder visibility
- FFmpeg is bundled via imageio-ffmpeg (no system installation needed)
- BGM (background music) infrastructure is present but not fully integrated
- Fallback mechanisms in place for audio assembly if FFmpeg unavailable
- All data persisted to ChromaDB for cross-session state

## Future Enhancements

- BGM integration with royalty-free music APIs
- Advanced audio mixing and effects
- Video synthesis from audio + images
- Multi-language TTS support
- Advanced emotion-driven voice synthesis


When the app starts:

```text
Enter mode (auto/manual): auto
Enter story prompt: <type your prompt>
```

If the human-in-the-loop checkpoint appears, respond with:

```text
Do you approve this script to continue? (yes/no): yes
```

Use `manual` mode if you want the workflow to read `manual_script.json` instead of generating a script from a prompt.