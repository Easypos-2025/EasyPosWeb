from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.asset_inquiry_model import AssetInquiry
from app.models.asset_model import Asset
from app.models.user_model import User
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/asset-inquiries", tags=["AssetInquiries"])

INTEREST_LABEL = {"arriendo": "Arriendo", "compra": "Compra", "info": "Información"}
STATUS_LABEL   = {"pending": "Pendiente", "confirmed": "Confirmada", "expired": "Expirada"}


async def _ser(inq: AssetInquiry, db: AsyncSession) -> dict:
    asset = await db.get(Asset, inq.asset_id)
    return {
        "id":           inq.id,
        "asset_id":     inq.asset_id,
        "asset_name":   asset.name if asset else "—",
        "list_code":    asset.list_code if asset else None,
        "name":         inq.name,
        "phone":        inq.phone,
        "email":        inq.email,
        "interest":     inq.interest,
        "interest_label": INTEREST_LABEL.get(inq.interest, inq.interest),
        "message":      inq.message or "",
        "status":       inq.status,
        "status_label": STATUS_LABEL.get(inq.status, inq.status),
        "ip_address":   inq.ip_address or "",
        "confirmed_at": inq.confirmed_at.isoformat() if inq.confirmed_at else None,
        "created_at":   inq.created_at.isoformat() if inq.created_at else None,
    }


@router.get("/")
async def list_inquiries(
    asset_id:  Optional[int] = None,
    status:    Optional[str] = None,
    interest:  Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.role_model import Role
    role = await db.get(Role, current_user.role_id)
    is_system = role.is_system if role else False

    q = select(AssetInquiry).order_by(AssetInquiry.created_at.desc())
    if not is_system:
        q = q.where(AssetInquiry.company_id == current_user.company_id)
    if asset_id:
        q = q.where(AssetInquiry.asset_id == asset_id)
    if status:
        q = q.where(AssetInquiry.status == status)
    if interest:
        q = q.where(AssetInquiry.interest == interest)
    result = await db.execute(q)
    return [await _ser(i, db) for i in result.scalars().all()]


@router.get("/kpis")
async def inquiry_kpis(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.role_model import Role
    role = await db.get(Role, current_user.role_id)
    is_system = role.is_system if role else False
    base = select(func.count()).select_from(AssetInquiry)
    if not is_system:
        base = base.where(AssetInquiry.company_id == current_user.company_id)
    cond = [] if is_system else [AssetInquiry.company_id == current_user.company_id]
    total     = (await db.execute(base)).scalar() or 0
    confirmed = (await db.execute(select(func.count()).select_from(AssetInquiry).where(AssetInquiry.status == "confirmed", *cond))).scalar() or 0
    pending   = (await db.execute(select(func.count()).select_from(AssetInquiry).where(AssetInquiry.status == "pending",   *cond))).scalar() or 0
    return {"total": total, "confirmed": confirmed, "pending": pending}


@router.get("/new-count")
async def inquiry_new_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Nuevas solicitudes confirmadas (sin leer). Usado por el topbar."""
    from sqlalchemy import text
    count = (await db.execute(
        select(func.count()).select_from(AssetInquiry)
        .where(AssetInquiry.status == "confirmed", AssetInquiry.notified == False)
    )).scalar() or 0
    return {"count": count}


@router.post("/mark-notified")
async def mark_inquiries_notified(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Marca todas las solicitudes confirmadas como notificadas."""
    result = await db.execute(select(AssetInquiry).where(AssetInquiry.status == "confirmed", AssetInquiry.notified == False))
    for inq in result.scalars().all():
        inq.notified = True
    await db.commit()
    return {"message": "ok"}


@router.delete("/{inquiry_id:int}")
async def delete_inquiry(
    inquiry_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AssetInquiry).where(AssetInquiry.id == inquiry_id))
    inq = result.scalar_one_or_none()
    if not inq:
        raise HTTPException(status_code=404, detail="Consulta no encontrada")
    await db.delete(inq)
    await db.commit()
    return {"message": "Consulta eliminada"}
