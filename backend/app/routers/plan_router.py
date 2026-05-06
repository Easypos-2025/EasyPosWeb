from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.plan_model import Plan
from app.models.plan_price_model import PlanPrice
from app.models.role_model import Role

router = APIRouter(prefix="/plans", tags=["Plans"])


async def _require_sysadmin(current_user, db: AsyncSession):
    role = await db.get(Role, current_user.role_id)
    if not role or not role.is_system:
        raise HTTPException(status_code=403, detail="Solo SYSADMIN")


def _validate(data):
    if not data.get("name", "").strip():
        raise HTTPException(status_code=400, detail="El nombre del plan es obligatorio")


def _fields(data):
    return {
        "name":           data.get("name", "").strip(),
        "description":    data.get("description", ""),
        "max_users":      int(data.get("max_users", 1)),
        "max_products":   int(data.get("max_products", -1)),
        "max_categories": int(data.get("max_categories", -1)),
        "price":          float(data.get("price", 0)),
        "is_active":      bool(data.get("is_active", True)),
    }


def _serialize(p):
    return {"id": p.id, "name": p.name, "description": p.description,
            "max_users": p.max_users, "max_products": p.max_products,
            "max_categories": p.max_categories, "price": p.price, "is_active": p.is_active}


@router.get("/")
async def get_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Plan).order_by(Plan.id))
    return [_serialize(p) for p in result.scalars().all()]


@router.get("/with-prices")
async def get_plans_with_prices(currency: str = "COP", db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Plan).where(Plan.is_active == True).order_by(Plan.price))
    plans = result.scalars().all()
    items = []
    for p in plans:
        r = await db.execute(select(PlanPrice).where(PlanPrice.plan_id == p.id,
                                                      PlanPrice.currency_code == currency.upper(),
                                                      PlanPrice.is_active == True))
        pp = r.scalar_one_or_none()
        data = _serialize(p)
        data["price_in_currency"] = pp.amount if pp else p.price
        data["currency"] = currency.upper()
        items.append(data)
    return items


@router.get("/{plan_id}/prices")
async def get_plan_prices(plan_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    await _require_sysadmin(current_user, db)
    result = await db.execute(select(PlanPrice).where(PlanPrice.plan_id == plan_id))
    return [{"id": pp.id, "currency_code": pp.currency_code, "amount": pp.amount, "is_active": pp.is_active}
            for pp in result.scalars().all()]


@router.put("/{plan_id}/prices/{currency_code}")
async def upsert_plan_price(plan_id: int, currency_code: str, data: dict = Body(...),
                             db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    await _require_sysadmin(current_user, db)
    plan = await db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    amount = float(data.get("amount", 0))
    if amount < 0:
        raise HTTPException(status_code=400, detail="El precio no puede ser negativo")
    currency = currency_code.upper()[:3]
    result = await db.execute(select(PlanPrice).where(PlanPrice.plan_id == plan_id, PlanPrice.currency_code == currency))
    existing = result.scalar_one_or_none()
    if existing:
        existing.amount = amount
        existing.is_active = bool(data.get("is_active", True))
    else:
        db.add(PlanPrice(plan_id=plan_id, currency_code=currency, amount=amount))
    await db.commit()
    return {"message": f"Precio en {currency} actualizado para el plan {plan.name}"}


@router.delete("/{plan_id}/prices/{currency_code}")
async def delete_plan_price(plan_id: int, currency_code: str, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    await _require_sysadmin(current_user, db)
    result = await db.execute(select(PlanPrice).where(PlanPrice.plan_id == plan_id, PlanPrice.currency_code == currency_code.upper()))
    pp = result.scalar_one_or_none()
    if not pp:
        raise HTTPException(status_code=404, detail="Precio no encontrado")
    await db.delete(pp)
    await db.commit()
    return {"message": "Precio eliminado"}


@router.get("/{plan_id}")
async def get_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return _serialize(plan)


@router.post("/")
async def create_plan(data: dict = Body(...), db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    await _require_sysadmin(current_user, db)
    _validate(data)
    result = await db.execute(select(Plan).where(Plan.name == data["name"]))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya existe un plan con ese nombre")
    plan = Plan(**_fields(data))
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return _serialize(plan)


@router.put("/{plan_id}")
async def update_plan(plan_id: int, data: dict = Body(...), db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    await _require_sysadmin(current_user, db)
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    _validate(data)
    result = await db.execute(select(Plan).where(Plan.name == data["name"], Plan.id != plan_id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya existe un plan con ese nombre")
    for k, v in _fields(data).items():
        setattr(plan, k, v)
    await db.commit()
    await db.refresh(plan)
    return _serialize(plan)


@router.delete("/{plan_id}")
async def delete_plan(plan_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    await _require_sysadmin(current_user, db)
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    await db.delete(plan)
    await db.commit()
    return {"message": "Plan eliminado"}
