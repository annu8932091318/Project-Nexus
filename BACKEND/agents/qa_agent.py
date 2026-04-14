from crewai import Agent, Task
from core.llm_config import get_llm

class NexusQA:
    def __init__(self):
        self.llm = get_llm("manager")
        self.agent = Agent(
            role='Quality Assurance Specialist',
            goal='Test the code for bugs and logic errors.',
            backstory='Picky specialist ensuring zero-defect delivery.',
            llm=self.llm,
            verbose=True
        )

    def create_qa_task(self, code_context):
        return Task(
            description=f"Review the code: {code_context}",
            expected_output="A PASS/FAIL report with bug list.",
            agent=self.agent
        )
