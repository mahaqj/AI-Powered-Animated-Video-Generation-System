# Phase 3 — Video Generation & Composition

## Overview
Phase 3 is the visual production engine of the Agentic AI Video Pipeline. It transforms the structured story and character definitions from Phase 1 and the synchronized audio timing manifests from Phase 2 into a polished animated short film. This module handles AI image generation, dynamic motion effects, and final high-definition video compositing.

## Image Generation (Pollinations.ai)
We are using **Pollinations.ai** for zero-cost, high-quality image generation.
- **Model**: Flux (Highly detailed, photorealistic, and excellent prompt adherence).
- **Access**: Automated via `image_generator.py` using the public API. No API key is required.
- **Robustness**: Includes built-in exponential backoff to handle 429 Rate Limiting errors.

## Folder Structure
```
phase3/
├── __init__.py           # Package marker
├── animator.py          # FFmpeg Ken Burns & A/V sync logic
├── compositor.py        # Video stitching, BGM mixing, subtitles
├── config.py            # Pydantic Settings management
├── image_generator.py   # Pollinations.ai integration
├── pipeline.py          # Orchestration for full and partial runs
├── router.py            # FastAPI endpoints for web access
├── schemas.py           # Pydantic data models
├── state_manager.py     # SQLite-based version control & undo
└── tests/               # Comprehensive unit test suite
```

## Setup & Running the Pipeline
To run the full end-to-end pipeline (Phase 1, 2, and 3), use the main entry point:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup environment
cp .env.example .env
# Edit .env and add GROQ_API_KEY (mandatory) 
# and FREESOUND_API_KEY (optional, for BGM)

# 3. Execute
python3 main.py
```

### Background Music (BGM)
By default, BGM generation is silent because it requires a **Freesound API Key**.
- **How to get one**: Register at [freesound.org](https://freesound.org/apiv2/apply/).
- **Configuration**: Add `FREESOUND_API_KEY=your_key_here` to your `.env` file.

## Standalone Usage
```python
import asyncio
import json
from phase3.pipeline import get_pipeline
from phase3.schemas import PipelineInput, TimingManifest

# Load inputs
pipeline_input = PipelineInput(**json.load(open("sample_phase1_output.json")))
timing_manifest = TimingManifest(**json.load(open("sample_timing_manifest.json")))

# Execute pipeline
result = asyncio.run(get_pipeline().run(pipeline_input, timing_manifest))
print(f"Final Video path: {result.final_video_path}")
```

## API Endpoints
| Method | Path | Description |
|---|---|---|
| POST | /api/phase3/run | Run the full video generation pipeline |
| POST | /api/phase3/run-partial | Re-run specific scenes (targeted editing) |
| GET | /api/phase3/status | Check current generation status |
| GET | /api/phase3/video | Stream/Download the final MP4 |
| GET | /api/phase3/state | Retrieve the full phase3_state.json |
| GET | /api/phase3/history | List all version snapshots (for undo) |
| POST | /api/phase3/revert/{version} | Revert to a previous version |

## Known Issues
- **Performance**: Ken Burns `zoompan` filters are CPU-intensive.
- **Hardware**: No GPU is required as all AI generation (LLM and Image) is offloaded to remote APIs.
