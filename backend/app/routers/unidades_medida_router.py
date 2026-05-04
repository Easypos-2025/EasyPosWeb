from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.unidad_medida_model import UnidadMedida
from app.auth.dependencies import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/unidades-medida", tags=["UnidadesMedida"])


def _ser(u: UnidadMedida):
    return {"id": u.id, "company_id": u.company_id, "name": u.name, "abreviatura": u.abreviatura}


@router.get("/")
def list_unidades(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(UnidadMedida).filter(UnidadMedida.company_id == current_user.company_id)\
               .order_by(UnidadMedida.name).all()
    return [_ser(u) for u in items]


@router.post("/")
def create_unidad(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    exists = db.query(UnidadMedida).filter(
        UnidadMedida.company_id == current_user.company_id, UnidadMedida.name == name
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail=f"Ya existe la unidad '{name}'")

    item = UnidadMedida(
        company_id=current_user.company_id,
        name=name,
        abreviatura=(data.get("abreviatura") or "").strip() or None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _ser(item)


@router.put("/{unidad_id}")
def update_unidad(
    unidad_id: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item = db.query(UnidadMedida).filter(
        UnidadMedida.id == unidad_id, UnidadMedida.company_id == current_user.company_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")

    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    item.name        = name
    item.abreviatura = (data.get("abreviatura") or "").strip() or None
    db.commit()
    db.refresh(item)
    return _ser(item)


@router.delete("/{unidad_id}")
def delete_unidad(
    unidad_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item = db.query(UnidadMedida).filter(
        UnidadMedida.id == unidad_id, UnidadMedida.company_id == current_user.company_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")

    db.delete(item)
    db.commit()
    return {"message": "Unidad eliminada"}
