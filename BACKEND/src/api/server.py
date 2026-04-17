from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict

from core.logger import get_logger
from src.api.contracts import SkillRunRequest
from src.api.service import SkillService
from src.factory import NexusFactory

logger = get_logger(__name__)


class _Handler(BaseHTTPRequestHandler):
    service: SkillService | None = None

    def _service(self) -> SkillService:
        if self.service is None:
            self.__class__.service = SkillService()
        return self.__class__.service

    def _json(self, status: HTTPStatus, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        logger.info("GET request received", extra={"path": self.path})
        if self.path == "/health":
            logger.debug("Health check requested")
            self._json(HTTPStatus.OK, {"status": "ok"})
            return

        if self.path == "/skills":
            skills = self._service().factory.list_skills()
            logger.info("Skills list requested", extra={"skill_count": len(skills)})
            self._json(HTTPStatus.OK, {"skills": skills})
            return

        logger.warning("Unknown GET endpoint requested", extra={"path": self.path})
        self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT.value)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        logger.info("POST request received", extra={"path": self.path})
        if self.path != "/run-skill":
            logger.warning("Unknown POST endpoint", extra={"path": self.path})
            self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(content_length).decode("utf-8") or "{}")
            logger.debug("Request payload received", extra={"has_prompt": "prompt" in payload, "has_skill_key": "skill_key" in payload})
            
            request = SkillRunRequest(
                prompt=str(payload.get("prompt", "")),
                skill_key=payload.get("skill_key"),
                working_dir=payload.get("working_dir"),
            )
            
            logger.info("Running skill", extra={
                "prompt_length": len(request.prompt),
                "skill_key": request.skill_key,
                "working_dir": request.working_dir
            })
            
            response = self._service().run(request)
            
            logger.info("Skill execution completed", extra={
                "matched_skill": response.matched_skill,
                "confidence": response.confidence,
                "mode": response.mode
            })
            
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
            logger.error("Error processing skill request", extra={"error": str(exc)}, exc_info=True)
            self._json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})


def run_server(host: str = "127.0.0.1", port: int = 8765, workspace_root: Path | None = None) -> None:
    from core.logger import init_logging
    init_logging(log_level="INFO", log_dir="logs")
    logger.info("Initializing Skill API server", extra={"host": host, "port": port})
    
    if workspace_root is not None:
        logger.info("Setting custom workspace root", extra={"workspace_root": str(workspace_root)})
        _Handler.service = SkillService(factory=NexusFactory(workspace_root=workspace_root))
    
    server = ThreadingHTTPServer((host, port), _Handler)
    logger.info("Server started successfully", extra={"url": f"http://{host}:{port}"})
    print(f"Skill API listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
