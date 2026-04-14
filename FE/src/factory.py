from pathlib import Path
from datetime import datetime

import yaml
from crewai import Agent, Crew, LLM, Process, Task

from core.memory import NexusMemory
from src.tools.browser import send_telegram
from training.feedback_loop import analyze_failure, save_lesson


ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"


def load_config(file_path: Path) -> dict:
    with file_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


agents_config = load_config(CONFIG_DIR / "agents.yaml")
tasks_config = load_config(CONFIG_DIR / "tasks.yaml")

# Local LLMs (Ollama)
manager_llm = LLM(model="ollama/llama3:8b")
coder_llm = LLM(model="ollama/deepseek-coder-v2")


class NexusFactory:
    def __init__(self) -> None:
        self.memory = NexusMemory()
        self.agents = self.create_agents()

    @staticmethod
    def _qa_passed(report_text: str) -> bool:
        lowered = report_text.lower()
        if "fail" in lowered and "pass" not in lowered:
            return False
        return True

    def _persist_success_card(self, prompt: str, result: str) -> None:
        card_key = f"card-{datetime.utcnow().timestamp()}"
        card_value = f"Prompt:\n{prompt}\n\nResult:\n{result}"
        self.memory.store_skill(
            key=card_key,
            value=card_value,
            metadata={
                "saved_at": datetime.utcnow().isoformat(),
                "project_type": "general",
            },
        )

    def _persist_project_context(self, prompt: str) -> None:
        self.memory.store_context(
            key=f"context-{datetime.utcnow().timestamp()}",
            value=prompt,
            metadata={"saved_at": datetime.utcnow().isoformat()},
        )

    def create_agents(self) -> dict:
        return {
            "manager": Agent(
                config=agents_config["manager"],
                llm=manager_llm,
                verbose=True,
                allow_delegation=True,
            ),
            "designer": Agent(
                config=agents_config["designer"],
                llm=coder_llm,
                verbose=True,
            ),
            "developer": Agent(
                config=agents_config["developer"],
                llm=coder_llm,
                verbose=True,
                allow_delegation=True,
            ),
            "qa": Agent(
                config=agents_config["qa_engineer"],
                llm=manager_llm,
                verbose=True,
                allow_delegation=True,
            ),
        }

    def run_build(
        self,
        user_prompt: str,
        max_reflections: int = 1,
        approval_telegram_url: str | None = None,
    ):
        self._persist_project_context(user_prompt)

        # Task 1: PRD
        t1 = Task(
            config=tasks_config["prd_task"],
            agent=self.agents["manager"],
            inputs={"user_input": user_prompt},
        )

        # Task 2: Design
        t2 = Task(
            config=tasks_config["design_task"],
            agent=self.agents["designer"],
            context=[t1],
        )

        # Task 3: Development
        t3 = Task(
            config=tasks_config["dev_task"],
            agent=self.agents["developer"],
            context=[t1, t2],
        )

        # Task 4: QA
        t4 = Task(
            config=tasks_config["qa_task"],
            agent=self.agents["qa"],
            context=[t3],
        )

        crew = Crew(
            agents=list(self.agents.values()),
            tasks=[t1, t2, t3, t4],
            process=Process.sequential,
            verbose=True,
        )

        result = str(crew.kickoff())
        reflections = 0
        while not self._qa_passed(result) and reflections < max_reflections:
            lesson = analyze_failure(result)
            save_lesson(lesson)
            reflections += 1
            result = str(crew.kickoff())

        if self._qa_passed(result):
            self._persist_success_card(user_prompt, result)
            if approval_telegram_url:
                send_telegram(
                    message="Nexus build completed and is ready for approval.",
                    telegram_url=approval_telegram_url,
                )

        return result


if __name__ == "__main__":
    factory = NexusFactory()
    print("--- Nexus Local AI Factory ---")
    prompt = input("What would you like me to build? ")
    result = factory.run_build(prompt)
    print("\n\n########################")
    print("## FINAL BUILD REPORT ##")
    print("########################\n")
    print(result)
