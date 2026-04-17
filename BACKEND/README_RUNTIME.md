# Project Nexus Skill Runtime

This runtime makes all skills in `claude-skills-kit-main/skills` executable through a single backend orchestrator.

## What is implemented

- Automatic registry loading from all `SKILL.md` files
- Trigger-based multilingual skill routing
- Validation checks for skill metadata and source files
- Session persistence for each execution in `BACKEND/data/skill_sessions.json`
- Draft artifact generation in `BACKEND/workspace/artifacts`
- Backward-compatible fallback to existing manager/designer/developer/qa draft pipeline

## Core modules

- `BACKEND/src/skill_runtime/registry.py`
- `BACKEND/src/skill_runtime/router.py`
- `BACKEND/src/skill_runtime/executor.py`
- `BACKEND/src/factory.py`

## Usage

Run from backend directory:

```powershell
python main.py
```

List skills:

```powershell
python main.py list-skills
```

Run direct skill:

```powershell
python main.py run-skill --prompt "generate closure report"
```

Start local skill API:

```powershell
python main.py serve-api --host 127.0.0.1 --port 8765
```

For direct service use:

```python
from src.api.contracts import SkillRunRequest
from src.api.service import SkillService

service = SkillService()
response = service.run(SkillRunRequest(prompt="generate closure report"))
print(response.output)
```

## Safety model

- All skill executions are draft-first
- Approval is required before any finalization workflow
- Input assumptions and preflight issues are logged in each session
