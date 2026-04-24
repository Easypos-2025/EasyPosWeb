"""
========================================================
ASSET CATEGORY ROUTER
========================================================
CRUD para categorías de activos
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.asset_category_model import AssetCategory
from app.models.user_model import User
from app.schemas.asset_category_schema import (
    AssetCategoryCreate,
    AssetCategoryUpdate
)
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/asset-categories",
    tags=["Asset Categories"]
)

# =====================================================
# CREATE CATEGORY
# =====================================================

@router.post("/")
def create_category(
    data: AssetCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category = AssetCategory(
        name=data.name,
        description=data.description or ""
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


# =====================================================
# GET ALL CATEGORIES
# =====================================================

@router.get("/")
def get_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(AssetCategory).order_by(AssetCategory.name).all()


# =====================================================
# GET CATEGORY BY ID
# =====================================================

@router.get("/{category_id}")
def get_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category = db.query(AssetCategory).filter(
        AssetCategory.id == category_id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return category


# =====================================================
# UPDATE CATEGORY
# =====================================================

@router.put("/{category_id}")
def update_category(
    category_id: int,
    data: AssetCategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category = db.query(AssetCategory).filter(
        AssetCategory.id == category_id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    category.name        = data.name
    category.description = data.description or ""
    db.commit()
    db.refresh(category)
    return category


# =====================================================
# DELETE CATEGORY
# =====================================================

@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category = db.query(AssetCategory).filter(
        AssetCategory.id == category_id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    db.delete(category)
    db.commit()
    return {"message": "Categoría eliminada"}
