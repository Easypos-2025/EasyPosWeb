from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.profession_model import Profession
from app.auth.dependencies import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/professions", tags=["Professions"])


def _ser(p: Profession):
    return {"id": p.id, "name": p.name, "description": p.description}


@router.get("/")
def get_professions(db: Session = Depends(get_db)):
    return [_ser(p) for p in db.query(Profession).order_by(Profession.name).all()]


@router.post("/")
def create_profession(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    exists = db.query(Profession).filter(Profession.name == name).first()
    if exists:
        raise HTTPException(status_code=409, detail=f"Ya existe la profesión '{name}'")

    p = Profession(name=name, description=(data.get("description") or "").strip() or None)
    db.add(p)
    db.commit()
    db.refresh(p)
    return _ser(p)


@router.put("/{profession_id}")
def update_profession(
    profession_id: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = db.get(Profession, profession_id)
    if not p:
        raise HTTPException(status_code=404, detail="Profesión no encontrada")

    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    p.name        = name
    p.description = (data.get("description") or "").strip() or None
    db.commit()
    db.refresh(p)
    return _ser(p)


@router.delete("/{profession_id}")
def delete_profession(
    profession_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = db.get(Profession, profession_id)
    if not p:
        raise HTTPException(status_code=404, detail="Profesión no encontrada")

    if p.workers:
        raise HTTPException(
            status_code=409,
            detail=f"No se puede eliminar: hay {len(p.workers)} ejecutor(es) con esta profesión"
        )

    db.delete(p)
    db.commit()
    return {"message": "Profesión eliminada"}
