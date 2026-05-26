"""
CRUD de límites personalizados por asociado + gestión de registros bloqueados por plan.
Solo SYSADMIN puede acceder.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
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
from app.services.downgrade_service import (
    apply_downgrade_blocks,
    get_blocked_summary,
    unblock_records,
)

router = APIRouter(prefix="/plan-associate-limits", tags=["PlanAssociateLimits"])


def _ser(cpl: CompanyPlanLimits, company: Company = None, plan: Plan = None) -> dict:
    row = {
        "id":                    cpl.id,
        "company_id":            cpl.company_id,
        "company_name":          company.name if company else "—",
        "identification_number": company.identification_number if company else "",
        "plan_id":               cpl.plan_id,
        "plan_name":             plan.name if plan else "—",
        "is_custom":             cpl.is_custom,
        "notes":                 cpl.notes,
        "updated_at":            cpl.updated_at.isoformat() if cpl.updated_at else None,
    }
    for f in LIMIT_FIELDS:
        row[f] = getattr(cpl, f, -1)
    row["plan_base"] = {f: getattr(plan, f, -1) for f in LIMIT_FIELDS} if plan else {f: -1 for f in LIMIT_FIELDS}
    return row


@router.get("/")
async def list_limits(
    _: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    # Obtener todas las empresas con plan activo
    all_cp = await db.execute(
        select(CompanyPlan)
        .where(CompanyPlan.is_active == True)
        .order_by(CompanyPlan.company_id)
    )
    active_plans = {cp.company_id: cp.plan_id for cp in all_cp.scalars().all()}

    # Auto-generar snapshots para empresas sin registro
    existing_res = await db.execute(select(CompanyPlanLimits.company_id))
    existing_ids = {r[0] for r in existing_res.fetchall()}

    for company_id, plan_id in active_plans.items():
        if company_id not in existing_ids:
            await snapshot_plan_limits(company_id, plan_id, db)

    if set(active_plans.keys()) - existing_ids:
        await db.commit()

    # Devolver todos los registros ordenados por empresa
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
    result = await db.execute(
        select(CompanyPlanLimits).where(CompanyPlanLimits.company_id == company_id)
    )
    cpl = result.scalar_one_or_none()
    if not cpl:
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
    Marca is_custom=True si algún límite difiere del plan base.
    Si se reducen límites, aplica downgrade automático.
    """
    result = await db.execute(
        select(CompanyPlanLimits).where(CompanyPlanLimits.company_id == company_id)
    )
    cpl = result.scalar_one_or_none()
    if not cpl:
        raise HTTPException(status_code=404, detail="Snapshot no encontrado. Activa el plan del asociado primero.")

    changed = False
    reduced = False
    for field in LIMIT_FIELDS:
        if field in data:
            val = int(data[field])
            old_val = getattr(cpl, field, -1)
            if old_val != val:
                if val != -1 and (old_val == -1 or val < old_val):
                    reduced = True
                setattr(cpl, field, val)
                changed = True

    if changed:
        cpl.is_custom = True

    if "notes" in data:
        cpl.notes = (data["notes"] or "").strip() or None

    if data.get("reset_to_plan"):
        plan = await db.get(Plan, cpl.plan_id)
        if plan:
            for field in LIMIT_FIELDS:
                old_val = getattr(cpl, field, -1)
                new_val = getattr(plan, field, -1)
                if new_val != -1 and (old_val == -1 or new_val < old_val):
                    reduced = True
                setattr(cpl, field, new_val)
            cpl.is_custom = False

    await db.commit()
    await db.refresh(cpl)

    blocked_summary = {}
    if reduced:
        blocked_summary = await apply_downgrade_blocks(company_id, db)

    company = await db.get(Company, cpl.company_id)
    plan    = await db.get(Plan,    cpl.plan_id)
    return {**_ser(cpl, company, plan), "blocked_summary": blocked_summary}


@router.post("/{company_id}/reset")
async def reset_to_plan(
    company_id: int,
    _: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CompanyPlanLimits).where(CompanyPlanLimits.company_id == company_id)
    )
    cpl = result.scalar_one_or_none()
    if not cpl:
        raise HTTPException(status_code=404, detail="Snapshot no encontrado")
    plan = await db.get(Plan, cpl.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan base no encontrado")

    reduced = False
    for field in LIMIT_FIELDS:
        old_val = getattr(cpl, field, -1)
        new_val = getattr(plan, field, -1)
        if new_val != -1 and (old_val == -1 or new_val < old_val):
            reduced = True
        setattr(cpl, field, new_val)
    cpl.is_custom = False
    cpl.notes = None
    await db.commit()
    await db.refresh(cpl)

    blocked_summary = {}
    if reduced:
        blocked_summary = await apply_downgrade_blocks(company_id, db)

    company = await db.get(Company, cpl.company_id)
    return {**_ser(cpl, company, plan), "blocked_summary": blocked_summary}


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS DE DESBLOQUEO MANUAL (SYSADMIN)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{company_id}/blocked")
async def get_blocked(
    company_id: int,
    _: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    """Lista todos los registros bloqueados por plan para el asociado."""
    summary = await get_blocked_summary(company_id, db)
    total = sum(len(v) for v in summary.values())
    return {"company_id": company_id, "total_blocked": total, "resources": summary}


@router.post("/{company_id}/unblock")
async def unblock_resource(
    company_id: int,
    data: dict = Body(...),
    _: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Desbloquea registros específicos de un recurso para el asociado.
    Body: { "resource": "users", "ids": [1, 2, 3] }

    Recursos válidos: users, pos_waiters, products, categories,
                      workers, clients, bodega_items, assets
    """
    resource = data.get("resource")
    ids = data.get("ids", [])

    if not resource:
        raise HTTPException(status_code=400, detail="Campo 'resource' requerido")
    if not ids or not isinstance(ids, list):
        raise HTTPException(status_code=400, detail="Campo 'ids' debe ser una lista de IDs")

    result = await unblock_records(company_id, resource, [int(i) for i in ids], db)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return {
        "message":   f"{len(result['unblocked'])} registro(s) desbloqueado(s) correctamente",
        "resource":  resource,
        "unblocked": result["unblocked"],
    }


@router.post("/{company_id}/apply-downgrade")
async def force_downgrade(
    company_id: int,
    _: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Fuerza la aplicación de bloqueos según los límites actuales del plan.
    Útil si se cambiaron límites manualmente o para recalcular.
    """
    blocked_summary = await apply_downgrade_blocks(company_id, db)
    total = sum(len(v) for v in blocked_summary.values())
    return {
        "message":         f"Downgrade aplicado. {total} registro(s) bloqueado(s).",
        "blocked_summary": blocked_summary,
    }
