"""
Phase 2: Audio Generation & Integration

This module synthesizes dialogue to speech, selects background music, and
assembles audio with precise timing for A/V synchronization.
Output: timing_manifest.json with per-scene audio timings
"""

from .agents import (
    audio_synthesizer_node,
    bgm_selector_node,
    audio_assembler_node,
)

__all__ = [
    "audio_synthesizer_node",
    "bgm_selector_node",
    "audio_assembler_node",
]
