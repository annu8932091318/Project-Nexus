import unittest
import tempfile
import os
import json
from pathlib import Path

from src.factory import NexusFactory


class FactoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._old_force_chat = os.environ.get("NEXUS_FORCE_CHAT_ONLY")
        self._old_disable_project_creation = os.environ.get("NEXUS_DISABLE_PROJECT_CREATION")

    def tearDown(self) -> None:
        if self._old_force_chat is None:
            os.environ.pop("NEXUS_FORCE_CHAT_ONLY", None)
        else:
            os.environ["NEXUS_FORCE_CHAT_ONLY"] = self._old_force_chat

        if self._old_disable_project_creation is None:
            os.environ.pop("NEXUS_DISABLE_PROJECT_CREATION", None)
        else:
            os.environ["NEXUS_DISABLE_PROJECT_CREATION"] = self._old_disable_project_creation

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

    def test_project_prompt_can_generate_html_immediately(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            factory = NexusFactory(workspace_root=Path(temp_dir))
            output = factory.run_build(
                "create project for this requirement where a html file that has portfolio website code "
                "of a software developer, in same file create a json data from where the data will be picked"
            )

            self.assertIn("Project Created", output)
            html_path = Path(temp_dir) / "artifacts" / "developer-portfolio.html"
            self.assertTrue(html_path.exists())

            memory_path = Path(temp_dir) / ".project-nexus" / "agent_memory.json"
            self.assertTrue(memory_path.exists())
            memory = json.loads(memory_path.read_text(encoding="utf-8"))
            self.assertIn("manager", memory)
            self.assertIn("designer", memory)
            self.assertIn("developer", memory)
            self.assertIn("qa", memory)
            self.assertIn("QA->Developer Loop", output)
            self.assertIn("Agentic Flow Diagram", output)

            flow_path = Path(temp_dir) / "artifacts" / "agentic-project-flow.mmd"
            self.assertTrue(flow_path.exists())
            flow_text = flow_path.read_text(encoding="utf-8")
            self.assertIn("Project Scope", flow_text)
            self.assertIn("portfolio website code", flow_text)
            self.assertIn("QA -->|FAIL: fix commands| DEV", flow_text)

    def test_send_files_returns_recent_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            factory = NexusFactory(workspace_root=Path(temp_dir))
            factory.run_build(
                "create project for this requirement where a html file that has portfolio website code "
                "of a software developer, in same file create a json data from where the data will be picked"
            )

            send_output = factory.handle_message(prompt="send me files", channel="telegram")

            self.assertEqual(send_output.mode, "send_files")
            self.assertIn("prepared them for delivery", send_output.summary)
            self.assertIn("project_html", send_output.payload)
            self.assertIn("agentic_flow_mmd", send_output.payload)
            self.assertIn("agentic_flow_latest_mmd", send_output.payload)

    def test_force_chat_only_mode_blocks_all_actions(self) -> None:
        os.environ["NEXUS_FORCE_CHAT_ONLY"] = "1"
        factory = NexusFactory()

        output = factory.run_build("create project for inventory dashboard")

        self.assertIn("Safe mode is enabled", output)

    def test_disable_project_creation_blocks_prd_and_project(self) -> None:
        os.environ["NEXUS_DISABLE_PROJECT_CREATION"] = "1"
        factory = NexusFactory()

        output = factory.run_build("create PRD for inventory dashboard")

        self.assertIn("temporarily disabled", output)


if __name__ == "__main__":
    unittest.main()
