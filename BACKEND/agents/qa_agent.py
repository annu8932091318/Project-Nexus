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
            description=(
                "Review this implementation. Return PASS/FAIL with evidence. "
                "If FAIL, provide a detailed command list for Developer with exact fixes and retest criteria.\n\n"
                f"Implementation Context:\n{code_context}"
            ),
            expected_output="A PASS/FAIL report, bug list, and developer remediation command set when needed.",
            agent=self.agent
        )
