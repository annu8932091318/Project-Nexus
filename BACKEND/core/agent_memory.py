from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, List


@dataclass
class AgentMemoryEntry:
    timestamp: str
    prompt: str
    context: str


class AgentMemoryStore:
    """Persistent, per-agent rolling memory for recent execution context."""

    def __init__(self, file_path: Path, max_entries_per_agent: int = 50):
        self.file_path = file_path
        self.max_entries_per_agent = max(1, max_entries_per_agent)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text("{}", encoding="utf-8")

    def append(self, agent: str, prompt: str, context: str) -> None:
        data = self._load()
        rows = data.get(agent, [])
        rows.append(
            asdict(
                AgentMemoryEntry(
                    timestamp=self._now_iso(),
                    prompt=prompt.strip(),
                    context=context.strip(),
                )
            )
        )
        data[agent] = rows[-self.max_entries_per_agent :]
        self.file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def recent(self, agent: str, n: int = 5) -> List[Dict[str, str]]:
        data = self._load()
        return list(data.get(agent, []))[-max(1, n) :]

    def _load(self) -> Dict[str, list]:
        try:
            raw = json.loads(self.file_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                return raw
            return {}
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
