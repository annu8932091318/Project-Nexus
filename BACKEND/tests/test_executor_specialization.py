from pathlib import Path
import tempfile
import unittest

from src.skill_runtime.executor import SkillExecutor
from src.skill_runtime.models import SkillDefinition
from src.skill_runtime.session_store import SkillSessionStore


class ExecutorSpecializationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.executor = SkillExecutor(
            sessions=SkillSessionStore(root / "sessions.json"),
            artifact_dir=root / "artifacts",
        )
        self.skill_path = root / "SKILL.md"
        self.skill_path.write_text("# test", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _skill(self, name: str) -> SkillDefinition:
        return SkillDefinition(
            name=name,
            description="test description",
            version="1.0",
            path=self.skill_path,
            triggers=["run test"],
        )

    def test_project_management_executor_renders_dependency_guidance(self) -> None:
        result = self.executor.execute(
            prompt="generate project plan from charter",
            skill_key="project-management-kit/generate-project-plan",
            skill=self._skill("generate-project-plan"),
        )

        self.assertIn("PM Skill Draft", result.output)
        self.assertIn("Suggested next skill after approval", result.output)

    def test_report_analyzer_executor_renders_extraction_workflow(self) -> None:
        result = self.executor.execute(
            prompt="analyze report q1.pdf",
            skill_key="report-analyzer",
            skill=self._skill("report-analyzer"),
        )

        self.assertIn("Report Analyzer Draft", result.output)
        self.assertIn("Extraction Workflow", result.output)

    def test_stakeholder_adapter_executor_renders_audience_sections(self) -> None:
        result = self.executor.execute(
            prompt="adapt this update for leadership and client",
            skill_key="stakeholder-adapter",
            skill=self._skill("stakeholder-adapter"),
        )

        self.assertIn("Stakeholder Adaptation Draft", result.output)
        self.assertIn("Leadership", result.output)
        self.assertIn("Engineering", result.output)
        self.assertIn("Client", result.output)


if __name__ == "__main__":
    unittest.main()
