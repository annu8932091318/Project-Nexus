from __future__ import annotations

import json
import mimetypes
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from core.logger import get_logger
from src.api.contracts import MessageRequest
from src.api.service import SkillService

logger = get_logger(__name__)


@dataclass(frozen=True)
class TelegramMessage:
    update_id: int
    chat_id: int
    text: str


class TelegramBotBridge:
    """Long-poll Telegram bridge that routes incoming text to Project Nexus."""

    def __init__(
        self,
        token: str,
        service: SkillService,
        poll_timeout_seconds: int = 30,
    ):
        if not token.strip():
            raise ValueError("Telegram bot token is required")
        self.token = token.strip()
        self.service = service
        self.poll_timeout_seconds = max(1, int(poll_timeout_seconds))
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.offset: Optional[int] = None

    def run_forever(self) -> None:
        logger.info("Telegram bridge started", extra={"poll_timeout_seconds": self.poll_timeout_seconds})
        while True:
            try:
                updates = self._get_updates()
                for update in updates:
                    message = self._parse_message(update)
                    if message is None:
                        continue
                    self.offset = message.update_id + 1
                    self._handle_message(message)
            except Exception as exc:  # pragma: no cover
                logger.error("Telegram bridge loop error", extra={"error": str(exc)}, exc_info=True)
                time.sleep(2)

    def _handle_message(self, incoming: TelegramMessage) -> None:
        prompt = incoming.text.strip()
        if not prompt:
            self._send_message(incoming.chat_id, "Please send a text prompt.")
            return

        logger.info(
            "Telegram message received",
            extra={"chat_id": incoming.chat_id, "prompt_length": len(prompt)},
        )

        route = "chat"
        try:
            response = self.service.message(MessageRequest(prompt=prompt, channel="telegram"))
            output = response.output.strip() or "I processed your request but there is no text output."
            artifacts = response.artifacts or {}
            route = response.route
        except Exception as exc:  # pragma: no cover
            logger.error("Telegram message processing failed", extra={"error": str(exc)}, exc_info=True)
            output = "I could not process your request right now. Please try again."
            artifacts = {}

        for chunk in self._chunk_text(output, 3500):
            self._send_message(incoming.chat_id, chunk)

        if route == "send_files" or self._wants_files(prompt):
            sent = 0
            for name, path in artifacts.items():
                file_path = Path(path)
                if not file_path.exists() or not file_path.is_file():
                    continue
                self._send_document(incoming.chat_id, file_path, caption=f"{name}: {file_path.name}")
                sent += 1

            if sent == 0:
                self._send_message(incoming.chat_id, "I do not have any available files to send yet.")

    def _get_updates(self) -> list[dict]:
        query = {
            "timeout": str(self.poll_timeout_seconds),
            "allowed_updates": json.dumps(["message"]),
        }
        if self.offset is not None:
            query["offset"] = str(self.offset)

        url = f"{self.base_url}/getUpdates?{urllib.parse.urlencode(query)}"
        payload = self._http_json(url)
        if not payload.get("ok"):
            raise RuntimeError(f"Telegram getUpdates failed: {payload}")
        result = payload.get("result")
        if not isinstance(result, list):
            return []
        return result

    def _send_message(self, chat_id: int, text: str) -> None:
        data = urllib.parse.urlencode(
            {
                "chat_id": str(chat_id),
                "text": text,
                "disable_web_page_preview": "true",
            }
        ).encode("utf-8")
        url = f"{self.base_url}/sendMessage"
        payload = self._http_json(url, method="POST", data=data)
        if not payload.get("ok"):
            raise RuntimeError(f"Telegram sendMessage failed: {payload}")

    def _send_document(self, chat_id: int, file_path: Path, caption: str = "") -> None:
        boundary = f"----nexus-{uuid.uuid4().hex}"
        mime = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        file_bytes = file_path.read_bytes()

        parts: list[bytes] = []
        parts.append(f"--{boundary}\r\n".encode("utf-8"))
        parts.append(b'Content-Disposition: form-data; name="chat_id"\r\n\r\n')
        parts.append(str(chat_id).encode("utf-8"))
        parts.append(b"\r\n")

        if caption:
            parts.append(f"--{boundary}\r\n".encode("utf-8"))
            parts.append(b'Content-Disposition: form-data; name="caption"\r\n\r\n')
            parts.append(caption.encode("utf-8"))
            parts.append(b"\r\n")

        parts.append(f"--{boundary}\r\n".encode("utf-8"))
        parts.append(
            (
                f'Content-Disposition: form-data; name="document"; filename="{file_path.name}"\r\n'
                f"Content-Type: {mime}\r\n\r\n"
            ).encode("utf-8")
        )
        parts.append(file_bytes)
        parts.append(b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode("utf-8"))

        body = b"".join(parts)
        url = f"{self.base_url}/sendDocument"
        req = urllib.request.Request(url=url, method="POST", data=body)
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        req.add_header("Content-Length", str(len(body)))

        try:
            with urllib.request.urlopen(req, timeout=self.poll_timeout_seconds + 15) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Telegram sendDocument HTTP error {exc.code}: {body}") from exc

        if not payload.get("ok"):
            raise RuntimeError(f"Telegram sendDocument failed: {payload}")

    def _http_json(self, url: str, method: str = "GET", data: bytes | None = None) -> dict:
        req = urllib.request.Request(url=url, method=method, data=data)
        if method == "POST":
            req.add_header("Content-Type", "application/x-www-form-urlencoded")

        try:
            with urllib.request.urlopen(req, timeout=self.poll_timeout_seconds + 5) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Telegram HTTP error {exc.code}: {body}") from exc

    def _parse_message(self, update: dict) -> Optional[TelegramMessage]:
        try:
            update_id = int(update.get("update_id"))
        except (TypeError, ValueError):
            return None

        message = update.get("message")
        if not isinstance(message, dict):
            return None
        chat = message.get("chat")
        if not isinstance(chat, dict):
            return None
        text = message.get("text")
        if not isinstance(text, str):
            return None

        try:
            chat_id = int(chat.get("id"))
        except (TypeError, ValueError):
            return None

        return TelegramMessage(update_id=update_id, chat_id=chat_id, text=text)

    def _chunk_text(self, text: str, max_len: int) -> list[str]:
        content = text.strip()
        if not content:
            return [""]
        if len(content) <= max_len:
            return [content]

        chunks: list[str] = []
        remaining = content
        while remaining:
            if len(remaining) <= max_len:
                chunks.append(remaining)
                break

            split_at = remaining.rfind("\n", 0, max_len)
            if split_at < int(max_len * 0.5):
                split_at = remaining.rfind(" ", 0, max_len)
            if split_at < int(max_len * 0.5):
                split_at = max_len

            chunks.append(remaining[:split_at].rstrip())
            remaining = remaining[split_at:].lstrip()

        return chunks

    def _wants_files(self, prompt: str) -> bool:
        lowered = prompt.lower()
        trigger_words = ("send", "share", "deliver", "attach")
        file_words = ("file", "files", "artifact", "artifacts", "document", "documents")
        return any(w in lowered for w in trigger_words) and any(w in lowered for w in file_words)
