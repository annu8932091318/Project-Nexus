import os
from crewai import Agent, Task
from core.llm_config import get_llm

class NexusManager:
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
