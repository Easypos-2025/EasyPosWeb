from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.concepto_compra_model import ConceptoCompra
from app.auth.dependencies import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/conceptos-compras", tags=["ConceptosCompras"])


def _ser(c: ConceptoCompra):
    return {"id": c.id, "company_id": c.company_id, "name": c.name, "description": c.description}


@router.get("/")
def list_conceptos(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(ConceptoCompra).filter(ConceptoCompra.company_id == current_user.company_id)\
               .order_by(ConceptoCompra.name).all()
    return [_ser(c) for c in items]


@router.post("/")
def create_concepto(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    exists = db.query(ConceptoCompra).filter(
        ConceptoCompra.company_id == current_user.company_id, ConceptoCompra.name == name
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail=f"Ya existe el concepto '{name}'")

    item = ConceptoCompra(
        company_id=current_user.company_id,
        name=name,
        description=(data.get("description") or "").strip() or None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _ser(item)


@router.put("/{concepto_id}")
def update_concepto(
    concepto_id: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item = db.query(ConceptoCompra).filter(
        ConceptoCompra.id == concepto_id, ConceptoCompra.company_id == current_user.company_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Concepto no encontrado")

    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    item.name        = name
    item.description = (data.get("description") or "").strip() or None
    db.commit()
    db.refresh(item)
    return _ser(item)


@router.delete("/{concepto_id}")
def delete_concepto(
    concepto_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item = db.query(ConceptoCompra).filter(
        ConceptoCompra.id == concepto_id, ConceptoCompra.company_id == current_user.company_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Concepto no encontrado")

    db.delete(item)
    db.commit()
    return {"message": "Concepto eliminado"}
