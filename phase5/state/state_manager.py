"""
Phase 5: State Manager
SQLite-backed versioning system for pipeline state.
Supports: snapshot(), revert(), history(), diff between versions.
"""

import sqlite3
import json
import shutil
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


class StateManager:
    """
    Manages versioned snapshots of the pipeline state.
    
    Each snapshot stores:
      - version number (v1, v2, ...)
      - the full JSON state at that point
      - paths to all asset files
      - a human-readable description of what changed
      - timestamp
    
    Usage:
        sm = StateManager("D:/AI-Powered.../outputs/run_dir", "D:/AI-Powered.../phase5/versions.db")
        sm.snapshot("Initial generation", state_dict, [list_of_asset_paths])
        sm.snapshot("Made scene darker", updated_state, [list_of_asset_paths])
        sm.revert(1)   # Go back to version 1
        sm.history()   # See all versions
    """

    def __init__(self, run_dir: str, db_path: Optional[str] = None):
        self.run_dir = Path(run_dir)
        self.snapshots_dir = self.run_dir / "snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

        # Default DB path inside the run directory
        if db_path is None:
            db_path = str(self.run_dir / "versions.db")
        self.db_path = db_path

        self._init_db()

    # ─── DB Setup ────────────────────────────────────────────────────────────

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_label TEXT NOT NULL,
                    description TEXT,
                    state_json TEXT NOT NULL,
                    asset_paths TEXT NOT NULL,
                    snapshot_dir TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    # ─── Snapshot ─────────────────────────────────────────────────────────────

    def snapshot(self, description: str, state: dict, asset_paths: list[str] = None) -> int:
        """
        Save a snapshot of the current pipeline state.

        Args:
            description: Human-readable label e.g. "Initial generation" or "Made scene darker"
            state: The full pipeline state dict
            asset_paths: List of file paths for assets to preserve (images, audio, video)

        Returns:
            version_id (int)
        """
        if asset_paths is None:
            asset_paths = self._auto_discover_assets()

        # Determine version label
        version_id = self._next_version_id()
        version_label = f"v{version_id}"

        # Create snapshot folder and copy assets
        snap_dir = self.snapshots_dir / version_label
        snap_dir.mkdir(parents=True, exist_ok=True)

        # Save state JSON
        state_file = snap_dir / "state.json"
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

        # Copy asset files into snapshot
        copied_assets = []
        for asset_path in asset_paths:
            src = Path(asset_path)
            if src.exists():
                dest = snap_dir / src.name
                shutil.copy2(src, dest)
                copied_assets.append(str(dest))

        # Record in DB
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO versions (version_label, description, state_json, asset_paths, snapshot_dir, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                version_label,
                description,
                json.dumps(state),
                json.dumps(copied_assets),
                str(snap_dir),
                datetime.now().isoformat()
            ))
            conn.commit()

        print(f"[StateManager] Snapshot saved: {version_label} — {description}")
        return version_id

    # ─── Revert ───────────────────────────────────────────────────────────────

    def revert(self, version_id: int) -> dict:
        """
        Revert the pipeline to a specific version.

        Returns:
            The restored state dict
        """
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT version_label, state_json, asset_paths, snapshot_dir FROM versions WHERE id = ?",
                (version_id,)
            ).fetchone()

        if not row:
            raise ValueError(f"Version {version_id} not found.")

        version_label, state_json, asset_paths_json, snap_dir = row
        state = json.loads(state_json)
        asset_paths = json.loads(asset_paths_json)
        snap_dir = Path(snap_dir)

        # Restore asset files back to run_dir
        for asset_path in asset_paths:
            src = Path(asset_path)
            if src.exists():
                # Determine destination — mirror original folder structure
                # Assets in snapshot are flat (just filenames), restore to subfolders
                filename = src.name
                dest = self._find_asset_destination(filename)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)

        print(f"[StateManager] Reverted to {version_label}")
        return state

    def _find_asset_destination(self, filename: str) -> Path:
        """Route asset back to the right subfolder based on extension."""
        ext = Path(filename).suffix.lower()
        if ext in [".mp3", ".wav"]:
            return self.run_dir / "audio" / filename
        elif ext in [".png", ".jpg", ".jpeg"]:
            return self.run_dir / "images" / filename
        elif ext in [".mp4"]:
            return self.run_dir / "final" / filename
        else:
            return self.run_dir / filename

    # ─── History ──────────────────────────────────────────────────────────────

    def history(self) -> list[dict]:
        """
        Return all saved versions with summary info.

        Returns:
            List of dicts: {id, version_label, description, created_at, state_summary}
        """
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, version_label, description, state_json, created_at FROM versions ORDER BY id"
            ).fetchall()

        result = []
        for row in rows:
            vid, label, desc, state_json, created_at = row
            state = json.loads(state_json)
            summary = self._summarize_state(state)
            result.append({
                "id": vid,
                "version_label": label,
                "description": desc,
                "created_at": created_at,
                "summary": summary
            })
        return result

    def get_version_state(self, version_id: int) -> dict:
        """Get the state dict for a specific version."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT state_json FROM versions WHERE id = ?", (version_id,)
            ).fetchone()
        if not row:
            raise ValueError(f"Version {version_id} not found.")
        return json.loads(row[0])

    def latest_version_id(self) -> Optional[int]:
        """Return the ID of the most recent snapshot."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT MAX(id) FROM versions").fetchone()
        return row[0] if row and row[0] else None

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _next_version_id(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT COUNT(*) FROM versions").fetchone()
        return (row[0] + 1) if row else 1

    def _auto_discover_assets(self) -> list[str]:
        """Automatically find all relevant assets in the run directory."""
        assets = []
        for subdir in ["audio", "images", "clips", "final"]:
            folder = self.run_dir / subdir
            if folder.exists():
                for f in folder.iterdir():
                    if f.is_file():
                        assets.append(str(f))
        return assets

    def _summarize_state(self, state: dict) -> dict:
        """Extract a brief summary from a state dict."""
        return {
            "title": state.get("title", "Untitled"),
            "scene_count": len(state.get("scenes", [])),
            "character_count": len(state.get("characters", [])),
            "last_edit": state.get("last_edit", None),
            "subtitles_enabled": state.get("subtitles_enabled", True),
            "bgm_enabled": state.get("bgm_enabled", True),
        }
