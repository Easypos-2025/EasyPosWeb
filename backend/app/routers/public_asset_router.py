"""
Endpoints públicos del activo (sin autenticación).
URL pública: /activo/{list_code}
"""
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.asset_model import Asset
from app.models.asset_category_model import AssetCategory
from app.models.asset_media_model import AssetMedia
from app.models.asset_inquiry_model import AssetInquiry

router = APIRouter(prefix="/public", tags=["PublicAsset"])

# ── Rate limiter en memoria (max 5 envíos por IP en 10 min) ──────────────────
_ip_log: dict[str, list[datetime]] = defaultdict(list)

def _rate_ok(ip: str) -> bool:
    now    = datetime.utcnow()
    cutoff = now - timedelta(minutes=10)
    valid  = [t for t in _ip_log[ip] if t > cutoff]
    _ip_log[ip] = valid
    if len(valid) >= 5:
        return False
    _ip_log[ip].append(now)
    return True


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _get_asset_by_code(list_code: int, db: AsyncSession) -> Asset:
    result = await db.execute(
        select(Asset).where(Asset.list_code == list_code, Asset.is_active == 1)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Activo no encontrado o inactivo")
    return asset


def _public_fields(asset: Asset, category_name: str, media: list) -> dict:
    """Solo expone campos seguros para la vista pública."""
    return {
        "id":                   asset.id,
        "name":                 asset.name,
        "short_name":           asset.short_name or "",
        "category_name":        category_name,
        "location":             asset.location or "",
        "address":              asset.address or "",
        "description":          asset.description or "",
        "canon_value":          float(asset.canon_value) if asset.canon_value is not None else None,
        "has_sale_option":      bool(asset.has_sale_option),
        "is_rented":            bool(asset.is_rented),
        "list_code":            asset.list_code,
        "rental_requirements":  asset.rental_requirements or "",
        "general_observations": asset.general_observations or "",
        "media": [
            {"file_url": m.file_url, "file_type": m.file_type, "sort_order": m.sort_order}
            for m in media
        ],
    }


# ── GET /public/activo/{list_code} ───────────────────────────────────────────

@router.get("/activo/{list_code:int}")
async def get_public_asset(list_code: int, db: AsyncSession = Depends(get_db)):
    asset = await _get_asset_by_code(list_code, db)
    cat   = await db.get(AssetCategory, asset.category_id)
    media_res = await db.execute(
        select(AssetMedia)
        .where(AssetMedia.asset_id == asset.id)
        .order_by(AssetMedia.sort_order.asc(), AssetMedia.id.asc())
    )
    media = media_res.scalars().all()
    return _public_fields(asset, cat.name if cat else "", media)


# ── POST /public/activo/{list_code}/inquiry ──────────────────────────────────

class InquiryRequest(BaseModel):
    name:     str
    phone:    str
    email:    EmailStr
    interest: str          # 'arriendo' | 'compra' | 'info'
    message:  Optional[str] = None
    hp_field: Optional[str] = ""    # honeypot — debe llegar vacío


@router.post("/activo/{list_code:int}/inquiry")
async def submit_inquiry(
    list_code: int,
    body: InquiryRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # Honeypot: si viene con valor, es bot — responde 200 silenciosamente
    if body.hp_field:
        return {"message": "Solicitud recibida"}

    ip = request.client.host if request.client else "unknown"

    # Rate limit por IP
    if not _rate_ok(ip):
        return {"message": "Solicitud recibida"}  # silencioso, no revelar bloqueo

    # Validaciones de negocio
    if body.interest not in ("arriendo", "compra", "info"):
        raise HTTPException(status_code=400, detail="Tipo de interés no válido")
    if not body.name.strip() or not body.phone.strip():
        raise HTTPException(status_code=400, detail="Nombre y teléfono son obligatorios")

    asset = await _get_asset_by_code(list_code, db)

    # Deduplicación silenciosa: mismo email + mismo activo (pending o confirmed)
    dup = await db.execute(
        select(AssetInquiry).where(
            AssetInquiry.asset_id == asset.id,
            AssetInquiry.email    == str(body.email).lower(),
            AssetInquiry.status.in_(["pending", "confirmed"]),
        )
    )
    if dup.scalar_one_or_none():
        return {"message": "Solicitud recibida"}  # silencioso

    confirm_token = uuid.uuid4().hex + uuid.uuid4().hex[:32]  # 64 chars

    inquiry = AssetInquiry(
        asset_id      = asset.id,
        company_id    = asset.company_id or None,
        list_code     = asset.list_code,
        name          = body.name.strip()[:100],
        phone         = body.phone.strip()[:20],
        email         = str(body.email).lower()[:150],
        interest      = body.interest,
        message       = (body.message or "").strip()[:2000] or None,
        confirm_token = confirm_token,
        status        = "pending",
        ip_address    = ip[:45],
    )
    db.add(inquiry)
    await db.commit()
    await db.refresh(inquiry)

    # Enviar email de confirmación (double opt-in) en background
    try:
        from app.utils.email_service import send_inquiry_confirmation
        from app.utils.email_service import FRONTEND_URL
        confirm_link = f"{FRONTEND_URL}/activo/confirmar/{confirm_token}"
        send_inquiry_confirmation(
            to_email   = inquiry.email,
            name       = inquiry.name,
            asset_name = asset.name,
            confirm_link = confirm_link,
        )
    except Exception:
        pass  # no bloquear la respuesta si el email falla

    return {"message": "Solicitud recibida"}


# ── GET /public/inquiry/confirm/{token} ──────────────────────────────────────

@router.get("/inquiry/confirm/{token}")
async def confirm_inquiry(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AssetInquiry).where(AssetInquiry.confirm_token == token)
    )
    inquiry = result.scalar_one_or_none()

    if not inquiry:
        raise HTTPException(status_code=404, detail="Token no válido")
    if inquiry.status == "confirmed":
        return {"message": "already_confirmed", "name": inquiry.name}
    if inquiry.status == "expired":
        raise HTTPException(status_code=410, detail="Este enlace ha expirado")

    inquiry.status       = "confirmed"
    inquiry.confirmed_at = datetime.utcnow()
    await db.commit()

    # Notificar al administrador — usar email del admin del asociado dueño del activo
    try:
        asset = await db.get(Asset, inquiry.asset_id)
        from app.utils.email_service import send_new_inquiry_notification, EMAIL_SENDER
        from app.models.user_model import User
        from app.models.role_model import Role

        admin_email = EMAIL_SENDER  # fallback
        if asset and asset.company_id:
            # Buscar el admin del asociado que creó el activo
            role_res = await db.execute(
                select(Role).where(Role.company_id == asset.company_id, Role.is_system == False)
                .order_by(Role.id)
            )
            roles = role_res.scalars().all()
            if roles:
                user_res = await db.execute(
                    select(User).where(
                        User.company_id == asset.company_id,
                        User.role_id.in_([r.id for r in roles]),
                        User.is_active == True,
                    ).order_by(User.id)
                )
                admin = user_res.scalars().first()
                if admin and admin.email:
                    admin_email = admin.email

        send_new_inquiry_notification(
            admin_email = admin_email,
            inquiry     = inquiry,
            asset_name  = asset.name if asset else "—",
            list_code   = asset.list_code if asset else None,
        )
    except Exception:
        pass

    return {"message": "confirmed", "name": inquiry.name}
