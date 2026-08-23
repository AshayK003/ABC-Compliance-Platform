from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import TokenPayload, get_current_user, require_role
from src.database import get_db
from src.models.base import Allocation, Centre, Expense, Grant, Inspection, Surgery
from src.reports.exporters import _fmt, build_excel, build_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


# ─── Report Templates ───

class ReportTemplate(BaseModel):
    id: str
    name: str
    code: str
    icon: str
    color: str


# Static report templates (could be moved to DB later)
REPORT_TEMPLATES = [
    {"id": "TMPL-001", "name": "Monthly Compliance", "code": "TMPL-001", "icon": "summarize", "color": "primary"},
    {"id": "TMPL-042", "name": "Surgery Trends", "code": "TMPL-042", "icon": "trending_up", "color": "secondary"},
    {"id": "TMPL-108", "name": "Inspection Summary", "code": "TMPL-108", "icon": "plagiarism", "color": "tertiary"},
    {"id": "TMPL-205", "name": "Financial Audit", "code": "TMPL-205", "icon": "account_balance", "color": "error"},
]


@router.get("/templates", response_model=list[ReportTemplate])
async def list_report_templates(
    _: TokenPayload = Depends(get_current_user),
):
    """Get all available report templates."""
    return REPORT_TEMPLATES


@router.get("/templates/{template_id}", response_model=ReportTemplate)
async def get_report_template(
    template_id: str,
    _: TokenPayload = Depends(get_current_user),
):
    """Get a specific report template by ID."""
    template = next((t for t in REPORT_TEMPLATES if t["id"] == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


# ─── Report Generation ───

class ReportGenerateRequest(BaseModel):
    template_id: str
    date_range: str = "Last 30 Days"
    region: str = "All India"
    metric: str = "Overall Compliance %"
    include_sub_entities: bool = True
    highlight_critical: bool = False
    compare_benchmark: bool = True
    format: str = "json"  # json, excel, pdf


_RANGE_DAYS = {
    "last 7 days": 7,
    "last 30 days": 30,
    "last 90 days": 90,
    "last 6 months": 180,
    "last 1 year": 365,
}


def _range_start(date_range: str) -> datetime | None:
    """Parse the report's date_range label into a real cutoff datetime.

    Returns None for ranges we don't recognise so callers fall back to
    all-time data rather than silently returning an empty report.
    """
    days = _RANGE_DAYS.get(date_range.strip().lower())
    if days is None:
        return None
    return datetime.now() - timedelta(days=days)


class ReportPreviewResponse(BaseModel):
    template_id: str
    template_name: str
    generated_at: str
    date_range: str
    region: str
    metric: str
    data: dict
    preview_data: list


@router.post("/generate", response_model=ReportPreviewResponse)
async def generate_report(
    body: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_role("admin", "vet", "surgeon")),
):
    """Generate a report preview based on template and parameters."""
    # Find template
    template = next((t for t in REPORT_TEMPLATES if t["id"] == body.template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    range_start = _range_start(body.date_range)
    region = (body.region or "").strip()
    region_states = {s.strip().lower() for s in re.split(r"[,;]", region) if s.strip()} \
        if region and region.lower() != "all india" else None

    async def _visible_centres():
        stmt = select(Centre).where(Centre.status == "active")
        if region_states:
            stmt = stmt.where(func.lower(Centre.state).in_(region_states))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    preview_data: list[dict] = []

    if body.template_id == "TMPL-001":  # Monthly Compliance
        centres = await _visible_centres()
        centre_ids = [c.id for c in centres]
        completed_data: dict[str, int] = {}
        total_data: dict[str, int] = {}
        if centre_ids:
            ins_stmt = (
                select(Inspection.centre_id, Inspection.status, func.count(Inspection.id))
                .where(Inspection.centre_id.in_(centre_ids))
                .group_by(Inspection.centre_id, Inspection.status)
            )
            if range_start:
                ins_stmt = ins_stmt.where(Inspection.scheduled_at >= range_start)
            for centre_id, status_val, count in (await db.execute(ins_stmt)).all():
                total_data[centre_id] = total_data.get(centre_id, 0) + count
                if status_val == "completed":
                    completed_data[centre_id] = count

        for centre in centres:
            completed = completed_data.get(centre.id, 0)
            total = total_data.get(centre.id, 0)
            compliance = round((completed / total * 100) if total > 0 else 0, 1)
            preview_data.append({
                "centre_id": centre.id,
                "centre_name": centre.name,
                "centre_code": centre.code,
                "district": centre.district,
                "state": centre.state,
                "compliance_score": compliance,
                "completed_inspections": completed,
                "total_inspections": total,
            })

    elif body.template_id == "TMPL-042":  # Surgery Trends
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_month_start = (
            month_start.replace(month=month_start.month - 1)
            if month_start.month > 1
            else month_start.replace(year=month_start.year - 1, month=12, day=1)
        )

        surgery_stmt = select(Surgery.timestamp).join(Centre, Surgery.centre_id == Centre.id)
        if range_start:
            surgery_stmt = surgery_stmt.where(Surgery.timestamp >= range_start)
        else:
            surgery_stmt = surgery_stmt.where(
                Surgery.timestamp >= prev_month_start,
                Surgery.timestamp < datetime.now(),
            )
        if region_states:
            surgery_stmt = surgery_stmt.where(func.lower(Centre.state).in_(region_states))
        rows = (await db.execute(surgery_stmt)).all()

        monthly_counts: dict[str, int] = {}
        for (ts,) in rows:
            month_key = ts.strftime("%Y-%m")
            monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1

        preview_data = [
            {"month": m, "surgeries": monthly_counts[m]} for m in sorted(monthly_counts.keys())
        ]

    elif body.template_id == "TMPL-108":  # Inspection Summary
        stmt = select(Inspection.status, func.count(Inspection.id))
        if region_states:
            stmt = stmt.join(Centre, Inspection.centre_id == Centre.id).where(
                func.lower(Centre.state).in_(region_states)
            )
        if range_start:
            stmt = stmt.where(Inspection.scheduled_at >= range_start)
        stmt = stmt.group_by(Inspection.status)
        rows = (await db.execute(stmt)).all()
        preview_data = [{"status": status_val, "count": count} for status_val, count in rows]

    elif body.template_id == "TMPL-205":  # Financial Audit
        alloc_rows = (await db.execute(select(Allocation))).scalars().all()
        grant_count = len(set(a.grant_id for a in alloc_rows)) or (
            len((await db.execute(select(Grant.id))).all())
        )
        total_allocated = sum((a.amount for a in alloc_rows), Decimal("0"))

        exp_stmt = select(func.coalesce(func.sum(Expense.amount), 0))
        if range_start:
            exp_stmt = exp_stmt.where(Expense.expense_at >= range_start.date())
        total_expensed = (await db.execute(exp_stmt)).scalar() or Decimal("0")

        utilization = (
            round(float(total_expensed) / float(total_allocated) * 100, 1)
            if float(total_allocated) > 0 else 0.0
        )
        preview_data = [{
            "total_grants": grant_count,
            "total_allocated": float(total_allocated),
            "total_expensed": float(total_expensed),
            "utilization_rate": utilization,
        }]

    return ReportPreviewResponse(
        template_id=template["id"],
        template_name=template["name"],
        generated_at=datetime.now(UTC).isoformat(),
        date_range=body.date_range,
        region=body.region,
        metric=body.metric,
        data={
            "include_sub_entities": body.include_sub_entities,
            "highlight_critical": body.highlight_critical,
            "compare_benchmark": body.compare_benchmark,
        },
        preview_data=preview_data,
    )


# ─── File Exports (PDF via pdf-studio, Excel via openpyxl) ───
@router.post("/export/pdf")
async def export_report_pdf(
    body: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_role("admin", "vet", "surgeon")),
):
    """Render the report as a themed PDF and stream it as a download."""
    from fastapi import Response

    template = next((t for t in REPORT_TEMPLATES if t["id"] == body.template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    preview = await generate_report(body, db, _)
    headers, rows, summary = _tabularize(preview.preview_data)
    pdf_bytes = build_pdf(
        template_name=template["name"],
        headers=headers,
        rows=rows,
        summary=summary,
    )
    filename = f"{body.template_id.lower().replace('-', '_')}_{datetime.now():%Y%m%d}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/export/excel")
async def export_report_excel(
    body: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(require_role("admin", "vet", "surgeon")),
):
    """Render the report as a styled Excel workbook and stream it as a download."""
    from fastapi import Response

    template = next((t for t in REPORT_TEMPLATES if t["id"] == body.template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    preview = await generate_report(body, db, _)
    headers, rows, summary = _tabularize(preview.preview_data)
    xlsx_bytes = build_excel(
        template_name=template["name"],
        headers=headers,
        rows=rows,
        summary=summary,
    )
    filename = f"{body.template_id.lower().replace('-', '_')}_{datetime.now():%Y%m%d}.xlsx"
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _tabularize(preview_data: list[dict]) -> tuple[list[str], list[list[Any]], dict[str, Any] | None]:
    """Convert heterogeneous preview payloads into (headers, rows, summary).

    Single-summary payloads (TMPL-205) become KPI summary rows; list payloads
    become table rows with their keys as headers.
    """
    if not preview_data:
        return ["No data"], [[]], None
    if len(preview_data) == 1 and all(not isinstance(v, (list, dict)) for v in preview_data[0].values()):
        summary = preview_data[0]
        return ["Metric", "Value"], [[k, _fmt(v)] for k, v in summary.items()], summary
    headers = list(preview_data[0].keys())
    rows = [[row.get(h) for h in headers] for row in preview_data]
    return [h.replace("_", " ").title() for h in headers], rows, None


# ─── Year-over-Year Adherence Chart Data ───
@router.get("/charts/yoy-adherence")
async def get_yoy_adherence(
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    """Get year-over-year adherence data for chart."""
    from src.models.base import Centre, Surgery

    current_year = datetime.now().year
    prev_year = current_year - 1

    # Current year surgeries
    curr_stmt = select(Surgery, Centre).join(Centre, Surgery.centre_id == Centre.id).where(
        Surgery.timestamp >= datetime(current_year, 1, 1),
        Surgery.timestamp < datetime(current_year + 1, 1, 1)
    )
    curr_result = await db.execute(curr_stmt)
    curr_surgeries = curr_result.all()

    # Previous year surgeries
    prev_stmt = select(Surgery, Centre).join(Centre, Surgery.centre_id == Centre.id).where(
        Surgery.timestamp >= datetime(prev_year, 1, 1),
        Surgery.timestamp < datetime(current_year, 1, 1)
    )
    prev_result = await db.execute(prev_stmt)
    prev_surgeries = prev_result.all()

    # Group by quarter
    from collections import defaultdict
    curr_quarterly = defaultdict(int)
    for s, c in curr_surgeries:
        quarter = (s.timestamp.month - 1) // 3 + 1
        curr_quarterly[f"Q{quarter}"] += 1

    prev_quarterly = defaultdict(int)
    for s, c in prev_surgeries:
        quarter = (s.timestamp.month - 1) // 3 + 1
        prev_quarterly[f"Q{quarter}"] += 1

    quarters = ["Q1", "Q2", "Q3", "Q4"]
    return {
        "quarters": quarters,
        "current_year": {q: curr_quarterly.get(q, 0) for q in quarters},
        "previous_year": {q: prev_quarterly.get(q, 0) for q in quarters},
    }


# ─── Monthly Fund Disbursement Chart Data ───
@router.get("/charts/monthly-disbursements")
async def get_monthly_disbursements(
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    """Get monthly fund disbursement data for chart."""
    from src.models.base import Allocation

    # Get last 6 months
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    for _ in range(5):
        if month_start.month == 1:
            month_start = month_start.replace(year=month_start.year - 1, month=12)
        else:
            month_start = month_start.replace(month=month_start.month - 1)

    allocs_stmt = select(Allocation).where(Allocation.allocated_at >= month_start)
    allocs_result = await db.execute(allocs_stmt)
    allocations = allocs_result.scalars().all()

    from collections import defaultdict
    monthly = defaultdict(float)
    for alloc in allocations:
        month_key = alloc.allocated_at.strftime("%Y-%m")
        monthly[month_key] += float(alloc.amount)

    sorted_months = sorted(monthly.keys())[-6:]  # Last 6 months
    return {
        "months": sorted_months,
        "amounts": [monthly[m] for m in sorted_months],
    }


# ─── Expense Categories Chart Data ───
@router.get("/charts/expense-categories")
async def get_expense_categories(
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    """Get expense category breakdown for chart."""
    from src.models.base import Expense

    exp_stmt = select(Expense.category, func.sum(Expense.amount)).group_by(Expense.category)
    exp_result = await db.execute(exp_stmt)
    expenses = exp_result.all()

    total = sum(float(e[1]) for e in expenses) if expenses else 1
    return {
        "categories": [
            {
                "category": e[0],
                "amount": float(e[1]),
                "percentage": round(float(e[1]) / total * 100, 1) if total > 0 else 0
            }
            for e in expenses
        ]
    }


# ─── Monthly Surgeries Chart Data ───
@router.get("/charts/monthly-surgeries")
async def get_monthly_surgeries(
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    """Get monthly surgeries data for chart."""
    from src.models.base import Surgery

    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    for _ in range(5):
        if month_start.month == 1:
            month_start = month_start.replace(year=month_start.year - 1, month=12)
        else:
            month_start = month_start.replace(month=month_start.month - 1)

    surg_stmt = select(Surgery).where(Surgery.timestamp >= month_start)
    surg_result = await db.execute(surg_stmt)
    surgeries = surg_result.scalars().all()

    from collections import defaultdict
    monthly = defaultdict(int)
    for s in surgeries:
        month_key = s.timestamp.strftime("%Y-%m")
        monthly[month_key] += 1

    sorted_months = sorted(monthly.keys())
    return {
        "months": sorted_months,
        "counts": [monthly[m] for m in sorted_months],
    }
