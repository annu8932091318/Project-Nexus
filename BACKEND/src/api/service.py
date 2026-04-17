from __future__ import annotations

from src.api.contracts import SkillRunRequest, SkillRunResponse
from src.factory import NexusFactory


class SkillService:
    """Service wrapper that can be reused by CLI, web API, or worker jobs."""

    def __init__(self, factory: NexusFactory | None = None):
        self.factory = factory or NexusFactory()

    def run(self, request: SkillRunRequest) -> SkillRunResponse:
        result = self.factory.run_skill(prompt=request.prompt, skill_key=request.skill_key)
        return SkillRunResponse(
            matched_skill=result.matched_skill,
            confidence=result.confidence,
            mode=result.mode,
            output=result.output,
            assumptions=result.assumptions,
            issues=result.issues,
            artifacts=result.artifacts,
        )
