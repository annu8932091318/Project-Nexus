import argparse
import json

from src.api.server import run_server
from src.factory import NexusFactory


def run_nexus_factory(prompt: str):
    factory = NexusFactory()
    return factory.run_build(prompt)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Project Nexus runtime")
    parser.add_argument(
        "mode",
        nargs="?",
        default="build",
        choices=["build", "run-skill", "list-skills", "serve-api"],
        help="Execution mode",
    )
    parser.add_argument("--prompt", default="", help="Prompt for build/run-skill modes")
    parser.add_argument("--skill", default=None, help="Explicit skill key for run-skill mode")
    parser.add_argument("--host", default="127.0.0.1", help="Host for serve-api mode")
    parser.add_argument("--port", default=8765, type=int, help="Port for serve-api mode")
    return parser


if __name__ == "__main__":
    parser = _build_parser()
    args = parser.parse_args()
    factory = NexusFactory()

    if args.mode == "serve-api":
        run_server(host=args.host, port=args.port)
    elif args.mode == "list-skills":
        print(json.dumps(factory.list_skills(), indent=2))
    elif args.mode == "run-skill":
        if not args.prompt.strip():
            raise SystemExit("--prompt is required for run-skill mode")
        result = factory.run_skill(prompt=args.prompt, skill_key=args.skill)
        print(result.output)
    else:
        prompt = args.prompt.strip()
        if not prompt:
            print("--- Project Nexus Local AI Factory ---")
            prompt = input("What would you like me to build? ")
        print(factory.run_build(prompt))
