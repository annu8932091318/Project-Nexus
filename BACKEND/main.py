import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from core.logger import get_logger, init_logging
from core.setup_wizard import ensure_setup
from src.api.server import run_server
from src.factory import NexusFactory

logger = get_logger(__name__)


def run_nexus_factory(prompt: str):
    factory = NexusFactory()
    logger.info("Running Nexus factory", extra={"prompt_length": len(prompt)})
    return factory.run_build(prompt)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Project Nexus runtime")
    parser.add_argument(
        "mode",
        nargs="?",
        default="build",
        choices=["build", "run-skill", "list-skills", "serve-api", "shell", "setup"],
        help="Execution mode",
    )
    parser.add_argument("--prompt", default="", help="Prompt for build/run-skill modes")
    parser.add_argument("--skill", default=None, help="Explicit skill key for run-skill mode")
    parser.add_argument("--cwd", default=None, help="Working directory for artifact output")
    parser.add_argument("--host", default=None, help="Host for serve-api mode")
    parser.add_argument("--port", default=None, type=int, help="Port for serve-api mode")
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run setup wizard before executing selected mode",
    )
    parser.add_argument(
        "--no-setup",
        action="store_true",
        help="Skip setup wizard prompts",
    )
    return parser


def _run_shell(factory: NexusFactory) -> None:
    print("--- Project Nexus Shell (local) ---")
    print("Type a prompt to execute. Commands: :help, :skills, :exit")
    while True:
        try:
            line = input("nexus> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting shell.")
            return

        if not line:
            continue
        if line in {":exit", "exit", "quit", ":q"}:
            print("Exiting shell.")
            return
        if line in {":help", "help"}:
            print("Commands: :help, :skills, :exit")
            print("Any other text is treated as a build/run request.")
            continue
        if line in {":skills", "skills"}:
            print(json.dumps(factory.list_skills(), indent=2))
            continue

        print(factory.run_build(line))


if __name__ == "__main__":
    init_logging(log_level="INFO", log_dir="logs")
    parser = _build_parser()
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parent
    load_dotenv(project_root / ".env", override=False)

    if args.setup and args.no_setup:
        raise SystemExit("Use either --setup or --no-setup, not both.")

    interactive_terminal = sys.stdin.isatty()
    setup_config = ensure_setup(
        project_root=project_root,
        force=(args.mode == "setup" or args.setup),
        interactive=interactive_terminal,
    ) if not args.no_setup else {}

    # Make configured notification credentials available for runtime tools.
    if setup_config.get("telegram_enabled"):
        os.environ.setdefault("TELEGRAM_BOT_TOKEN", setup_config.get("telegram_bot_token", ""))
        os.environ.setdefault("TELEGRAM_CHAT_ID", setup_config.get("telegram_chat_id", ""))

    configured_cwd = setup_config.get("workspace_root") if setup_config else None
    workspace_root = Path(args.cwd or configured_cwd or Path.cwd()).resolve()
    host = args.host or (setup_config.get("api_host") if setup_config else None) or "127.0.0.1"
    port = args.port if args.port is not None else int(
        (setup_config.get("api_port") if setup_config else 8765) or 8765
    )
    
    logger.info("Project Nexus started", extra={"mode": args.mode, "workspace_root": str(workspace_root)})

    if args.mode == "setup":
        raise SystemExit(0)
    
    factory = NexusFactory(workspace_root=workspace_root)

    if args.mode == "serve-api":
        logger.info("Starting API server", extra={"host": host, "port": port})
        run_server(host=host, port=port, workspace_root=workspace_root)
    elif args.mode == "list-skills":
        skills = factory.list_skills()
        logger.info("Listing skills", extra={"skill_count": len(skills)})
        print(json.dumps(skills, indent=2))
    elif args.mode == "shell":
        logger.info("Starting interactive shell")
        _run_shell(factory)
    elif args.mode == "run-skill":
        if not args.prompt.strip():
            logger.error("run-skill mode requires --prompt argument")
            raise SystemExit("--prompt is required for run-skill mode")
        logger.info("Running skill", extra={"prompt": args.prompt, "skill_key": args.skill})
        result = factory.run_skill(prompt=args.prompt, skill_key=args.skill)
        print(result.output)
    else:
        prompt = args.prompt.strip()
        if not prompt:
            print("--- Project Nexus Local AI Factory ---")
            prompt = input("What would you like me to build? ")
        logger.info("Running build mode", extra={"prompt_length": len(prompt)})
        print(factory.run_build(prompt))
