from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from crewai import Agent, Task
from core.llm_config import get_llm


@dataclass(frozen=True)
class ManagerDecision:
    intent: str
    reason: str


class NexusManager:
    _APPROVAL_RE = re.compile(r"\b(approve|approved|go ahead|proceed|ship it|yes build)\b", re.IGNORECASE)
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

        if self._PRD_RE.search(text):
            return ManagerDecision(intent="create_prd", reason="explicit_prd_request")

        if self._PROJECT_RE.search(text):
            return ManagerDecision(intent="create_project", reason="explicit_project_request")

        action_words = ("generate", "create", "build", "analyze", "prepare", "run", "draft", "synthesize")
        if route_key and route_confidence >= 0.60 and any(word in text.lower() for word in action_words):
            return ManagerDecision(intent="skill", reason="high_confidence_skill_route")

        return ManagerDecision(intent="chat", reason="default_chat_mode")
