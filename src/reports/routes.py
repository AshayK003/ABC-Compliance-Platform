from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import TokenPayload, get_current_user, require_role
from src.database import get_db
from src.models.base import Allocation, Expense, Grant, Inspection, Surgery

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

    # Build query based on template
    preview_data = []
    
    if body.template_id == "TMPL-001":  # Monthly Compliance
        # Get compliance data per centre
        from src.models.base import Centre, Inspection
        
        centres_stmt = select(Centre).where(Centre.status == "active")
        centres_result = await db.execute(centres_stmt)
        centres = centres_result.scalars().all()
        
        # Get inspection data for compliance calculation
        ins_stmt = (
            select(Inspection.centre_id, Inspection.status, func.count(Inspection.id))
            .where(Inspection.status == "completed")
            .group_by(Inspection.centre_id, Inspection.status)
        )
        ins_result = await db.execute(ins_stmt)
        completed_data = {r[0]: r[2] for r in ins_result.all()}
        
        total_stmt = select(Inspection.centre_id, func.count(Inspection.id)).group_by(Inspection.centre_id)
        total_result = await db.execute(total_stmt)
        total_data = {r[0]: r[1] for r in total_result.all()}
        
        preview_data = []
        for centre in centres:
            completed = completed_data.get(centre.id, 0)
            total = total_data.get(centre.id, 1)
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
        from src.models.base import Surgery, Centre
        
        month_start = datetime.now()
        month_start = month_start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_month_start = month_start.replace(day=1)
        prev_month_start = prev_month_start.replace(month=month_start.month - 1) if month_start.month > 1 else month_start.replace(year=month_start.year - 1, month=12, day=1)
        
        surgery_stmt = select(Surgery, Centre).join(Centre, Surgery.centre_id == Centre.id).where(
            Surgery.timestamp >= prev_month_start,
            Surgery.timestamp < datetime.now()
        )
        surgeries_result = await db.execute(surgery_stmt)
        surgeries = surgeries_result.all()
        
        # Group by month
        from collections import defaultdict
        monthly_counts = defaultdict(int)
        for surgery, centre in surgeries:
            month_key = surgery.timestamp.strftime("%Y-%m")
            monthly_counts[month_key] += 1
        
        sorted_months = sorted(monthly_counts.keys())
        preview_data = [
            {"month": m, "surgeries": monthly_counts[m]} 
            for m in sorted_months
        ]
    
    elif body.template_id == "TMPL-108":  # Inspection Summary
        from src.models.base import Inspection, Centre
        
        ins_stmt = select(Inspection, Centre).join(Centre, Inspection.centre_id == Centre.id)
        ins_result = await db.execute(ins_stmt)
        inspections = ins_result.all()
        
        status_counts = {}
        for ins, centre in inspections:
            if ins.status not in status_counts:
                status_counts[ins.status] = 0
            status_counts[ins.status] += 1
        
        preview_data = [
            {"status": k, "count": v} for k, v in status_counts.items()
        ]
    
    elif body.template_id == "TMPL-205":  # Financial Audit
        from src.models.base import Grant, Allocation, Expense
        
        grants_stmt = select(Grant)
        grants_result = await db.execute(grants_stmt)
        grants = grants_result.scalars().all()
        
        total_allocated = 0
        total_expensed = 0
        for grant in grants:
            allocs_stmt = select(Allocation).where(Allocation.grant_id == grant.id)
            allocs_result = await db.execute(allocs_stmt)
            allocs = allocs_result.scalars().all()
            for alloc in allocs:
                total_allocated += alloc.amount
                exp_stmt = select(func.sum(Expense.amount)).where(Expense.allocation_id == alloc.id)
                exp_result = await db.execute(exp_stmt)
                total_expensed += exp_result.scalar() or 0
        
        preview_data = [{
            "total_grants": len(grants),
            "total_allocated": float(total_allocated),
            "total_expensed": float(total_expensed),
            "utilization_rate": round((float(total_expensed) / float(total_allocated) * 100) if total_allocated > 0 else 0, 1)
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


# ─── Year-over-Year Adherence Chart Data ───
@router.get("/charts/yoy-adherence")
async def get_yoy_adherence(
    db: AsyncSession = Depends(get_db),
    _: TokenPayload = Depends(get_current_user),
):
    """Get year-over-year adherence data for chart."""
    from src.models.base import Surgery, Centre
    
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