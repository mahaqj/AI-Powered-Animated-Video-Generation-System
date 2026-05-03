import chromadb
from chromadb.config import Settings
import json
import os

class MemoryManager:
    def __init__(self, persist_directory="./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.script_collection = self.client.get_or_create_collection("script_history")
        self.character_collection = self.client.get_or_create_collection("character_metadata")

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
        """Stores a character identity profile including an image path."""
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

# Singleton instance
memory_db = MemoryManager()
