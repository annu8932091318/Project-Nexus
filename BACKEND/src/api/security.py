from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class SecurityConfig:
    require_auth: bool
    api_key: str
    rate_limit_per_minute: int
    max_prompt_chars: int
    telegram_webhook_secret: str
    whatsapp_webhook_secret: str
    allowed_origin: str

    @staticmethod
    def from_env() -> "SecurityConfig":
        return SecurityConfig(
            require_auth=os.getenv("NEXUS_REQUIRE_AUTH", "1") == "1",
            api_key=os.getenv("NEXUS_API_KEY", "").strip(),
            rate_limit_per_minute=max(1, int(os.getenv("NEXUS_RATE_LIMIT_PER_MINUTE", "60"))),
            max_prompt_chars=max(256, int(os.getenv("NEXUS_MAX_PROMPT_CHARS", "4000"))),
            telegram_webhook_secret=os.getenv("NEXUS_TELEGRAM_WEBHOOK_SECRET", "").strip(),
            whatsapp_webhook_secret=os.getenv("NEXUS_WHATSAPP_WEBHOOK_SECRET", "").strip(),
            allowed_origin=os.getenv("NEXUS_ALLOWED_ORIGIN", "").strip(),
        )


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str = ""


class InMemoryRateLimiter:
    """Simple fixed-window limiter suitable for single-process runtime."""

    def __init__(self, per_minute: int):
        self.per_minute = max(1, per_minute)
        self._hits: dict[str, list[float]] = {}
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - 60.0
        with self._lock:
            timestamps = [t for t in self._hits.get(key, []) if t >= cutoff]
            if len(timestamps) >= self.per_minute:
                self._hits[key] = timestamps
                return False
            timestamps.append(now)
            self._hits[key] = timestamps
            return True


class PromptPolicy:
    _BLOCKED_PATTERNS = [
        re.compile(r"(?i)\brm\s+-rf\b"),
        re.compile(r"(?i)\bdel\s+/f\b"),
        re.compile(r"(?i)\bformat\s+[a-z]:\b"),
        re.compile(r"(?i)\bshutdown\b"),
        re.compile(r"(?i)\breboot\b"),
    ]

    @classmethod
    def evaluate(cls, prompt: str, max_prompt_chars: int) -> PolicyDecision:
        text = (prompt or "").strip()
        if not text:
            return PolicyDecision(allowed=False, reason="Empty prompt is not allowed.")
        if len(text) > max_prompt_chars:
            return PolicyDecision(
                allowed=False,
                reason=f"Prompt exceeds max length ({max_prompt_chars} characters).",
            )
        for pattern in cls._BLOCKED_PATTERNS:
            if pattern.search(text):
                return PolicyDecision(allowed=False, reason="Prompt contains blocked destructive pattern.")
        return PolicyDecision(allowed=True)


def is_authorized(config: SecurityConfig, path: str, api_key_header: str, bearer_header: str) -> bool:
    if not config.require_auth:
        return True
    if path in {"/webhook/telegram", "/webhook/whatsapp"}:
        return True
    if not config.api_key:
        return False

    candidate = api_key_header.strip()
    if not candidate and bearer_header.lower().startswith("bearer "):
        candidate = bearer_header[7:].strip()
    return bool(candidate and candidate == config.api_key)


def is_valid_webhook_secret(config: SecurityConfig, path: str, header_secret: str) -> bool:
    if path == "/webhook/telegram":
        if not config.telegram_webhook_secret:
            return True
        return header_secret.strip() == config.telegram_webhook_secret
    if path == "/webhook/whatsapp":
        if not config.whatsapp_webhook_secret:
            return True
        return header_secret.strip() == config.whatsapp_webhook_secret
    return True
