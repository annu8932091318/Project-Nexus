from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List

import yaml

from .models import SkillDefinition

_FRONTMATTER_PATTERN = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_CACHE_SCHEMA_VERSION = 4


class SkillRegistry:
    """Loads and validates skill definitions from SKILL.md files."""

    def __init__(self, skills_root: Path, cache_path: Path):
        self.skills_root = skills_root
        self.cache_path = cache_path
        self._skills: Dict[str, SkillDefinition] = {}

    def load(self, use_cache: bool = True) -> Dict[str, SkillDefinition]:
        if use_cache and self._load_cache_if_fresh():
            return self._skills

        skills: Dict[str, SkillDefinition] = {}
        trigger_index: Dict[str, List[str]] = {}

        for skill_file in sorted(self.skills_root.glob("**/SKILL.md")):
            definition = self._parse_skill_file(skill_file)
            key = self._key_for(definition)

            for trigger in definition.normalized_triggers:
                owners = trigger_index.setdefault(trigger, [])
                if key not in owners:
                    owners.append(key)

            skills[key] = definition

        self._skills = skills
        self._write_cache()
        return self._skills

    def all(self) -> Dict[str, SkillDefinition]:
        return self._skills

    def get(self, key: str) -> SkillDefinition:
        return self._skills[key]

    def _parse_skill_file(self, file_path: Path) -> SkillDefinition:
        raw = file_path.read_text(encoding="utf-8")
        metadata: Dict[str, object] = {}
        description = ""
        name = file_path.parent.name
        version = "0"
        language = None
        triggers: List[str] = []

        match = _FRONTMATTER_PATTERN.search(raw)
        if match:
            metadata = yaml.safe_load(match.group(1)) or {}
            name = str(metadata.get("name") or name)
            description = str(metadata.get("description") or "")
            version = str(metadata.get("version") or "0")
            language = metadata.get("language")
            declared = metadata.get("triggers")
            if isinstance(declared, list):
                triggers.extend(str(item) for item in declared)

        # Collect explicit trigger phrases from frontmatter text fields.
        for key in ("trigger", "description"):
            value = metadata.get(key)
            if isinstance(value, str):
                triggers.extend(re.findall(r"[\"«](.*?)[\"»]", value))

        trigger_matches = re.findall(
            r"(?:Triggers?|Keywords?)\s*(?:\(?(?:RU|EN|Russian|English)\)?)?\s*:\s*(.*)",
            raw,
        )
        for block in trigger_matches:
            for quoted in re.findall(r"[\"«](.*?)[\"»]", block):
                triggers.append(quoted)

        # Handle markdown lists such as '**English:** "...", "..."'.
        language_lines = re.findall(r"\*\*(?:English|Russian):\*\*\s*(.*)", raw)
        for line in language_lines:
            for quoted in re.findall(r"[\"«](.*?)[\"»]", line):
                triggers.append(quoted)

        # Keep order but deduplicate.
        seen = set()
        unique_triggers: List[str] = []
        for trigger in triggers:
            normalized = trigger.strip()
            if normalized and normalized not in seen:
                unique_triggers.append(normalized)
                seen.add(normalized)

        return SkillDefinition(
            name=name,
            description=description,
            version=version,
            path=file_path,
            language=str(language) if language is not None else None,
            triggers=unique_triggers,
            metadata={k: v for k, v in metadata.items()},
        )

    def _key_for(self, definition: SkillDefinition) -> str:
        rel = definition.path.relative_to(self.skills_root)
        return str(rel.parent).replace("\\", "/")

    def _fingerprint(self) -> str:
        digest = hashlib.sha256()
        for skill_file in sorted(self.skills_root.glob("**/SKILL.md")):
            stat = skill_file.stat()
            digest.update(str(skill_file).encode("utf-8"))
            digest.update(str(stat.st_mtime_ns).encode("utf-8"))
            digest.update(str(stat.st_size).encode("utf-8"))
        return digest.hexdigest()

    def _load_cache_if_fresh(self) -> bool:
        if not self.cache_path.exists():
            return False

        payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != _CACHE_SCHEMA_VERSION:
            return False
        if payload.get("fingerprint") != self._fingerprint():
            return False

        skills: Dict[str, SkillDefinition] = {}
        for key, data in payload.get("skills", {}).items():
            skills[key] = SkillDefinition(
                name=data["name"],
                description=data["description"],
                version=data["version"],
                path=Path(data["path"]),
                language=data.get("language"),
                triggers=data.get("triggers", []),
                metadata=data.get("metadata", {}),
            )

        self._skills = skills
        return True

    def _write_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": _CACHE_SCHEMA_VERSION,
            "fingerprint": self._fingerprint(),
            "skills": {
                key: {
                    "name": value.name,
                    "description": value.description,
                    "version": value.version,
                    "path": str(value.path),
                    "language": value.language,
                    "triggers": value.triggers,
                    "metadata": value.metadata,
                }
                for key, value in self._skills.items()
            },
        }
        self.cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
