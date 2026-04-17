from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.shared import Inches, Pt


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs" / "paper.md"
TARGET = ROOT / "docs" / "paper.docx"


def flush_paragraph(doc: Document, lines: list[str]) -> None:
    if not lines:
        return
    text = "\n".join(lines).strip()
    if text:
        p = doc.add_paragraph(text)
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(6)
    lines.clear()


def flush_code(doc: Document, lines: list[str]) -> None:
    if not lines:
        return
    p = doc.add_paragraph()
    p.style = "No Spacing"
    run = p.add_run("\n".join(lines))
    run.font.name = "Consolas"
    run.font.size = Pt(9)
    lines.clear()


def add_image(doc: Document, raw: str) -> None:
    match = re.match(r"!\[(.*?)\]\((.*?)\)", raw.strip())
    if not match:
        return
    caption = match.group(1).strip()
    rel_path = match.group(2).strip()
    image_path = (SOURCE.parent / rel_path).resolve()
    if image_path.exists():
        doc.add_picture(str(image_path), width=Inches(6.2))
        cp = doc.add_paragraph(caption)
        cp.alignment = 1
        cp.paragraph_format.space_after = Pt(10)


def build_table(doc: Document, rows: list[list[str]]) -> None:
    if len(rows) < 2:
        return
    table = doc.add_table(rows=1, cols=len(rows[0]))
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    for idx, cell_text in enumerate(rows[0]):
        hdr[idx].text = cell_text.strip()
    for row in rows[1:]:
        if set("".join(row).replace("-", "").replace(" ", "")) == set():
            continue
        cells = table.add_row().cells
        for idx, cell_text in enumerate(row):
            cells[idx].text = cell_text.strip()
    doc.add_paragraph()


def parse_table_line(line: str) -> list[str]:
    return [part.strip() for part in line.strip().strip("|").split("|")]


def main() -> None:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.9)
    section.bottom_margin = Inches(0.9)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)

    normal = doc.styles["Normal"]
    normal.font.name = "宋体"
    normal.font.size = Pt(12)

    current_para: list[str] = []
    current_code: list[str] = []
    current_table: list[list[str]] = []
    in_code = False
    in_table = False

    for raw_line in SOURCE.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()

        if line.startswith("```"):
            if in_table:
                build_table(doc, current_table)
                current_table.clear()
                in_table = False
            flush_paragraph(doc, current_para)
            if in_code:
                flush_code(doc, current_code)
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            current_code.append(line)
            continue

        if line.startswith("|") and line.endswith("|"):
            flush_paragraph(doc, current_para)
            in_table = True
            current_table.append(parse_table_line(line))
            continue

        if in_table:
            build_table(doc, current_table)
            current_table.clear()
            in_table = False

        if not line.strip():
            flush_paragraph(doc, current_para)
            continue

        if line.startswith("# "):
            flush_paragraph(doc, current_para)
            p = doc.add_paragraph()
            p.style = "Title"
            p.add_run(line[2:].strip())
            continue

        if line.startswith("## "):
            flush_paragraph(doc, current_para)
            doc.add_heading(line[3:].strip(), level=1)
            continue

        if line.startswith("### "):
            flush_paragraph(doc, current_para)
            doc.add_heading(line[4:].strip(), level=2)
            continue

        if line.startswith("!["):
            flush_paragraph(doc, current_para)
            add_image(doc, line)
            continue

        current_para.append(line)

    if in_table:
        build_table(doc, current_table)
    flush_paragraph(doc, current_para)
    flush_code(doc, current_code)
    doc.save(TARGET)


if __name__ == "__main__":
    main()
