# Project Nexus Skill Runtime (Backend Only)

This runtime executes skills from claude-skills-kit through a single backend orchestrator.

## Implemented capabilities

- Automatic skill registry loading from all SKILL.md files
- Trigger-based multilingual skill routing
- Manager-first intent routing for all prompts (chat, PRD, project, skill)
- Validation checks for skill metadata and source files
- Session persistence in `<working-dir>/.project-nexus/skill_sessions.json`
- Draft artifact generation directly in the selected working directory
- Interactive local shell mode for terminal-first operation
- Chat-agent fallback when prompt is not an explicit build/skill request

## Core modules

- `BACKEND/src/skill_runtime/registry.py`
- `BACKEND/src/skill_runtime/router.py`
- `BACKEND/src/skill_runtime/executor.py`
- `BACKEND/src/factory.py`

## Quick start

From repository root:

```powershell
cd BACKEND
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the setup wizard (interactive terminal Q&A):

```powershell
py -3 main.py setup
```

Notes:
- First run auto-prompts setup if no local setup file exists.
- Setup is one-time per device/user until you rerun setup.
- Wizard can install a global `nexus` command for post-restart usage.
- Force setup on demand: `py -3 main.py --setup shell`
- Skip prompts: `py -3 main.py --no-setup shell`

Run interactive shell:

```powershell
nexus shell
```

If `nexus` is not recognized yet, close and open terminal once.

## Runtime commands

List skills:

```powershell
py -3 main.py list-skills
```

Run direct skill:

```powershell
py -3 main.py run-skill --prompt "generate closure report"
```

Run with explicit target directory:

```powershell
py -3 main.py run-skill --prompt "generate project plan" --cwd "D:\work\client-a"
```

Start local skill API:

```powershell
py -3 main.py serve-api --host 127.0.0.1 --port 8765 --cwd "D:\work\client-a"
```

Managed message API (chat first):

```powershell
curl -X POST http://127.0.0.1:8765/message ^
	-H "Content-Type: application/json" ^
	-d "{\"prompt\":\"hello\",\"channel\":\"api\"}"
```

Telegram webhook style:

```powershell
curl -X POST http://127.0.0.1:8765/webhook/telegram ^
	-H "Content-Type: application/json" ^
	-d "{\"message\":{\"text\":\"create prd for inventory app\"}}"
```

WhatsApp webhook style:

```powershell
curl -X POST http://127.0.0.1:8765/webhook/whatsapp ^
	-H "Content-Type: application/json" ^
	-d "{\"Body\":\"approve project\"}"
```

Routing behavior:
- Normal chat input stays in chat mode.
- PRD is generated only for explicit PRD requests.
- Project requests generate PRD first and wait for explicit `approve project`.

Telegram direct reply bridge (long polling):

```powershell
py -3 scripts\run_telegram_bot_bridge.py
```

Use this when your bot is not configured with a public HTTPS webhook endpoint.
The bridge reads Telegram updates and sends Project Nexus responses back to the same chat.

## Terminal-first usage pattern (Clawbot style)

```powershell
py -3 main.py shell
```

Useful shell commands:

- `:help` to list shell commands
- `:skills` to print loaded skills
- `:exit` to quit

## Notifications

## Telegram

Set variables before runtime:

```powershell
$env:TELEGRAM_BOT_TOKEN="<your_bot_token>"
$env:TELEGRAM_CHAT_ID="<your_chat_id>"
```

Behavior in current build:
- Runtime can validate Telegram configuration.
- Outbound send from generic tools is safe-mode, but the Telegram bridge sends normal chat replies.

## WhatsApp

WhatsApp delivery is not native yet. Recommended implementation path:

1. Use Twilio WhatsApp API or an Apprise-compatible bridge.
2. Create a tiny notifier wrapper script that takes final output text.
3. Run wrapper after `run-skill`/`shell` output as a post-step.

## Windows Explorer integration

Register context menu:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\register_windows_context_menu.ps1
```

Unregister context menu:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\unregister_windows_context_menu.ps1
```

## Direct service usage

```python
from src.api.contracts import SkillRunRequest
from src.api.service import SkillService

service = SkillService()
response = service.run(SkillRunRequest(prompt="generate closure report"))
print(response.output)
```

## Safety model

- All skill executions are draft-first.
- Approval is required before any finalization workflow.
- Input assumptions and preflight issues are logged in each session.
