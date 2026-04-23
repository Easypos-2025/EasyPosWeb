"""
========================================================
ASSET CATEGORY ROUTER
========================================================
CRUD para categorías de activos
"""

# =====================================================
# IMPORTS
# =====================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.asset_category_model import AssetCategory
from app.schemas.asset_category_schema import (
    AssetCategoryCreate,
    AssetCategoryUpdate
)

# =====================================================
# ROUTER
# =====================================================

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
    db: Session = Depends(get_db)
):

    category = AssetCategory(
        name=data.name,
        description=data.description
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


# =====================================================
# GET ALL CATEGORIES
# =====================================================

@router.get("/")
def get_categories(db: Session = Depends(get_db)):

    categories = db.query(AssetCategory).all()

    return categories


# =====================================================
# GET CATEGORY BY ID
# =====================================================

@router.get("/{category_id}")
def get_category(category_id: int, db: Session = Depends(get_db)):

    category = db.query(AssetCategory).filter(
        AssetCategory.id == category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    return category


# =====================================================
# UPDATE CATEGORY
# =====================================================

@router.put("/{category_id}")
def update_category(
    category_id: int,
    data: AssetCategoryUpdate,
    db: Session = Depends(get_db)
):

    category = db.query(AssetCategory).filter(
        AssetCategory.id == category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    category.name = data.name
    category.description = data.description

    db.commit()

    return category


# =====================================================
# DELETE CATEGORY
# =====================================================

@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db)
):

    category = db.query(AssetCategory).filter(
        AssetCategory.id == category_id
    ).first()

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    db.delete(category)
    db.commit()

    return {
        "message": "Category deleted successfully"
    }