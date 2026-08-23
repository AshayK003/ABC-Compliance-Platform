"""File deliverables for reports: PDF (pdf-studio, cypher theme) and Excel (openpyxl).

Builds real downloads from the same computed preview data that powers the
JSON responses, so numbers in files always match the on-screen report.
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any

import matplotlib
matplotlib.use("Agg")  # headless servers

from src.models.base import Centre


def _fmt(value: Any) -> Any:
    """Make values spreadsheet/serialisation friendly."""
    if isinstance(value, float):
        return round(value, 2)
    return value


def build_excel(
    template_name: str,
    headers: list[str],
    rows: list[list[Any]],
    summary: dict[str, Any] | None = None,
) -> bytes:
    import openpyxl
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Report"

    # Title row
    ws.cell(row=1, column=1, value=template_name).font = Font(bold=True, size=14)
    ws.cell(row=2, column=1, value=f"Generated {datetime.now().strftime('%d %b %Y %H:%M')}").font = Font(italic=True, size=10)

    r = 4
    if summary:
        for k, v in summary.items():
            ws.cell(row=r, column=1, value=k).font = Font(bold=True)
            ws.cell(row=r, column=2, value=_fmt(v))
            r += 1
        r += 1

    # Header row — teal accent fill to match the app's primary colour
    header_fill = PatternFill(start_color="FF29A195", end_color="FF29A195", fill_type="solid")
    for c, h in enumerate(headers, 1):
        cell = ws.cell(row=r, column=c, value=h)
        cell.font = Font(bold=True, color="FFFFFFFF")
        cell.fill = header_fill

    for row in rows:
        r += 1
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=_fmt(v))

    # Auto-fit column widths (bounded)
    for c in range(1, len(headers) + 1):
        width = max(len(str(h)) for h in [headers[c - 1]]) + 4
        ws.column_dimensions[get_column_letter(c)].width = min(max(width, 12), 40)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def build_pdf(
    template_name: str,
    headers: list[str],
    rows: list[list[Any]],
    summary: dict[str, Any] | None = None,
    centre_map: dict[str, Centre] | None = None,
) -> bytes:
    from pdf_studio import Document

    doc = Document(theme="cypher")
    doc.set_header(f"{template_name} | Page {{page}} of {{total}}")
    doc.add_heading(template_name, level=0)
    doc.add_paragraph(f"Generated {datetime.now().strftime('%d %B %Y, %H:%M UTC')}")

    if summary:
        doc.add_kpi_row([
            {"label": k.replace("_", " ").title(), "value": str(_fmt(v))}
            for k, v in summary.items()
        ])

    if rows:
        table_data = [headers] + [[_fmt(v) for v in row] for row in rows]
        doc.add_table(table_data, caption=f"{len(rows)} records")

    # pdf-studio's render() takes a filesystem path; render to a temp file
    # and return the bytes.
    import os
    import tempfile

    fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    try:
        doc.render(tmp_path)
        with open(tmp_path, "rb") as f:
            return f.read()
    finally:
        os.remove(tmp_path)


def chart_png(labels: list[str], values: list[int], title: str) -> bytes:
    """Render a bar chart as PNG bytes via matplotlib."""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(labels, values, color="#29A195")
    ax.set_title(title)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    return buf.getvalue()
