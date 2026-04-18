from crewai import Agent, Task

from core.llm_config import get_llm


class NexusDesigner:
    def __init__(self):
        self.llm = get_llm("coder")
        self.agent = Agent(
            role="UI/UX Designer",
            goal="Create modern UI structures and component schemas from PRD inputs.",
            backstory="You transform product requirements into practical, implementation-ready UI architecture.",
            llm=self.llm,
            verbose=True,
        )

    def create_design_task(self, prd_context: str) -> Task:
        return Task(
            description=(
                "Based on this PRD context, produce a detailed command sheet for the Developer. "
                "Include information architecture, component hierarchy, state behavior, and style system guidelines. "
                "Commands must be implementation-ready and unambiguous.\n\n"
                f"PRD:\n{prd_context}"
            ),
            expected_output="Detailed developer command sheet with component contract and handoff checklist.",
            agent=self.agent,
        )
