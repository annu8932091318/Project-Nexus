from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class SkillRunRequest:
    prompt: str
    skill_key: Optional[str] = None


@dataclass
class SkillRunResponse:
    matched_skill: Optional[str]
    confidence: float
    mode: str
    output: str
    assumptions: List[str]
    issues: List[str]
    artifacts: Dict[str, str]
