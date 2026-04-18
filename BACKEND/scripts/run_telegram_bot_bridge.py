from __future__ import annotations

import argparse
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
    print("Telegram bridge started. Send a message to your bot to receive Project Nexus responses.")
    bridge.run_forever()


if __name__ == "__main__":
    main()
