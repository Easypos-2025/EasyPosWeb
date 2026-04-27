"""
========================================================
ASSETS ROUTER
========================================================
CRUD de activos (con category_name y client_name en respuesta)
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.asset_model import Asset
from app.models.asset_category_model import AssetCategory
from app.models.client_model import Client
from app.models.user_model import User
from app.schemas.asset_schema import AssetCreate, AssetUpdate
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/assets", tags=["Assets"])


def _ser(asset: Asset, db: Session) -> dict:
    cat = db.query(AssetCategory).filter(AssetCategory.id == asset.category_id).first()
    cli = db.query(Client).filter(Client.id == asset.client_id).first() if asset.client_id else None
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
def create_asset(
    data: AssetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    asset = Asset(
        name=data.name,
        category_id=data.category_id,
        client_id=data.client_id,
        description=data.description or "",
        location=data.location or "",
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return _ser(asset, db)


@router.get("/")
def get_assets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    assets = db.query(Asset).order_by(Asset.name).all()
    return [_ser(a, db) for a in assets]


@router.get("/{asset_id}")
def get_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Activo no encontrado")
    return _ser(asset, db)


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
    asset.client_id   = data.client_id
    asset.description = data.description or ""
    asset.location    = data.location or ""

    db.commit()
    db.refresh(asset)
    return _ser(asset, db)


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
