# AI-Powered-Animated-Video-Generation-System
AI4015-Agentic Artificial Intelligence Course Project

## Phase 1: Story, Script & Character Design

This workspace currently implements the first phase of the pipeline:

- Accepts a free-form story prompt from the user.
- Expands the prompt into a full narrative and scene-by-scene script.
- Produces dialogue, setting, tone, and duration for each scene.
- Extracts a character roster with names, roles, voice personalities, and visual descriptions.
- Validates the final output with Pydantic models.
- Bundles the result into a validated JSON object shaped like `{ story, scenes[], characters[] }`.

### Current implementation files

- `app.py` - interactive entry point for auto/manual workflow execution.
- `main_graph.py` - LangGraph orchestration and node routing.
- `agents.py` - scriptwriter, validator, HITL, character design, image, and memory nodes.
- `tools.py` - LangChain tool registration and LLM-backed script/character generation tools.
- `state.py` - Pydantic models and workflow state definitions.
- `memory.py` - ChromaDB-backed persistence for scripts and characters.
- `manual_script.json` - example manual-mode scene input.

### Notes

- The current implementation uses the Groq-backed `ChatGroq` path.
- Multi-backend support such as Ollama, llama.cpp, Claude, or GPT-4/OpenAI is not yet wired in.
- The workflow writes generated outputs such as `scene_manifest.json`, `full_script.json`, and `character_db.json`.

### Run The Project

Use these commands from the project root:

```powershell
# 1. Create a virtual environment
python -m venv agenticproj

# 2. Activate it
.\agenticproj\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your Groq API key
$env:GROQ_API_KEY = "your-api-key-here"

# 5. Run the app
python app.py
```

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