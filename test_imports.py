#!/usr/bin/env python3
"""Test script to verify audio_tools imports and function calls."""

print("Testing audio_tools imports and function behavior...")

# Test 1: Import and check types
print("\n=== TEST 1: Import and Type Checking ===")
try:
    from audio_tools import (
        _synthesize_dialogue_impl,
        _cache_character_voice_impl,
        _select_bgm_track_impl,
        _download_bgm_track_impl,
        _assemble_audio_segments_impl,
    )
    print(f"✓ All _impl functions imported successfully")
    print(f"  - _synthesize_dialogue_impl: {type(_synthesize_dialogue_impl)}")
    print(f"  - _cache_character_voice_impl: {type(_cache_character_voice_impl)}")
    print(f"  - _select_bgm_track_impl: {type(_select_bgm_track_impl)}")
    print(f"  - _download_bgm_track_impl: {type(_download_bgm_track_impl)}")
    print(f"  - _assemble_audio_segments_impl: {type(_assemble_audio_segments_impl)}")
except Exception as e:
    print(f"✗ Failed to import _impl functions: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 2: Try calling a simple function
print("\n=== TEST 2: Function Callability ===")
try:
    result = _select_bgm_track_impl("calm", 30000)
    print(f"✓ _select_bgm_track_impl called successfully")
    print(f"  Result type: {type(result)}")
    print(f"  Result length: {len(result)}")
except Exception as e:
    print(f"✗ Failed to call _select_bgm_track_impl: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Compare with tool versions
print("\n=== TEST 3: Comparison with Tool Versions ===")
try:
    from audio_tools import (
        synthesize_dialogue,
        cache_character_voice,
        select_bgm_track,
        download_bgm_track,
        assemble_audio_segments,
    )
    print(f"✓ All tool versions imported successfully")
    print(f"  - synthesize_dialogue type: {type(synthesize_dialogue)}")
    print(f"  - cache_character_voice type: {type(cache_character_voice)}")
    print(f"  - select_bgm_track type: {type(select_bgm_track)}")
except Exception as e:
    print(f"✗ Failed to import tool versions: {e}")

print("\n✓ All tests completed!")

