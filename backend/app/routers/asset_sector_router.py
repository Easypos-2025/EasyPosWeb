from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.asset_sector_model import AssetSector
from app.auth.dependencies import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/asset-sectors", tags=["AssetSectors"])


def _ser(s: AssetSector) -> dict:
    return {
        "id": s.id, "company_id": s.company_id, "name": s.name,
        "description": s.description, "order_index": s.order_index, "is_active": s.is_active,
    }


@router.get("/")
async def list_sectors(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AssetSector)
        .where(AssetSector.company_id == current_user.company_id, AssetSector.is_active == 1)
        .order_by(AssetSector.order_index, AssetSector.name)
    )
    return [_ser(s) for s in result.scalars().all()]


@router.get("/all")
async def list_all_sectors(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AssetSector)
        .where(AssetSector.company_id == current_user.company_id)
        .order_by(AssetSector.order_index, AssetSector.name)
    )
    return [_ser(s) for s in result.scalars().all()]


@router.post("/")
async def create_sector(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")
    existing = await db.execute(
        select(AssetSector).where(AssetSector.name == name, AssetSector.company_id == current_user.company_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Ya existe el sector '{name}'")
    s = AssetSector(
        company_id  = current_user.company_id,
        name        = name,
        description = (data.get("description") or "").strip() or None,
        order_index = int(data.get("order_index") or 0),
        is_active   = int(data.get("is_active") if data.get("is_active") is not None else 1),
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return _ser(s)


@router.put("/{sector_id}")
async def update_sector(
    sector_id: int,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AssetSector).where(AssetSector.id == sector_id, AssetSector.company_id == current_user.company_id)
    )
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Sector no encontrado")
    if "name" in data:
        s.name = (data["name"] or "").strip() or s.name
    if "description" in data:
        s.description = (data["description"] or "").strip() or None
    if "order_index" in data:
        s.order_index = int(data["order_index"] or 0)
    if "is_active" in data:
        s.is_active = int(data["is_active"])
    await db.commit()
    await db.refresh(s)
    return _ser(s)


@router.delete("/{sector_id}")
async def delete_sector(
    sector_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AssetSector).where(AssetSector.id == sector_id, AssetSector.company_id == current_user.company_id)
    )
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Sector no encontrado")
    await db.delete(s)
    await db.commit()
    return {"ok": True}
