from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.worker_model import Worker
from app.auth.dependencies import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/workers", tags=["Workers"])


def _ser(w: Worker):
    return {
        "id":              w.id,
        "name":            w.name,
        "profession_id":   w.profession_id,
        "profession_name": w.profession.name if w.profession else None,
        "phone":           w.phone,
    }


@router.get("/")
def get_workers(db: Session = Depends(get_db)):
    workers = db.query(Worker).options(
        joinedload(Worker.profession)
    ).order_by(Worker.name).all()
    return [_ser(w) for w in workers]


@router.post("/")
def create_worker(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    w = Worker(
        name=          name,
        profession_id= data.get("profession_id") or None,
        phone=         (data.get("phone") or "").strip() or None,
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    db.refresh(w)  # reload relationship
    return _ser(db.query(Worker).options(joinedload(Worker.profession)).filter(Worker.id == w.id).first())


@router.put("/{worker_id}")
def update_worker(
    worker_id: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    w = db.query(Worker).options(joinedload(Worker.profession)).filter(Worker.id == worker_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Ejecutor no encontrado")

    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    w.name          = name
    w.profession_id = data.get("profession_id") or None
    w.phone         = (data.get("phone") or "").strip() or None
    db.commit()
    return _ser(db.query(Worker).options(joinedload(Worker.profession)).filter(Worker.id == worker_id).first())


@router.delete("/{worker_id}")
def delete_worker(
    worker_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    w = db.query(Worker).filter(Worker.id == worker_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Ejecutor no encontrado")
    db.delete(w)
    db.commit()
    return {"message": "Ejecutor eliminado"}
