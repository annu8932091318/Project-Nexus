from __future__ import annotations

from src.factory import NexusFactory


if __name__ == "__main__":
    factory = NexusFactory()
    skills = factory.list_skills()
    print(f"Loaded skills: {len(skills)}")

    probe_prompts = [
        "generate closure report for project completion",
        "compile weekly digest from status notes",
        "analyze user interviews and synthesize feedback",
        "prepare one-to-one prep for my direct report",
    ]

    for probe in probe_prompts:
        result = factory.run_skill(probe)
        print(f"- '{probe}' => {result.matched_skill} ({result.confidence:.2f})")

    print("Healthcheck completed.")
