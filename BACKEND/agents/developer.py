from crewai import Agent, Task
from core.llm_config import get_llm

class NexusDeveloper:
    def __init__(self, role='Fullstack'):
        self.llm = get_llm("coder")
        self.agent = Agent(
            role=f'{role} Software Engineer',
            goal='Write clean, documented code and save it to the workspace.',
            backstory='Master of Python, React, and modern web technologies.',
            llm=self.llm,
            verbose=True
        )

    def create_dev_task(self, prd_context):
        return Task(
            description=(
                "Implement code from this context and include a complete QA handoff command list "
                "that explains how to validate behavior, expected outcomes, and known risk points.\n\n"
                f"Context:\n{prd_context}"
            ),
            expected_output="Working source code files plus explicit QA command handoff instructions.",
            agent=self.agent
        )
