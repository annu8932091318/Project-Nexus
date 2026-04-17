from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class SkillDefinition:
    name: str
    description: str
    version: str
    path: Path
    language: Optional[str] = None
    triggers: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def normalized_triggers(self) -> List[str]:
        return [t.strip().lower() for t in self.triggers if t and t.strip()]


@dataclass
class SkillExecutionResult:
    matched_skill: Optional[str]
    confidence: float
    mode: str
    output: str
    assumptions: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    artifacts: Dict[str, str] = field(default_factory=dict)
