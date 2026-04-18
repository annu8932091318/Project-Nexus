import unittest
import tempfile
from pathlib import Path

from src.factory import NexusFactory


class FactoryTests(unittest.TestCase):
    def test_factory_lists_skills(self) -> None:
        factory = NexusFactory()
        skills = factory.list_skills()

        self.assertTrue(skills)
        self.assertTrue(any("project-onboarding" in key for key in skills))

    def test_factory_routes_skill_prompt(self) -> None:
        factory = NexusFactory()
        output = factory.run_build("generate project plan from approved charter")

        self.assertIn("Skill Matched", output)

    def test_factory_uses_chat_mode_for_greeting(self) -> None:
        factory = NexusFactory()
        output = factory.run_build("hi")

        self.assertIn("chat mode", output.lower())
        self.assertNotIn("PRD Artifacts", output)

    def test_project_creation_requires_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            factory = NexusFactory(workspace_root=Path(temp_dir))
            first = factory.run_build("create project for inventory dashboard")

            self.assertIn("PRD draft generated", first)
            self.assertIn("approve project", first.lower())

            second = factory.run_build("approve project")
            self.assertIn("Project Creation Started", second)


if __name__ == "__main__":
    unittest.main()
