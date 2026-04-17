import unittest

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


if __name__ == "__main__":
    unittest.main()
