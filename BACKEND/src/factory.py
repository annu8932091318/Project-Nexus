from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from agents.designer import NexusDesigner
from agents.developer import NexusDeveloper
from agents.manager import NexusManager
from agents.qa_agent import NexusQA
from core.logger import get_logger
from src.prd_generator import generate_prd_assets
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

    def __init__(self, project_root: Optional[Path] = None, workspace_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).resolve().parents[2]
        self.backend_root = self.project_root / "BACKEND"
        self.skills_root = self.project_root / "claude-skills-kit-main" / "skills"
        self.workspace_root = (workspace_root or Path.cwd()).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)

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
            sessions=SkillSessionStore(self.workspace_root / ".project-nexus" / "skill_sessions.json"),
            artifact_dir=self.workspace_root,
        )

        # Keep existing swarm actors for non-skill prompts, initialized lazily.
        self.manager: NexusManager | None = None
        self.designer: NexusDesigner | None = None
        self.developer: NexusDeveloper | None = None
        self.qa: NexusQA | None = None
        self.logger = get_logger(__name__)

    def run_build(self, prompt: str) -> str:
        route = self.router.match(prompt)
        if route.key:
            result = self.run_skill(prompt=prompt, skill_key=route.key)
            return self._format_skill_result(result)

        # Fallback to existing swarm summary flow for generic build prompts.
        if self.manager is None:
            self.manager = NexusManager()
        if self.designer is None:
            self.designer = NexusDesigner()
        if self.developer is None:
            self.developer = NexusDeveloper()
        if self.qa is None:
            self.qa = NexusQA()

        prd = self.manager.create_prd_task(prompt)
        design = self.designer.create_design_task(prd.description)
        dev = self.developer.create_dev_task(design.description)
        qa = self.qa.create_qa_task(dev.description)
        prd_artifacts = self._safe_generate_prd(prompt)
        prd_lines = [f"- {key}: {value}" for key, value in prd_artifacts.items()] or ["- None"]

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
                "",
                "## PRD Artifacts",
                *prd_lines,
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
        result = self.executor.execute(prompt=prompt, skill_key=selected_key, skill=definition)
        result.artifacts.update(self._safe_generate_prd(prompt))
        return result

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

    def _safe_generate_prd(self, prompt: str) -> Dict[str, str]:
        if not prompt.strip():
            return {}
        try:
            md_path, pdf_path = generate_prd_assets(prompt, self.workspace_root)
            artifacts = {
                "prd_markdown": str(md_path),
                "prd_pdf": str(pdf_path),
            }
            self.logger.info("PRD artifacts generated", extra=artifacts)
            return artifacts
        except Exception as exc:  # pragma: no cover
            self.logger.error("PRD generation failed", extra={"error": str(exc)}, exc_info=True)
            return {}
