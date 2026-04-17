from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional

from .models import SkillDefinition


@dataclass
class SkillMatch:
    key: Optional[str]
    confidence: float


class SkillRouter:
    """Deterministic trigger-based skill router with confidence scoring."""

    def __init__(self, skills: Dict[str, SkillDefinition]):
        self.skills = skills

    def match(self, prompt: str) -> SkillMatch:
        normalized = self._normalize(prompt)
        best_key: Optional[str] = None
        best_score = 0.0

        for key, skill in self.skills.items():
            score = self._score(normalized, key, skill)
            if score > best_score:
                best_score = score
                best_key = key

        if best_score < 0.30:
            return SkillMatch(key=None, confidence=best_score)
        return SkillMatch(key=best_key, confidence=best_score)

    def _score(self, normalized_prompt: str, key: str, skill: SkillDefinition) -> float:
        score = 0.0

        for trigger in skill.normalized_triggers:
            t = self._normalize(trigger)
            if not t:
                continue

            if normalized_prompt == t:
                score = max(score, 1.0)
            elif t in normalized_prompt:
                score = max(score, min(0.95, 0.5 + min(len(t), 80) / 200))
            elif normalized_prompt in t and len(normalized_prompt) > 5:
                score = max(score, 0.4)

        # Lightweight description overlap for better fallback intent matching.
        desc = self._normalize(skill.description)
        if desc:
            prompt_tokens = set(normalized_prompt.split())
            desc_tokens = set(desc.split())
            overlap = len(prompt_tokens & desc_tokens)
            if overlap:
                score = max(score, min(0.6, overlap / 10))

        # Boost for explicit skill-name/path intent, useful for short prompts.
        key_phrase = self._normalize(key.split("/")[-1].replace("-", " "))
        name_phrase = self._normalize(skill.name.replace("-", " "))
        for phrase in (key_phrase, name_phrase):
            if not phrase:
                continue
            phrase_tokens = phrase.split()
            if phrase in normalized_prompt:
                score = max(score, 0.85)
            elif len(phrase_tokens) >= 2 and all(tok in normalized_prompt for tok in phrase_tokens[:2]):
                score = max(score, 0.7)
            elif any(tok in normalized_prompt for tok in phrase_tokens):
                score = max(score, 0.35)

        return score

    def _normalize(self, text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^\w\s\-]+", " ", text, flags=re.UNICODE)
        return re.sub(r"\s+", " ", text).strip()
