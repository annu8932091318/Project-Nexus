from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from agents.chat_agent import NexusChatAgent
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
        self.chat: NexusChatAgent | None = None
        self.pending_project_prompt: str | None = None
        self.logger = get_logger(__name__)

    def run_build(self, prompt: str) -> str:
        result = self.handle_message(prompt=prompt)
        return result.summary

    def handle_message(self, prompt: str, skill_key: Optional[str] = None, channel: str = "terminal") -> BuildResult:
        manager = self._ensure_manager()
        route = self.router.match(prompt)
        decision = manager.decide(
            prompt=prompt,
            route_key=route.key,
            route_confidence=route.confidence,
            has_pending_project=bool(self.pending_project_prompt),
            explicit_skill=bool(skill_key),
        )

        self.logger.info(
            "Manager routed prompt",
            extra={
                "channel": channel,
                "intent": decision.intent,
                "reason": decision.reason,
                "router_key": route.key,
                "router_confidence": round(route.confidence, 3),
            },
        )

        if decision.intent == "skill":
            selected_key = skill_key or route.key
            if not selected_key:
                return BuildResult(mode="chat", summary=self._ensure_chat().respond(prompt), payload={})
            result = self.run_skill(prompt=prompt, skill_key=selected_key)
            return BuildResult(
                mode="skill",
                summary=self._format_skill_result(result),
                payload={
                    "matched_skill": str(result.matched_skill or ""),
                    "confidence": f"{result.confidence:.2f}",
                    **result.artifacts,
                },
            )

        if decision.intent == "create_prd":
            artifacts = self._safe_generate_prd(prompt)
            lines = [f"- {k}: {v}" for k, v in artifacts.items()] or ["- PRD generation failed."]
            summary = "\n".join(
                [
                    "# PRD Draft Ready",
                    "",
                    "PRD was generated because you explicitly requested it.",
                    "",
                    "## Artifacts",
                    *lines,
                ]
            )
            return BuildResult(mode="create_prd", summary=summary, payload=artifacts)

        if decision.intent == "create_project":
            artifacts = self._safe_generate_prd(prompt)
            self.pending_project_prompt = prompt
            lines = [f"- {k}: {v}" for k, v in artifacts.items()] or ["- PRD generation failed."]
            summary = "\n".join(
                [
                    "# Project Request Received",
                    "",
                    "Step 1 complete: PRD draft generated.",
                    "Reply with 'approve project' to continue with project creation.",
                    "",
                    "## PRD Artifacts",
                    *lines,
                ]
            )
            return BuildResult(mode="project_pending_approval", summary=summary, payload=artifacts)

        if decision.intent == "approve_project":
            if not self.pending_project_prompt:
                return BuildResult(
                    mode="chat",
                    summary="No pending project request found. Ask me to create a project first.",
                    payload={},
                )
            return self._finalize_project_after_approval()

        return BuildResult(mode="chat", summary=self._ensure_chat().respond(prompt), payload={})

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

    def _ensure_manager(self) -> NexusManager:
        if self.manager is None:
            self.manager = NexusManager()
        return self.manager

    def _ensure_chat(self) -> NexusChatAgent:
        if self.chat is None:
            self.chat = NexusChatAgent()
        return self.chat

    def _finalize_project_after_approval(self) -> BuildResult:
        approved_prompt = self.pending_project_prompt or ""
        self.pending_project_prompt = None

        try:
            result = self.run_skill(
                prompt=f"create project from approved prd: {approved_prompt}",
                skill_key="project-onboarding",
            )
            summary = "\n".join(
                [
                    "# Project Creation Started",
                    "",
                    "Approval received. Executing project setup agent.",
                    "",
                    self._format_skill_result(result),
                ]
            )
            payload = {
                "matched_skill": str(result.matched_skill or ""),
                "confidence": f"{result.confidence:.2f}",
                **result.artifacts,
            }
            return BuildResult(mode="project_created", summary=summary, payload=payload)
        except Exception as exc:  # pragma: no cover
            self.logger.error("Project creation failed after approval", extra={"error": str(exc)}, exc_info=True)
            return BuildResult(
                mode="project_failed",
                summary=f"Project creation failed after approval: {exc}",
                payload={},
            )
