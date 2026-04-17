from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer


def generate_prd_assets(requirement: str, artifact_root: Path) -> Tuple[Path, Path]:
    """Generate PRD markdown + PDF artifacts for a requirement prompt."""
    slug = _slugify(requirement)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    artifact_dir = artifact_root / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    md_path = artifact_dir / f"prd-{slug}-{stamp}.md"
    pdf_path = artifact_dir / f"prd-{slug}-{stamp}.pdf"

    content = _build_prd_markdown(requirement)
    md_path.write_text(content, encoding="utf-8")
    _render_pdf_from_markdown(md_path, pdf_path)

    return md_path, pdf_path


def _slugify(text: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    if not normalized:
        return "requirement"
    return normalized[:48]


def _build_prd_markdown(requirement: str) -> str:
    req = requirement.strip() or "[empty requirement]"
    today = datetime.now().strftime("%Y-%m-%d")
    return "\n".join(
        [
            "# Product Requirements Document (PRD)",
            "",
            "## Document Control",
            "- Product: Derived from runtime requirement",
            "- Version: 1.0",
            f"- Date: {today}",
            "- Status: Draft",
            "",
            "## Requirement",
            f"- {req}",
            "",
            "## Problem Statement",
            "Define the user problem, why current solutions are insufficient, and expected business impact.",
            "",
            "## Objectives",
            "1. Deliver a clear, testable scope for implementation.",
            "2. Minimize ambiguity for design, development, and QA.",
            "3. Define measurable success outcomes.",
            "",
            "## Scope",
            "### In Scope",
            "- Core user workflow implementation.",
            "- Essential error handling and edge-case behavior.",
            "- Acceptance-ready documentation for engineering handoff.",
            "",
            "### Out of Scope",
            "- Non-essential phase-2 enhancements.",
            "- Unspecified integrations and unsupported platforms.",
            "",
            "## User Stories",
            "1. As a user, I can complete the primary workflow quickly and reliably.",
            "2. As a user, I receive clear feedback on failures and recovery actions.",
            "3. As a stakeholder, I can verify outcomes using measurable criteria.",
            "",
            "## Functional Requirements",
            "1. System accepts and validates required inputs.",
            "2. System executes the primary workflow with deterministic output.",
            "3. System exposes actionable errors for invalid or missing input.",
            "4. System records key events for troubleshooting and audits.",
            "",
            "## Non-Functional Requirements",
            "- Performance: responsive under expected usage.",
            "- Reliability: graceful degradation on dependency failures.",
            "- Security: validate and sanitize user-provided data.",
            "- Observability: structured logs and traceable artifact output.",
            "",
            "## Success Metrics",
            "- Task completion rate and median time-to-complete.",
            "- Error rate in core workflow.",
            "- User satisfaction and support ticket trend.",
            "",
            "## Acceptance Criteria",
            "1. All in-scope requirements are implemented and testable.",
            "2. QA validation passes on critical scenarios.",
            "3. Documentation and artifacts are generated for release readiness.",
            "",
            "## Risks and Mitigations",
            "- Risk: unclear inputs. Mitigation: up-front validation and guided errors.",
            "- Risk: integration drift. Mitigation: explicit contracts and tests.",
            "- Risk: performance regressions. Mitigation: baseline profiling and guardrails.",
        ]
    )


def _parse_markdown(lines: list[str]) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    for raw in lines:
        line = raw.rstrip("\n")
        if not line.strip():
            blocks.append(("space", ""))
            continue
        if line.startswith("# "):
            blocks.append(("h1", line[2:].strip()))
        elif line.startswith("## "):
            blocks.append(("h2", line[3:].strip()))
        elif line.startswith("### "):
            blocks.append(("h3", line[4:].strip()))
        elif line.startswith("- "):
            blocks.append(("bullet", line[2:].strip()))
        elif re.match(r"^\d+\.\s+", line):
            blocks.append(("number", re.sub(r"^\d+\.\s+", "", line).strip()))
        else:
            blocks.append(("p", line.strip()))
    return blocks


def _render_pdf_from_markdown(md_path: Path, pdf_path: Path) -> None:
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=8,
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1D4ED8"),
        spaceBefore=8,
        spaceAfter=6,
    )
    h3 = ParagraphStyle(
        "H3",
        parent=styles["Heading3"],
        fontSize=12,
        leading=14,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=6,
        spaceAfter=4,
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#111827"),
        spaceAfter=4,
    )

    lines = md_path.read_text(encoding="utf-8").splitlines()
    blocks = _parse_markdown(lines)
    story = []
    bullet_buffer: list[str] = []
    number_buffer: list[str] = []

    def flush_lists() -> None:
        nonlocal bullet_buffer, number_buffer
        if bullet_buffer:
            items = [ListItem(Paragraph(item, body), leftIndent=6) for item in bullet_buffer]
            story.append(ListFlowable(items, bulletType="bullet", start="circle", leftIndent=16))
            story.append(Spacer(1, 3))
            bullet_buffer = []
        if number_buffer:
            items = [ListItem(Paragraph(item, body), leftIndent=6) for item in number_buffer]
            story.append(ListFlowable(items, bulletType="1", leftIndent=16))
            story.append(Spacer(1, 3))
            number_buffer = []

    for kind, text in blocks:
        if kind not in {"bullet", "number"}:
            flush_lists()

        if kind == "h1":
            story.append(Paragraph(text, h1))
        elif kind == "h2":
            story.append(Paragraph(text, h2))
        elif kind == "h3":
            story.append(Paragraph(text, h3))
        elif kind == "p":
            story.append(Paragraph(text, body))
        elif kind == "bullet":
            bullet_buffer.append(text)
        elif kind == "number":
            number_buffer.append(text)
        elif kind == "space":
            story.append(Spacer(1, 5))

    flush_lists()

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="PRD",
        author="Project Nexus",
    )
    doc.build(story)