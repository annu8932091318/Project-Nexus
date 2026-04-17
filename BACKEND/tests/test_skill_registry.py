from pathlib import Path
import unittest

from src.skill_runtime.registry import SkillRegistry
from src.skill_runtime.router import SkillRouter


class SkillRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        project_root = Path(__file__).resolve().parents[2]
        self.registry = SkillRegistry(
            skills_root=project_root / "claude-skills-kit-main" / "skills",
            cache_path=project_root / "BACKEND" / "data" / "skill_registry_cache.test.json",
        )

    def test_registry_loads_skills(self) -> None:
        skills = self.registry.load(use_cache=False)

        self.assertTrue(skills, "Expected non-empty skill registry")
        self.assertTrue(any("report-analyzer" in key for key in skills), "Expected report-analyzer to be loaded")

    def test_router_matches_trigger(self) -> None:
        skills = self.registry.load(use_cache=False)
        router = SkillRouter(skills)

        match = router.match("please generate closure report for this project")

        self.assertIsNotNone(match.key)
        self.assertGreaterEqual(match.confidence, 0.30)


if __name__ == "__main__":
    unittest.main()
