"""File deliverables for reports: PDF (pdf-studio, cypher theme) and Excel (openpyxl).

Builds real downloads from the same computed preview data that powers the
JSON responses, so numbers in files always match the on-screen report.
"""
from __future__ import annotations

import io
from datetime import UTC, datetime
from typing import Any


def _fmt(value: Any) -> Any:
    """Make values spreadsheet/serialisation friendly."""
    if isinstance(value, float):
        return round(value, 2)
    return value


def _safe_cell(value: Any) -> Any:
    """Neutralise CSV/Excel formula injection: strings starting with
    =,+,-,@ (or a tab/CR) execute on open. Prefixing with a single quote
    keeps the visible text identical while forcing text interpretation."""
    value = _fmt(value)
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
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
    assert ws is not None  # a fresh workbook always has an active sheet
    ws.title = "Report"

    # Title row
    ws.cell(row=1, column=1, value=_safe_cell(template_name)).font = Font(bold=True, size=14)
    ws.cell(row=2, column=1, value=f"Generated {datetime.now(UTC).strftime('%d %b %Y %H:%M UTC')}").font = Font(italic=True, size=10)

    r = 4
    if summary:
        for k, v in summary.items():
            ws.cell(row=r, column=1, value=_safe_cell(k)).font = Font(bold=True)
            ws.cell(row=r, column=2, value=_safe_cell(v))
            r += 1
        r += 1

    # Header row — teal accent fill to match the app's primary colour
    header_fill = PatternFill(start_color="FF29A195", end_color="FF29A195", fill_type="solid")
    for c, h in enumerate(headers, 1):
        cell = ws.cell(row=r, column=c, value=_safe_cell(h))
        cell.font = Font(bold=True, color="FFFFFFFF")
        cell.fill = header_fill

    for row in rows:
        r += 1
        for c, v in enumerate(row, 1):
            ws.cell(row=r, column=c, value=_safe_cell(v))

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
) -> bytes:
    from pdf_studio import Document

    doc = Document(theme="cypher")
    doc.set_header(f"{template_name} | Page {{page}} of {{total}}")
    doc.add_heading(template_name, level=0)
    doc.add_paragraph(f"Generated {datetime.now(UTC).strftime('%d %B %Y, %H:%M UTC')}")

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
