from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from datetime import date
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.company_plan_model import CompanyPlan
from app.models.plan_model import Plan
from app.models.role_model import Role

router = APIRouter(prefix="/company-plan", tags=["CompanyPlan"])


def _is_system(current_user, db):
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    return role.is_system if role else False


@router.get("/{company_id}")
def get_company_plan(
    company_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Devuelve el plan activo de una empresa."""
    cp = (
        db.query(CompanyPlan)
        .filter(CompanyPlan.company_id == company_id, CompanyPlan.is_active == True)
        .order_by(CompanyPlan.id.desc())
        .first()
    )

    if not cp:
        return {"plan_name": "Sin plan", "expiration_date": None, "is_free": False}

    plan = db.query(Plan).filter(Plan.id == cp.plan_id).first()

    exp = cp.expiration_date
    is_free = (plan.price == 0) if plan else False

    return {
        "plan_name":       plan.name if plan else "Desconocido",
        "plan_id":         cp.plan_id,
        "start_date":      cp.start_date.isoformat() if cp.start_date else None,
        "expiration_date": exp.isoformat() if exp else None,
        "is_free":         is_free,
        "is_active":       cp.is_active
    }


@router.post("/{company_id}")
def assign_plan(
    company_id: int,
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Asigna o renueva el plan de una empresa. Solo SYSADMIN."""
    if not _is_system(current_user, db):
        raise HTTPException(status_code=403, detail="Solo SYSADMIN puede asignar planes")

    # Desactivar planes anteriores
    db.query(CompanyPlan).filter(
        CompanyPlan.company_id == company_id
    ).update({"is_active": False})

    exp_str = data.get("expiration_date")
    exp     = date.fromisoformat(exp_str) if exp_str else None

    cp = CompanyPlan(
        company_id=      company_id,
        plan_id=         data["plan_id"],
        expiration_date= exp,
        is_active=       True
    )
    db.add(cp)
    db.commit()
    db.refresh(cp)

    plan = db.query(Plan).filter(Plan.id == cp.plan_id).first()
    return {
        "message":         "Plan asignado correctamente",
        "plan_name":       plan.name if plan else "",
        "expiration_date": cp.expiration_date.isoformat() if cp.expiration_date else None
    }
