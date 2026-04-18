from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from agents.chat_agent import NexusChatAgent
from agents.designer import NexusDesigner
from agents.developer import NexusDeveloper
from agents.manager import NexusManager
from agents.qa_agent import NexusQA
from core.agent_memory import AgentMemoryStore
from core.logger import get_logger
from src.project_builder import generate_project_artifacts
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
        self.agent_memory = AgentMemoryStore(self.workspace_root / ".project-nexus" / "agent_memory.json")

        # Keep existing swarm actors for non-skill prompts, initialized lazily.
        self.manager: NexusManager | None = None
        self.designer: NexusDesigner | None = None
        self.developer: NexusDeveloper | None = None
        self.qa: NexusQA | None = None
        self.chat: NexusChatAgent | None = None
        self.pending_project_prompt: str | None = None
        self.last_artifacts_by_channel: Dict[str, Dict[str, str]] = {}
        self.logger = get_logger(__name__)

    def run_build(self, prompt: str) -> str:
        result = self.handle_message(prompt=prompt)
        return result.summary

    def handle_message(self, prompt: str, skill_key: Optional[str] = None, channel: str = "terminal") -> BuildResult:
        force_chat_only = os.getenv("NEXUS_FORCE_CHAT_ONLY", "0") == "1"
        if force_chat_only:
            return BuildResult(
                mode="chat_only",
                summary=manager.compose_manager_response(
                    intent="chat_only",
                    reason="safe_mode",
                    main_output="Safe mode is enabled. Only chat responses are allowed right now.",
                ) if (manager := self._ensure_manager()) else "Safe mode is enabled. Only chat responses are allowed right now.",
                payload={},
            )

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
        self.agent_memory.append(
            "manager",
            prompt,
            f"intent={decision.intent}; reason={decision.reason}; router_key={route.key}; confidence={route.confidence:.2f}",
        )

        if decision.intent == "skill":
            if os.getenv("NEXUS_DISABLE_SKILLS", "0") == "1":
                return BuildResult(
                    mode="skill_blocked",
                    summary=manager.compose_manager_response(
                        intent="skill_blocked",
                        reason="runtime_policy",
                        main_output="Skill execution is temporarily disabled by runtime policy.",
                    ),
                    payload={},
                )
            selected_key = skill_key or route.key
            if not selected_key:
                self.agent_memory.append("chat", prompt, "Routed to chat due to missing skill key.")
                chat_output = self._ensure_chat().respond(prompt)
                return BuildResult(
                    mode="chat",
                    summary=manager.compose_manager_response(
                        intent="chat",
                        reason="missing_skill_key",
                        main_output=chat_output,
                    ),
                    payload={},
                )
            result = self.run_skill(prompt=prompt, skill_key=selected_key)
            payload = {
                "matched_skill": str(result.matched_skill or ""),
                "confidence": f"{result.confidence:.2f}",
                **result.artifacts,
            }
            self._remember_artifacts(channel, payload)
            return BuildResult(
                mode="skill",
                summary=manager.compose_manager_response(
                    intent="skill",
                    reason=decision.reason,
                    main_output=self._format_skill_result(result),
                    artifacts={k: v for k, v in payload.items() if k not in {"matched_skill", "confidence"}},
                ),
                payload=payload,
            )

        if decision.intent == "create_prd":
            if os.getenv("NEXUS_DISABLE_PROJECT_CREATION", "0") == "1":
                return BuildResult(
                    mode="project_ops_blocked",
                    summary=manager.compose_manager_response(
                        intent="project_ops_blocked",
                        reason="runtime_policy",
                        main_output="Project and PRD creation are temporarily disabled by runtime policy.",
                    ),
                    payload={},
                )
            artifacts = self._safe_generate_prd(prompt)
            self._remember_artifacts(channel, artifacts)
            lines = [f"- {k}: {v}" for k, v in artifacts.items()] or ["- PRD generation failed."]
            raw_summary = "\n".join(
                [
                    "# PRD Draft Ready",
                    "",
                    "PRD was generated because you explicitly requested it.",
                    "",
                    "## Artifacts",
                    *lines,
                ]
            )
            return BuildResult(
                mode="create_prd",
                summary=manager.compose_manager_response(
                    intent="create_prd",
                    reason=decision.reason,
                    main_output=raw_summary,
                    handoffs=manager.build_agent_handoffs(prompt),
                    project_prompt=prompt,
                    artifacts=artifacts,
                ),
                payload=artifacts,
            )

        if decision.intent == "create_project":
            if os.getenv("NEXUS_DISABLE_PROJECT_CREATION", "0") == "1":
                return BuildResult(
                    mode="project_ops_blocked",
                    summary=manager.compose_manager_response(
                        intent="project_ops_blocked",
                        reason="runtime_policy",
                        main_output="Project and PRD creation are temporarily disabled by runtime policy.",
                    ),
                    payload={},
                )
            artifacts = self._safe_generate_prd(prompt)
            self._remember_artifacts(channel, artifacts)
            handoffs = manager.build_agent_handoffs(prompt)

            if self._should_execute_project_immediately(prompt):
                project_artifacts = self._safe_generate_project(prompt)
                flow_artifacts = self._safe_generate_flow_diagram_artifacts(prompt=prompt, handoffs=handoffs)
                chain_summary = self._build_agent_chain_summary(prompt)
                all_artifacts = {
                    **artifacts,
                    **project_artifacts,
                    **flow_artifacts,
                    "agent_memory": str(self.agent_memory.file_path),
                }
                self._remember_artifacts(channel, all_artifacts)
                lines = [f"- {k}: {v}" for k, v in all_artifacts.items()] or ["- No artifacts generated."]
                raw_summary = "\n".join(
                    [
                        "# Project Created",
                        "",
                        "PRD and implementation artifacts were generated immediately from your explicit build request.",
                        "",
                        "## Agent Chain",
                        *chain_summary,
                        "",
                        "## Artifacts",
                        *lines,
                    ]
                )
                return BuildResult(
                    mode="project_created",
                    summary=manager.compose_manager_response(
                        intent="project_created",
                        reason=decision.reason,
                        main_output=raw_summary,
                        handoffs=handoffs,
                        project_prompt=prompt,
                        artifacts=all_artifacts,
                    ),
                    payload=all_artifacts,
                )

            self.pending_project_prompt = prompt
            lines = [f"- {k}: {v}" for k, v in artifacts.items()] or ["- PRD generation failed."]
            raw_summary = "\n".join(
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
            return BuildResult(
                mode="project_pending_approval",
                summary=manager.compose_manager_response(
                    intent="project_pending_approval",
                    reason=decision.reason,
                    main_output=raw_summary,
                    handoffs=handoffs,
                    project_prompt=prompt,
                    artifacts=artifacts,
                    needs_user_choice=True,
                    choice_prompt="Reply with: approve project  |  revise requirements",
                ),
                payload=artifacts,
            )

        if decision.intent == "approve_project":
            if not self.pending_project_prompt:
                return BuildResult(
                    mode="chat",
                    summary=manager.compose_manager_response(
                        intent="chat",
                        reason="missing_pending_project",
                        main_output="No pending project request found. Ask me to create a project first.",
                    ),
                    payload={},
                )
            return self._finalize_project_after_approval(channel=channel)

        if decision.intent == "send_files":
            recent = self._get_recent_artifacts(channel)
            if recent:
                return BuildResult(
                    mode="send_files",
                    summary=manager.compose_manager_response(
                        intent="send_files",
                        reason=decision.reason,
                        main_output="I found the latest generated files and prepared them for delivery.",
                        artifacts=recent,
                    ),
                    payload=recent,
                )
            return BuildResult(
                mode="send_files",
                summary=manager.compose_manager_response(
                    intent="send_files",
                    reason="no_recent_artifacts",
                    main_output="I do not have recent artifacts to send yet. Ask me to create a PRD/project first.",
                    needs_user_choice=True,
                    choice_prompt="Choose one: create PRD for ...  |  create project for ...",
                ),
                payload={},
            )

        self.agent_memory.append("chat", prompt, "Standard chat response mode.")
        chat_output = self._ensure_chat().respond(prompt)
        return BuildResult(
            mode="chat",
            summary=manager.compose_manager_response(
                intent="chat",
                reason=decision.reason,
                main_output=chat_output,
            ),
            payload={},
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

    def _finalize_project_after_approval(self, channel: str) -> BuildResult:
        approved_prompt = self.pending_project_prompt or ""
        self.pending_project_prompt = None
        manager = self._ensure_manager()

        try:
            handoffs = manager.build_agent_handoffs(approved_prompt)
            artifacts = self._safe_generate_project(approved_prompt)
            flow_artifacts = self._safe_generate_flow_diagram_artifacts(prompt=approved_prompt, handoffs=handoffs)
            chain_summary = self._build_agent_chain_summary(approved_prompt)
            all_artifacts = {**artifacts, **flow_artifacts, "agent_memory": str(self.agent_memory.file_path)}
            self._remember_artifacts(channel, all_artifacts)
            raw_summary = "\n".join(
                [
                    "# Project Creation Started",
                    "",
                    "Approval received. Project implementation artifacts were generated.",
                    "",
                    "## Agent Chain",
                    *chain_summary,
                    "",
                    "## Artifacts",
                    *([
                        f"- {k}: {v}" for k, v in all_artifacts.items()
                    ] or ["- No artifacts generated."]),
                ]
            )
            return BuildResult(
                mode="project_created",
                summary=manager.compose_manager_response(
                    intent="project_created",
                    reason="approved_by_user",
                    main_output=raw_summary,
                    handoffs=handoffs,
                    project_prompt=approved_prompt,
                    artifacts=all_artifacts,
                ),
                payload=all_artifacts,
            )
        except Exception as exc:  # pragma: no cover
            self.logger.error("Project creation failed after approval", extra={"error": str(exc)}, exc_info=True)
            return BuildResult(
                mode="project_failed",
                summary=manager.compose_manager_response(
                    intent="project_failed",
                    reason="exception",
                    main_output=f"Project creation failed after approval: {exc}",
                ),
                payload={},
            )

    def _safe_generate_project(self, prompt: str) -> Dict[str, str]:
        if not prompt.strip():
            return {}
        try:
            artifacts = generate_project_artifacts(prompt=prompt, workspace_root=self.workspace_root)
            self.logger.info("Project artifacts generated", extra=artifacts)
            return artifacts
        except Exception as exc:  # pragma: no cover
            self.logger.error("Project artifact generation failed", extra={"error": str(exc)}, exc_info=True)
            return {}

    def _safe_generate_flow_diagram_artifacts(self, prompt: str, handoffs) -> Dict[str, str]:
        try:
            manager = self._ensure_manager()
            mermaid = manager.project_creation_flow_mermaid(project_prompt=prompt, handoffs=handoffs)
            artifact_dir = self.workspace_root / "artifacts"
            artifact_dir.mkdir(parents=True, exist_ok=True)
            slug = self._slugify(prompt)
            flow_path = artifact_dir / f"agentic-project-flow-{slug}.mmd"
            latest_flow_path = artifact_dir / "agentic-project-flow.mmd"
            flow_path.write_text(mermaid + "\n", encoding="utf-8")
            latest_flow_path.write_text(mermaid + "\n", encoding="utf-8")
            return {
                "agentic_flow_mmd": str(flow_path),
                "agentic_flow_latest_mmd": str(latest_flow_path),
            }
        except Exception as exc:  # pragma: no cover
            self.logger.error("Flow diagram artifact generation failed", extra={"error": str(exc)}, exc_info=True)
            return {}

    def _slugify(self, text: str) -> str:
        base = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
        if not base:
            return "project"
        return base[:60]

    def _should_execute_project_immediately(self, prompt: str) -> bool:
        lowered = prompt.lower()
        patterns = [
            r"\bcreate\s+.*\bhtml\b",
            r"\bimplement\b",
            r"\bsend\s+me\s+that\s+html\s+file\b",
            r"\bin\s+same\s+file\b",
            r"\bportfolio\b",
        ]
        matched = sum(1 for pattern in patterns if re.search(pattern, lowered))
        return matched >= 2

    def _ensure_designer(self) -> NexusDesigner:
        if self.designer is None:
            self.designer = NexusDesigner()
        return self.designer

    def _ensure_developer(self) -> NexusDeveloper:
        if self.developer is None:
            self.developer = NexusDeveloper()
        return self.developer

    def _ensure_qa(self) -> NexusQA:
        if self.qa is None:
            self.qa = NexusQA()
        return self.qa

    def _build_agent_chain_summary(self, prompt: str) -> list[str]:
        manager = self._ensure_manager()
        designer = self._ensure_designer()
        developer = self._ensure_developer()
        qa = self._ensure_qa()

        prd = manager.create_prd_task(prompt)
        design = designer.create_design_task(prd.description)
        dev = developer.create_dev_task(design.description)
        qa_task = qa.create_qa_task(dev.description)

        self.agent_memory.append("manager", prompt, prd.description)
        self.agent_memory.append("designer", prompt, design.description)
        self.agent_memory.append("developer", prompt, dev.description)
        self.agent_memory.append("qa", prompt, qa_task.description)
        self.agent_memory.append(
            "qa",
            prompt,
            "If QA finds defects, return a detailed fix-command list to Developer, then re-run validation before release.",
        )

        return [
            f"1. Manager: {prd.description}",
            f"2. Designer: {design.description}",
            f"3. Developer: {dev.description}",
            f"4. QA: {qa_task.description}",
            "5. QA->Developer Loop: On FAIL, QA sends exact remediation commands and blocks release until PASS.",
        ]

    def _remember_artifacts(self, channel: str, artifacts: Dict[str, str]) -> None:
        if not artifacts:
            return
        existing = self.last_artifacts_by_channel.get(channel, {})
        existing.update(artifacts)
        self.last_artifacts_by_channel[channel] = existing

    def _get_recent_artifacts(self, channel: str) -> Dict[str, str]:
        artifacts = self.last_artifacts_by_channel.get(channel, {})
        if not artifacts:
            for by_channel in self.last_artifacts_by_channel.values():
                if by_channel:
                    artifacts = by_channel
                    break
        valid: Dict[str, str] = {}
        for key, value in artifacts.items():
            try:
                if Path(value).exists():
                    valid[key] = value
            except Exception:
                continue
        return valid
