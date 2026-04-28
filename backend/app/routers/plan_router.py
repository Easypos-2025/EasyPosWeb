from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.plan_model import Plan
from app.models.plan_price_model import PlanPrice
from app.models.role_model import Role

router = APIRouter(prefix="/plans", tags=["Plans"])


def _require_sysadmin(current_user, db):
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    if not role or not role.is_system:
        raise HTTPException(status_code=403, detail="Solo SYSADMIN")


@router.get("/")
def get_plans(db: Session = Depends(get_db)):
    plans = db.query(Plan).order_by(Plan.id).all()
    return [_serialize(p) for p in plans]


@router.get("/with-prices")
def get_plans_with_prices(currency: str = "COP", db: Session = Depends(get_db)):
    """Retorna planes activos con el precio en la moneda solicitada (fallback a COP)."""
    plans = db.query(Plan).filter(Plan.is_active == True).order_by(Plan.price).all()
    result = []
    for p in plans:
        pp = db.query(PlanPrice).filter(
            PlanPrice.plan_id == p.id,
            PlanPrice.currency_code == currency.upper(),
            PlanPrice.is_active == True,
        ).first()
        price_in_currency = pp.amount if pp else p.price
        data = _serialize(p)
        data["price_in_currency"] = price_in_currency
        data["currency"] = currency.upper()
        result.append(data)
    return result


# ── SYSADMIN: gestión de precios por moneda ───────────────────────────────────

@router.get("/{plan_id}/prices")
def get_plan_prices(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _require_sysadmin(current_user, db)
    prices = db.query(PlanPrice).filter(PlanPrice.plan_id == plan_id).all()
    return [{"id": pp.id, "currency_code": pp.currency_code, "amount": pp.amount, "is_active": pp.is_active}
            for pp in prices]


@router.put("/{plan_id}/prices/{currency_code}")
def upsert_plan_price(
    plan_id: int,
    currency_code: str,
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _require_sysadmin(current_user, db)
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    amount = float(data.get("amount", 0))
    if amount < 0:
        raise HTTPException(status_code=400, detail="El precio no puede ser negativo")

    currency = currency_code.upper()[:3]
    existing = db.query(PlanPrice).filter(
        PlanPrice.plan_id == plan_id,
        PlanPrice.currency_code == currency,
    ).first()

    if existing:
        existing.amount    = amount
        existing.is_active = bool(data.get("is_active", True))
    else:
        db.add(PlanPrice(plan_id=plan_id, currency_code=currency, amount=amount))

    db.commit()
    return {"message": f"Precio en {currency} actualizado para el plan {plan.name}"}


@router.delete("/{plan_id}/prices/{currency_code}")
def delete_plan_price(
    plan_id: int,
    currency_code: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _require_sysadmin(current_user, db)
    pp = db.query(PlanPrice).filter(
        PlanPrice.plan_id == plan_id,
        PlanPrice.currency_code == currency_code.upper(),
    ).first()
    if not pp:
        raise HTTPException(status_code=404, detail="Precio no encontrado")
    db.delete(pp)
    db.commit()
    return {"message": "Precio eliminado"}


@router.get("/{plan_id}")
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return _serialize(plan)


@router.post("/")
def create_plan(
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    _require_sysadmin(current_user, db)
    _validate(data)

    if db.query(Plan).filter(Plan.name == data["name"]).first():
        raise HTTPException(status_code=400, detail="Ya existe un plan con ese nombre")

    plan = Plan(**_fields(data))
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _serialize(plan)


@router.put("/{plan_id}")
def update_plan(
    plan_id: int,
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    _require_sysadmin(current_user, db)
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    _validate(data)

    duplicate = db.query(Plan).filter(Plan.name == data["name"], Plan.id != plan_id).first()
    if duplicate:
        raise HTTPException(status_code=400, detail="Ya existe un plan con ese nombre")

    for k, v in _fields(data).items():
        setattr(plan, k, v)

    db.commit()
    db.refresh(plan)
    return _serialize(plan)


@router.delete("/{plan_id}")
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    _require_sysadmin(current_user, db)
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    db.delete(plan)
    db.commit()
    return {"message": "Plan eliminado"}


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
    return {
        "id":             p.id,
        "name":           p.name,
        "description":    p.description,
        "max_users":      p.max_users,
        "max_products":   p.max_products,
        "max_categories": p.max_categories,
        "price":          p.price,
        "is_active":      p.is_active,
    }
