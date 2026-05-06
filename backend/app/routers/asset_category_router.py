from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.asset_category_model import AssetCategory
from app.models.user_model import User
from app.schemas.asset_category_schema import AssetCategoryCreate, AssetCategoryUpdate
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/asset-categories", tags=["Asset Categories"])


@router.post("/")
async def create_category(
    data: AssetCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    category = AssetCategory(name=data.name, description=data.description or "")
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.get("/")
async def get_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AssetCategory).order_by(AssetCategory.name))
    return result.scalars().all()


@router.get("/{category_id:int}")
async def get_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AssetCategory).where(AssetCategory.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return category


@router.put("/{category_id:int}")
async def update_category(
    category_id: int,
    data: AssetCategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AssetCategory).where(AssetCategory.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    category.name        = data.name
    category.description = data.description or ""
    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/{category_id:int}")
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(AssetCategory).where(AssetCategory.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    await db.delete(category)
    await db.commit()
    return {"message": "Categoría eliminada"}
