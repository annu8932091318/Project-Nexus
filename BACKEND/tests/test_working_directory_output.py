from pathlib import Path
import tempfile
import unittest

from src.api.contracts import SkillRunRequest
from src.api.service import SkillService


class WorkingDirectoryOutputTests(unittest.TestCase):
    def test_artifacts_are_written_to_requested_working_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            request = SkillRunRequest(
                prompt="generate project plan from approved charter",
                skill_key="project-management-kit/generate-project-plan",
                working_dir=temp_dir,
            )
            service = SkillService()
            response = service.run(request)

            self.assertIn("draft", response.artifacts)
            draft_path = Path(response.artifacts["draft"])
            self.assertTrue(draft_path.exists())
            self.assertTrue(str(draft_path).startswith(str(Path(temp_dir).resolve())))
            self.assertEqual(draft_path.name, "project-plan.md")


if __name__ == "__main__":
    unittest.main()
