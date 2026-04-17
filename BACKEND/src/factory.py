from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from agents.designer import NexusDesigner
from agents.developer import NexusDeveloper
from agents.manager import NexusManager
from agents.qa_agent import NexusQA
from src.skill_runtime import SkillExecutor, SkillRegistry, SkillRouter, SkillSessionStore
from src.skill_runtime.models import SkillExecutionResult
from src.skill_runtime.validators import SkillValidation


@dataclass
class BuildResult:
    mode: str
    summary: str
    payload: Dict[str, str]


class NexusFactory:
    """Production-oriented orchestrator for both swarm tasks and skill runtime."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).resolve().parents[2]
        self.backend_root = self.project_root / "BACKEND"
        self.skills_root = self.project_root / "claude-skills-kit-main" / "skills"

        self.registry = SkillRegistry(
            skills_root=self.skills_root,
            cache_path=self.backend_root / "data" / "skill_registry_cache.json",
        )
        self._skills = self.registry.load(use_cache=True)

        validation = SkillValidation.validate_registry(self._skills)
        if not validation.ok:
            details = "\n".join(validation.errors)
            raise RuntimeError(f"Skill registry validation failed:\n{details}")

        self.router = SkillRouter(self._skills)
        self.executor = SkillExecutor(
            sessions=SkillSessionStore(self.backend_root / "data" / "skill_sessions.json"),
            artifact_dir=self.backend_root / "workspace" / "artifacts",
        )

        # Keep existing swarm actors for non-skill prompts.
        self.manager = NexusManager()
        self.designer = NexusDesigner()
        self.developer = NexusDeveloper()
        self.qa = NexusQA()

    def run_build(self, prompt: str) -> str:
        route = self.router.match(prompt)
        if route.key:
            result = self.run_skill(prompt=prompt, skill_key=route.key)
            return self._format_skill_result(result)

        # Fallback to existing swarm summary flow for generic build prompts.
        prd = self.manager.create_prd_task(prompt)
        design = self.designer.create_design_task(prd.description)
        dev = self.developer.create_dev_task(design.description)
        qa = self.qa.create_qa_task(dev.description)

        return "\n".join(
            [
                "# Nexus Swarm Draft Execution",
                "",
                "No direct skill trigger detected. Fallback path executed.",
                "",
                "## Task Graph",
                f"1. Manager: {prd.description}",
                f"2. Designer: {design.description}",
                f"3. Developer: {dev.description}",
                f"4. QA: {qa.description}",
                "",
                "## Status",
                "Draft generated. Execute with Crew runtime integration for full autonomous run.",
            ]
        )

    def run_skill(self, prompt: str, skill_key: Optional[str] = None) -> SkillExecutionResult:
        selected_key = skill_key
        if selected_key is None:
            selected = self.router.match(prompt)
            if not selected.key:
                return SkillExecutionResult(
                    matched_skill=None,
                    confidence=selected.confidence,
                    mode="none",
                    output="No matching skill found for this prompt.",
                )
            selected_key = selected.key

        definition = self.registry.get(selected_key)
        return self.executor.execute(prompt=prompt, skill_key=selected_key, skill=definition)

    def list_skills(self) -> Dict[str, str]:
        return {key: value.name for key, value in self._skills.items()}

    def _format_skill_result(self, result: SkillExecutionResult) -> str:
        artifact_lines = [f"- {k}: {v}" for k, v in result.artifacts.items()]
        if not artifact_lines:
            artifact_lines = ["- None"]

        return "\n".join(
            [
                f"# Skill Matched: {result.matched_skill}",
                f"- Confidence: {result.confidence:.2f}",
                f"- Mode: {result.mode}",
                "",
                result.output,
                "",
                "## Artifacts",
                *artifact_lines,
            ]
        )
