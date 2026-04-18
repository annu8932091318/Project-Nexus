# Project Nexus (Backend Only)

Project Nexus now runs as a backend-only local AI runtime. This repository no longer depends on any frontend stack.

You can run it from terminal in a Clawbot-style workflow:
- interactive shell mode
- one-shot skill execution
- local API server mode

## Install and Setup First (Step-by-Step)

Follow these steps in order on Windows.

### 1. Install prerequisites

- Python 3.10 or newer
- Ollama desktop app
- Git

### 2. Clone and enter repository

```powershell
git clone <your-repo-url>
cd Project-Nexus
```

### 3. Go to backend runtime folder

```powershell
cd BACKEND
```

### 4. Create and activate virtual environment

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 5. Install Python dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Pull required local Ollama models

```powershell
ollama pull llama3:8b
ollama pull deepseek-coder-v2
```

If ollama is not in PATH, use full executable path:

```powershell
& "C:\Users\<YOUR_USER>\AppData\Local\Programs\Ollama\ollama.exe" list
```

### 7. Verify installation

```powershell
ollama list
py -3 main.py list-skills
python test_logging_setup.py
```

Expected result:
- `ollama list` shows pulled models
- `list-skills` prints available skills JSON
- logging test writes to `BACKEND/logs/nexus.log`

### 8. Run guided setup wizard (interactive)

Project Nexus now supports Clawbot-style setup questions in terminal.

```powershell
py -3 main.py setup
```

The wizard asks for:
- default output folder (`--cwd` fallback)
- default API host/port
- install global `nexus` command on this device
- Telegram config
- optional Twilio WhatsApp credentials (saved for future use)

Behavior notes:
- First run auto-prompts setup if config is missing.
- Setup is saved once per device/user until changed.
- If launcher install is enabled, restart terminal and run `nexus ...` directly.
- To force setup again: `py -3 main.py --setup shell`
- To skip setup prompts: `py -3 main.py --no-setup shell`

### 9. Optional bot environment variables

Telegram variables:

```powershell
$env:TELEGRAM_BOT_TOKEN="<your_bot_token>"
$env:TELEGRAM_CHAT_ID="<your_chat_id>"
```

Note:
- Telegram config is detected by runtime tools.
- Outbound send is still safe-mode in current build.

WhatsApp option:
- Use Twilio WhatsApp API or an Apprise bridge script as a post-step.

### 10. First run (Clawbot style)

Interactive shell:

```powershell
nexus shell
```

One-shot command:

```powershell
nexus run-skill --prompt "generate project plan"
```

API mode:

```powershell
nexus serve-api --host 127.0.0.1 --port 8765
```

If `nexus` is not recognized in the current terminal, close and reopen terminal once.

### 11. Optional: make command available globally

Add to PowerShell profile:

```powershell
function nexus {
    py -3 "C:\Users\Anup\Documents\projects\Project-Nexus\BACKEND\main.py" @args
}
```

Then use:

```powershell
nexus shell
nexus list-skills
nexus run-skill --prompt "generate risk register"
```

## What you get

- Local-first backend runtime
- Skill routing from claude-skills-kit
- Draft artifact generation in your selected folder
- Structured JSON logs in BACKEND/logs/nexus.log
- Optional notification setup (Telegram now, WhatsApp via provider bridge)

## Chat-first behavior (new)

Runtime now behaves like a chatbot by default:
- Normal prompts (for example: hi, explain this, answer my question) are handled by chat agent response mode.
- PRD is generated only when you explicitly ask for it (for example: create PRD ...).
- Project creation is approval-gated:
    1. Ask: create project ...
    2. Nexus generates PRD draft and waits.
    3. You reply: approve project
    4. Nexus starts project creation flow.

This same manager routing logic is used for terminal prompts, API prompts, and bot webhook prompts.

## 1. Run like Clawbot (terminal workflow)

### Interactive shell mode

```powershell
py -3 main.py shell
```

Then type prompts directly:

```text
nexus> generate project plan from approved charter
nexus> :skills
nexus> :exit
```

### One-shot run

```powershell
py -3 main.py run-skill --prompt "generate closure report"
```

### Target a specific output directory

```powershell
py -3 main.py run-skill --prompt "generate project plan" --cwd "D:\work\client-a"
```

### API mode

```powershell
py -3 main.py serve-api --host 127.0.0.1 --port 8765 --cwd "D:\work\client-a"
```

## 2. Make it feel installed (quick command alias)

Add this to your PowerShell profile so you can run `nexus` from anywhere:

```powershell
function nexus {
    py -3 "C:\Users\Anup\Documents\projects\Project-Nexus\BACKEND\main.py" @args
}
```

After reloading PowerShell:

```powershell
nexus shell
nexus list-skills
nexus run-skill --prompt "generate project plan"
```

## 3. Optional bot notifications

## Telegram option (supported in runtime)

Set environment variables:

```powershell
$env:TELEGRAM_BOT_TOKEN="<your_bot_token>"
$env:TELEGRAM_CHAT_ID="<your_chat_id>"
```

Current behavior in this build:
- Telegram config is detected by runtime tools.
- Outbound delivery is intentionally safe-mode (no live send call yet).

## WhatsApp option (recommended path)

WhatsApp is not natively wired yet in this codebase. Use one of these bridges:
- Twilio WhatsApp API
- Apprise target URL bridge

Recommended approach:
1. Keep Nexus runtime unchanged.
2. Add a small notifier wrapper script that sends final build summaries to your provider.
3. Trigger wrapper from your terminal workflow or post-processing step.

## 4. Windows Explorer right-click integration

To register context menu command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\register_windows_context_menu.ps1
```

To remove it:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\unregister_windows_context_menu.ps1
```

## 5. Common commands

```powershell
py -3 main.py list-skills
py -3 main.py shell
py -3 main.py run-skill --prompt "generate risk register"
py -3 main.py serve-api --host 127.0.0.1 --port 8765
python test_logging_setup.py
pytest
```

## 6. API message endpoints for bots

Generic managed message endpoint:

```powershell
curl -X POST http://127.0.0.1:8765/message ^
    -H "Content-Type: application/json" ^
    -d "{\"prompt\":\"hi\",\"channel\":\"telegram\"}"
```

Telegram webhook-style endpoint:

```powershell
curl -X POST http://127.0.0.1:8765/webhook/telegram ^
    -H "Content-Type: application/json" ^
    -d "{\"message\":{\"text\":\"create project for inventory app\"}}"
```

WhatsApp webhook-style endpoint:

```powershell
curl -X POST http://127.0.0.1:8765/webhook/whatsapp ^
    -H "Content-Type: application/json" ^
    -d "{\"Body\":\"hi\"}"
```

For direct Telegram bot replies without public webhook hosting, run long-poll bridge:

```powershell
py -3 BACKEND\scripts\run_telegram_bot_bridge.py
```

Keep that command running in a terminal while chatting with your Telegram bot.

## 7. Troubleshooting

- Virtual environment not active: run `.\.venv\Scripts\Activate.ps1`
- Missing packages: run `pip install -r requirements.txt`
- Model not found: run `ollama list` and pull required models
- API port in use: change with `--port`

## 8. Notes

- This repository is backend-only now.
- No Node.js, npm, or frontend build steps are required.
- Main runtime docs are in BACKEND/README_RUNTIME.md.
