"""
storage.py — Simple persistent storage for AgentK.

Notes and reminders are kept in a JSON file on disk so they survive between
sessions, without requiring a database for this lightweight assistant.
"""

import json
from pathlib import Path
from typing import List


class Storage:
    def __init__(self, path: str = "data/agentk_data.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"notes": [], "reminders": []})

    def _read(self) -> dict:
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: dict) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ---- Notes ----
    def add_note(self, content: str) -> int:
        data = self._read()
        data["notes"].append(content)
        self._write(data)
        return len(data["notes"])

    def list_notes(self) -> List[str]:
        return self._read()["notes"]

    def delete_note(self, index: int) -> bool:
        data = self._read()
        if 0 <= index < len(data["notes"]):
            data["notes"].pop(index)
            self._write(data)
            return True
        return False

    # ---- Reminders ----
    def add_reminder(self, content: str) -> int:
        data = self._read()
        data["reminders"].append(content)
        self._write(data)
        return len(data["reminders"])

    def list_reminders(self) -> List[str]:
        return self._read()["reminders"]
