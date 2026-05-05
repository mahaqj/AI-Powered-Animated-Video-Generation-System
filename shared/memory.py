"""
ChromaDB Memory Manager: Persistent storage for Phase 1 & 2 outputs

Collections:
- script_history: Scene metadata and story content
- character_metadata: Character profiles with traits
- audio_manifest: TTS task records per scene
- timing_manifest: Audio assembly timing entries
"""

import chromadb
from chromadb.config import Settings
import json
import os


class MemoryManager:
    def __init__(self, persist_directory="output/chroma_db"):
        """Initialize ChromaDB with collections for all phases."""
        os.makedirs(persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.script_collection = self.client.get_or_create_collection("script_history")
        self.character_collection = self.client.get_or_create_collection("character_metadata")
        self.audio_manifest_collection = self.client.get_or_create_collection("audio_manifest")
        self.timing_manifest_collection = self.client.get_or_create_collection("timing_manifest")

    def commit_script_segment(self, scene_id: str, content: str, metadata: dict = None):
        """Stores a script segment in the vector database."""
        if metadata is None:
            metadata = {}
        self.script_collection.upsert(
            documents=[content],
            metadatas=[metadata],
            ids=[scene_id]
        )
        return f"Successfully committed scene {scene_id} to memory."

    def commit_character(self, name: str, traits: dict, appearance: str, image_path: str = ""):
        """Stores a character identity profile."""
        metadata = {
            "name": name,
            "traits": json.dumps(traits),
            "appearance": appearance,
            "image_path": image_path
        }
        self.character_collection.upsert(
            documents=[f"Character Profile for {name}: {appearance}"],
            metadatas=[metadata],
            ids=[name.lower()]
        )
        return f"Successfully committed character {name} to memory."

    def get_character(self, name: str):
        """Retrieves character metadata by name."""
        results = self.character_collection.get(ids=[name.lower()])
        if results and results["metadatas"] and len(results["metadatas"]) > 0:
            return results["metadatas"][0]
        return None

    def query_script_history(self, query: str, n_results: int = 3):
        """Queries for similar past scenes to maintain continuity."""
        results = self.script_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results

    # ==============================================================================
    # Phase 2: Audio Persistence Methods
    # ==============================================================================

    def commit_audio_manifest(self, scene_id: str, audio_tasks: list, metadata: dict = None):
        """Stores audio synthesis tasks for a scene."""
        if metadata is None:
            metadata = {}
        
        audio_doc = json.dumps(audio_tasks, default=str)
        metadata["scene_id"] = scene_id
        metadata["task_count"] = len(audio_tasks)
        
        self.audio_manifest_collection.upsert(
            documents=[audio_doc],
            metadatas=[metadata],
            ids=[f"audio_{scene_id}"]
        )
        return f"Committed {len(audio_tasks)} audio tasks for scene {scene_id}."

    def commit_timing_manifest(self, scene_id: str, timing_entry: dict, metadata: dict = None):
        """Stores the final timing manifest entry for a scene's assembled audio."""
        if metadata is None:
            metadata = {}
        
        timing_doc = json.dumps(timing_entry, default=str)
        metadata["scene_id"] = scene_id
        metadata["duration_ms"] = timing_entry.get("duration_ms", 0)
        metadata["dialogue_count"] = timing_entry.get("dialogue_count", 0)
        
        self.timing_manifest_collection.upsert(
            documents=[timing_doc],
            metadatas=[metadata],
            ids=[f"timing_{scene_id}"]
        )
        return f"Committed timing manifest for scene {scene_id}."

    def get_audio_manifest(self, scene_id: str):
        """Retrieves audio tasks for a scene."""
        try:
            results = self.audio_manifest_collection.get(ids=[f"audio_{scene_id}"])
            if results and results["documents"] and len(results["documents"]) > 0:
                return json.loads(results["documents"][0])
        except Exception:
            pass
        return None

    def get_timing_manifest(self, scene_id: str):
        """Retrieves timing manifest entry for a scene."""
        try:
            results = self.timing_manifest_collection.get(ids=[f"timing_{scene_id}"])
            if results and results["documents"] and len(results["documents"]) > 0:
                return json.loads(results["documents"][0])
        except Exception:
            pass
        return None

    def query_audio_by_duration(self, min_duration_ms: int, max_duration_ms: int, n_results: int = 5):
        """Query audio segments by duration range."""
        query_text = f"audio segments between {min_duration_ms}ms and {max_duration_ms}ms"
        try:
            results = self.timing_manifest_collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where={"$and": [
                    {"duration_ms": {"$gte": min_duration_ms}},
                    {"duration_ms": {"$lte": max_duration_ms}}
                ]}
            )
            return results
        except Exception:
            return None


# Singleton instance
memory_db = MemoryManager()
