from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import List

from .models import SkillDefinition, SkillExecutionResult
from .session_store import SkillSession, SkillSessionStore


class SkillExecutor:
    """Generic execution runtime that enforces confirmation-safe workflow."""

    def __init__(self, sessions: SkillSessionStore, artifact_dir: Path):
        self.sessions = sessions
        self.artifact_dir = artifact_dir
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, prompt: str, skill_key: str, skill: SkillDefinition) -> SkillExecutionResult:
        mode = self._detect_mode(prompt)
        assumptions = self._build_assumptions(skill, prompt)
        issues = self._preflight_issues(skill)
        output = self._render_output(
            skill=skill,
            skill_key=skill_key,
            prompt=prompt,
            mode=mode,
            assumptions=assumptions,
            issues=issues,
        )

        artifact_name = self._safe_name(skill.name) + "-draft.md"
        artifact_path = self.artifact_dir / artifact_name
        artifact_path.write_text(output, encoding="utf-8")

        session = SkillSession(
            session_id=str(uuid.uuid4()),
            prompt=prompt,
            skill_key=skill_key,
            status="draft",
            created_at=SkillSessionStore.now_iso(),
            updated_at=SkillSessionStore.now_iso(),
            assumptions=assumptions,
            issues=issues,
            artifacts={"draft": str(artifact_path)},
        )
        self.sessions.save(session)

        return SkillExecutionResult(
            matched_skill=skill_key,
            confidence=1.0,
            mode=mode,
            output=output,
            assumptions=assumptions,
            issues=issues,
            artifacts=session.artifacts,
        )

    def _detect_mode(self, prompt: str) -> str:
        text = prompt.lower()
        if "quick" in text or "быстрый" in text:
            return "quick"
        if "scan" in text or "rescan" in text or "перескан" in text:
            return "scan"
        if "append" in text or "update" in text or "обнов" in text:
            return "append"
        return "new"

    def _build_assumptions(self, skill: SkillDefinition, prompt: str) -> List[str]:
        assumptions: List[str] = []
        if skill.language is None:
            assumptions.append("Language inferred from user prompt.")
        if len(prompt.split()) < 8:
            assumptions.append("Prompt is short; runtime may request clarification for required fields.")
        if not skill.triggers:
            assumptions.append("Skill has no explicit trigger list in frontmatter; description-based routing was used.")
        return assumptions

    def _preflight_issues(self, skill: SkillDefinition) -> List[str]:
        issues: List[str] = []
        raw = skill.path.read_text(encoding="utf-8")

        if "do not" in raw.lower() and "constraints" not in raw.lower():
            issues.append("Skill includes prohibitions but has no explicit Constraints header.")

        if "template" in raw.lower() and "output" not in raw.lower():
            issues.append("Template reference found without explicit Output contract section.")

        return issues

    def _render_output(
        self,
        skill: SkillDefinition,
        skill_key: str,
        prompt: str,
        mode: str,
        assumptions: List[str],
        issues: List[str],
    ) -> str:
        if skill_key.startswith("project-management-kit/"):
            return self._render_project_management_output(skill, skill_key, prompt, mode, assumptions, issues)
        if skill_key.startswith("project-onboarding"):
            return self._render_project_onboarding_output(skill, prompt, mode, assumptions, issues)
        if "report-analyzer" in skill_key:
            return self._render_report_analyzer_output(skill, prompt, mode, assumptions, issues)
        if "retro-pattern-analyzer" in skill_key:
            return self._render_retro_pattern_output(skill, prompt, mode, assumptions, issues)
        if "stakeholder-adapter" in skill_key:
            return self._render_stakeholder_adapter_output(skill, prompt, mode, assumptions, issues)
        if "user-feedback-synthesizer" in skill_key:
            return self._render_feedback_synthesizer_output(skill, prompt, mode, assumptions, issues)
        if "weekly-digest-synthesizer" in skill_key:
            return self._render_weekly_digest_output(skill, prompt, mode, assumptions, issues)
        if "prompt-builder" in skill_key:
            return self._render_prompt_builder_output(skill, prompt, mode, assumptions, issues)
        return self._render_generic_output(skill, prompt, mode, assumptions, issues)

    def _render_generic_output(
        self,
        skill: SkillDefinition,
        prompt: str,
        mode: str,
        assumptions: List[str],
        issues: List[str],
    ) -> str:
        assumption_lines = [f"- {a}" for a in assumptions] or ["- None"]
        issue_lines = [f"- {i}" for i in issues] or ["- None"]
        return "\n".join(
            [
                f"# Skill Execution Draft: {skill.name}",
                "",
                f"- Version: {skill.version}",
                f"- Source: {skill.path}",
                f"- Mode: {mode}",
                "",
                "## Prompt",
                prompt.strip() or "[empty prompt]",
                "",
                "## Execution Plan",
                "1. Validate required inputs from the user against skill instructions.",
                "2. Ask clarification questions only for missing mandatory fields.",
                "3. Generate structured output using the skill contract.",
                "4. Present draft and wait for explicit approval before finalization.",
                "5. Persist approved artifact and execution log.",
                "",
                "## Assumptions",
                *assumption_lines,
                "",
                "## Detected Issues",
                *issue_lines,
                "",
                "## Approval",
                "Status: draft",
                "Action required: Approve, revise, or reject.",
            ]
        )

    def _render_project_management_output(
        self,
        skill: SkillDefinition,
        skill_key: str,
        prompt: str,
        mode: str,
        assumptions: List[str],
        issues: List[str],
    ) -> str:
        phase = str(skill.metadata.get("phase") or "unknown")
        template = str(skill.metadata.get("template") or "not specified")
        output_file = str(skill.metadata.get("output_file") or "artifact.md")
        next_skill_hint = {
            "generate-charter": "generate-risk-register (initial) and generate-project-plan",
            "generate-project-plan": "generate-risk-register (detailed) and generate-comm-plan",
            "generate-plan-fact-report": "generate-closure-report",
            "generate-closure-report": "none (final lifecycle artifact)",
        }.get(skill.name, "follow declared dependencies in SKILL.md")

        return "\n".join(
            [
                f"# PM Skill Draft: {skill.name}",
                "",
                f"- Phase: {phase}",
                f"- Mode: {mode}",
                f"- Template: {template}",
                f"- Target file: {output_file}",
                f"- Skill key: {skill_key}",
                "",
                "## Prompt",
                prompt.strip() or "[empty prompt]",
                "",
                "## Intake Checklist",
                "- Verify required upstream artifacts are present and approved.",
                "- Detect and resolve contradictions before drafting content.",
                "- Ask only minimum clarifying questions needed for mandatory fields.",
                "",
                "## Drafting Workflow",
                "1. Build a normalized input model (goals, scope, dates, owners, constraints).",
                "2. Populate all required sections and placeholders from verified inputs.",
                "3. Flag all assumptions explicitly and keep them auditable.",
                "4. Run checklist validation from skill instructions before presenting.",
                "5. Request approval, then finalize output file and log update recommendation.",
                "",
                "## Dependency Guidance",
                f"- Suggested next skill after approval: {next_skill_hint}",
                "",
                "## Assumptions",
                *([f"- {item}" for item in assumptions] or ["- None"]),
                "",
                "## Detected Issues",
                *([f"- {item}" for item in issues] or ["- None"]),
                "",
                "## Approval",
                "Status: draft",
                "Action required: Approve, revise, or reject.",
            ]
        )

    def _render_project_onboarding_output(
        self,
        skill: SkillDefinition,
        prompt: str,
        mode: str,
        assumptions: List[str],
        issues: List[str],
    ) -> str:
        return "\n".join(
            [
                f"# Onboarding Draft: {skill.name}",
                "",
                f"- Mode: {mode}",
                "- Outputs: context.md, folder-instructions.md, resources/prompts/*",
                "",
                "## Prompt",
                prompt.strip() or "[empty prompt]",
                "",
                "## Interview Plan",
                "1. Collect project basics and current phase goals.",
                "2. Capture constraints, stakeholders, and open questions.",
                "3. Run file-map scan and summarize the workspace structure.",
                "4. Generate context and instruction assets based on project type.",
                "",
                "## Mode Notes",
                "- new: full interview, rules, prompts, and file map.",
                "- quick: minimal interview plus file map and context output.",
                "- scan: refresh only file map section in existing context.",
                "",
                "## Assumptions",
                *([f"- {item}" for item in assumptions] or ["- None"]),
                "",
                "## Detected Issues",
                *([f"- {item}" for item in issues] or ["- None"]),
                "",
                "## Approval",
                "Status: draft",
                "Action required: Approve, revise, or reject.",
            ]
        )

    def _render_report_analyzer_output(
        self,
        skill: SkillDefinition,
        prompt: str,
        mode: str,
        assumptions: List[str],
        issues: List[str],
    ) -> str:
        return "\n".join(
            [
                f"# Report Analyzer Draft: {skill.name}",
                "",
                f"- Mode: {mode}",
                "- Output target: report-summary_<name>_<date>.md",
                "",
                "## Prompt",
                prompt.strip() or "[empty prompt]",
                "",
                "## Extraction Workflow",
                "1. Locate report file (PDF/PPTX) in provided path or uploads.",
                "2. Gather required run preferences: language, focus, and output format.",
                "3. Extract text, metadata, and tabular evidence from the source.",
                "4. Build summary with exact metrics and verbatim insight evidence.",
                "",
                "## Draft Sections",
                "- Report metadata",
                "- Executive summary",
                "- Key figures and data",
                "- Key insights",
                "- Section-by-section outline",
                "",
                "## Assumptions",
                *([f"- {item}" for item in assumptions] or ["- None"]),
                "",
                "## Detected Issues",
                *([f"- {item}" for item in issues] or ["- None"]),
                "",
                "## Approval",
                "Status: draft",
                "Action required: Approve, revise, or reject.",
            ]
        )

    def _render_retro_pattern_output(
        self,
        skill: SkillDefinition,
        prompt: str,
        mode: str,
        assumptions: List[str],
        issues: List[str],
    ) -> str:
        return "\n".join(
            [
                f"# Retro Pattern Draft: {skill.name}",
                "",
                f"- Mode: {mode}",
                "- Output target: retro-patterns-<date>.md",
                "",
                "## Prompt",
                prompt.strip() or "[empty prompt]",
                "",
                "## Analysis Workflow",
                "1. Validate at least two retro files (.md/.txt).",
                "2. Parse sections into went-well, went-wrong, and action buckets.",
                "3. Normalize themes and compute recurrence by sprint.",
                "4. Detect unresolved actions reappearing as future pain points.",
                "",
                "## Report Sections",
                "- Recurring pains with trend direction",
                "- Unresolved action items",
                "- Stable positive patterns",
                "",
                "## Assumptions",
                *([f"- {item}" for item in assumptions] or ["- None"]),
                "",
                "## Detected Issues",
                *([f"- {item}" for item in issues] or ["- None"]),
                "",
                "## Approval",
                "Status: draft",
                "Action required: Approve, revise, or reject.",
            ]
        )

    def _render_stakeholder_adapter_output(
        self,
        skill: SkillDefinition,
        prompt: str,
        mode: str,
        assumptions: List[str],
        issues: List[str],
    ) -> str:
        return "\n".join(
            [
                f"# Stakeholder Adaptation Draft: {skill.name}",
                "",
                f"- Mode: {mode}",
                "- Target audiences: Leadership, Engineering, Client",
                "",
                "## Prompt",
                prompt.strip() or "[empty prompt]",
                "",
                "## Adaptation Workflow",
                "1. Extract source document and detect source language.",
                "2. Confirm requested audiences and key message constraints.",
                "3. Produce audience-specific versions with framing rules:",
                "   - Leadership: decision and impact first",
                "   - Engineering: implementation detail and ownership",
                "   - Client: outcomes, next steps, no internal jargon",
                "",
                "## Delivery",
                "- Return labeled versions in chat.",
                "- Save separate files on user confirmation.",
                "",
                "## Assumptions",
                *([f"- {item}" for item in assumptions] or ["- None"]),
                "",
                "## Detected Issues",
                *([f"- {item}" for item in issues] or ["- None"]),
                "",
                "## Approval",
                "Status: draft",
                "Action required: Approve, revise, or reject.",
            ]
        )

    def _render_feedback_synthesizer_output(
        self,
        skill: SkillDefinition,
        prompt: str,
        mode: str,
        assumptions: List[str],
        issues: List[str],
    ) -> str:
        return "\n".join(
            [
                f"# Feedback Synthesis Draft: {skill.name}",
                "",
                f"- Mode: {mode}",
                "- Output target: feedback-insights-<date>.md",
                "",
                "## Prompt",
                prompt.strip() or "[empty prompt]",
                "",
                "## Synthesis Workflow",
                "1. Read all supported feedback files (.md/.txt/.csv).",
                "2. Extract pain, desire, compliment, and confusion signals.",
                "3. Cluster recurring themes and rank by distinct source count.",
                "4. Attach verbatim evidence and build prioritized insight table.",
                "5. List open questions and weak signals for follow-up research.",
                "",
                "## Assumptions",
                *([f"- {item}" for item in assumptions] or ["- None"]),
                "",
                "## Detected Issues",
                *([f"- {item}" for item in issues] or ["- None"]),
                "",
                "## Approval",
                "Status: draft",
                "Action required: Approve, revise, or reject.",
            ]
        )

    def _render_weekly_digest_output(
        self,
        skill: SkillDefinition,
        prompt: str,
        mode: str,
        assumptions: List[str],
        issues: List[str],
    ) -> str:
        return "\n".join(
            [
                f"# Weekly Digest Draft: {skill.name}",
                "",
                f"- Mode: {mode}",
                "- Output target: weekly-digest-<date>.md",
                "",
                "## Prompt",
                prompt.strip() or "[empty prompt]",
                "",
                "## Digest Workflow",
                "1. Scan provided .md/.txt status files.",
                "2. Extract project-level status, updates, blockers, and actions.",
                "3. Group updates by project and build cross-cutting action table.",
                "4. Summarize overall weekly health and risk hotspots.",
                "",
                "## Assumptions",
                *([f"- {item}" for item in assumptions] or ["- None"]),
                "",
                "## Detected Issues",
                *([f"- {item}" for item in issues] or ["- None"]),
                "",
                "## Approval",
                "Status: draft",
                "Action required: Approve, revise, or reject.",
            ]
        )

    def _render_prompt_builder_output(
        self,
        skill: SkillDefinition,
        prompt: str,
        mode: str,
        assumptions: List[str],
        issues: List[str],
    ) -> str:
        return "\n".join(
            [
                f"# Prompt Builder Draft: {skill.name}",
                "",
                f"- Mode: {mode}",
                "- Output target: prompt-<topic>.md",
                "",
                "## Prompt",
                prompt.strip() or "[empty prompt]",
                "",
                "## Interactive Questionnaire",
                "1. Role",
                "2. Context",
                "3. Main task",
                "4. Input data",
                "5. Output requirements",
                "6. Constraints and tone",
                "7. Optional examples",
                "",
                "## Prompt Assembly",
                "- Build final prompt blocks from validated answers.",
                "- Show final draft and request save confirmation.",
                "",
                "## Assumptions",
                *([f"- {item}" for item in assumptions] or ["- None"]),
                "",
                "## Detected Issues",
                *([f"- {item}" for item in issues] or ["- None"]),
                "",
                "## Approval",
                "Status: draft",
                "Action required: Approve, revise, or reject.",
            ]
        )

    def _safe_name(self, name: str) -> str:
        name = name.lower().strip()
        name = re.sub(r"[^a-z0-9\-_]+", "-", name)
        return re.sub(r"-+", "-", name).strip("-") or "skill"
