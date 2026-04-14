import json
from pathlib import Path
from typing import Dict

LESSONS_FILE = Path("data/lessons_learned.json")


def analyze_failure(error_logs: str) -> Dict[str, str]:
    lowered = error_logs.lower()
    if "import" in lowered and "module" in lowered:
        lesson = "Always verify required dependencies and imports before finalizing generated code."
    elif "async" in lowered or "await" in lowered:
        lesson = "Validate async boundaries and ensure awaited coroutines are handled safely."
    elif "type" in lowered:
        lesson = "Add explicit type checks and align interfaces before implementation."
    else:
        lesson = "Reproduce the failure locally, isolate root cause, and update implementation constraints."

    return {
        "error_logs": error_logs,
        "negative_constraint": lesson,
    }


def save_lesson(lesson: Dict[str, str], file_path: Path = LESSONS_FILE) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)

    existing = []
    if file_path.exists():
        try:
            existing = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = []

    existing.append(lesson)
    file_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
