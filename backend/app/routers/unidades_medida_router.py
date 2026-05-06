from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.unidad_medida_model import UnidadMedida
from app.auth.dependencies import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/unidades-medida", tags=["UnidadesMedida"])


def _ser(u: UnidadMedida):
    return {"id": u.id, "company_id": u.company_id, "name": u.name, "abreviatura": u.abreviatura}


@router.get("/")
async def list_unidades(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(UnidadMedida).where(UnidadMedida.company_id == current_user.company_id).order_by(UnidadMedida.name)
    )
    return [_ser(u) for u in result.scalars().all()]


@router.post("/")
async def create_unidad(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    result = await db.execute(
        select(UnidadMedida).where(UnidadMedida.company_id == current_user.company_id, UnidadMedida.name == name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Ya existe la unidad '{name}'")

    item = UnidadMedida(
        company_id=current_user.company_id,
        name=name,
        abreviatura=(data.get("abreviatura") or "").strip() or None,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return _ser(item)


@router.put("/{unidad_id}")
async def update_unidad(
    unidad_id: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(UnidadMedida).where(UnidadMedida.id == unidad_id, UnidadMedida.company_id == current_user.company_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")

    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    item.name        = name
    item.abreviatura = (data.get("abreviatura") or "").strip() or None
    await db.commit()
    await db.refresh(item)
    return _ser(item)


@router.delete("/{unidad_id}")
async def delete_unidad(
    unidad_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(UnidadMedida).where(UnidadMedida.id == unidad_id, UnidadMedida.company_id == current_user.company_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")

    await db.delete(item)
    await db.commit()
    return {"message": "Unidad eliminada"}
