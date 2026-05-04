"""
Audio Configuration for Phase 2: Audio Generation & Integration

Uses gTTS (Google Text-to-Speech) for TTS synthesis and pydub for audio assembly.
"""

# ==============================================================================
# TTS (Text-to-Speech) Configuration
# ==============================================================================

TTS_CONFIG = {
    "engine": "gtts",  # Google Text-to-Speech
    "sample_rate": 22050,
    "language": "en",
    "cache_embeddings": True,
}

# ==============================================================================
# Character Voice Parameters: Personality → Synthesis Parameters
# ==============================================================================

PERSONALITY_TO_VOICE_PARAMS = {
    # Key: personality trait fragment (case-insensitive substring match)
    # Value: {speed_multiplier, pitch_offset, emotion_label}
    
    "determined": {"speed": 1.1, "pitch_offset": 0.0, "emotion": "strong"},
    "bold": {"speed": 1.3, "pitch_offset": 0.1, "emotion": "intense"},
    "reckless": {"speed": 1.3, "pitch_offset": 0.1, "emotion": "intense"},
    "mysterious": {"speed": 0.85, "pitch_offset": -0.05, "emotion": "calm"},
    "cautious": {"speed": 0.85, "pitch_offset": -0.05, "emotion": "calm"},
    "authoritative": {"speed": 0.8, "pitch_offset": -0.1, "emotion": "formal"},
    "cold": {"speed": 0.8, "pitch_offset": -0.1, "emotion": "formal"},
    "warm": {"speed": 1.0, "pitch_offset": 0.05, "emotion": "friendly"},
    "playful": {"speed": 1.2, "pitch_offset": 0.1, "emotion": "upbeat"},
    "sad": {"speed": 0.9, "pitch_offset": -0.1, "emotion": "melancholic"},
    "angry": {"speed": 1.2, "pitch_offset": 0.15, "emotion": "intense"},
}

# Default voice parameters if no personality match
DEFAULT_VOICE_PARAMS = {
    "speed": 1.0,
    "pitch_offset": 0.0,
    "emotion": "neutral",
}

# ==============================================================================
# Audio Output Settings
# ==============================================================================

AUDIO_OUTPUT_CONFIG = {
    "output_format": "mp3",  # Options: "wav", "mp3"
    "bitrate": "192k",  # For MP3 encoding
    "output_directory": "output/audio",  # Where to save all audio files (TTS + assembled)
    "bgm_directory": "output/bgm_library",  # BGM cache directory (for future use)
    "dialogue_volume_db": -3,  # Dialogue level for mixing
}

# ==============================================================================
# Caching Strategy
# ==============================================================================

CACHING_CONFIG = {
    "enable_voice_cache": True,
    "cache_directory": ".voice_cache",  # Local directory for embeddings
    "cache_ttl_hours": 24 * 7,  # Refresh cache every 7 days
    "bgm_cache_ttl_hours": 24 * 30,  # BGM tracks cached for 30 days
}

# ==============================================================================
# Character Gender Detection (for voice parameter adjustment)
# ==============================================================================

GENDER_KEYWORDS = {
    "female": ["she", "her", "woman", "girl", "lady", "queen", "princess", "actress"],
    "male": ["he", "his", "man", "boy", "lord", "king", "prince", "actor"],
}

# Gender-based pitch adjustment multipliers
GENDER_PITCH_MULTIPLIERS = {
    "female": 1.25,  # Slightly higher pitch
    "male": 0.85,  # Slightly lower pitch
    "neutral": 1.0,  # No adjustment
}
