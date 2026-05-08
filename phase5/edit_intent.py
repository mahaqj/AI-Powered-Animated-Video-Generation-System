from pydantic import BaseModel, Field
from typing import Literal, Optional, Dict, Any
import re


class EditIntent(BaseModel):
    target: Literal["character", "scene", "audio", "video", "script"]
    action: str
    target_id: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)


class EditIntentClassifier:
    """Simple rule-based classifier. Replaceable by an LLM integration.

    The README describes using an LLM + Pydantic structured output; this
    implementation mirrors that contract but uses deterministic heuristics
    so it works offline and in tests.
    """

    def classify(self, text: str) -> EditIntent:
        txt = text.lower().strip()

        # Character voice edits
        if "voice" in txt or "tone" in txt or "speak" in txt:
            # try to extract character name
            m = re.search(r"for (?P<char>[A-Za-z0-9_\- ]+)", txt)
            name = m.group("char").strip() if m else None
            # look for explicit voice param
            voice = None
            m2 = re.search(r"make .*voice (?:more |less )?(?P<voice>[a-z ]+)", txt)
            if m2:
                voice = m2.group("voice").strip()

            return EditIntent(target="character", action="change_voice", target_id=name, params={"voice": voice, "raw": text})

        # Scene-level edits (brightness, duration, mood)
        if "scene" in txt or "longer" in txt or "shorter" in txt or "duration" in txt or "bright" in txt or "darker" in txt:
            # try to extract scene id or number
            m = re.search(r"scene (?P<id>[0-9]+)", txt)
            sid = m.group("id") if m else None
            # duration change
            m2 = re.search(r"(longer|shorter|duration .*?([0-9]+)s?)", txt)
            duration = None
            if m2 and m2.groups():
                # naive seconds extractor
                sm = re.search(r"([0-9]+)", m2.group(0))
                duration = int(sm.group(1)) if sm else None
            return EditIntent(target="scene", action="adjust_scene", target_id=sid, params={"duration_seconds": duration, "raw": text})

        # Script / dialogue edits
        if "line" in txt or "dialogue" in txt or "say" in txt or "replace" in txt:
            # capture pattern: replace "old" with "new" for <character>
            m = re.search(r'replace "(?P<old>.+?)" with "(?P<new>.+?)"(?: for (?P<char>.+))?', text, re.I)
            if m:
                return EditIntent(target="script", action="replace_line", params={"old": m.group("old"), "new": m.group("new"), "character": m.group("char")})
            # fallback: generic script edit
            return EditIntent(target="script", action="edit_dialogue", params={"raw": text})

        # Audio / video general edits
        if "audio" in txt or "bgm" in txt or "music" in txt:
            return EditIntent(target="audio", action="adjust_audio", params={"raw": text})

        # Default fallback: treat as high-level video edit
        return EditIntent(target="video", action="meta_edit", params={"raw": text})
