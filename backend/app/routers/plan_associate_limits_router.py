"""
CRUD de límites personalizados por asociado.
Solo SYSADMIN puede acceder.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.company_plan_limits_model import CompanyPlanLimits
from app.models.company_plan_model import CompanyPlan
from app.models.plan_model import Plan
from app.models.company_model import Company
from app.auth.dependencies import require_sysadmin
from app.models.user_model import User
from app.services.plan_limits_service import LIMIT_FIELDS, snapshot_plan_limits

router = APIRouter(prefix="/plan-associate-limits", tags=["PlanAssociateLimits"])


def _ser(cpl: CompanyPlanLimits, company: Company = None, plan: Plan = None) -> dict:
    return {
        "id":                 cpl.id,
        "company_id":         cpl.company_id,
        "company_name":       company.name if company else "—",
        "plan_id":            cpl.plan_id,
        "plan_name":          plan.name if plan else "—",
        "max_users":          cpl.max_users,
        "max_products":       cpl.max_products,
        "max_categories":     cpl.max_categories,
        "max_workers":        cpl.max_workers,
        "max_clients":        cpl.max_clients,
        "max_bodega_items":   cpl.max_bodega_items,
        "max_tasks":          cpl.max_tasks,
        "max_daily_invoices": cpl.max_daily_invoices,
        "max_assets":         cpl.max_assets,
        "is_custom":          cpl.is_custom,
        "notes":              cpl.notes,
        "updated_at":         cpl.updated_at.isoformat() if cpl.updated_at else None,
    }


@router.get("/")
async def list_limits(
    _: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    """Lista todos los snapshots de límites por asociado."""
    result = await db.execute(select(CompanyPlanLimits).order_by(CompanyPlanLimits.company_id))
    rows = result.scalars().all()
    out = []
    for cpl in rows:
        company = await db.get(Company, cpl.company_id)
        plan    = await db.get(Plan,    cpl.plan_id)
        out.append(_ser(cpl, company, plan))
    return out


@router.get("/{company_id}")
async def get_limits_by_company(
    company_id: int,
    _: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    """Devuelve los límites efectivos de un asociado específico."""
    result = await db.execute(
        select(CompanyPlanLimits).where(CompanyPlanLimits.company_id == company_id)
    )
    cpl = result.scalar_one_or_none()
    if not cpl:
        # Si no hay snapshot, intentar generarlo desde el plan activo
        cp_res = await db.execute(
            select(CompanyPlan)
            .where(CompanyPlan.company_id == company_id, CompanyPlan.is_active == True)
            .order_by(CompanyPlan.id.desc())
        )
        cp = cp_res.scalar_one_or_none()
        if not cp:
            raise HTTPException(status_code=404, detail="Este asociado no tiene plan activo ni snapshot registrado")
        await snapshot_plan_limits(company_id, cp.plan_id, db)
        await db.commit()
        result2 = await db.execute(
            select(CompanyPlanLimits).where(CompanyPlanLimits.company_id == company_id)
        )
        cpl = result2.scalar_one_or_none()
        if not cpl:
            raise HTTPException(status_code=404, detail="No se pudo generar el snapshot")

    company = await db.get(Company, cpl.company_id)
    plan    = await db.get(Plan,    cpl.plan_id)
    return _ser(cpl, company, plan)


@router.put("/{company_id}")
async def update_limits(
    company_id: int,
    data: dict,
    _: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Actualiza los límites de un asociado.
    Marca automáticamente is_custom=True si algún límite difiere del plan base.
    """
    result = await db.execute(
        select(CompanyPlanLimits).where(CompanyPlanLimits.company_id == company_id)
    )
    cpl = result.scalar_one_or_none()
    if not cpl:
        raise HTTPException(status_code=404, detail="Snapshot no encontrado. Activa el plan del asociado primero.")

    changed = False
    for field in LIMIT_FIELDS:
        if field in data:
            val = int(data[field])
            if getattr(cpl, field) != val:
                setattr(cpl, field, val)
                changed = True

    if changed:
        cpl.is_custom = True

    if "notes" in data:
        cpl.notes = (data["notes"] or "").strip() or None

    # Permitir resetear a valores del plan base
    if data.get("reset_to_plan"):
        plan = await db.get(Plan, cpl.plan_id)
        if plan:
            for field in LIMIT_FIELDS:
                setattr(cpl, field, getattr(plan, field, -1))
            cpl.is_custom = False

    await db.commit()
    await db.refresh(cpl)
    company = await db.get(Company, cpl.company_id)
    plan    = await db.get(Plan,    cpl.plan_id)
    return _ser(cpl, company, plan)


@router.post("/{company_id}/reset")
async def reset_to_plan(
    company_id: int,
    _: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    """Resetea los límites del asociado a los valores actuales de su plan base."""
    result = await db.execute(
        select(CompanyPlanLimits).where(CompanyPlanLimits.company_id == company_id)
    )
    cpl = result.scalar_one_or_none()
    if not cpl:
        raise HTTPException(status_code=404, detail="Snapshot no encontrado")
    plan = await db.get(Plan, cpl.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan base no encontrado")
    for field in LIMIT_FIELDS:
        setattr(cpl, field, getattr(plan, field, -1))
    cpl.is_custom = False
    cpl.notes = None
    await db.commit()
    await db.refresh(cpl)
    company = await db.get(Company, cpl.company_id)
    return _ser(cpl, company, plan)
