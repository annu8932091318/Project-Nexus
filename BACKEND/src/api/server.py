from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict

from src.api.contracts import SkillRunRequest
from src.api.service import SkillService


class _Handler(BaseHTTPRequestHandler):
    service = SkillService()

    def _json(self, status: HTTPStatus, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._json(HTTPStatus.OK, {"status": "ok"})
            return

        if self.path == "/skills":
            self._json(HTTPStatus.OK, {"skills": self.service.factory.list_skills()})
            return

        self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/run-skill":
            self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(content_length).decode("utf-8") or "{}")
            request = SkillRunRequest(
                prompt=str(payload.get("prompt", "")),
                skill_key=payload.get("skill_key"),
            )
            response = self.service.run(request)
            self._json(
                HTTPStatus.OK,
                {
                    "matched_skill": response.matched_skill,
                    "confidence": response.confidence,
                    "mode": response.mode,
                    "output": response.output,
                    "assumptions": response.assumptions,
                    "issues": response.issues,
                    "artifacts": response.artifacts,
                },
            )
        except Exception as exc:  # pragma: no cover
            self._json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})


def run_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = ThreadingHTTPServer((host, port), _Handler)
    print(f"Skill API listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
