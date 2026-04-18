from __future__ import annotations

import json
import os
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
        "launcher_enabled": False,
        "launcher_installed": False,
        "launcher_bin_dir": "",
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


def _install_windows_launcher(project_root: Path) -> Dict[str, Any]:
    if os.name != "nt":
        return {
            "installed": False,
            "bin_dir": "",
            "message": "Global launcher install is currently implemented for Windows only.",
        }

    # Store launcher in user profile so it survives reboot and works across projects.
    bin_dir = Path.home() / ".project-nexus" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    launcher_path = bin_dir / "nexus.cmd"
    main_py = (project_root / "main.py").resolve()

    launcher_path.write_text(
        "@echo off\r\n"
        f'py -3 "{main_py}" %*\r\n',
        encoding="utf-8",
    )

    try:
        import winreg

        env_key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            "Environment",
            0,
            winreg.KEY_READ | winreg.KEY_SET_VALUE,
        )
        try:
            current_path, _ = winreg.QueryValueEx(env_key, "Path")
        except FileNotFoundError:
            current_path = ""

        current_entries = [p.strip() for p in current_path.split(";") if p.strip()]
        lower_entries = {p.lower() for p in current_entries}
        bin_str = str(bin_dir)

        if bin_str.lower() not in lower_entries:
            updated_entries = current_entries + [bin_str]
            new_path = ";".join(updated_entries)
            winreg.SetValueEx(env_key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
            os.environ["PATH"] = new_path
            return {
                "installed": True,
                "bin_dir": bin_str,
                "message": "Global `nexus` command installed. Open a new terminal to use it.",
            }

        return {
            "installed": True,
            "bin_dir": bin_str,
            "message": "Global `nexus` command already configured.",
        }
    except OSError as exc:
        return {
            "installed": False,
            "bin_dir": str(bin_dir),
            "message": f"Created launcher file but could not update PATH automatically: {exc}",
        }


def run_setup_wizard(project_root: Path) -> Dict[str, Any]:
    current = load_setup_config(project_root)

    print("\n=== Project Nexus Setup Wizard ===")
    print("Answer a few questions to configure your local runtime.\n")

    default_workspace = current.get("workspace_root") or str(Path.cwd().resolve())
    workspace_root = _prompt("Default working directory for generated artifacts", default_workspace)

    host = _prompt("Default API host", str(current.get("api_host") or "127.0.0.1"))
    port = _prompt_int("Default API port", int(current.get("api_port") or 8765))

    launcher_enabled = _prompt_yes_no(
        "Install global `nexus` command for this device (recommended)",
        bool(current.get("launcher_enabled", True)),
    )
    launcher_result = {"installed": False, "bin_dir": "", "message": ""}
    if launcher_enabled:
        launcher_result = _install_windows_launcher(project_root)
        print(launcher_result["message"])

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
        "launcher_enabled": launcher_enabled,
        "launcher_installed": bool(launcher_result.get("installed", False)),
        "launcher_bin_dir": str(launcher_result.get("bin_dir", "")),
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
    if updated.get("launcher_installed"):
        print("After opening a new terminal, run: nexus shell")
    else:
        print("Run `py -3 main.py shell` to start interactive runtime.")
    print("")
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
