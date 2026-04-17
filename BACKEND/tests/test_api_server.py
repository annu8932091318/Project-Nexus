import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

from src.api.contracts import SkillRunResponse
from src.api.server import _Handler


class _FakeFactory:
    def list_skills(self):
        return {"project-onboarding": "project-onboarding"}


class _FakeService:
    def __init__(self):
        self.factory = _FakeFactory()
        self.last_request = None

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


class ApiServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
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
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            payload = json.loads(resp.read().decode("utf-8"))

        self.assertEqual(payload["matched_skill"], "project-onboarding")
        self.assertEqual(payload["mode"], "new")
        self.assertIn("handled", payload["output"])
        self.assertEqual(self.fake_service.last_request.working_dir, "C:/tmp/demo")


if __name__ == "__main__":
    unittest.main()
