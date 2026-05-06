from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.asset_model import Asset
from app.models.asset_category_model import AssetCategory
from app.models.client_model import Client
from app.models.user_model import User
from app.schemas.asset_schema import AssetCreate, AssetUpdate
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/assets", tags=["Assets"])


async def _ser(asset: Asset, db: AsyncSession) -> dict:
    cat = await db.get(AssetCategory, asset.category_id) if asset.category_id else None
    cli = await db.get(Client, asset.client_id) if asset.client_id else None
    return {
        "id":            asset.id,
        "name":          asset.name,
        "category_id":   asset.category_id,
        "category_name": cat.name if cat else "",
        "client_id":     asset.client_id,
        "client_name":   cli.name if cli else "",
        "description":   asset.description or "",
        "location":      asset.location or "",
    }


@router.post("/")
async def create_asset(
    data: AssetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    asset = Asset(name=data.name, category_id=data.category_id, client_id=data.client_id,
                  description=data.description or "", location=data.location or "")
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return await _ser(asset, db)


@router.get("/")
async def get_assets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Asset).order_by(Asset.name))
    return [await _ser(a, db) for a in result.scalars().all()]


@router.get("/{asset_id:int}")
async def get_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Activo no encontrado")
    return await _ser(asset, db)


@router.put("/{asset_id:int}")
async def update_asset(
    asset_id: int,
    data: AssetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Activo no encontrado")
    asset.name = data.name
    asset.category_id = data.category_id
    asset.client_id = data.client_id
    asset.description = data.description or ""
    asset.location = data.location or ""
    await db.commit()
    await db.refresh(asset)
    return await _ser(asset, db)


@router.delete("/{asset_id:int}")
async def delete_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Activo no encontrado")
    await db.delete(asset)
    await db.commit()
    return {"message": "Activo eliminado"}
