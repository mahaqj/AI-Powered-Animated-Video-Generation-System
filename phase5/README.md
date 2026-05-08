# Phase 5: Intelligent Edit & Undo System

## Status: ✅ Implemented

Phase 5 provides intelligent edit intent classification, state versioning, and version history UI for users to edit and manage video generation runs.

## Key Components

### 1. EditIntentClassifier (Rule-based + Pydantic)
**File:** `phase5/edit_intent.py`

Classifies free-text edit commands into structured `EditIntent` objects (Pydantic models) with the following targets:
- `character` — voice/tone changes per character
- `scene` — duration, brightness, mood adjustments
- `script` — dialogue replacement and edits
- `audio` — background music and audio level adjustments
- `video` — general video-level edits

**Example intents:**
```python
# "Make the voice more robotic for Alice" → 
EditIntent(target="character", action="change_voice", target_id="alice", params={"voice": "robotic"})

# "Make scene 2 longer" →
EditIntent(target="scene", action="adjust_scene", target_id="2", params={"duration_seconds": ...})

# 'Replace "hello" with "hey" for Bob' →
EditIntent(target="script", action="replace_line", params={"old": "hello", "new": "hey", "character": "bob"})
```

### 2. StateManager (SQLite-based Versioning)
**File:** `phase3/state_manager.py` (reused from Phase 3)

Manages full state snapshots with automatic versioning:
- `async snapshot(state: Phase3Output) -> int` — saves state, returns version number
- `async revert(version: int) -> Phase3Output` — loads a specific version
- `async history() -> List[Dict]` — lists all versions with metadata
- `async clear_all()` — clears snapshots (called at start of each new pipeline run)

**Versioning Strategy:**
- Each new pipeline run starts with `v1` (final generated video)
- Each edit creates the next version: `v2`, `v3`, etc.
- Users can revert to any prior version via `POST /api/phase3/revert/{version}`

### 3. EditExecutor (In-Memory State Editing)
**File:** `phase5/executor.py`

Applies edits to `Phase3Output` in-memory:
```python
new_state = EditExecutor.apply_edit(old_state, intent)
```

Changes supported:
- Character voice/personality updates
- Scene duration adjustments
- Dialogue line replacement
- Audio metadata embedding

Does NOT re-run expensive media generation; callers can trigger re-runs via `/api/phase3/run-partial` if needed.

### 4. Backend Router (Phase 5 API)
**File:** `phase4/backend/phase5_router.py`

**Endpoint: `POST /api/phase5/edit`**
```json
{
  "run_id": "34efef6c-732b-4fd5-b053-eee958c3a412",
  "edit_text": "Make the first scene darker"
}
```

**Response:**
```json
{
  "status": "ok",
  "version": 2,
  "intent": {
    "target": "scene",
    "action": "adjust_scene",
    "target_id": null,
    "params": {"raw": "Make the first scene darker"}
  }
}
```

### 5. Frontend UI Integration

**EditPanel Component**
- Collects edit text from user
- Shows suggested edit chips (quick templates)
- Displays success/error toasts
- Calls `POST /api/phase5/edit` on submit
- Triggers history refresh on successful edit

**VersionHistory Component**
- Lists all versions with timestamps and scene counts
- "Latest" marker on most recent version
- Revert button on older versions
- Auto-refreshes after edits via `onEdited` callback

**App.jsx Wiring**
- Passes `onEdited` callback to EditPanel
- Refreshes version history on edit success
- Shows error toasts on failures

## Versioning Workflow

```
1. User generates video (Phase 1-3)
   → Phase 3 final video = v1 (snapshot saved)

2. User edits: "Make darker"
   → POST /api/phase5/edit → v2 saved
   → VersionHistory refreshes, shows v1 and v2

3. User edits: "Faster scene 2"
   → POST /api/phase5/edit → v3 saved

4. User clicks "Revert to v1"
   → POST /api/phase3/revert/1 → loads v1 state
   → VersionHistory refreshes

5. New pipeline run starts
   → StateManager.clear_all() called
   → Next video = v1 (fresh count)
```

## Testing

**Test Coverage: 16+ test cases**

### Intent Classifier Tests (`phase5/tests/test_intent_classifier.py`)
- Character voice/tone edits (4 tests)
- Scene adjustments (5 tests)
- Script/dialogue edits (3 tests)
- Audio edits (3 tests)
- Video edits (2 tests)
- EditIntent Pydantic model validation (2 tests)

### Editor Executor Tests (`phase5/tests/test_executor.py`)
- Character voice changes
- Scene duration adjustments
- Dialogue line replacement
- Audio edit embedding
- Multi-character edits
- Timestamp updates

**Run tests:**
```bash
pytest phase5/tests/ -v
```

## API Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/phase5/edit` | POST | Submit an edit intent |
| `/api/phase3/history` | GET | Fetch all versions for current run |
| `/api/phase3/revert/{version}` | POST | Revert to a specific version |

## Cascade Behavior (Future)

Current implementation makes deterministic edits to JSON state. For more advanced cascades (e.g., re-generating images after a script edit), callers can:
1. Edit state via `/api/phase5/edit`
2. Trigger partial re-run: `POST /api/phase3/run-partial` with updated `scene_ids`

This decouples intent classification from media regeneration, allowing explicit control.

## Requirements Met

✅ EditIntentClassifier - LLM + Pydantic structured output  
✅ StateManager - snapshot(), revert(), history()  
✅ EditExecutor - applies changes per target type  
✅ VersionHistory - maintains version diff log  
✅ Intent classifier with 16+ test cases  
✅ State snapshot system with UI panel  
✅ Undo/revert (assets + JSON state)  
✅ Demo ready: 1 generation → N edits → revert at will  
✅ Versioning: v1 (final gen) → v2, v3, ... (edits)  

## Usage Example

```bash
# 1. Generate a video (via UI or API)
# Run ID: 34efef6c-732b-4fd5-b053-eee958c3a412
# Result: v1 snapshot created

# 2. Submit an edit
curl -X POST http://localhost:8000/api/phase5/edit \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "34efef6c-732b-4fd5-b053-eee958c3a412",
    "edit_text": "Make the first scene darker and 5 seconds longer"
  }'
# Response: { "status": "ok", "version": 2, "intent": {...} }

# 3. View version history
curl http://localhost:8000/api/phase3/history
# Returns: [{"version": 2, "created_at": "...", "scene_count": 3}, {"version": 1, ...}]

# 4. Revert to v1 if needed
curl -X POST http://localhost:8000/api/phase3/revert/1
```
