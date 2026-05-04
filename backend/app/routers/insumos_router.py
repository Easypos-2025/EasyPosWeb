from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.insumo_model import Insumo
from app.auth.dependencies import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/insumos", tags=["Insumos"])


def _ser(i: Insumo):
    return {"id": i.id, "company_id": i.company_id, "name": i.name, "description": i.description}


@router.get("/")
def list_insumos(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(Insumo).filter(Insumo.company_id == current_user.company_id)\
               .order_by(Insumo.name).all()
    return [_ser(i) for i in items]


@router.post("/")
def create_insumo(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    exists = db.query(Insumo).filter(
        Insumo.company_id == current_user.company_id, Insumo.name == name
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail=f"Ya existe el insumo '{name}'")

    item = Insumo(
        company_id=current_user.company_id,
        name=name,
        description=(data.get("description") or "").strip() or None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _ser(item)


@router.put("/{insumo_id}")
def update_insumo(
    insumo_id: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item = db.query(Insumo).filter(
        Insumo.id == insumo_id, Insumo.company_id == current_user.company_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")

    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    item.name        = name
    item.description = (data.get("description") or "").strip() or None
    db.commit()
    db.refresh(item)
    return _ser(item)


@router.delete("/{insumo_id}")
def delete_insumo(
    insumo_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item = db.query(Insumo).filter(
        Insumo.id == insumo_id, Insumo.company_id == current_user.company_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")

    db.delete(item)
    db.commit()
    return {"message": "Insumo eliminado"}
