"""
========================================================
ASSETS ROUTER
========================================================
CRUD de activos
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.asset_model import Asset
from app.schemas.asset_schema import AssetCreate, AssetUpdate
from app.core.permissions import check_permission

router = APIRouter(
    prefix="/assets",
    tags=["Assets"]
)


# =====================================================
# CREATE ASSET
# =====================================================

@router.post("/",
    dependencies=[Depends(check_permission("/assets", "can_create"))])
def create_asset(
    data: AssetCreate,
    db: Session = Depends(get_db)
):

    asset = Asset(
        name=data.name,
        category_id=data.category_id,
        description=data.description,
        location=data.location
    )

    db.add(asset)
    db.commit()
    db.refresh(asset)

    return asset


# =====================================================
# GET ALL ASSETS
# =====================================================

@router.get("/",
    dependencies=[Depends(check_permission("/assets", "can_view"))])
def get_assets(db: Session = Depends(get_db)):

    assets = db.query(Asset).all()

    return assets


# =====================================================
# GET ASSET BY ID
# =====================================================

@router.get("/{asset_id}",
    dependencies=[Depends(check_permission("/assets", "can_view"))])
def get_asset(asset_id: int, db: Session = Depends(get_db)):

    asset = db.query(Asset).filter(
        Asset.id == asset_id
    ).first()

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    return asset


# =====================================================
# UPDATE ASSET
# =====================================================

@router.put("/{asset_id}",
    dependencies=[Depends(check_permission("/assets", "can_edit"))])
def update_asset(
    asset_id: int,
    data: AssetUpdate,
    db: Session = Depends(get_db)
):

    asset = db.query(Asset).filter(
        Asset.id == asset_id
    ).first()

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    asset.name = data.name
    asset.category_id = data.category_id
    asset.description = data.description
    asset.location = data.location

    db.commit()

    return asset


# =====================================================
# DELETE ASSET
# =====================================================

@router.delete("/{asset_id}",
    dependencies=[Depends(check_permission("/assets", "can_delete"))])
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db)
):

    asset = db.query(Asset).filter(
        Asset.id == asset_id
    ).first()

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    db.delete(asset)
    db.commit()

    return {
        "message": "Asset deleted successfully"
    }
    
    
    