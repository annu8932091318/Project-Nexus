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
            description=f"Write the code based on this PRD: {prd_context}",
            expected_output="Working source code files.",
            agent=self.agent
        )
