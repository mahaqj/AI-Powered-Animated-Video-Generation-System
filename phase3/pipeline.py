import logging
import json
from pathlib import Path
from datetime import datetime
from functools import lru_cache
from typing import List, Dict, Optional

from . import image_generator, animator, compositor
from .schemas import PipelineInput, TimingManifest, Phase3Output, GeneratedScene
from .config import get_settings, Settings
from .state_manager import StateManager

settings = get_settings()

class Phase3Pipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.logger = logging.getLogger("phase3.pipeline")
        self.state_manager = StateManager(Path(settings.STATE_DB_PATH))

    async def run(self, pipeline_input: PipelineInput, timing_manifest: TimingManifest, add_subtitles: bool = False, seed: int | None = None, run_dir: str | None = None) -> Phase3Output:
        """Execute the full Phase 3 pipeline with optional run_dir override."""
        base_dir = Path(run_dir) if run_dir else Path(self.settings.OUTPUT_DIR)
        
        images_dir = base_dir / "images"
        clips_dir  = base_dir / "clips"
        final_dir  = base_dir / "final"
        
        # Ensure directories exist
        for d in [images_dir, clips_dir, final_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # STEP 1: Generate scene images
        self.logger.info("[Pipeline] STEP 1/4 — Generating scene images")
        scene_image_map = await image_generator.generate_all_images(pipeline_input, images_dir, seed)

        # STEP 2: Apply Ken Burns animation
        self.logger.info("[Pipeline] STEP 2/4 — Applying Ken Burns animation")
        animated_clips = await animator.animate_all_scenes(scene_image_map, pipeline_input.scenes, clips_dir)

        # STEP 3: Sync audio per scene
        self.logger.info("[Pipeline] STEP 3/4 — Syncing audio per scene")
        generated_scenes = await animator.sync_all_scenes(animated_clips, scene_image_map, timing_manifest, pipeline_input.scenes, clips_dir)

        # STEP 4: Composite final video
        self.logger.info("[Pipeline] STEP 4/4 — Compositing final video")
        final_path = await compositor.compose_final_video(generated_scenes, timing_manifest, final_dir, add_subtitles, pipeline_input)

        # Build Phase3Output
        output = Phase3Output(
            pipeline_input=pipeline_input,
            generated_scenes=generated_scenes,
            final_video_path=final_path,
            version=1,
            created_at=datetime.utcnow()
        )

        # Persist state to JSON
        state_json_path = base_dir / "phase3_state.json"
        with open(state_json_path, "w") as f:
            f.write(output.model_dump_json(indent=2))

        # Snapshot in StateManager
        version = await self.state_manager.snapshot(output)
        output.version = version
        
        self.logger.info(f"[Pipeline] Complete. Final video: {final_path}")
        return output

    async def run_partial(self, phase3_output: Phase3Output, scene_ids: List[str], timing_manifest: TimingManifest, seed: int | None = None, run_dir: str | None = None) -> Phase3Output:
        """Re-run specified scenes only and recomposite the full video."""
        self.logger.info(f"[Pipeline] Starting partial re-run for scenes: {scene_ids}")
        
        base_dir = Path(run_dir) if run_dir else Path(self.settings.OUTPUT_DIR)
        images_dir = base_dir / "images"
        clips_dir  = base_dir / "clips"
        final_dir  = base_dir / "final"
        
        # Filter scenes to re-run
        scenes_to_rerun = [s for s in phase3_output.pipeline_input.scenes if s.scene_id in scene_ids]
        
        # Create a temporary pipeline input for the partial generation
        partial_input = PipelineInput(
            story=phase3_output.pipeline_input.story,
            scenes=scenes_to_rerun,
            characters=phase3_output.pipeline_input.characters
        )
        
        # STEP 1: Re-generate specified images
        partial_image_map = await image_generator.generate_all_images(partial_input, images_dir, seed)
        
        # STEP 2: Re-animate specified clips
        partial_animated_clips = await animator.animate_all_scenes(partial_image_map, scenes_to_rerun, clips_dir)
        
        # STEP 3: Re-sync specified scenes
        partial_generated_scenes = await animator.sync_all_scenes(partial_animated_clips, partial_image_map, timing_manifest, scenes_to_rerun, clips_dir)
        
        # Merge updated scenes back into the main list
        scene_map = {s.scene_id: s for s in phase3_output.generated_scenes}
        for updated_scene in partial_generated_scenes:
            scene_map[updated_scene.scene_id] = updated_scene
            
        updated_scenes_list = sorted(scene_map.values(), key=lambda s: s.sequence)
        
        # STEP 4: Full recomposition using all scenes (cached + updated)
        self.logger.info("[Pipeline] STEP 4/4 — Re-compositing final video")
        final_path = await compositor.compose_final_video(updated_scenes_list, timing_manifest, final_dir, True, phase3_output.pipeline_input)
        
        # Update output object
        phase3_output.generated_scenes = updated_scenes_list
        phase3_output.final_video_path = final_path
        phase3_output.created_at = datetime.utcnow()
        
        # Persist and snapshot
        state_json_path = base_dir / "phase3_state.json"
        with open(state_json_path, "w") as f:
            f.write(phase3_output.model_dump_json(indent=2))
            
        version = await self.state_manager.snapshot(phase3_output)
        phase3_output.version = version
        
        return phase3_output

@lru_cache(maxsize=1)
def get_pipeline() -> Phase3Pipeline:
    return Phase3Pipeline(settings=get_settings())
