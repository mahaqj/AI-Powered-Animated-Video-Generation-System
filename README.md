# AI-Powered-Animated-Video-Generation-System

AI4015-Agentic Artificial Intelligence Course Project

How to Launch
Start Backend:
bash
source venv/bin/activate
python -m uvicorn phase4.backend.main:app --host 0.0.0.0 --port 8002 --reload
Start Frontend:
bash
cd phase4/frontend
npm run dev

## Overview

A multi-phase agentic AI system for generating complete animated video content from natural language prompts. The system orchestrates multiple specialized agents to handle scriptwriting, character design, audio synthesis, and video composition.

### Phase 1: Story, Script & Character Design
- **Process**: LLM-based script generation (Groq), automated validation, and character extraction.
- **Output**: Validated script manifest and character visual profiles.

### Phase 2: Audio Generation & Integration
- **Process**: TTS synthesis (gTTS) with personality-mapped parameters, BGM discovery (Freesound API), and audio assembly.
- **Output**: Synchronized dialogue and background music tracks.

### Phase 3: Video Generation & Composition
- **Process**: AI image generation (Pollinations.ai), Ken Burns animation effects (FFmpeg), and final A/V synchronization.
- **Output**: High-definition MP4 video with burned-in subtitles.

---

## Project Structure

```
.
├── phase1/                 # Script & Character Design
├── phase2/                 # Audio Synthesis & BGM
├── phase3/                 # Video Generation & Composition
├── phase4/                 # Web Interface (API & Dashboard)
├── phase5/                 # Edit Agent & State Management
├── shared/                 # Core Infrastructure (Memory, Tools, Graph)
├── src/                    # Application Core
├── outputs/                # Unified, timestamped run outputs
├── main.py                 # Root entry point
├── requirements.txt        # Comprehensive project dependencies
└── README.md               # This file
```

---

## Setup & Installation

### 1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux
# OR
.\venv\Scripts\Activate.ps1 # Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_key_here
FREESOUND_API_KEY=your_key_here  # Optional, for background music
```

---

## Running the Application

Execute the full pipeline through the root entry point:

```bash
python3 main.py
```

### Execution Modes:
- **Auto Mode**: Provide a prompt, and the system generates the script autonomously.
- **Manual Mode**: Reads from `manual_script.json` for deterministic execution.
- **Human-in-the-Loop**: The system pauses after script generation for user approval before proceeding to audio/video production.

---

## Output Architecture

All artifacts for a specific execution are stored in a unified, timestamped directory:
`outputs/DDMMM-HHMMAM-RUN/`

- `audio/`: Synchronized dialogue tracks (MP3).
- `images/`: AI-generated scene visuals (PNG).
- `clips/`: Animated video segments (MP4).
- `final/`: The final short film (`final_output_subtitled.mp4`).

---

## Technology Stack

- **LLM & Logic**: Groq (Llama 3.3 70B), LangGraph, LangChain.
- **Image Generation**: Pollinations.ai (Flux Model).
- **Audio**: gTTS (Speech), Pydub (Mixing), Freesound API (BGM).
- **Video**: FFmpeg (via imageio-ffmpeg).
- **Database**: ChromaDB (Vector memory), SQLite (State tracking).
- **Framework**: FastAPI (Backend API).

---

## Known Issues & Development Notes

- **API Rate Limits**: Pollinations.ai may return 429 errors; the system includes automatic backoff retries.
- **FFmpeg Performance**: Video animation (zoompan) is CPU-intensive. Sequential processing is used to maintain stability.
- **BGM**: Requires `FREESOUND_API_KEY` for actual music; otherwise, defaults to silent placeholders.