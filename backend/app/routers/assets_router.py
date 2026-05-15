from io import BytesIO
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.asset_model import Asset
from app.models.asset_category_model import AssetCategory
from app.models.client_model import Client
from app.models.user_model import User
from app.schemas.asset_schema import AssetCreate, AssetUpdate
from app.auth.dependencies import get_current_user
from app.services.plan_limits_service import check_limit

router = APIRouter(prefix="/assets", tags=["Assets"])


async def _ser(asset: Asset, db: AsyncSession) -> dict:
    cat   = await db.get(AssetCategory, asset.category_id) if asset.category_id else None
    cli   = await db.get(Client, asset.client_id)          if asset.client_id   else None
    owner = await db.get(Client, asset.owner_id)           if asset.owner_id    else None
    return {
        "id":                   asset.id,
        "name":                 asset.name,
        "short_name":           asset.short_name or "",
        "category_id":          asset.category_id,
        "category_name":        cat.name if cat else "",
        "client_id":            asset.client_id,
        "client_name":          cli.name if cli else "",
        "owner_id":             asset.owner_id,
        "owner_name":           owner.name if owner else "",
        "description":          asset.description or "",
        "location":             asset.location or "",
        "address":              asset.address or "",
        "phone":                asset.phone or "",
        "sector_id":            asset.sector_id,
        "is_rented":            asset.is_rented or 0,
        "is_active":            asset.is_active if asset.is_active is not None else 1,
        "has_sale_option":      asset.has_sale_option or 0,
        "canon_value":          float(asset.canon_value)      if asset.canon_value      is not None else None,
        "cadastral_value":      float(asset.cadastral_value)  if asset.cadastral_value  is not None else None,
        "commercial_value":     float(asset.commercial_value) if asset.commercial_value is not None else None,
        "sale_price":           float(asset.sale_price)       if asset.sale_price       is not None else None,
        "appraisal_year":       asset.appraisal_year,
        "acquisition_type":     asset.acquisition_type or "",
        "registration":         asset.registration or "",
        "property_number":      asset.property_number or "",
        "additional_reference": asset.additional_reference or "",
        "list_code":            asset.list_code,
        "rental_requirements":  asset.rental_requirements or "",
        "general_observations": asset.general_observations or "",
    }


def _apply(asset: Asset, data: AssetCreate) -> None:
    asset.name                 = data.name
    asset.short_name           = data.short_name or None
    asset.category_id          = data.category_id
    asset.client_id            = data.client_id
    asset.owner_id             = data.owner_id
    asset.description          = data.description or None
    asset.location             = data.location or None
    asset.address              = data.address or None
    asset.phone                = data.phone or None
    asset.sector_id            = data.sector_id
    asset.is_rented            = data.is_rented or 0
    asset.is_active            = data.is_active if data.is_active is not None else 1
    asset.has_sale_option      = data.has_sale_option or 0
    asset.canon_value          = data.canon_value
    asset.cadastral_value      = data.cadastral_value
    asset.commercial_value     = data.commercial_value
    asset.sale_price           = data.sale_price
    asset.appraisal_year       = data.appraisal_year
    asset.acquisition_type     = data.acquisition_type or None
    asset.registration         = data.registration or None
    asset.property_number      = data.property_number or None
    asset.additional_reference = data.additional_reference or None
    asset.list_code            = data.list_code
    asset.rental_requirements  = data.rental_requirements or None
    asset.general_observations = data.general_observations or None


@router.post("/")
async def create_asset(
    data: AssetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await check_limit(current_user.company_id, "max_assets", Asset, db)
    if data.list_code is not None:
        dup = await db.execute(select(Asset).where(Asset.list_code == data.list_code))
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="El Código de Lista ya existe en otro activo")
    asset = Asset(company_id=current_user.company_id)
    _apply(asset, data)
    db.add(asset)
    try:
        await db.commit()
        await db.refresh(asset)
        return await _ser(asset, db)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=422, detail="Error de integridad: verifica categoría, cliente o propietario.")


@router.get("/")
async def get_assets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Asset)
        .where(Asset.company_id == current_user.company_id)
        .order_by(Asset.name)
    )
    return [await _ser(a, db) for a in result.scalars().all()]


@router.get("/{asset_id:int}")
async def get_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.company_id == current_user.company_id)
    )
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
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.company_id == current_user.company_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Activo no encontrado")
    if data.list_code is not None:
        dup = await db.execute(
            select(Asset).where(Asset.list_code == data.list_code, Asset.id != asset_id)
        )
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="El Código de Lista ya existe en otro activo")
    _apply(asset, data)
    await db.commit()
    await db.refresh(asset)
    return await _ser(asset, db)


@router.get("/{asset_id:int}/qr-image")
async def get_asset_qr_image(
    asset_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Activo no encontrado")
    if not asset.list_code:
        raise HTTPException(status_code=400, detail="El activo no tiene Código de Lista asignado")
    try:
        import qrcode
        base = str(request.base_url).rstrip("/")
        url  = f"{base}/activo/{asset.list_code}"
        qr   = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img  = qr.make_image(fill_color="#1e293b", back_color="white")
        buf  = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return StreamingResponse(
            buf, media_type="image/png",
            headers={"Content-Disposition": f"inline; filename=qr-activo-{asset.list_code}.png"}
        )
    except ImportError:
        raise HTTPException(status_code=500, detail="Librería qrcode no instalada en el servidor")


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
