from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, List


@dataclass
class SkillSession:
    session_id: str
    prompt: str
    skill_key: str
    status: str
    created_at: str
    updated_at: str
    assumptions: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    artifacts: Dict[str, str] = field(default_factory=dict)


class SkillSessionStore:
    """Durable session store for auditability and recovery."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text("{}", encoding="utf-8")

    def save(self, session: SkillSession) -> None:
        data = self._load()
        data[session.session_id] = asdict(session)
        self.file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get(self, session_id: str) -> SkillSession | None:
        data = self._load().get(session_id)
        if not data:
            return None
        return SkillSession(**data)

    def _load(self) -> Dict[str, dict]:
        try:
            return json.loads(self.file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def now_iso() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
