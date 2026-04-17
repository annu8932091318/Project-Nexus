from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def _config_dir(project_root: Path) -> Path:
    return project_root / ".project-nexus"


def _config_path(project_root: Path) -> Path:
    return _config_dir(project_root) / "setup.json"


def _default_config() -> Dict[str, Any]:
    return {
        "workspace_root": "",
        "api_host": "127.0.0.1",
        "api_port": 8765,
        "telegram_enabled": False,
        "telegram_bot_token": "",
        "telegram_chat_id": "",
        "whatsapp_enabled": False,
        "twilio_account_sid": "",
        "twilio_auth_token": "",
        "twilio_whatsapp_from": "",
        "twilio_whatsapp_to": "",
    }


def setup_exists(project_root: Path) -> bool:
    return _config_path(project_root).exists()


def load_setup_config(project_root: Path) -> Dict[str, Any]:
    config = _default_config()
    path = _config_path(project_root)
    if not path.exists():
        return config

    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            config.update(loaded)
    except (json.JSONDecodeError, OSError):
        return config

    return config


def save_setup_config(project_root: Path, config: Dict[str, Any]) -> Path:
    path = _config_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return path


def _prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def _prompt_yes_no(label: str, default: bool = False) -> bool:
    default_str = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{label} [{default_str}]: ").strip().lower()
        if not raw:
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("Please answer y or n.")


def _prompt_int(label: str, default: int) -> int:
    while True:
        raw = input(f"{label} [{default}]: ").strip()
        if not raw:
            return default
        try:
            return int(raw)
        except ValueError:
            print("Please enter a valid number.")


def run_setup_wizard(project_root: Path) -> Dict[str, Any]:
    current = load_setup_config(project_root)

    print("\n=== Project Nexus Setup Wizard ===")
    print("Answer a few questions to configure your local runtime.\n")

    default_workspace = current.get("workspace_root") or str(Path.cwd().resolve())
    workspace_root = _prompt("Default working directory for generated artifacts", default_workspace)

    host = _prompt("Default API host", str(current.get("api_host") or "127.0.0.1"))
    port = _prompt_int("Default API port", int(current.get("api_port") or 8765))

    telegram_enabled = _prompt_yes_no(
        "Configure Telegram notifications", bool(current.get("telegram_enabled", False))
    )
    telegram_bot_token = ""
    telegram_chat_id = ""
    if telegram_enabled:
        telegram_bot_token = _prompt(
            "Telegram bot token", str(current.get("telegram_bot_token") or "")
        )
        telegram_chat_id = _prompt(
            "Telegram chat id", str(current.get("telegram_chat_id") or "")
        )

    whatsapp_enabled = _prompt_yes_no(
        "Store WhatsApp (Twilio) credentials for future use",
        bool(current.get("whatsapp_enabled", False)),
    )
    twilio_account_sid = ""
    twilio_auth_token = ""
    twilio_whatsapp_from = ""
    twilio_whatsapp_to = ""
    if whatsapp_enabled:
        twilio_account_sid = _prompt(
            "Twilio Account SID", str(current.get("twilio_account_sid") or "")
        )
        twilio_auth_token = _prompt(
            "Twilio Auth Token", str(current.get("twilio_auth_token") or "")
        )
        twilio_whatsapp_from = _prompt(
            "Twilio WhatsApp From (example: whatsapp:+14155238886)",
            str(current.get("twilio_whatsapp_from") or ""),
        )
        twilio_whatsapp_to = _prompt(
            "Recipient WhatsApp To (example: whatsapp:+919999999999)",
            str(current.get("twilio_whatsapp_to") or ""),
        )

    updated = {
        "workspace_root": workspace_root,
        "api_host": host,
        "api_port": port,
        "telegram_enabled": telegram_enabled,
        "telegram_bot_token": telegram_bot_token,
        "telegram_chat_id": telegram_chat_id,
        "whatsapp_enabled": whatsapp_enabled,
        "twilio_account_sid": twilio_account_sid,
        "twilio_auth_token": twilio_auth_token,
        "twilio_whatsapp_from": twilio_whatsapp_from,
        "twilio_whatsapp_to": twilio_whatsapp_to,
    }

    path = save_setup_config(project_root, updated)
    print(f"\nSetup saved to: {path}")
    print("Run `py -3 main.py shell` to start interactive runtime.\n")
    return updated


def ensure_setup(project_root: Path, force: bool, interactive: bool) -> Dict[str, Any]:
    if force:
        if not interactive:
            raise RuntimeError("Setup wizard requires an interactive terminal.")
        return run_setup_wizard(project_root)

    if setup_exists(project_root):
        return load_setup_config(project_root)

    if interactive:
        return run_setup_wizard(project_root)

    defaults = load_setup_config(project_root)
    save_setup_config(project_root, defaults)
    return defaults
