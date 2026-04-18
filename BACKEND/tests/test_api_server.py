import json
import os
import threading
import unittest
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer

from src.api.contracts import MessageResponse, SkillRunResponse
from src.api.security import InMemoryRateLimiter, SecurityConfig
from src.api.server import _Handler


class _FakeFactory:
    def list_skills(self):
        return {"project-onboarding": "project-onboarding"}


class _FakeService:
    def __init__(self):
        self.factory = _FakeFactory()
        self.last_request = None
        self.last_message_request = None

    def run(self, request):
        self.last_request = request
        return SkillRunResponse(
            matched_skill="project-onboarding",
            confidence=0.91,
            mode="new",
            output=f"handled: {request.prompt}",
            assumptions=[],
            issues=[],
            artifacts={"draft": "artifact.md"},
        )

    def message(self, request):
        self.last_message_request = request
        return MessageResponse(
            route="chat",
            output=f"chat handled: {request.prompt}",
            matched_skill=None,
            confidence=0.0,
            artifacts={},
        )


class ApiServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._old_env = {
            "NEXUS_REQUIRE_AUTH": os.environ.get("NEXUS_REQUIRE_AUTH"),
            "NEXUS_API_KEY": os.environ.get("NEXUS_API_KEY"),
            "NEXUS_RATE_LIMIT_PER_MINUTE": os.environ.get("NEXUS_RATE_LIMIT_PER_MINUTE"),
            "NEXUS_MAX_PROMPT_CHARS": os.environ.get("NEXUS_MAX_PROMPT_CHARS"),
        }
        os.environ["NEXUS_REQUIRE_AUTH"] = "1"
        os.environ["NEXUS_API_KEY"] = "test-api-key"
        os.environ["NEXUS_RATE_LIMIT_PER_MINUTE"] = "20"
        os.environ["NEXUS_MAX_PROMPT_CHARS"] = "100"

        _Handler.security = SecurityConfig.from_env()
        _Handler.rate_limiter = InMemoryRateLimiter(_Handler.security.rate_limit_per_minute)
        cls.fake_service = _FakeService()
        _Handler.service = cls.fake_service
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        for key, value in cls._old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def _get_json(self, path: str):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}") as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return payload

    def test_health_endpoint(self) -> None:
        payload = self._get_json("/health")
        self.assertEqual(payload["status"], "ok")

    def test_skills_endpoint(self) -> None:
        payload = self._get_json("/skills")
        self.assertIn("project-onboarding", payload["skills"])

    def test_run_skill_endpoint(self) -> None:
        body = json.dumps({"prompt": "create project context", "working_dir": "C:/tmp/demo"}).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/run-skill",
            data=body,
            headers={"Content-Type": "application/json", "X-API-Key": "test-api-key"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        self.assertEqual(payload["matched_skill"], "project-onboarding")
        self.assertEqual(payload["mode"], "new")
        self.assertIn("handled", payload["output"])
        self.assertEqual(self.fake_service.last_request.working_dir, "C:/tmp/demo")

    def test_message_endpoint(self) -> None:
        body = json.dumps({"prompt": "hi", "channel": "api"}).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/message",
            data=body,
            headers={"Content-Type": "application/json", "X-API-Key": "test-api-key"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        self.assertEqual(payload["route"], "chat")
        self.assertIn("chat handled", payload["output"])
        self.assertEqual(self.fake_service.last_message_request.channel, "api")

    def test_telegram_webhook_endpoint(self) -> None:
        body = json.dumps({"message": {"text": "hello from telegram"}}).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/webhook/telegram",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        self.assertEqual(payload["route"], "chat")
        self.assertIn("telegram", self.fake_service.last_message_request.channel)

    def test_message_endpoint_rejects_missing_auth(self) -> None:
        body = json.dumps({"prompt": "hi", "channel": "api"}).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/message",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 401)

    def test_message_endpoint_rejects_policy_violations(self) -> None:
        body = json.dumps({"prompt": "shutdown server now", "channel": "api"}).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/message",
            data=body,
            headers={"Content-Type": "application/json", "X-API-Key": "test-api-key"},
            method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
