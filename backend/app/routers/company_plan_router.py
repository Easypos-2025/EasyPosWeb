from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import date
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.company_plan_model import CompanyPlan
from app.models.plan_model import Plan
from app.models.role_model import Role

router = APIRouter(prefix="/company-plan", tags=["CompanyPlan"])


async def _is_system(current_user, db: AsyncSession) -> bool:
    role = await db.get(Role, current_user.role_id)
    return role.is_system if role else False


@router.get("/{company_id}")
async def get_company_plan(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
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


@router.post("/{company_id}")
async def assign_plan(
    company_id: int,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not await _is_system(current_user, db):
        raise HTTPException(status_code=403, detail="Solo SYSADMIN puede asignar planes")

    await db.execute(update(CompanyPlan).where(CompanyPlan.company_id == company_id).values(is_active=False))

    exp_str = data.get("expiration_date")
    exp = date.fromisoformat(exp_str) if exp_str else None

    cp = CompanyPlan(company_id=company_id, plan_id=data["plan_id"], expiration_date=exp, is_active=True)
    db.add(cp)
    await db.commit()
    await db.refresh(cp)

    plan = await db.get(Plan, cp.plan_id)
    return {
        "message":         "Plan asignado correctamente",
        "plan_name":       plan.name if plan else "",
        "expiration_date": cp.expiration_date.isoformat() if cp.expiration_date else None,
    }
