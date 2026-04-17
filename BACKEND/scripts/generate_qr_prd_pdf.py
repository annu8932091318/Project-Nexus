from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem


def parse_markdown_lines(lines: list[str]) -> list[tuple[str, str]]:
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
        elif line[:2].isdigit() and line[2:4] == ". ":
            blocks.append(("number", line[4:].strip()))
        elif line[:1].isdigit() and line[1:3] == ". ":
            blocks.append(("number", line[3:].strip()))
        else:
            blocks.append(("p", line.strip()))
    return blocks


def build_pdf(md_path: Path, pdf_path: Path) -> None:
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=10,
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
        leading=15,
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

    story = []
    lines = md_path.read_text(encoding="utf-8").splitlines()
    blocks = parse_markdown_lines(lines)

    bullet_buffer: list[str] = []
    number_buffer: list[str] = []

    def flush_lists() -> None:
        nonlocal bullet_buffer, number_buffer
        if bullet_buffer:
            items = [ListItem(Paragraph(item, body), leftIndent=6) for item in bullet_buffer]
            story.append(ListFlowable(items, bulletType="bullet", start="circle", leftIndent=16))
            story.append(Spacer(1, 4))
            bullet_buffer = []
        if number_buffer:
            items = [ListItem(Paragraph(item, body), leftIndent=6) for item in number_buffer]
            story.append(ListFlowable(items, bulletType="1", leftIndent=16))
            story.append(Spacer(1, 4))
            number_buffer = []

    for kind, text in blocks:
        if kind not in {"bullet", "number"}:
            flush_lists()

        if kind == "h1":
            story.append(Paragraph(text, h1))
            story.append(Spacer(1, 2))
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
            story.append(Spacer(1, 6))

    flush_lists()

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="QR Scanner App PRD",
        author="Project Nexus",
    )
    doc.build(story)


def main() -> int:
    default_md = Path("workspace/artifacts/qr-scanner-prd.md")
    default_pdf = Path("workspace/artifacts/qr-scanner-prd.pdf")

    md_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_md
    pdf_path = Path(sys.argv[2]) if len(sys.argv) > 2 else default_pdf

    if not md_path.exists():
        print(f"Markdown file not found: {md_path}")
        return 1

    build_pdf(md_path, pdf_path)
    print(f"PDF generated: {pdf_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
