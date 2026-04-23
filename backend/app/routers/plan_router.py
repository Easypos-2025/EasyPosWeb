from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.plan_model import Plan
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
