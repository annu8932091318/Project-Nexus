from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from crewai import Agent, Task
from core.llm_config import get_llm


@dataclass(frozen=True)
class ManagerDecision:
    intent: str
    reason: str


@dataclass(frozen=True)
class AgentHandoff:
    agent: str
    goal: str
    commands: List[str]
    handoff_to: Optional[str] = None
    handoff_commands: Optional[List[str]] = None


class NexusManager:
    _APPROVAL_RE = re.compile(r"\b(approve|approved|go ahead|proceed|ship it|yes build)\b", re.IGNORECASE)
    _SEND_FILES_RE = re.compile(r"\b(send|share|deliver|attach)\b.*\b(file|files|artifact|artifacts|document|documents)\b", re.IGNORECASE)
    _PRD_RE = re.compile(
        r"\b(create|generate|draft|write)\b.*\b(prd|product requirements document)\b"
        r"|\b(prd|product requirements document)\b.*\b(create|generate|draft|write)\b",
        re.IGNORECASE,
    )
    _PROJECT_RE = re.compile(
        r"\b(create|build|start|scaffold|implement)\b.*\b(project|app|application)\b"
        r"|\b(project|app|application)\b.*\b(create|build|start|scaffold|implement)\b",
        re.IGNORECASE,
    )

    def __init__(self):
        self.llm = get_llm("manager")
        self.agent = Agent(
            role='Software Product Manager',
            goal='Transform user ideas into a PRD and oversee the swarm.',
            backstory='Expert at system design and workflow management.',
            llm=self.llm,
            verbose=True
        )

    def create_prd_task(self, user_input):
        return Task(
            description=f"Analyze the user requirement: {user_input}. Create a detailed PRD.",
            expected_output="A complete Markdown PRD.",
            agent=self.agent
        )

    def decide(
        self,
        prompt: str,
        route_key: Optional[str],
        route_confidence: float,
        has_pending_project: bool,
        explicit_skill: bool,
    ) -> ManagerDecision:
        """Deterministic micro-latency intent router used across terminal/API/bot inputs."""
        text = prompt.strip()
        if not text:
            return ManagerDecision(intent="chat", reason="empty_prompt")

        if explicit_skill:
            return ManagerDecision(intent="skill", reason="explicit_skill_override")

        if has_pending_project and self._APPROVAL_RE.search(text):
            return ManagerDecision(intent="approve_project", reason="pending_project_approval")

        if self._SEND_FILES_RE.search(text):
            return ManagerDecision(intent="send_files", reason="explicit_file_delivery_request")

        if self._PRD_RE.search(text):
            return ManagerDecision(intent="create_prd", reason="explicit_prd_request")

        if self._PROJECT_RE.search(text):
            return ManagerDecision(intent="create_project", reason="explicit_project_request")

        action_words = ("generate", "create", "build", "analyze", "prepare", "run", "draft", "synthesize")
        if route_key and route_confidence >= 0.60 and any(word in text.lower() for word in action_words):
            return ManagerDecision(intent="skill", reason="high_confidence_skill_route")

        return ManagerDecision(intent="chat", reason="default_chat_mode")

    def build_agent_handoffs(self, prompt: str) -> List[AgentHandoff]:
        concise_prompt = " ".join(prompt.strip().split())
        return [
            AgentHandoff(
                agent="Manager",
                goal="Break user request into an executable multi-agent plan with acceptance criteria.",
                commands=[
                    f"Parse and restate user objective: '{concise_prompt}'.",
                    "Define deliverables, constraints, and completion criteria.",
                    "Assign design/build/test sequence with explicit handoff contracts.",
                ],
                handoff_to="Designer",
                handoff_commands=[
                    "Create UI/architecture blueprint mapped to PRD scope.",
                    "List component contracts and edge-case behavior.",
                    "Return implementation-ready structure and style guidance.",
                ],
            ),
            AgentHandoff(
                agent="Designer",
                goal="Translate product requirements into implementation-ready design instructions.",
                commands=[
                    "Produce information architecture and component hierarchy.",
                    "Define interactions, states, and validation behavior.",
                    "Specify token/style guidelines and file-level structure.",
                ],
                handoff_to="Developer",
                handoff_commands=[
                    "Implement files exactly according to component contract.",
                    "Document assumptions and unresolved ambiguities.",
                    "Provide test notes for QA reproducibility.",
                ],
            ),
            AgentHandoff(
                agent="Developer",
                goal="Implement working artifacts and provide a verifiable change set.",
                commands=[
                    "Create/update source files for requested feature scope.",
                    "Ensure run-time behavior matches design and user constraints.",
                    "Prepare QA handoff with file list, expected outputs, and known risks.",
                ],
                handoff_to="QA",
                handoff_commands=[
                    "Run behavioral validation against acceptance criteria.",
                    "Return PASS with evidence or FAIL with exact defect commands.",
                    "If FAIL, send actionable fix list back to Developer.",
                ],
            ),
            AgentHandoff(
                agent="QA",
                goal="Gate delivery quality and control pass/fail transitions.",
                commands=[
                    "Validate implementation against requested outcomes and edge cases.",
                    "Record PASS/FAIL and evidence summary.",
                    "On FAIL, issue precise remediation commands for Developer and retest.",
                ],
                handoff_to="Manager",
                handoff_commands=[
                    "If PASS: provide release-ready summary and artifact verification.",
                    "If FAIL: provide defect command sheet and block release.",
                ],
            ),
        ]

    def compose_manager_response(
        self,
        *,
        intent: str,
        reason: str,
        main_output: str,
        handoffs: Optional[List[AgentHandoff]] = None,
        project_prompt: str = "",
        artifacts: Optional[Dict[str, str]] = None,
        needs_user_choice: bool = False,
        choice_prompt: str = "",
    ) -> str:
        lines: List[str] = [
            "# Manager Update",
            "",
            f"I received your request and routed it as **{intent}** ({reason}).",
            "",
            "## What I Completed",
            main_output.strip() or "- Request processed.",
        ]

        if handoffs:
            lines.extend(["", "## Agent Command Handoffs"])
            for idx, step in enumerate(handoffs, start=1):
                lines.append(f"{idx}. {step.agent} Goal: {step.goal}")
                for cmd in step.commands:
                    lines.append(f"   - Command: {cmd}")
                if step.handoff_to:
                    lines.append(f"   - Handoff To: {step.handoff_to}")
                for cmd in step.handoff_commands or []:
                    lines.append(f"   - Handoff Command: {cmd}")

            lines.extend(
                [
                    "",
                    "## Agentic Flow Diagram",
                    "```mermaid",
                    self.project_creation_flow_mermaid(project_prompt=project_prompt, handoffs=handoffs),
                    "```",
                ]
            )

        if artifacts:
            lines.extend(["", "## Files / Artifacts"])
            for key, value in artifacts.items():
                lines.append(f"- {key}: {value}")

        if needs_user_choice:
            lines.extend(["", "## Next Input Needed", choice_prompt or "Please choose how you want to continue."])

        lines.extend(["", "I will continue coordinating all agent handoffs and report back in clear language."])
        return "\n".join(lines)

    def project_creation_flow_mermaid(self, project_prompt: str, handoffs: Optional[List[AgentHandoff]] = None) -> str:
        scope = self._label(project_prompt or "Project request")
        manager_cmd = self._handoff_command(handoffs, "Manager")
        designer_cmd = self._handoff_command(handoffs, "Designer")
        developer_cmd = self._handoff_command(handoffs, "Developer")
        qa_cmd = self._handoff_command(handoffs, "QA")

        return "\n".join(
            [
                "flowchart LR",
                f"  P[Project Scope\\n{scope}] --> M1[Manager\\n{manager_cmd}]",
                f"  M1 --> D[Designer\\n{designer_cmd}]",
                f"  D --> DEV[Developer\\n{developer_cmd}]",
                f"  DEV --> QA[QA\\n{qa_cmd}]",
                "  QA -->|FAIL: fix commands| DEV",
                "  DEV -->|Re-submit build| QA",
                "  QA -->|PASS| M2[Manager: Final Human Response]",
            ]
        )

    def _handoff_command(self, handoffs: Optional[List[AgentHandoff]], agent: str) -> str:
        if not handoffs:
            return "No command"
        for handoff in handoffs:
            if handoff.agent.lower() == agent.lower() and handoff.commands:
                return self._label(handoff.commands[0])
        return "No command"

    def _label(self, text: str) -> str:
        cleaned = " ".join(text.strip().split())
        cleaned = cleaned.replace("[", "(").replace("]", ")").replace("|", "/")
        if len(cleaned) > 90:
            return cleaned[:87].rstrip() + "..."
        return cleaned
