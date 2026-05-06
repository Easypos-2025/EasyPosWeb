from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.concepto_compra_model import ConceptoCompra
from app.auth.dependencies import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/conceptos-compras", tags=["ConceptosCompras"])


def _ser(c: ConceptoCompra):
    return {"id": c.id, "company_id": c.company_id, "name": c.name, "description": c.description}


@router.get("/")
async def list_conceptos(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ConceptoCompra)
        .where(ConceptoCompra.company_id == current_user.company_id)
        .order_by(ConceptoCompra.name)
    )
    return [_ser(c) for c in result.scalars().all()]


@router.post("/")
async def create_concepto(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    result = await db.execute(
        select(ConceptoCompra).where(ConceptoCompra.company_id == current_user.company_id, ConceptoCompra.name == name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Ya existe el concepto '{name}'")

    item = ConceptoCompra(
        company_id=current_user.company_id,
        name=name,
        description=(data.get("description") or "").strip() or None,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return _ser(item)


@router.put("/{concepto_id}")
async def update_concepto(
    concepto_id: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ConceptoCompra).where(ConceptoCompra.id == concepto_id, ConceptoCompra.company_id == current_user.company_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Concepto no encontrado")

    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    item.name        = name
    item.description = (data.get("description") or "").strip() or None
    await db.commit()
    await db.refresh(item)
    return _ser(item)


@router.delete("/{concepto_id}")
async def delete_concepto(
    concepto_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ConceptoCompra).where(ConceptoCompra.id == concepto_id, ConceptoCompra.company_id == current_user.company_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Concepto no encontrado")

    await db.delete(item)
    await db.commit()
    return {"message": "Concepto eliminado"}
