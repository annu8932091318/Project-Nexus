# Nexus-Factory (Project Nexus)

Project Nexus is a local-first, multi-agent software factory that turns a high-level prompt into PRD context, design suggestions, implementation output, QA feedback, and iterative correction.

This repository aligns with the provided PRD set:
- Project Nexus (local agentic software factory)
- Nexus Agent Training and Optimization Module (NTOM)

## Setup First (Quick Start)

Use this section if you want to run the project immediately.

### 1. Clone and enter project

```bash
git clone <your-repo-url>
cd project-nexus
```

### 2. Python setup

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Node setup

```bash
npm install
```

### 4. Pull local Ollama models

```bash
ollama pull llama3:8b
ollama pull deepseek-coder-v2
```

### 5. Run backend and frontend

Backend:

```bash
python main.py
```

Frontend dashboard:

```bash
npm run dev
```

If Ollama is not in PATH on Windows, run it via full executable path:

```powershell
& "C:\Users\<YOUR_USER>\AppData\Local\Programs\Ollama\ollama.exe" list
```

## Table of Contents

1. Product Overview
2. System Architecture
3. Agent Responsibilities
4. End-to-End Workflow
5. Memory and Training Design
6. Repository Map
7. Setup and Installation
8. Runbook
9. Configuration Reference
10. PRD Coverage Matrix
11. Troubleshooting
12. Cost and Hardware

## 1. Product Overview

### 1.1 Objectives

| Objective | Description |
|---|---|
| Zero API Cost | Uses local LLM inference through Ollama by default. |
| Privacy-First | Runs locally on your machine without mandatory cloud services. |
| Multi-Agent Autonomy | Uses Manager, Designer, Developer, and QA roles in sequence. |
| Learning Loop | Persists lessons and reusable solution patterns. |
| Extensibility | Supports optional search, notifications, and future RAG/fine-tuning layers. |

### 1.2 What This Project Does Today

- Runs a sequential CrewAI pipeline across 4 core agents.
- Supports local model routing:
	- `llama3:8b` for manager/reasoning tasks.
	- `deepseek-coder-v2` for coding/design tasks.
- Stores project context and skills memory in local Chroma collections.
- Persists QA-derived lessons into `data/lessons_learned.json`.
- Includes optional internet search and Telegram notification tooling.

## 2. System Architecture

### 2.1 High-Level Flow

```text
User (CLI / React UI)
	-> NexusFactory Orchestrator (CrewAI process)
		-> Manager Agent (PRD task)
		-> Designer Agent (UI/schema task)
		-> Developer Agent (implementation task)
		-> QA Agent (verification task)
	-> Reflection Loop (optional retries on FAIL)
	-> Memory Persistence (Chroma + lessons JSON)
	-> Optional Notifications / Search Tools
```

### 2.2 Component Architecture

| Layer | Module(s) | Purpose |
|---|---|---|
| Orchestration | `src/factory.py`, `main.py` | Builds agents/tasks, runs sequence, handles reflection loop. |
| Agent Definitions | `config/agents.yaml`, `config/tasks.yaml`, `agents/*.py` | Role profiles and task contracts. |
| LLM Routing | `core/llm_config.py` | Maps roles to local Ollama model identifiers. |
| Memory | `core/memory.py` | Project context, skill memory, user preference collections. |
| Tools | `src/tools/browser.py`, `core/tool_registry.py` | Search and notification integrations. |
| Training Loop | `training/*.py` | Ingestion, feedback analysis, memory-card management. |
| Data | `data/*` | Knowledge base, vector store path, lessons, skill metadata. |

## 3. Agent Responsibilities

| Agent | Primary Goal | Inputs | Outputs |
|---|---|---|---|
| Manager | Build PRD-oriented context and coordinate flow | User prompt | Structured PRD task context |
| Designer | Convert PRD context to UI/component schema | PRD output | Design schema + component list |
| Developer | Generate implementation artifacts | PRD + design context | Source outputs in workspace |
| QA | Validate quality and logic | Generated code/context | PASS/FAIL report with issues |

## 4. End-to-End Workflow

### 4.1 Build Pipeline

| Phase | Owner | Description | Exit Criteria |
|---|---|---|---|
| Requirement | Manager | Parses prompt and creates PRD-focused context. | PRD task generated |
| Design | Designer | Produces UI/component structure. | Design schema produced |
| Development | Developer | Generates code from accumulated context. | Code output generated |
| Verification | QA | Reviews outputs for quality and defects. | PASS/FAIL report emitted |
| Reflection | Factory + QA/Dev | On FAIL, stores lesson and retries (bounded). | PASS or max retries reached |
| HITL (Optional) | Manager/Tools | Sends approval notification when pass state reached. | Notification sent |

### 4.2 Reflection Logic

- QA result text is evaluated.
- If failure is detected:
	- failure pattern is analyzed.
	- lesson is appended to `data/lessons_learned.json`.
	- pipeline may re-run up to configured retry count.
- On pass:
	- a success card is persisted to skills memory.

## 5. Memory and Training Design

### 5.1 Memory Collections

| Collection | Backing Store | Purpose |
|---|---|---|
| `project_context` | Chroma | Stores prompt/context snapshots for current and historical builds. |
| `skills_memory` | Chroma | Stores successful patterns and reusable solutions. |
| `user_profile` | Chroma | Stores user preference signals. |

### 5.2 Training/Optimization Modules

| Module | Purpose | Typical Use |
|---|---|---|
| `training/ingestion.py` | Ingest local markdown/text docs into vector store | Bootstrap domain knowledge |
| `training/feedback_loop.py` | Convert failures into negative constraints | Improve next iteration quality |
| `training/memory_manager.py` | Save/retrieve knowledge cards | Skill retention and reuse |

Note: `bootstrap_knowledge()` returns `0` when `data/knowledge_base` has no `.md` or `.txt` files.

## 6. Repository Map

```text
project-nexus/
├── agents/
│   ├── manager.py
│   ├── designer.py
│   ├── developer.py
│   └── qa_agent.py
├── config/
│   ├── agents.yaml
│   └── tasks.yaml
├── core/
│   ├── llm_config.py
│   ├── memory.py
│   └── tool_registry.py
├── src/
│   ├── factory.py
│   ├── App.tsx
│   └── tools/
│       └── browser.py
├── training/
│   ├── ingestion.py
│   ├── memory_manager.py
│   └── feedback_loop.py
├── data/
│   ├── knowledge_base/
│   ├── vector_store/
│   ├── fine_tune_sets/
│   ├── skills.json
│   └── lessons_learned.json
├── workspace/
├── docker-compose.yml
├── main.py
├── requirements.txt
└── README.md
```

## 7. Setup and Installation

### 7.1 Python Environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 7.2 Node Environment

```bash
npm install
```

### 7.3 Ollama and Models

```bash
ollama pull llama3:8b
ollama pull deepseek-coder-v2
```

If `ollama` is not in PATH on Windows, use the local executable path:

```powershell
& "C:\Users\<YOUR_USER>\AppData\Local\Programs\Ollama\ollama.exe" list
```

### 7.4 Optional Local Services

```bash
docker compose up -d
```

This starts ChromaDB and SearXNG as defined in `docker-compose.yml`.

## 8. Runbook

| Task | Command | Notes |
|---|---|---|
| Run backend swarm | `python main.py` | Starts interactive prompt-driven build flow. |
| Run frontend dev server | `npm run dev` | Starts Vite dashboard. |
| Type-check frontend | `npm run lint` | Runs `tsc --noEmit`. |
| Build frontend | `npm run build` | Produces production assets in `dist/`. |
| Bootstrap knowledge | `python -c "from training.ingestion import bootstrap_knowledge; print(bootstrap_knowledge())"` | Returns ingested document count. |

## 9. Configuration Reference

| File | Purpose |
|---|---|
| `config/agents.yaml` | Agent roles, goals, and backstories |
| `config/tasks.yaml` | Task descriptions and expected outputs |
| `requirements.txt` | Python dependency list |
| `docker-compose.yml` | Optional local service stack |

## 10. PRD Coverage Matrix

| PRD Area | Current Status | Notes |
|---|---|---|
| Multi-agent orchestration | Implemented | Sequential Manager->Designer->Developer->QA flow |
| Local LLM runtime | Implemented | Ollama with Llama3 and DeepSeek-Coder-V2 |
| QA reflection loop | Implemented | Lessons persisted to `data/lessons_learned.json` |
| Skills/project memory | Implemented | Chroma collections and memory helpers |
| Domain ingestion | Implemented (scaffold + runtime) | Ingests local `.md`/`.txt` docs |
| HITL approval gate | Partial | Telegram notification hook exists; manual approval gate can be extended |
| Deterministic test harnesses | Partial | QA is LLM-driven; per-stack runners can be added |
| FE/BE split dev agents | Planned | Current developer role can be expanded into specialized agents |
| Advanced RAG/fine-tune stack | Planned | Haystack/RAGFlow/Unsloth and related tooling not fully integrated |

## 11. Troubleshooting

| Symptom | Likely Cause | Resolution |
|---|---|---|
| `ollama` command not found | PATH not updated | Use full executable path or restart terminal |
| Model pull fails | Network or disk space | Retry pull and verify available storage |
| Repeated QA failure loops | Prompt/task ambiguity | Reduce `max_reflections`, improve task descriptions |
| Ingestion returns `0` | Empty knowledge base folder | Add markdown/text docs to `data/knowledge_base` |
| Docker service start failure | Docker not running or port conflict | Check Docker Desktop and ports `8000`, `8080` |

## 12. Cost and Hardware

### 12.1 Cost Model

| Area | Cost |
|---|---|
| Local inference | Free |
| Orchestration | Open source |
| Memory storage | Local filesystem |
| Search/notifications | Free-tier/open integrations |

Expected direct API cost for local runs: `0.00`.

### 12.2 Hardware Guidance

| Tier | Suggested Hardware |
|---|---|
| Minimum | 16 GB RAM, modern CPU or mid-range GPU |
| Recommended | 32 GB+ RAM and high-end GPU for larger local models |

## 13. Detailed Execution Lifecycle

This section explains what happens internally from the moment a user enters a prompt to the moment a final report is printed.

### 13.1 Lifecycle Stages

| Stage | Internal Trigger | Primary Module | Output |
|---|---|---|---|
| Prompt Intake | User input from CLI/UI | `main.py` | Raw prompt text |
| Factory Initialization | `run_nexus_factory()` call | `src/factory.py` | `NexusFactory` instance |
| Memory Preload | Factory constructor | `core/memory.py` | Chroma collections attached |
| Agent Build | `create_agents()` | `src/factory.py` + YAML configs | Runtime `Agent` objects |
| Task Graph Build | `run_build()` | `src/factory.py` + `config/tasks.yaml` | Runtime `Task` objects |
| Sequential Kickoff | Crew kickoff | CrewAI process engine | Task outputs and final result |
| QA Decision | result text evaluation | `_qa_passed()` | PASS/FAIL boolean |
| Reflection Loop | QA fail + retries left | `training/feedback_loop.py` | Saved lesson + rerun |
| Success Persistence | PASS state | `core/memory.py` | Skill card stored |
| Optional Notification | Approval URL provided | `src/tools/browser.py` | Telegram message |

### 13.2 Runtime Timeline (Conceptual)

```text
t0  user enters prompt
t1  factory starts and binds memory + agents
t2  manager task runs
t3  designer task runs
t4  developer task runs
t5  qa task runs
t6  if fail: save lesson + rerun loop
t7  if pass: save success card
t8  optional notification
t9  final output printed
```

### 13.3 Why Sequential Process Is Used

The project intentionally uses a strict sequential process because:

1. PRD context should exist before design context.
2. Design context should exist before development output.
3. QA should evaluate the latest generated output, not stale intermediate state.
4. Reflection loop quality is better when output provenance is deterministic.

## 14. Module Reference (Backend)

### 14.1 `main.py`

Purpose:
- Entry point for CLI execution.

Responsibilities:
- Accept user prompt.
- Instantiate factory.
- Print final report.

Extension ideas:
- Add command-line arguments for retries and notification endpoint.
- Add non-interactive mode for CI execution.

### 14.2 `src/factory.py`

Purpose:
- Runtime orchestration kernel for Nexus.

Responsibilities:
- Load YAML configs.
- Build agent objects.
- Build task objects.
- Execute crew sequentially.
- Handle reflection loop.
- Persist context and successful patterns.

Key methods:

| Method | Role |
|---|---|
| `load_config` | Reads YAML config files |
| `create_agents` | Builds runtime Manager/Designer/Developer/QA agents |
| `_qa_passed` | Normalizes QA report into pass/fail signal |
| `_persist_project_context` | Saves user prompt and metadata |
| `_persist_success_card` | Saves successful output pattern |
| `run_build` | End-to-end execution entrypoint |

### 14.3 `core/memory.py`

Purpose:
- Local vector-backed persistence API wrapper.

Collections:

| Collection | Description |
|---|---|
| `project_context` | Prompt and context snapshots |
| `skills_memory` | Success cards and reusable solutions |
| `user_profile` | User preferences and personalization hints |

Operations:

| Operation | Method |
|---|---|
| Add context | `store_context` |
| Add skill card | `store_skill` |
| Add preference | `store_user_preference` |
| Query skills | `query_skills` |
| Query context | `query_project_context` |

### 14.4 `core/llm_config.py`

Purpose:
- Role-based model selection abstraction.

Model routing:

| Role key | Model |
|---|---|
| manager | `ollama/llama3:8b` |
| coder | `ollama/deepseek-coder-v2` |

### 14.5 `core/tool_registry.py`

Purpose:
- Central catalog for external callable tool functions.

Registered tools:

| Tool key | Function |
|---|---|
| `search_internet` | DuckDuckGo query execution |
| `send_telegram` | Apprise-based message notification |

### 14.6 `training/feedback_loop.py`

Purpose:
- Convert failure logs into actionable negative constraints.

Core flow:

1. Detect failure category from QA logs.
2. Map category to a stable lesson template.
3. Persist lesson to `data/lessons_learned.json`.

### 14.7 `training/ingestion.py`

Purpose:
- Ingest local docs into vector memory.

Doc sources:
- `data/knowledge_base/**/*.md`
- `data/knowledge_base/**/*.txt`

Vector target:
- `data/vector_store`

### 14.8 `training/memory_manager.py`

Purpose:
- Programmatic helper for writing and retrieving structured knowledge cards.

Primary methods:

| Method | Description |
|---|---|
| `save_knowledge_card` | Store reusable learned solution with metadata |
| `retrieve_similar_solutions` | Query memory for related previous solutions |

## 15. Module Reference (Agent Layer)

### 15.1 Agent Layer Design

Agent definitions appear in two forms:

1. YAML runtime profiles used directly by factory orchestration.
2. Python class wrappers in `agents/` for extensibility patterns.

### 15.2 Agent Class Summary

| Class | File | Current Use |
|---|---|---|
| `NexusManager` | `agents/manager.py` | Optional class-based extension path |
| `NexusDesigner` | `agents/designer.py` | Optional class-based extension path |
| `NexusDeveloper` | `agents/developer.py` | Optional class-based extension path |
| `NexusQA` | `agents/qa_agent.py` | Optional class-based extension path |

### 15.3 YAML Profile Summary

| Profile Key | File | Purpose |
|---|---|---|
| `manager` | `config/agents.yaml` | Product/coordination reasoning |
| `designer` | `config/agents.yaml` | UX and component planning |
| `developer` | `config/agents.yaml` | Code generation |
| `qa_engineer` | `config/agents.yaml` | Quality and defect detection |

## 16. Data Contracts and Schemas

### 16.1 Lessons Schema (`data/lessons_learned.json`)

Each entry follows this shape:

```json
{
	"error_logs": "<original failure text>",
	"negative_constraint": "<future prevention guideline>"
}
```

### 16.2 Skill Card Metadata Schema

Current metadata keys:

| Field | Type | Meaning |
|---|---|---|
| `saved_at` | string (ISO datetime) | Save timestamp |
| `project_type` | string | Solution domain label |
| `user_approval_rating` | int/null | Optional human quality score |

### 16.3 Project Context Metadata Schema

Current metadata keys:

| Field | Type | Meaning |
|---|---|---|
| `saved_at` | string (ISO datetime) | Context snapshot timestamp |

## 17. Configuration Handbook

### 17.1 `config/agents.yaml` Fields

| Field | Required | Description |
|---|---|---|
| `role` | Yes | Human-readable role title used by agent prompt context |
| `goal` | Yes | Outcome target for agent behavior |
| `backstory` | Yes | Persona constraints and strategy hints |

### 17.2 `config/tasks.yaml` Fields

| Field | Required | Description |
|---|---|---|
| `description` | Yes | Task prompt template |
| `expected_output` | Yes | Contract-style expected response |

### 17.3 Recommended Prompt Authoring Pattern

Use this style for task descriptions:

1. Explain objective.
2. Provide context constraints.
3. Specify output format.
4. Include non-goals.

Example:

```text
Objective: Build a production-safe API scaffold.
Constraints: Use Python + FastAPI, no external paid APIs, include health endpoint.
Output: File list + code snippets + run command.
Non-goals: No cloud deployment setup.
```

## 18. Validation and Quality Gates

### 18.1 Local Checks Used in This Project

| Check | Command | Expected Result |
|---|---|---|
| Backend import check | `py -c "import src.factory"` | No exception |
| Frontend type check | `npm run lint` | No TypeScript errors |
| Frontend build | `npm run build` | Build succeeds |
| Model availability | `ollama list` | Required models listed |
| Training bootstrap | `bootstrap_knowledge()` | Returns int, no crash |

### 18.2 Suggested Additional Gates

1. Add unit tests for memory helper methods.
2. Add regression tests for `_qa_passed` classification.
3. Add snapshot tests for README command blocks.
4. Add integration test for reflection loop persistence.
5. Add deterministic mock LLM layer for CI.

### 18.3 QA Failure Classification Guide

| Pattern in Logs | Suggested Correction Strategy |
|---|---|
| Import/module errors | Verify dependencies, module paths, and environment activation |
| Async/await misuse | Ensure coroutine boundaries are awaited correctly |
| Type/contract mismatch | Align data schemas and interface expectations |
| Runtime path errors | Normalize workspace-relative paths |
| Tool execution errors | Validate tool registration and call signatures |

## 19. Operations Runbook

### 19.1 First-Time Bring-Up

1. Install Python dependencies.
2. Install Node dependencies.
3. Pull Ollama models.
4. Run backend.
5. Run frontend.
6. Execute one smoke prompt.
7. Confirm lessons file can be updated.

### 19.2 Daily Start Procedure

1. Activate virtual environment.
2. Check model availability.
3. Start backend process.
4. Start frontend process (optional).
5. Run one short build prompt as warm-up.

### 19.3 Incident Response Checklist

| Step | Action |
|---|---|
| 1 | Capture exact error output |
| 2 | Classify failure type (dependency, model, path, runtime) |
| 3 | Verify baseline commands (lint/build/import/ollama list) |
| 4 | Apply smallest fix |
| 5 | Re-run baseline checks |
| 6 | Record new lesson if useful |

## 20. Security and Privacy Notes

### 20.1 Current Security Posture

- Local-first architecture reduces external data exposure.
- Optional integrations are explicitly opt-in.
- No mandatory paid API keys required by default path.

### 20.2 Recommended Hardening

1. Keep notification tokens outside source control.
2. Restrict docker network exposure if using local services.
3. Add `.env`-driven configuration for sensitive values.
4. Add role-based file write boundaries if enabling autonomous code execution.
5. Periodically prune local memory stores for sensitive data.

### 20.3 Secrets Handling

| Secret Type | Recommended Storage |
|---|---|
| Telegram URL/token | `.env` file + runtime load |
| Future API tokens | OS keychain or secret manager |
| Internal service creds | Non-committed local config |

## 21. Deployment Modes

### 21.1 Supported Modes

| Mode | Description | Best For |
|---|---|---|
| CLI only | Run backend from terminal | Local development and testing |
| CLI + Dashboard | Backend plus Vite UI | Visual monitoring and demos |
| Docker-assisted | Add local service containers | Local search/vector service integration |

### 21.2 Environment Matrix

| Environment | Mandatory Components | Optional Components |
|---|---|---|
| Dev laptop | Python, Node, Ollama | Docker services, Telegram |
| Workstation | Python, Node, Ollama | Larger models, dedicated vector service |
| Lab server | Python, Ollama | Frontend UI host, shared memory volume |

### 21.3 Recommended Directory Discipline

1. Keep generated app artifacts in `workspace/`.
2. Keep knowledge sources in `data/knowledge_base/`.
3. Keep lessons append-only in `data/lessons_learned.json`.
4. Avoid writing generated files to core orchestration modules.
5. Use source control for configs and docs, not transient outputs.

## 22. Command Cookbook

This section provides commonly used command patterns for operations, debugging, and maintenance.

### 22.1 Environment and Tooling Commands

| Purpose | Command |
|---|---|
| Show Python version | `py --version` |
| Show pip version | `py -m pip --version` |
| Upgrade pip | `py -m pip install --upgrade pip` |
| Create venv | `python -m venv .venv` |
| Activate venv (PowerShell) | `.\.venv\Scripts\Activate.ps1` |
| Install Python deps | `pip install -r requirements.txt` |
| Install Node deps | `npm install` |
| Show Node version | `node -v` |
| Show npm version | `npm -v` |
| Type-check frontend | `npm run lint` |
| Build frontend | `npm run build` |
| Run frontend dev | `npm run dev` |
| Run backend | `python main.py` |

### 22.2 Ollama Commands

| Purpose | Command |
|---|---|
| Show version | `ollama --version` |
| List models | `ollama list` |
| Pull manager model | `ollama pull llama3:8b` |
| Pull coder model | `ollama pull deepseek-coder-v2` |
| Quick prompt test | `ollama run llama3:8b "Respond with exactly: OK"` |
| Remove model | `ollama rm <model>` |

### 22.3 Windows Full-Path Ollama Commands

```powershell
$ollama = "C:\Users\<YOUR_USER>\AppData\Local\Programs\Ollama\ollama.exe"
& $ollama --version
& $ollama list
& $ollama pull llama3:8b
& $ollama pull deepseek-coder-v2
```

### 22.4 Python Smoke Tests

```bash
py -c "import src.factory; print('factory module ok')"
py -c "import core.memory; print('memory module ok')"
py -c "import training.feedback_loop; print('feedback module ok')"
py -c "from src.factory import NexusFactory; print('factory init', bool(NexusFactory()))"
```

### 22.5 Training and Memory Commands

```bash
python -c "from training.ingestion import bootstrap_knowledge; print(bootstrap_knowledge())"
python -c "from training.memory_manager import TrainingMemoryManager as T; m=T(); print('manager ok')"
```

## 23. Extension Playbooks

### 23.1 Add a New Agent Role

1. Add role profile in `config/agents.yaml`.
2. Add new task template in `config/tasks.yaml`.
3. Create optional wrapper class in `agents/`.
4. Wire agent into `src/factory.py:create_agents()`.
5. Add task in execution graph with explicit context dependencies.
6. Update README role and coverage tables.

### 23.2 Add a New Tool

1. Implement function in `src/tools/` or `core/`.
2. Register in `core/tool_registry.py`.
3. Validate function signature and side effects.
4. Add minimal runtime smoke test.
5. Document in README tool tables and troubleshooting section.

### 23.3 Add a New Memory Collection

1. Define collection in `core/memory.py`.
2. Add helper write/query methods.
3. Add metadata schema table in docs.
4. Add migration note if existing data layout changes.

### 23.4 Add Deterministic Test Runner to QA

1. Decide generated project type targets (Python, React, API, etc.).
2. Add test-run command builder in QA flow.
3. Parse exit codes and append deterministic failures to QA report.
4. Blend deterministic output with LLM narrative.
5. Store failure constraints via existing feedback loop.

### 23.5 Add HITL Gate

1. On PASS, pause before final acceptance.
2. Send approval request message with build summary.
3. Wait for explicit approval event (file flag, CLI input, webhook).
4. Finalize only after approval.
5. Persist approval metadata to success card.

## 24. Testing Strategy

### 24.1 Unit Testing Targets

| Module | Suggested Unit Tests |
|---|---|
| `core/memory.py` | add/query operations, metadata handling |
| `training/feedback_loop.py` | pattern classification and JSON persistence |
| `src/factory.py` | qa pass classifier, retry behavior |
| `core/tool_registry.py` | registry completeness and callable validity |

### 24.2 Integration Testing Targets

| Scenario | Assertion |
|---|---|
| Full build with valid prompt | no exception and non-empty final result |
| Forced QA fail path | lesson entry appended |
| Success path with notification URL | notifier function called |
| Empty knowledge base ingestion | returns 0 and no crash |

### 24.3 Regression Testing Checklist

1. `npm run lint` passes.
2. `npm run build` passes.
3. `python main.py` starts interactive flow.
4. `ollama list` contains required models.
5. Memory initialization does not crash.
6. Feedback loop can append to lessons file.

## 25. Operational Checklists

### 25.1 Pre-Run Checklist

- Virtual environment active.
- Required Python packages installed.
- Required Node packages installed.
- Ollama runtime reachable.
- Required models available.
- Optional docker services healthy (if used).

### 25.2 Post-Run Checklist

- Final result captured.
- Lessons file updated when failure occurred.
- Success card stored on pass.
- Generated artifacts written to workspace.
- Any manual approval event recorded.

### 25.3 Weekly Maintenance Checklist

- Update dependencies in a controlled branch.
- Re-run lint/build/import smoke checks.
- Prune stale generated artifacts.
- Review lessons for recurring failure patterns.
- Review memory growth and storage usage.

### 25.4 Monthly Maintenance Checklist

- Validate model versions and performance.
- Refresh knowledge base docs.
- Audit optional integrations and tokens.
- Revisit PRD coverage and roadmap status.

## 26. Failure Mode Catalog

| Category | Symptom | Diagnosis | Mitigation |
|---|---|---|---|
| Dependency | Import error at startup | Missing package or wrong environment | Activate venv and install requirements |
| Model | Inference request hangs | Ollama not running or model missing | Validate runtime and pull model |
| Config | Task key missing | YAML mismatch between code and config | Validate keys and reload |
| Memory | Write failure | Path or permissions issue | Ensure writable workspace path |
| Notification | Send fails | Invalid Telegram URL | Verify Apprise URL format |
| Frontend | `tsc` not found | Node modules not installed | Run `npm install` |
| Build | Large chunk warning | Bundle size growth | Add code-splitting strategy |

## 27. Glossary

| Term | Meaning |
|---|---|
| PRD | Product Requirements Document |
| CrewAI | Multi-agent orchestration framework used by this project |
| Chroma | Local vector database for memory persistence |
| Reflection Loop | Retry cycle after QA failure with lesson persistence |
| HITL | Human-in-the-loop approval step |
| Skill Card | Persisted successful solution pattern |
| Knowledge Bootstrap | Ingestion of local docs into vector memory |

## 28. FAQ (Extensive)

### 28.1 Setup FAQ

Q1: Do I need paid API keys to run this?
A1: No. The default path uses local Ollama models and open-source tooling.

Q2: Can I run backend without frontend?
A2: Yes. Backend CLI is fully functional independently.

Q3: Can I run frontend without backend?
A3: You can run the UI, but end-to-end generation requires backend orchestration.

Q4: Is Docker mandatory?
A4: No. Docker services are optional for local auxiliary infrastructure.

Q5: Which Python version is recommended?
A5: Python 3.11+ is generally recommended for dependency compatibility.

Q6: Which Node version is recommended?
A6: A modern active LTS version is recommended.

Q7: Does this work on Windows?
A7: Yes, including full local model workflow.

Q8: Does this work on Linux and macOS?
A8: Yes, with equivalent setup commands.

Q9: Can I use CPU-only inference?
A9: Yes, but performance depends on hardware and model size.

Q10: How much disk space do models need?
A10: Plan for multiple gigabytes per model plus cache overhead.

### 28.2 Runtime FAQ

Q11: Why does QA still fail after retries?
A11: The generated code may need stronger constraints or deterministic tests.

Q12: How do I reduce infinite-looking loops?
A12: Keep retries bounded and improve task specificity.

Q13: Where are failures stored?
A13: In `data/lessons_learned.json` via feedback loop module.

Q14: Where are successes stored?
A14: In Chroma `skills_memory` collection.

Q15: Where is user context stored?
A15: In Chroma `project_context` and optional `user_profile`.

Q16: Why is ingestion returning 0?
A16: There are no `.md` or `.txt` files in the knowledge base folder.

Q17: Does this edit existing project code automatically?
A17: The current architecture is oriented around generated workspace outputs.

Q18: Can I force JSON outputs from agents?
A18: Yes, by strengthening task output contracts.

Q19: Can I make QA deterministic?
A19: Yes, add concrete test commands and exit-code checks.

Q20: Does the manager currently split FE/BE tasks separately?
A20: Not yet; this is a roadmap extension.

### 28.3 Tooling FAQ

Q21: Why does `ollama` command fail but models exist?
A21: Windows PATH may not include Ollama binary; use full executable path.

Q22: Is Telegram mandatory?
A22: No, notification integration is optional.

Q23: Can I use WhatsApp?
A23: Possible through supported Apprise notification backends.

Q24: Is SearXNG required for search?
A24: No, current search tool uses DuckDuckGo integration.

Q25: Can I disable all external tools?
A25: Yes, keep tool calls unused and avoid optional integrations.

Q26: Is Chroma required?
A26: Current memory module is designed around Chroma persistence.

Q27: Can I swap Chroma for another store?
A27: Yes, by replacing memory adapter methods in `core/memory.py`.

Q28: Can I use different local models?
A28: Yes, update model names in LLM routing.

Q29: Can I route by task instead of role?
A29: Yes, with a task-aware LLM selection layer.

Q30: Can I run without internet?
A30: Yes, except optional tool calls and package/model downloads.

### 28.4 Development FAQ

Q31: Where should I add new orchestration logic?
A31: In `src/factory.py` with explicit method boundaries.

Q32: Where should I add new data files?
A32: Under `data/` with clear schema docs.

Q33: How do I version lessons schema?
A33: Add explicit schema version fields and migration scripts.

Q34: How do I track PRD coverage changes?
A34: Update the PRD coverage matrix section in this README.

Q35: Should I edit generated artifacts manually?
A35: Prefer regeneration and constraints first, manual edits second.

Q36: How do I add custom prompts?
A36: Extend task descriptions or add profile-specific prompt templates.

Q37: How do I add strict coding standards?
A37: Include standards in task contracts and QA criteria.

Q38: Can I enforce project templates?
A38: Yes, add scaffold constraints in developer task descriptions.

Q39: Can I integrate CI?
A39: Yes, run lint/build/smoke checks in pipeline jobs.

Q40: Can I run this in a monorepo?
A40: Yes, with path and workspace adjustments.

### 28.5 Performance FAQ

Q41: Why is first run slower?
A41: Model warm-up, cache creation, and dependency cold start.

Q42: Why is model pull slow?
A42: Large model size and network throughput limitations.

Q43: How to reduce latency?
A43: Use smaller models, optimize prompts, and reduce unnecessary retries.

Q44: How to reduce memory use?
A44: Choose smaller models and avoid parallel heavyweight operations.

Q45: How to improve output quality?
A45: Improve task constraints, examples, and QA criteria.

Q46: How to improve consistency?
A46: Use deterministic templates and stricter expected outputs.

Q47: Should I keep historical context forever?
A47: No, periodically prune or archive stale context.

Q48: Should I store every failed attempt?
A48: Store significant failures; avoid noisy duplicates.

Q49: Is GPU mandatory for deepseek-coder-v2?
A49: Not mandatory, but performance and usability improve with capable hardware.

Q50: Is 16 GB RAM enough?
A50: Minimum workable baseline for smaller workloads.

### 28.6 Security FAQ

Q51: Does this send code to cloud by default?
A51: No, default model inference is local.

Q52: Where should tokens be stored?
A52: Local secret storage or environment variables, not committed files.

Q53: Are lessons encrypted?
A53: Not by default; add encryption if needed for sensitive environments.

Q54: Is vector data encrypted at rest?
A54: Not by default in current implementation.

Q55: Can I isolate runtime further?
A55: Yes, use container sandboxing and restricted file permissions.

Q56: Can generated code be dangerous?
A56: Any generated code should be reviewed before production execution.

Q57: Should I run as admin?
A57: Prefer least-privilege execution.

Q58: Can notifications leak sensitive data?
A58: Yes, sanitize message payloads.

Q59: Is local search private?
A59: Local services reduce exposure, but external queries may still leave your machine.

Q60: How do I audit changes?
A60: Use version control and explicit change logs.

### 28.7 Architecture FAQ

Q61: Why keep YAML configs?
A61: They allow behavior tuning without code edits.

Q62: Why have both YAML and agent classes?
A62: YAML for runtime flexibility, classes for extension scaffolding.

Q63: Why not parallel process by default?
A63: Sequential dependencies improve deterministic context flow.

Q64: Why use Chroma collections split by concern?
A64: Separation simplifies query intent and retention policy.

Q65: Why lessons in JSON and not DB?
A65: Simplicity and transparency for quick iteration.

Q66: Why optional HITL?
A66: Different teams need different governance levels.

Q67: Why not force strict JSON output now?
A67: Current implementation prioritizes flexibility over strict schemas.

Q68: Why is QA textual pass/fail parsing simple?
A68: It is intentionally lightweight and easy to evolve.

Q69: Why not include Open Interpreter by default?
A69: It is listed as roadmap due to control and safety considerations.

Q70: Why keep UI separate?
A70: Clean separation enables backend-only and UI-assisted modes.

### 28.8 Integration FAQ

Q71: Can I integrate GitHub automation?
A71: Yes, with additional tool hooks.

Q72: Can I integrate Jira?
A72: Yes, add a task sync tool and workflow mapping.

Q73: Can I integrate Slack instead of Telegram?
A73: Yes, via notification backend extensions.

Q74: Can I use a remote vector DB?
A74: Yes, by replacing local memory adapter implementation.

Q75: Can I split one factory into multiple domains?
A75: Yes, create domain-specific configs and routing logic.

Q76: Can I version agent prompts?
A76: Yes, store prompt templates in versioned config files.

Q77: Can I add environment-specific configs?
A77: Yes, use per-env YAML overlays.

Q78: Can I run this as a service?
A78: Yes, wrap backend in an API service layer.

Q79: Can I support multi-user sessions?
A79: Yes, add user-scoped memory and session keys.

Q80: Can I stream intermediate status?
A80: Yes, expose event hooks from factory stages.

### 28.9 Documentation FAQ

Q81: Why is this README long?
A81: It acts as a complete project handbook and operations guide.

Q82: How often should docs be updated?
A82: Every meaningful architecture or workflow change.

Q83: How to document a new module?
A83: Add purpose, interfaces, examples, and failure modes.

Q84: How to keep docs accurate?
A84: Tie docs updates to validation checks in each change cycle.

Q85: Should command outputs be included?
A85: Include representative outputs when they improve troubleshooting.

Q86: Should roadmaps stay in README?
A86: Keep concise roadmap here, move detailed planning to dedicated docs if needed.

Q87: How to reduce doc drift?
A87: Add checklist item in PR template: docs updated.

Q88: Should architecture diagrams be included?
A88: Yes, if maintainable and updated with code changes.

Q89: Should FAQ include edge cases?
A89: Yes, especially repeated operator pain points.

Q90: Is a changelog needed?
A90: Recommended for long-lived projects.

### 28.10 Future Scope FAQ

Q91: Will FE/BE specialist agents be added?
A91: Planned extension point.

Q92: Will deterministic QA be added?
A92: Recommended next milestone.

Q93: Will advanced RAG be added?
A93: Planned with Haystack/RAGFlow candidates.

Q94: Will local fine-tuning be supported?
A94: Planned as optional pipeline via tools like Unsloth.

Q95: Will voice control be added?
A95: PRD notes this as future capability.

Q96: Will policy guardrails be expanded?
A96: Recommended for production hardening.

Q97: Will CI templates be included?
A97: Good candidate for future enhancement.

Q98: Will artifact packaging be automated?
A98: Possible via release scripts.

Q99: Will memory pruning automation be added?
A99: Recommended as data volume grows.

Q100: Is this production-ready today?
A100: It is a strong local foundation with clear extension points for production hardening.

## 29. Example Prompts Library

Use these prompts to test different build styles and failure/retry behavior.

### 29.1 Product-Focused Prompts

1. Build a local expense tracker with categories, CSV export, and monthly charts.
2. Build a local markdown note app with tags and fuzzy search.
3. Build a local CRM mini-dashboard with contacts and interaction logs.
4. Build a local habit tracker with daily streak analytics.
5. Build a local inventory manager with reorder alerts.
6. Build a local student attendance app with weekly summaries.
7. Build a local project planner with Kanban views.
8. Build a local recipe manager with ingredient filtering.
9. Build a local invoice generator with PDF output.
10. Build a local issue tracker with priority labels.

### 29.2 API-Focused Prompts

11. Build a FastAPI service with CRUD endpoints and validation.
12. Build a Flask API with auth middleware and role checks.
13. Build a REST API with pagination and filtering.
14. Build an API with OpenAPI docs and error schema.
15. Build an API with rate limiting and health checks.
16. Build an API with audit logging and request IDs.
17. Build an API with SQLite persistence and migrations.
18. Build an API with Redis cache fallback stubs.
19. Build an API for task scheduling and status polling.
20. Build an API with webhook signature verification.

### 29.3 Frontend-Focused Prompts

21. Build a React dashboard with role-based views.
22. Build a responsive UI with table filtering and sorting.
23. Build a settings panel with form validation and save state.
24. Build a design system starter with button/input/card primitives.
25. Build a multi-step wizard with progress tracking.
26. Build a report page with chart placeholders and export action.
27. Build a log viewer with severity filters.
28. Build an onboarding flow with contextual tips.
29. Build a local analytics page with date range controls.
30. Build a compact mobile-first admin panel.

### 29.4 QA-Stress Prompts

31. Build with strict type checks and include test stubs.
32. Build with explicit error handling in every route.
33. Build with malformed input handling for all forms.
34. Build with async flows and robust timeout handling.
35. Build with import-path validation and module isolation.
36. Build with schema-first data contracts.
37. Build with retry-safe idempotent endpoints.
38. Build with deterministic seed data scripts.
39. Build with resilience to empty states.
40. Build with graceful failure messages for all major actions.

## 30. Contributor Guide

### 30.1 Contribution Rules

1. Keep changes scoped.
2. Update docs with code changes.
3. Run local validation checks before proposing changes.
4. Preserve current config and orchestration contracts unless intentionally updated.
5. Do not commit secrets.

### 30.2 Pull Request Checklist

- Feature or fix summary is clear.
- README updated when behavior changed.
- Config changes documented.
- Validation commands executed.
- No unrelated files modified.

### 30.3 Suggested Commit Prefixes

| Prefix | Use Case |
|---|---|
| `feat:` | New capability |
| `fix:` | Bug fix |
| `docs:` | Documentation update |
| `refactor:` | Internal code restructuring |
| `chore:` | Tooling, maintenance, housekeeping |

### 30.4 Documentation Maintenance Rules

1. Keep setup instructions at top-level and current.
2. Keep runbook commands copy-paste safe.
3. Keep PRD matrix aligned with implementation state.
4. Keep troubleshooting section based on real failures.
5. Keep FAQ based on actual operator questions.

### 30.5 Long-Term Documentation Plan

Phase 1:
- Keep single README handbook.

Phase 2:
- Split into `docs/` sections:
	- architecture.md
	- runbook.md
	- memory.md
	- training.md
	- troubleshooting.md

Phase 3:
- Auto-generate reference docs from source comments and validation scripts.

### 30.6 Final Notes

Project Nexus is intentionally designed as a local-first, highly extensible base platform.

Current implementation covers the core PRD loops:

1. Prompt -> PRD context -> design -> dev -> QA.
2. Failure -> lesson persistence -> retry.
3. Success -> memory retention -> optional notification.

For production-grade deployment, prioritize:

1. Deterministic QA runners.
2. Stronger HITL gating.
3. Secrets and permission hardening.
4. Richer RAG and memory governance.
5. CI-backed regression validation.

End of handbook.

## Appendix A: Quick Operator One-Liners

Use these one-liners during active development and issue triage.

1. Verify backend imports:
`py -c "import src.factory, core.memory, training.feedback_loop; print('ok')"`

2. Verify frontend checks:
`npm run lint`

3. Verify frontend production build:
`npm run build`

4. Verify models are available:
`ollama list`

5. Run a tiny local model response check:
`ollama run llama3:8b "Respond with exactly: OK"`

6. Bootstrap docs ingestion:
`python -c "from training.ingestion import bootstrap_knowledge; print(bootstrap_knowledge())"`

7. Start backend:
`python main.py`

8. Start frontend:
`npm run dev`

9. Start optional docker services:
`docker compose up -d`

10. Stop optional docker services:
`docker compose down`

## Appendix B: Documentation Change Log Policy

1. Any architecture change must update architecture section.
2. Any workflow change must update pipeline and runbook tables.
3. Any new module must be added to module reference.
4. Any new tool must be added to tool registry documentation.
5. Any persistent schema change must update data contract section.
6. Any new dependency must be reflected in setup guidance.
7. Any recurring error should be added to troubleshooting table.
8. Any feature maturity change should update PRD coverage matrix.
9. Keep examples minimal, copy-paste ready, and validated.
10. Keep this README as the primary operator handbook until docs are split.
