import aiosqlite
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any

from .schemas import Phase3Output

logger = logging.getLogger("phase3.state_manager")

class VersionNotFoundError(Exception):
    pass

class StateManager:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def _ensure_table(self, db):
        await db.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                version     INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at  TEXT NOT NULL,
                state_json  TEXT NOT NULL,
                asset_paths TEXT NOT NULL
            )
        """)
        await db.commit()

    async def snapshot(self, state: Phase3Output) -> int:
        """Save a new state snapshot and return the version number."""
        async with aiosqlite.connect(self.db_path) as db:
            await self._ensure_table(db)
            
            state_json = state.model_dump_json()
            
            # Extract asset paths for quick overview
            asset_paths = [str(scene.image_path) for scene in state.generated_scenes]
            asset_paths += [str(scene.clip_path) for scene in state.generated_scenes]
            asset_paths.append(str(state.final_video_path))
            
            cursor = await db.execute(
                "INSERT INTO snapshots (created_at, state_json, asset_paths) VALUES (?, ?, ?)",
                (datetime.utcnow().isoformat(), state_json, json.dumps(asset_paths))
            )
            version = cursor.lastrowid
            await db.commit()
            
            logger.info(f"[StateManager] Snapshot saved as version {version}")
            return version

    async def revert(self, version: int) -> Phase3Output:
        """Retrieve a specific version and deserialize back to Phase3Output."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT state_json FROM snapshots WHERE version = ?", (version,))
            row = await cursor.fetchone()
            
            if not row:
                raise VersionNotFoundError(f"Version {version} not found")
                
            state = Phase3Output.model_validate_json(row["state_json"])
            state.version = version
            return state

    async def history(self) -> List[Dict[str, Any]]:
        """List all snapshots with metadata."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT version, created_at, asset_paths FROM snapshots ORDER BY version DESC")
            rows = await cursor.fetchall()
            
            return [dict(row) for row in rows]

    async def latest(self) -> Optional[Phase3Output]:
        """Get the most recent snapshot."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT state_json, version FROM snapshots ORDER BY version DESC LIMIT 1")
            row = await cursor.fetchone()
            
            if not row:
                return None
                
            state = Phase3Output.model_validate_json(row["state_json"])
            state.version = row["version"]
            return state
