"""
Servicio centralizado de validación de límites de plan por asociado.

Orden de prioridad:
  1. company_plan_limits (snapshot + posibles overrides personalizados)
  2. plans (fallback si no existe snapshot — asociados anteriores a esta feature)
"""
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.company_plan_limits_model import CompanyPlanLimits
from app.models.company_plan_model import CompanyPlan
from app.models.plan_model import Plan


LIMIT_FIELDS = [
    "max_users", "max_products", "max_categories", "max_workers",
    "max_clients", "max_bodega_items", "max_tasks", "max_daily_invoices", "max_assets",
]

LIMIT_LABELS = {
    "max_users":          "usuarios",
    "max_products":       "productos",
    "max_categories":     "categorías",
    "max_workers":        "trabajadores",
    "max_clients":        "clientes",
    "max_bodega_items":   "artículos de bodega",
    "max_tasks":          "tareas activas",
    "max_daily_invoices": "facturas diarias",
    "max_assets":         "activos",
}


async def get_limits(company_id: int, db: AsyncSession) -> dict:
    """
    Devuelve el dict de límites efectivos para la empresa.
    Prioriza company_plan_limits; si no existe usa plans directamente.
    """
    result = await db.execute(
        select(CompanyPlanLimits).where(CompanyPlanLimits.company_id == company_id)
    )
    cpl = result.scalar_one_or_none()
    if cpl:
        return {f: getattr(cpl, f) for f in LIMIT_FIELDS}

    # Fallback: leer del plan directamente
    cp_res = await db.execute(
        select(CompanyPlan)
        .where(CompanyPlan.company_id == company_id, CompanyPlan.is_active == True)
        .order_by(CompanyPlan.id.desc())
    )
    cp = cp_res.scalar_one_or_none()
    if not cp:
        return {f: 1 if f == "max_users" else -1 for f in LIMIT_FIELDS}
    plan = await db.get(Plan, cp.plan_id)
    if not plan:
        return {f: 1 if f == "max_users" else -1 for f in LIMIT_FIELDS}
    return {f: getattr(plan, f, -1) for f in LIMIT_FIELDS}


async def check_limit(company_id: int, field: str, model, db: AsyncSession,
                      extra_filters: list = None) -> None:
    """
    Verifica si la empresa puede crear un registro más del tipo indicado.
    Lanza HTTPException 403 si el límite está alcanzado.

    Args:
        company_id: ID de la empresa.
        field: nombre del campo en LIMIT_FIELDS (e.g. "max_products").
        model: modelo SQLAlchemy sobre el que se hace el count.
        db: sesión de BD.
        extra_filters: filtros adicionales para el count (e.g. filtrar por fecha para invoices).
    """
    limits = await get_limits(company_id, db)
    max_val = limits.get(field, -1)
    if max_val == -1:
        return  # ilimitado

    stmt = select(func.count()).select_from(model).where(model.company_id == company_id)
    if extra_filters:
        for f in extra_filters:
            stmt = stmt.where(f)
    current = (await db.execute(stmt)).scalar() or 0

    if current >= max_val:
        label = LIMIT_LABELS.get(field, field)
        raise HTTPException(
            status_code=403,
            detail=f"Límite de {max_val} {label} alcanzado en tu plan. Actualiza tu plan para agregar más."
        )


async def snapshot_plan_limits(company_id: int, plan_id: int, db: AsyncSession) -> None:
    """
    Crea o actualiza el snapshot de límites para la empresa.
    Se llama al activar/renovar/cambiar plan (desde payment_router).
    Si el registro ya existe y is_custom=True, NO lo sobreescribe.
    """
    plan = await db.get(Plan, plan_id)
    if not plan:
        return

    result = await db.execute(
        select(CompanyPlanLimits).where(CompanyPlanLimits.company_id == company_id)
    )
    existing = result.scalar_one_or_none()

    if existing and existing.is_custom:
        # Solo actualizamos plan_id para tener la referencia correcta
        existing.plan_id = plan_id
        return

    values = {f: getattr(plan, f, -1) for f in LIMIT_FIELDS}

    if existing:
        existing.plan_id = plan_id
        for f, v in values.items():
            setattr(existing, f, v)
        existing.is_custom = False
    else:
        db.add(CompanyPlanLimits(
            company_id=company_id,
            plan_id=plan_id,
            is_custom=False,
            **values,
        ))
