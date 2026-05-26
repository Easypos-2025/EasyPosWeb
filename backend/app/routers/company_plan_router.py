from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from datetime import date, datetime

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.company_plan_model import CompanyPlan
from app.models.plan_model import Plan
from app.models.role_model import Role
from app.models.user_model import User as UserModel
from app.models.product_model import Product
from app.models.product_category_model import ProductCategory
from app.models.supply_item_model import SupplyItem
from app.models.client_model import Client
from app.services.plan_limits_service import LIMIT_FIELDS, LIMIT_LABELS, snapshot_plan_limits, get_limits
from app.services.downgrade_service import apply_downgrade_blocks, preview_downgrade_blocks

router = APIRouter(prefix="/company-plan", tags=["CompanyPlan"])


async def _is_system(current_user, db: AsyncSession) -> bool:
    role = await db.get(Role, current_user.role_id)
    return role.is_system if role else False


@router.get("/{company_id}")
async def get_company_plan(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(CompanyPlan)
        .where(CompanyPlan.company_id == company_id, CompanyPlan.is_active == True)
        .order_by(CompanyPlan.id.desc())
    )
    cp = result.scalar_one_or_none()
    if not cp:
        return {"plan_name": "Sin plan", "expiration_date": None, "is_free": False}

    plan = await db.get(Plan, cp.plan_id)
    exp = cp.expiration_date
    is_free = (plan.price == 0) if plan else False
    return {
        "plan_name":       plan.name if plan else "Desconocido",
        "plan_id":         cp.plan_id,
        "start_date":      cp.start_date.isoformat() if cp.start_date else None,
        "expiration_date": exp.isoformat() if exp else None,
        "is_free":         is_free,
        "is_active":       cp.is_active,
    }


@router.get("/my-plan-info")
async def my_plan_info(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Retorna plan activo + límites + uso actual para el asociado autenticado."""
    cid = current_user.company_id
    if not cid:
        raise HTTPException(status_code=400, detail="Usuario sin empresa asignada")

    # Plan activo
    cp_res = await db.execute(
        select(CompanyPlan)
        .where(CompanyPlan.company_id == cid, CompanyPlan.is_active == True)
        .order_by(CompanyPlan.id.desc())
    )
    cp = cp_res.scalar_one_or_none()
    plan_name = "Sin plan"
    expiration_date = None
    if cp:
        plan = await db.get(Plan, cp.plan_id)
        plan_name = plan.name if plan else "Desconocido"
        expiration_date = cp.expiration_date.isoformat() if cp.expiration_date else None

    limits = await get_limits(cid, db)

    # Contar uso actual de los recursos principales
    async def _count(model, *filters):
        stmt = select(func.count()).select_from(model).where(model.company_id == cid, *filters)
        return (await db.execute(stmt)).scalar() or 0

    counts = {
        "max_users":      await _count(UserModel),
        "max_products":   await _count(Product,  Product.is_active == 1),
        "max_categories": await _count(ProductCategory, ProductCategory.is_active == 1),
        "max_clients":    await _count(Client),
    }
    # Roles (no tienen company_id en el modelo base, usar query directa)
    role_count = (await db.execute(
        select(func.count()).select_from(Role)
        .where(Role.company_id == cid, Role.is_system == False)
    )).scalar() or 0
    counts["max_roles"] = role_count

    items = []
    for field in LIMIT_FIELDS:
        max_val = limits.get(field, -1)
        current = counts.get(field)
        items.append({
            "field":   field,
            "label":   LIMIT_LABELS.get(field, field),
            "max":     max_val,
            "current": current,
        })

    return {
        "plan_name":       plan_name,
        "expiration_date": expiration_date,
        "items":           items,
    }


@router.get("/my-downgrade-preview")
async def my_downgrade_preview(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Preview accesible para cualquier usuario autenticado (solo su propia empresa)."""
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="Usuario sin empresa asignada")
    new_plan = await db.get(Plan, plan_id)
    if not new_plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    new_limits = {f: getattr(new_plan, f, -1) for f in LIMIT_FIELDS}
    preview = await preview_downgrade_blocks(current_user.company_id, new_limits, db)
    total_affected = sum(v["count"] for v in preview.values())
    return {
        "plan_id":        plan_id,
        "plan_name":      new_plan.name,
        "affected_total": total_affected,
        "details":        preview,
    }


@router.get("/{company_id}/downgrade-preview")
async def downgrade_preview(
    company_id: int,
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Calcula qué registros se bloquearían si se cambia al plan indicado.
    No modifica la BD. Usar antes de confirmar el cambio.
    """
    if not await _is_system(current_user, db):
        raise HTTPException(status_code=403, detail="Solo SYSADMIN puede consultar este endpoint")

    new_plan = await db.get(Plan, plan_id)
    if not new_plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    new_limits = {f: getattr(new_plan, f, -1) for f in LIMIT_FIELDS}
    preview = await preview_downgrade_blocks(company_id, new_limits, db)

    total_affected = sum(v["count"] for v in preview.values())
    return {
        "plan_id":        plan_id,
        "plan_name":      new_plan.name,
        "affected_total": total_affected,
        "details":        preview,
    }


@router.post("/{company_id}")
async def assign_plan(
    company_id: int,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Asigna o cambia el plan de un asociado.
    Si el nuevo plan tiene límites menores, aplica downgrade automático.
    """
    if not await _is_system(current_user, db):
        raise HTTPException(status_code=403, detail="Solo SYSADMIN puede asignar planes")

    # Guardar límites actuales antes del cambio para detectar downgrade
    old_limits = await get_limits(company_id, db)

    await db.execute(
        update(CompanyPlan)
        .where(CompanyPlan.company_id == company_id)
        .values(is_active=False)
    )

    exp_str = data.get("expiration_date")
    exp = date.fromisoformat(exp_str) if exp_str else None

    cp = CompanyPlan(
        company_id=company_id,
        plan_id=data["plan_id"],
        expiration_date=exp,
        is_active=True,
    )
    db.add(cp)
    await db.flush()  # necesitamos el nuevo plan_id antes del snapshot

    # Actualizar snapshot de límites con el nuevo plan
    await snapshot_plan_limits(company_id, data["plan_id"], db)
    await db.commit()

    # Detectar si es downgrade en algún campo de conteo y aplicar bloqueos
    new_plan = await db.get(Plan, data["plan_id"])
    new_limits = {f: getattr(new_plan, f, -1) for f in LIMIT_FIELDS}

    is_downgrade = any(
        old_limits.get(f, -1) != -1 and
        new_limits.get(f, -1) != -1 and
        new_limits.get(f, -1) < old_limits.get(f, -1)
        for f in LIMIT_FIELDS
    ) or any(
        old_limits.get(f, -1) == -1 and new_limits.get(f, -1) != -1
        for f in LIMIT_FIELDS
    )

    blocked_summary = {}
    if is_downgrade:
        blocked_summary = await apply_downgrade_blocks(company_id, db)

    return {
        "message":         "Plan asignado correctamente",
        "plan_name":       new_plan.name if new_plan else "",
        "expiration_date": cp.expiration_date.isoformat() if cp.expiration_date else None,
        "downgrade_applied": bool(blocked_summary),
        "blocked_summary": blocked_summary,
    }
