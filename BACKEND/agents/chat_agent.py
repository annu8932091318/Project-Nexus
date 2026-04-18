from __future__ import annotations


class NexusChatAgent:
    """Lightweight conversational agent for non-build prompts."""

    def respond(self, user_input: str) -> str:
        text = user_input.strip()
        if not text:
            return "I am here. Ask a question or say 'create PRD' / 'create project' when you want build workflow actions."

        lowered = text.lower()
        if lowered in {"hi", "hello", "hey", "yo"}:
            return "Hello. I am in chat mode. Ask anything, or explicitly ask me to create a PRD or create a project."

        if "help" in lowered:
            return (
                "Chat mode is active. I will answer normally unless you explicitly ask to create a PRD or create a project. "
                "For project creation, I first generate a PRD draft and wait for your approval."
            )

        return (
            "Chat Agent response:\n"
            f"{text}\n\n"
            "I treated this as a normal conversation. "
            "If you want workflow execution, say 'create PRD for ...' or 'create project for ...'."
        )
