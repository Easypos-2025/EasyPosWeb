import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.asset_media_model import AssetMedia
from app.models.asset_model import Asset
from app.models.user_model import User
from app.auth.dependencies import get_current_user
from app.utils.storage import upload_file, delete_file

router = APIRouter(prefix="/asset-media", tags=["AssetMedia"])

ALLOWED_IMAGE  = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_VIDEO  = {".mp4", ".mov", ".avi", ".webm"}
MAX_IMAGE_MB   = 10
MAX_VIDEO_MB   = 100
MAX_PER_ASSET  = 20


def _ser(m: AssetMedia) -> dict:
    return {
        "id":         m.id,
        "asset_id":   m.asset_id,
        "file_url":   m.file_url,
        "file_name":  m.file_name,
        "file_type":  m.file_type,
        "file_size":  m.file_size,
        "sort_order": m.sort_order,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


@router.get("/{asset_id:int}")
async def list_media(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AssetMedia)
        .where(AssetMedia.asset_id == asset_id)
        .order_by(AssetMedia.sort_order.asc(), AssetMedia.id.asc())
    )
    return [_ser(m) for m in result.scalars().all()]


@router.post("/{asset_id:int}")
async def upload_media(
    asset_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Activo no encontrado")

    count_res = await db.execute(select(AssetMedia).where(AssetMedia.asset_id == asset_id))
    if len(count_res.scalars().all()) >= MAX_PER_ASSET:
        raise HTTPException(status_code=400, detail=f"Límite de {MAX_PER_ASSET} archivos por activo alcanzado")

    ext = Path(file.filename or "").suffix.lower()
    if ext in ALLOWED_IMAGE:
        file_type = "image"
        max_bytes = MAX_IMAGE_MB * 1024 * 1024
    elif ext in ALLOWED_VIDEO:
        file_type = "video"
        max_bytes = MAX_VIDEO_MB * 1024 * 1024
    else:
        raise HTTPException(
            status_code=400,
            detail="Formato no permitido. Imágenes: JPG, PNG, WEBP, GIF. Video: MP4, MOV, WEBM"
        )

    content = await file.read()
    if len(content) > max_bytes:
        limit = MAX_IMAGE_MB if file_type == "image" else MAX_VIDEO_MB
        raise HTTPException(status_code=413, detail=f"El archivo supera el límite de {limit} MB")

    safe_name = f"asset_{asset_id}_{uuid.uuid4().hex[:10]}{ext}"
    storage_path = f"assets/{safe_name}"

    try:
        url = await upload_file(content, storage_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando archivo: {str(e)}")

    order_res = await db.execute(
        select(AssetMedia).where(AssetMedia.asset_id == asset_id).order_by(AssetMedia.sort_order.desc())
    )
    last = order_res.scalars().first()
    next_order = (last.sort_order + 1) if last else 0

    media = AssetMedia(
        asset_id    = asset_id,
        file_url    = url,
        file_name   = file.filename or safe_name,
        file_type   = file_type,
        file_size   = len(content),
        sort_order  = next_order,
        uploaded_by = current_user.id,
    )
    db.add(media)
    await db.commit()
    await db.refresh(media)
    return _ser(media)


@router.delete("/{media_id:int}")
async def delete_media(
    media_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AssetMedia).where(AssetMedia.id == media_id))
    media = result.scalar_one_or_none()
    if not media:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    await delete_file(media.file_url)
    await db.delete(media)
    await db.commit()
    return {"message": "Archivo eliminado"}


class ReorderItem(BaseModel):
    id: int
    sort_order: int


@router.put("/{asset_id:int}/reorder")
async def reorder_media(
    asset_id: int,
    items: List[ReorderItem],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    for item in items:
        result = await db.execute(
            select(AssetMedia).where(AssetMedia.id == item.id, AssetMedia.asset_id == asset_id)
        )
        media = result.scalar_one_or_none()
        if media:
            media.sort_order = item.sort_order
    await db.commit()
    return {"message": "Orden actualizado"}
