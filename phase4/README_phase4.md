# Phase 4 — Full-Stack Web Application

## Overview
Phase 4 is the UI and orchestration layer of the AnimAI pipeline. It provides a web interface that lets users type a natural language prompt and watch as it flows through all three AI generation phases — script writing, audio synthesis, and video composition — in real time, with live SSE progress updates and a final video player.

## Aesthetic — Bubblegum Rave 🎪
The interface follows the "Bubblegum Rave" design direction: near-black backgrounds, neon acid-green + hot-pink accents, chunky Boogaloo display type, monospaced Space Mono body text, retro VT323 ticker font, and micro-animations on every interaction.

**Color palette:** `--acid: #c8ff00` · `--bubblegum: #ff2d9b` · `--sky: #00e5ff` · `--grape: #7b2fff`  
**Fonts:** Boogaloo (display) · Space Mono (body) · VT323 (ticker/status)

## Folder Structure
```
phase4/
├── backend/
│   ├── main.py            # FastAPI app, CORS, SSE endpoint, pipeline endpoints
│   ├── sse_manager.py     # Per-run SSE channels (async queue + stream generator)
│   ├── pipeline_runner.py # Drives Phases 1→2→3 via LangGraph, publishes SSE events
│   ├── schemas.py         # Pydantic request/response models
│   ├── requirements.txt   # Backend-specific dependencies
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/    # Navbar, PromptStudio, PipelineDashboard, PhaseCard, ...
│   │   ├── hooks/         # useSSE, usePipeline, useToast
│   │   ├── api/           # client.js — all fetch() calls
│   │   └── utils/         # constants.js, formatters.js
│   ├── index.html         # Google Fonts, viewport meta
│   ├── vite.config.js     # API proxy: /api/* → localhost:8000
│   └── Dockerfile
├── docker-compose.yml
└── README_phase4.md       # This file
```

## Running Locally (Docker)
```bash
# From project root
cp .env.example .env
# Add GROQ_API_KEY and FREESOUND_API_KEY to .env

docker-compose up --build
# Backend:  http://localhost:8000
# Frontend: http://localhost:5173
# API docs: http://localhost:8000/docs
```

## Running Without Docker
```bash
# Terminal 1 — Backend (from project root)
source venv/bin/activate
pip install -r requirements.txt
pip install -r phase4/backend/requirements.txt
python -m uvicorn phase4.backend.main:app --reload --port 8000

# Terminal 2 — Frontend
cd phase4/frontend
npm install
npm run dev
```

## API Endpoints (Phase 4 specific)
| Method | Path | Description |
|---|---|---|
| GET | /api/health | System health: ffmpeg, pollinations, phases |
| POST | /api/pipeline/run | Start full pipeline, returns run_id + stream URL |
| POST | /api/pipeline/rerun | Re-run a single phase for an existing run |
| GET | /api/stream/{run_id} | SSE stream: real-time phase progress events |
| GET | /api/video/{run_id} | Serve the generated MP4 for a specific run |

## SSE Event Types
| Event | Payload |
|---|---|
| `run_start` | `{ run_id, run_dir, prompt }` |
| `phase_start` | `{ phase, name }` |
| `phase_done` | `{ phase, data }` |
| `phase_error` | `{ phase, error }` |
| `pipeline_complete` | `{ video_url, run_id }` |
| `done` | `{}` — signals SSE stream close |

## Integration with Phases 1–3
The `pipeline_runner.py` imports `build_graph()` from `shared/main_graph.py` directly — no HTTP round-trip. HITL (human-in-the-loop) is auto-approved in API mode by setting `hitl_approved: True` in the initial LangGraph state.

## Phase 5 Hooks
- `EditPanel.jsx` calls `POST /api/phase5/edit` — Phase 5 team implements this endpoint
- `VersionHistory.jsx` uses `GET /api/phase3/history` and `POST /api/phase3/revert/{version}` (already implemented in Phase 3 router)
