from __future__ import annotations

import argparse
import atexit
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.logger import get_logger, init_logging
from core.setup_wizard import load_setup_config
from src.api.service import SkillService
from src.bot.telegram_bridge import TelegramBotBridge
from src.factory import NexusFactory


logger = get_logger(__name__)
PID_FILE = PROJECT_ROOT / ".project-nexus" / "telegram_bridge.pid"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Project Nexus Telegram bot bridge")
    parser.add_argument("--poll-timeout", type=int, default=30, help="Telegram long-poll timeout seconds")
    parser.add_argument("--cwd", default=None, help="Working directory for artifacts")
    return parser


def main() -> None:
    init_logging(log_level="INFO", log_dir="logs")
    args = _build_parser().parse_args()

    project_root = PROJECT_ROOT
    load_dotenv(project_root / ".env", override=False)
    config = load_setup_config(project_root)

    token = os.getenv("TELEGRAM_BOT_TOKEN") or str(config.get("telegram_bot_token") or "")
    if not token.strip():
        raise SystemExit("Telegram bot token not found. Run setup or set TELEGRAM_BOT_TOKEN.")

    configured_cwd = str(config.get("workspace_root") or "").strip()
    workspace_root = Path(args.cwd or configured_cwd or Path.cwd()).resolve()

    service = SkillService(factory=NexusFactory(workspace_root=workspace_root))
    bridge = TelegramBotBridge(
        token=token,
        service=service,
        poll_timeout_seconds=args.poll_timeout,
    )

    logger.info(
        "Starting Telegram bot bridge",
        extra={"workspace_root": str(workspace_root), "poll_timeout": args.poll_timeout},
    )
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")

    def _cleanup_pid() -> None:
        try:
            if PID_FILE.exists() and PID_FILE.read_text(encoding="utf-8").strip() == str(os.getpid()):
                PID_FILE.unlink(missing_ok=True)
        except OSError:
            pass

    atexit.register(_cleanup_pid)

    print("Telegram bridge started. Send a message to your bot to receive Project Nexus responses.")
    bridge.run_forever()


if __name__ == "__main__":
    main()
