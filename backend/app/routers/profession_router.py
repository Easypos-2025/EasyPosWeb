from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.profession_model import Profession
from app.auth.dependencies import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/professions", tags=["Professions"])


def _ser(p: Profession):
    return {"id": p.id, "name": p.name, "description": p.description}


@router.get("/")
async def get_professions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Profession).order_by(Profession.name))
    return [_ser(p) for p in result.scalars().all()]


@router.post("/")
async def create_profession(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    result = await db.execute(select(Profession).where(Profession.name == name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Ya existe la profesión '{name}'")

    p = Profession(name=name, description=(data.get("description") or "").strip() or None)
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return _ser(p)


@router.put("/{profession_id}")
async def update_profession(
    profession_id: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    p = await db.get(Profession, profession_id)
    if not p:
        raise HTTPException(status_code=404, detail="Profesión no encontrada")

    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    p.name        = name
    p.description = (data.get("description") or "").strip() or None
    await db.commit()
    await db.refresh(p)
    return _ser(p)


@router.delete("/{profession_id}")
async def delete_profession(
    profession_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    p = await db.get(Profession, profession_id)
    if not p:
        raise HTTPException(status_code=404, detail="Profesión no encontrada")

    if p.workers:
        raise HTTPException(
            status_code=409,
            detail=f"No se puede eliminar: hay {len(p.workers)} ejecutor(es) con esta profesión"
        )

    await db.delete(p)
    await db.commit()
    return {"message": "Profesión eliminada"}
