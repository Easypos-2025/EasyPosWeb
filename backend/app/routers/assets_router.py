"""
========================================================
ASSETS ROUTER
========================================================
CRUD de activos
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.asset_model import Asset
from app.models.user_model import User
from app.schemas.asset_schema import AssetCreate, AssetUpdate
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/assets",
    tags=["Assets"]
)


# =====================================================
# CREATE ASSET
# =====================================================

@router.post("/")
def create_asset(
    data: AssetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    asset = Asset(
        name=data.name,
        category_id=data.category_id,
        description=data.description or "",
        location=data.location or ""
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


# =====================================================
# GET ALL ASSETS
# =====================================================

@router.get("/")
def get_assets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Asset).order_by(Asset.name).all()


# =====================================================
# GET ASSET BY ID
# =====================================================

@router.get("/{asset_id}")
def get_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Activo no encontrado")
    return asset


# =====================================================
# UPDATE ASSET
# =====================================================

@router.put("/{asset_id}")
def update_asset(
    asset_id: int,
    data: AssetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Activo no encontrado")

    asset.name        = data.name
    asset.category_id = data.category_id
    asset.description = data.description or ""
    asset.location    = data.location or ""

    db.commit()
    db.refresh(asset)
    return asset


# =====================================================
# DELETE ASSET
# =====================================================

@router.delete("/{asset_id}")
def delete_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Activo no encontrado")

    db.delete(asset)
    db.commit()
    return {"message": "Activo eliminado"}
