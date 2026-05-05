"""
Phase 2: Audio Generation & Integration - README

## Overview
This phase takes scenes and character profiles from Phase 1 and produces:
- Dialogue synthesis (TTS) for each character speech line
- Background music selection per scene tone
- Audio assembly with precise timing manifest for A/V sync

## Input
- `full_script.json` from Phase 1
  - scenes[] with tone and duration
  - characters[] with voice_personality and appearance

## Output
- `timing_manifest.json` - Per-scene audio timing with segment start/end milliseconds
- `output/audio/*.mp3` - Individual dialogue files
- `output/bgm_library/*.mp3` - Background music files (if FREESOUND_API_KEY set)

## LangGraph Workflow
```
FROM: character_designer_node (Phase 1)
  ↓
[Parallel Path 1]
audio_synthesizer_node
  - For each scene's dialogue:
    - Detect gender from character.appearance
    - Map voice_personality → speed/pitch params
    - Synthesize via gTTS
    - Cache voice params for consistency
  ↓
[Parallel Path 2]
bgm_selector_node
  - For each scene (by tone):
    - Query Freesound API
    - Download and cache BGM
  ↓
[Convergence]
audio_assembler_node
  - Mix dialogue + BGM per scene
  - Generate timing manifest (start_ms, end_ms)
  ↓
assembler_node → TO Phase 3
```

## Data Schema
See `phase1/config/state.py` for:
- `AudioTask` - scene_id, dialogue_index, character, dialogue_text, audio_file
- `AudioSegment` - scene_id, dialogue_index, character, start_ms, end_ms, audio_file
- `TimingManifestEntry` - scene_id, audio_file, duration_ms, dialogue_count, has_bgm, segments[]

## Key Features
- **Gender Detection:** Keyword-based inference from character appearance
- **Personality → Voice Params:** bold→speed=1.3, mysterious→speed=0.85, etc.
- **Voice Consistency:** Per-character caching ensures same voice across scenes
- **FFmpeg Integration:** Uses imageio_ffmpeg for audio assembly
- **Fallback Mode:** If FFmpeg unavailable, uses first dialogue as output
- **BGM Optional:** Pipeline continues if Freesound API unavailable

## Configuration
See `config/audio_config.py` for:
- `PERSONALITY_TO_VOICE_PARAMS` - personality phrase → {speed, pitch, emotion}
- `AUDIO_OUTPUT_CONFIG` - MP3 bitrate, output paths, dialogue/BGM volumes
- `CACHING_CONFIG` - Voice cache directory and TTL
- `GENDER_KEYWORDS` - female/male keyword detection

## Implementation Details
- **TTS Engine:** gTTS (Google Text-to-Speech)
- **Audio Mixing:** pydub (with FFmpeg backend)
- **BGM Source:** Freesound API (optional, requires API key)
- **Cache:** In-memory + disk (7-day TTL)

## Dependencies
- gtts >= 2.5.4
- pydub >= 0.25.1
- imageio-ffmpeg
- requests (for Freesound API)
- chromadb (shared)

## Environment Variables
- `FREESOUND_API_KEY` - For BGM download (optional)

## Running
See root README.md for entry point (main.py)

## Notes
- Phase 2 runs in parallel with remaining Phase 1 tasks (character_designer)
- Timing manifest is critical for Phase 3 A/V synchronization
- Audio quality depends on gTTS availability and internet connectivity
"""
