from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .models import SkillDefinition


@dataclass
class ValidationResult:
    ok: bool
    errors: List[str]


class SkillValidation:
    """Validation checks for loaded skill metadata and runtime contracts."""

    @staticmethod
    def validate_registry(skills: Dict[str, SkillDefinition]) -> ValidationResult:
        errors: List[str] = []

        if not skills:
            errors.append("No skills were loaded from registry.")

        for key, skill in skills.items():
            if not skill.name:
                errors.append(f"{key}: missing skill name")
            if not skill.description:
                errors.append(f"{key}: missing description")
            if not skill.version:
                errors.append(f"{key}: missing version")
            if not skill.path.exists():
                errors.append(f"{key}: source file not found at {skill.path}")

        return ValidationResult(ok=not errors, errors=errors)
