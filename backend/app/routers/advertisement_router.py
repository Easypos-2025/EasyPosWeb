import uuid
import re
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.database import get_db
from app.models.advertisement_model import Advertisement, AdPiece, AdPayment
from app.models.user_model import User
from app.models.company_model import Company
from app.models.business_profile_model import BusinessProfile
from app.auth.dependencies import get_current_user, require_sysadmin
from app.utils.storage import upload_file, delete_file

router = APIRouter(prefix="/ads", tags=["Advertisements"])

ALLOWED_IMAGE  = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_VIDEO  = {".mp4", ".mov", ".webm"}
MAX_IMAGE_BYTES = 8 * 1024 * 1024   # 8 MB
MAX_VIDEO_BYTES = 8 * 1024 * 1024   # 8 MB
MAX_PIECES = 3
MAX_ACTIVE_ADS_PER_COMPANY = 3

_URL_RE = re.compile(r"^https://[^\s]{4,500}$")
_YT_RE  = re.compile(r"^[A-Za-z0-9_\-]{6,20}$")


def _detect_social_platform(url: str) -> tuple[str, str | None]:
    """Detecta plataforma y extrae youtube_id si aplica. Retorna (platform, yt_id|None)."""
    url = url.strip()
    yt_id = None
    try:
        p = urlparse(url)
        h = p.hostname or ""
        h = h.replace("www.", "").replace("m.", "")
        if h in ("youtube.com", "youtu.be"):
            if h == "youtu.be":
                yt_id = p.path.strip("/").split("?")[0].split("/")[0]
            else:
                qs = parse_qs(p.query)
                yt_id = qs.get("v", [None])[0]
                if not yt_id:
                    parts = p.path.strip("/").split("/")
                    if len(parts) >= 2 and parts[0] in ("embed", "shorts", "v"):
                        yt_id = parts[1]
            if yt_id:
                return "youtube", yt_id
        if "instagram" in h:
            return "instagram", None
        if "tiktok" in h:
            return "tiktok", None
        if "facebook" in h or h in ("fb.com", "fb.watch"):
            return "facebook", None
        if "twitter" in h or h == "x.com":
            return "twitter", None
    except Exception:
        pass
    lower = url.lower()
    if "youtube" in lower or "youtu.be" in lower:
        return "youtube", None
    if "instagram" in lower:
        return "instagram", None
    if "tiktok" in lower:
        return "tiktok", None
    if "facebook" in lower:
        return "facebook", None
    return "social", None


def _validate_url(url: str | None) -> str | None:
    if not url:
        return None
    url = url.strip()
    if url and not _URL_RE.match(url):
        raise HTTPException(status_code=400, detail="La URL debe comenzar con https:// y tener formato válido")
    return url


def _ser_piece(p: AdPiece) -> dict:
    return {
        "id": p.id, "advertisement_id": p.advertisement_id,
        "piece_type": p.piece_type, "media_url": p.media_url,
        "youtube_id": p.youtube_id, "text_content": p.text_content,
        "social_platform": p.social_platform,
        "order_index": p.order_index,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


def _ser_payment(py: AdPayment) -> dict:
    return {
        "id": py.id, "advertisement_id": py.advertisement_id,
        "company_id": py.company_id, "amount": py.amount,
        "currency_code": py.currency_code, "receipt_url": py.receipt_url,
        "payment_date": py.payment_date.isoformat() if py.payment_date else None,
        "status": py.status, "notes": py.notes,
        "verified_at": py.verified_at.isoformat() if py.verified_at else None,
        "created_at": py.created_at.isoformat() if py.created_at else None,
    }


async def _ser_ad(ad: Advertisement, db: AsyncSession, include_pieces=True, include_payments=False) -> dict:
    pieces, payments = [], []
    if include_pieces:
        res = await db.execute(select(AdPiece).where(AdPiece.advertisement_id == ad.id).order_by(AdPiece.order_index))
        pieces = [_ser_piece(p) for p in res.scalars().all()]
    if include_payments:
        res = await db.execute(select(AdPayment).where(AdPayment.advertisement_id == ad.id).order_by(AdPayment.created_at.desc()))
        payments = [_ser_payment(p) for p in res.scalars().all()]

    company_name = None
    if ad.company_id:
        c = await db.get(Company, ad.company_id)
        company_name = c.name if c else None

    profile_name = None
    if ad.target_profile_id:
        bp = await db.get(BusinessProfile, ad.target_profile_id)
        profile_name = bp.name if bp else None

    return {
        "id": ad.id, "company_id": ad.company_id, "company_name": company_name,
        "title": ad.title, "description": ad.description, "cta_url": ad.cta_url,
        "notes_to_admin": ad.notes_to_admin,
        "target_profile_id": ad.target_profile_id, "target_profile_name": profile_name,
        "status": ad.status, "slot_position": ad.slot_position, "priority": ad.priority,
        "start_date": ad.start_date.isoformat() if ad.start_date else None,
        "end_date": ad.end_date.isoformat() if ad.end_date else None,
        "rejection_reason": ad.rejection_reason,
        "approved_by": ad.approved_by,
        "approved_at": ad.approved_at.isoformat() if ad.approved_at else None,
        "impressions": ad.impressions,
        "social_instagram":       ad.social_instagram,
        "social_tiktok":          ad.social_tiktok,
        "social_facebook":        ad.social_facebook,
        "social_youtube_channel": ad.social_youtube_channel,
        "social_website":         ad.social_website,
        "created_at": ad.created_at.isoformat() if ad.created_at else None,
        "updated_at": ad.updated_at.isoformat() if ad.updated_at else None,
        "pieces": pieces,
        "payments": payments,
    }


# ── Helpers ─────────────────────────────────────────────────────────────────

async def _get_ad_owned(ad_id: int, company_id: int, db: AsyncSession) -> Advertisement:
    ad = await db.get(Advertisement, ad_id)
    if not ad or ad.company_id != company_id:
        raise HTTPException(status_code=404, detail="Pauta no encontrada")
    return ad


async def _count_pieces(ad_id: int, db: AsyncSession) -> int:
    res = await db.execute(select(func.count()).select_from(AdPiece).where(AdPiece.advertisement_id == ad_id))
    return res.scalar() or 0


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC ENDPOINT — no auth
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/active-slots")
async def get_active_slots(db: AsyncSession = Depends(get_db)):
    """Returns the 3 sidebar slots with their active ad content. No auth required."""
    today = date.today()
    slots = []
    for pos in (1, 2, 3):
        res = await db.execute(
            select(Advertisement)
            .where(
                Advertisement.slot_position == pos,
                Advertisement.status == "active",
                Advertisement.start_date <= today,
                Advertisement.end_date >= today,
            )
            .order_by(Advertisement.priority.desc(), Advertisement.id.desc())
            .limit(1)
        )
        ad = res.scalar_one_or_none()
        if ad:
            pieces_res = await db.execute(
                select(AdPiece).where(AdPiece.advertisement_id == ad.id).order_by(AdPiece.order_index)
            )
            pieces = [_ser_piece(p) for p in pieces_res.scalars().all()]
            await db.execute(
                update(Advertisement)
                .where(Advertisement.id == ad.id)
                .values(impressions=Advertisement.impressions + 1)
            )
            await db.commit()
            slots.append({
                "slot": pos, "ad_id": ad.id, "title": ad.title,
                "cta_url": ad.cta_url, "pieces": pieces, "active": True,
                "social_instagram":       ad.social_instagram,
                "social_tiktok":          ad.social_tiktok,
                "social_facebook":        ad.social_facebook,
                "social_youtube_channel": ad.social_youtube_channel,
                "social_website":         ad.social_website,
            })
        else:
            slots.append({"slot": pos, "active": False, "pieces": []})
    return slots


# ══════════════════════════════════════════════════════════════════════════════
# ASSOCIATE ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/my")
async def list_my_ads(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Advertisement)
        .where(Advertisement.company_id == current_user.company_id)
        .order_by(Advertisement.created_at.desc())
    )
    return [await _ser_ad(ad, db) for ad in res.scalars().all()]


@router.get("/my/stats")
async def my_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cid = current_user.company_id
    counts = {}
    for st in ("pending", "approved", "active", "paused", "expired", "rejected"):
        r = await db.execute(
            select(func.count()).select_from(Advertisement)
            .where(Advertisement.company_id == cid, Advertisement.status == st)
        )
        counts[st] = r.scalar() or 0
    return counts


@router.post("/")
async def create_ad(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Rate limit: max 3 non-expired active requests per company
    pending_res = await db.execute(
        select(func.count()).select_from(Advertisement)
        .where(
            Advertisement.company_id == current_user.company_id,
            Advertisement.status.in_(["pending", "approved", "active"]),
        )
    )
    if (pending_res.scalar() or 0) >= MAX_ACTIVE_ADS_PER_COMPANY:
        raise HTTPException(status_code=400, detail=f"Máximo {MAX_ACTIVE_ADS_PER_COMPANY} pautas activas o pendientes por empresa")

    title = (data.get("title") or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="El título es requerido")

    cta_url = _validate_url(data.get("cta_url"))

    ad = Advertisement(
        company_id=current_user.company_id,
        title=title,
        description=(data.get("description") or "").strip() or None,
        cta_url=cta_url,
        notes_to_admin=(data.get("notes_to_admin") or "").strip() or None,
        target_profile_id=data.get("target_profile_id") or None,
        start_date=_parse_date(data.get("start_date")),
        end_date=_parse_date(data.get("end_date")),
        social_instagram=_validate_url(data.get("social_instagram")),
        social_tiktok=_validate_url(data.get("social_tiktok")),
        social_facebook=_validate_url(data.get("social_facebook")),
        social_youtube_channel=_validate_url(data.get("social_youtube_channel")),
        social_website=_validate_url(data.get("social_website")),
        status="pending",
    )
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    return await _ser_ad(ad, db)


@router.put("/{ad_id}")
async def update_ad(
    ad_id: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ad = await _get_ad_owned(ad_id, current_user.company_id, db)
    if ad.status not in ("pending", "rejected"):
        raise HTTPException(status_code=400, detail="Solo se pueden editar pautas en estado pendiente o rechazada")

    if "title" in data:
        title = (data["title"] or "").strip()
        if not title:
            raise HTTPException(status_code=400, detail="El título es requerido")
        ad.title = title
    if "description" in data:
        ad.description = (data["description"] or "").strip() or None
    if "cta_url" in data:
        ad.cta_url = _validate_url(data["cta_url"])
    if "notes_to_admin" in data:
        ad.notes_to_admin = (data["notes_to_admin"] or "").strip() or None
    if "target_profile_id" in data:
        ad.target_profile_id = data["target_profile_id"] or None
    if "start_date" in data:
        ad.start_date = _parse_date(data["start_date"])
    if "end_date" in data:
        ad.end_date = _parse_date(data["end_date"])
    if "social_instagram" in data:
        ad.social_instagram = _validate_url(data["social_instagram"])
    if "social_tiktok" in data:
        ad.social_tiktok = _validate_url(data["social_tiktok"])
    if "social_facebook" in data:
        ad.social_facebook = _validate_url(data["social_facebook"])
    if "social_youtube_channel" in data:
        ad.social_youtube_channel = _validate_url(data["social_youtube_channel"])
    if "social_website" in data:
        ad.social_website = _validate_url(data["social_website"])

    if ad.status == "rejected":
        ad.status = "pending"
        ad.rejection_reason = None

    await db.commit()
    await db.refresh(ad)
    return await _ser_ad(ad, db)


@router.delete("/{ad_id}")
async def delete_ad(
    ad_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ad = await _get_ad_owned(ad_id, current_user.company_id, db)
    if ad.status not in ("pending", "rejected", "expired"):
        raise HTTPException(status_code=400, detail="Solo se pueden eliminar pautas pendientes, rechazadas o expiradas")
    pieces_res = await db.execute(select(AdPiece).where(AdPiece.advertisement_id == ad.id))
    for p in pieces_res.scalars().all():
        if p.media_url:
            await delete_file(p.media_url)
    await db.delete(ad)
    await db.commit()
    return {"ok": True}


@router.post("/{ad_id}/pieces/upload")
async def upload_piece(
    ad_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ad = await _get_ad_owned(ad_id, current_user.company_id, db)
    if ad.status not in ("pending", "rejected"):
        raise HTTPException(status_code=400, detail="No se pueden agregar piezas a una pauta en este estado")

    count = await _count_pieces(ad_id, db)
    if count >= MAX_PIECES:
        raise HTTPException(status_code=400, detail=f"Máximo {MAX_PIECES} piezas por pauta")

    ext = Path(file.filename or "").suffix.lower()
    if ext in ALLOWED_IMAGE:
        piece_type = "image"
        max_bytes  = MAX_IMAGE_BYTES
    elif ext in ALLOWED_VIDEO:
        piece_type = "video"
        max_bytes  = MAX_VIDEO_BYTES
    else:
        raise HTTPException(status_code=400, detail="Formato no permitido. Imágenes: JPG, PNG, WEBP. Video: MP4, MOV, WEBM")

    content = await file.read()

    # MIME magic-byte validation
    if piece_type == "image" and ext in (".jpg", ".jpeg") and content[:2] != b"\xff\xd8":
        raise HTTPException(status_code=400, detail="El archivo no es una imagen JPEG válida")
    if piece_type == "image" and ext == ".png" and content[:4] != b"\x89PNG":
        raise HTTPException(status_code=400, detail="El archivo no es una imagen PNG válida")
    if piece_type == "video" and ext == ".mp4" and content[4:8] not in (b"ftyp", b"moov"):
        pass  # MP4 headers vary, skip strict check

    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="El archivo supera el límite de 8 MB")

    safe_name    = f"ad_{ad_id}_{uuid.uuid4().hex[:10]}{ext}"
    storage_path = f"ads/{safe_name}"
    url = await upload_file(content, storage_path)

    piece = AdPiece(
        advertisement_id=ad_id,
        piece_type=piece_type,
        media_url=url,
        order_index=count,
    )
    db.add(piece)
    await db.commit()
    await db.refresh(piece)
    return _ser_piece(piece)


@router.post("/{ad_id}/pieces/youtube")
async def add_youtube_piece(
    ad_id: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ad = await _get_ad_owned(ad_id, current_user.company_id, db)
    if ad.status not in ("pending", "rejected"):
        raise HTTPException(status_code=400, detail="No se pueden agregar piezas a una pauta en este estado")

    count = await _count_pieces(ad_id, db)
    if count >= MAX_PIECES:
        raise HTTPException(status_code=400, detail=f"Máximo {MAX_PIECES} piezas por pauta")

    youtube_id = (data.get("youtube_id") or "").strip()
    if not youtube_id or not _YT_RE.match(youtube_id):
        raise HTTPException(status_code=400, detail="ID de YouTube inválido")

    piece = AdPiece(advertisement_id=ad_id, piece_type="youtube", youtube_id=youtube_id, order_index=count)
    db.add(piece)
    await db.commit()
    await db.refresh(piece)
    return _ser_piece(piece)


@router.post("/{ad_id}/pieces/text")
async def add_text_piece(
    ad_id: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ad = await _get_ad_owned(ad_id, current_user.company_id, db)
    if ad.status not in ("pending", "rejected"):
        raise HTTPException(status_code=400, detail="No se pueden agregar piezas a una pauta en este estado")

    count = await _count_pieces(ad_id, db)
    if count >= MAX_PIECES:
        raise HTTPException(status_code=400, detail=f"Máximo {MAX_PIECES} piezas por pauta")

    text_content = (data.get("text_content") or "").strip()
    if not text_content or len(text_content) > 500:
        raise HTTPException(status_code=400, detail="El texto es requerido y debe tener máximo 500 caracteres")

    piece = AdPiece(advertisement_id=ad_id, piece_type="text", text_content=text_content, order_index=count)
    db.add(piece)
    await db.commit()
    await db.refresh(piece)
    return _ser_piece(piece)


@router.post("/{ad_id}/pieces/social")
async def add_social_piece(
    ad_id: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ad = await _get_ad_owned(ad_id, current_user.company_id, db)
    if ad.status not in ("pending", "rejected"):
        raise HTTPException(status_code=400, detail="No se pueden agregar piezas a una pauta en este estado")

    count = await _count_pieces(ad_id, db)
    if count >= MAX_PIECES:
        raise HTTPException(status_code=400, detail=f"Máximo {MAX_PIECES} piezas por pauta")

    url = (data.get("url") or "").strip()
    if not url or not url.startswith("http"):
        raise HTTPException(status_code=400, detail="URL inválida")

    platform, yt_id = _detect_social_platform(url)

    if platform == "youtube" and yt_id:
        piece = AdPiece(
            advertisement_id=ad_id, piece_type="youtube",
            youtube_id=yt_id, social_platform="youtube", order_index=count,
        )
    else:
        if not platform or platform == "social":
            raise HTTPException(status_code=400, detail="Plataforma no reconocida. Acepta YouTube, Instagram, TikTok o Facebook")
        piece = AdPiece(
            advertisement_id=ad_id, piece_type="social",
            media_url=url, social_platform=platform, order_index=count,
        )
    db.add(piece)
    await db.commit()
    await db.refresh(piece)
    return _ser_piece(piece)


@router.delete("/{ad_id}/pieces/{piece_id}")
async def delete_piece(
    ad_id: int,
    piece_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ad = await _get_ad_owned(ad_id, current_user.company_id, db)
    if ad.status not in ("pending", "rejected"):
        raise HTTPException(status_code=400, detail="No se pueden eliminar piezas en este estado")

    res = await db.execute(select(AdPiece).where(AdPiece.id == piece_id, AdPiece.advertisement_id == ad_id))
    piece = res.scalar_one_or_none()
    if not piece:
        raise HTTPException(status_code=404, detail="Pieza no encontrada")

    if piece.media_url:
        await delete_file(piece.media_url)
    await db.delete(piece)
    await db.commit()
    return {"ok": True}


@router.post("/{ad_id}/payment")
async def submit_payment(
    ad_id: int,
    file: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ad = await _get_ad_owned(ad_id, current_user.company_id, db)
    if ad.status not in ("pending", "rejected", "approved"):
        raise HTTPException(status_code=400, detail="No se puede registrar pago en este estado")

    receipt_url = None
    if file:
        ext = Path(file.filename or "").suffix.lower()
        if ext not in {".jpg", ".jpeg", ".png", ".pdf", ".webp"}:
            raise HTTPException(status_code=400, detail="Comprobante: JPG, PNG, PDF únicamente")
        content = await file.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="El comprobante supera 5 MB")
        safe_name    = f"adpay_{ad_id}_{uuid.uuid4().hex[:10]}{ext}"
        storage_path = f"ad_payments/{safe_name}"
        receipt_url  = await upload_file(content, storage_path)

    existing = await db.execute(select(AdPayment).where(AdPayment.advertisement_id == ad_id).order_by(AdPayment.created_at.desc()).limit(1))
    pay = existing.scalar_one_or_none()
    if pay and pay.status == "pending":
        if receipt_url:
            pay.receipt_url = receipt_url
    else:
        pay = AdPayment(
            advertisement_id=ad_id,
            company_id=current_user.company_id,
            receipt_url=receipt_url,
            status="pending",
        )
        db.add(pay)

    await db.commit()
    await db.refresh(pay)
    return _ser_payment(pay)


@router.post("/{ad_id}/renew")
async def renew_ad(
    ad_id: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Clone an expired ad for renewal without re-uploading pieces."""
    ad = await _get_ad_owned(ad_id, current_user.company_id, db)
    if ad.status not in ("expired", "rejected"):
        raise HTTPException(status_code=400, detail="Solo se pueden renovar pautas expiradas o rechazadas")

    pending_res = await db.execute(
        select(func.count()).select_from(Advertisement)
        .where(
            Advertisement.company_id == current_user.company_id,
            Advertisement.status.in_(["pending", "approved", "active"]),
        )
    )
    if (pending_res.scalar() or 0) >= MAX_ACTIVE_ADS_PER_COMPANY:
        raise HTTPException(status_code=400, detail=f"Máximo {MAX_ACTIVE_ADS_PER_COMPANY} pautas activas o pendientes por empresa")

    new_ad = Advertisement(
        company_id=current_user.company_id,
        title=ad.title,
        description=ad.description,
        cta_url=ad.cta_url,
        notes_to_admin=(data.get("notes_to_admin") or ad.notes_to_admin),
        target_profile_id=ad.target_profile_id,
        start_date=_parse_date(data.get("start_date")),
        end_date=_parse_date(data.get("end_date")),
        status="pending",
    )
    db.add(new_ad)
    await db.commit()
    await db.refresh(new_ad)

    # Clone pieces (reuse same URLs — pieces belong to original but referenced)
    src_pieces = await db.execute(select(AdPiece).where(AdPiece.advertisement_id == ad_id).order_by(AdPiece.order_index))
    for p in src_pieces.scalars().all():
        new_piece = AdPiece(
            advertisement_id=new_ad.id,
            piece_type=p.piece_type,
            media_url=p.media_url,
            youtube_id=p.youtube_id,
            text_content=p.text_content,
            order_index=p.order_index,
        )
        db.add(new_piece)
    await db.commit()
    return await _ser_ad(new_ad, db)


# ══════════════════════════════════════════════════════════════════════════════
# SYSADMIN ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/admin/list")
async def admin_list(
    status: str = None,
    current_user: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    q = select(Advertisement).order_by(Advertisement.created_at.desc())
    if status:
        q = q.where(Advertisement.status == status)
    res = await db.execute(q)
    return [await _ser_ad(ad, db, include_payments=True) for ad in res.scalars().all()]


@router.get("/admin/pending-count")
async def admin_pending_count(
    current_user: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(func.count()).select_from(Advertisement)
        .where(Advertisement.status == "pending")
    )
    return {"count": res.scalar() or 0}


@router.get("/admin/{ad_id}")
async def admin_get_ad(
    ad_id: int,
    current_user: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    ad = await db.get(Advertisement, ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Pauta no encontrada")
    return await _ser_ad(ad, db, include_pieces=True, include_payments=True)


@router.patch("/admin/{ad_id}/approve")
async def admin_approve(
    ad_id: int,
    current_user: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    ad = await db.get(Advertisement, ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Pauta no encontrada")
    if ad.status != "pending":
        raise HTTPException(status_code=400, detail="Solo se pueden aprobar pautas pendientes")
    ad.status      = "approved"
    ad.approved_by = current_user.id
    ad.approved_at = datetime.utcnow()
    await db.commit()
    return await _ser_ad(ad, db)


@router.patch("/admin/{ad_id}/reject")
async def admin_reject(
    ad_id: int,
    data: dict = Body(...),
    current_user: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    ad = await db.get(Advertisement, ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Pauta no encontrada")
    reason = (data.get("reason") or "").strip()
    if not reason:
        raise HTTPException(status_code=400, detail="El motivo del rechazo es requerido")
    ad.status           = "rejected"
    ad.rejection_reason = reason
    await db.commit()
    return await _ser_ad(ad, db)


@router.patch("/admin/{ad_id}/activate")
async def admin_activate(
    ad_id: int,
    data: dict = Body(...),
    current_user: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    ad = await db.get(Advertisement, ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Pauta no encontrada")
    if ad.status not in ("approved", "paused", "active"):
        raise HTTPException(
            status_code=400,
            detail=f"No se puede activar una pauta en estado '{ad.status}'. Debe estar aprobada, pausada o activa."
        )

    slot = data.get("slot_position")
    if slot not in (1, 2, 3):
        raise HTTPException(status_code=400, detail="slot_position debe ser 1, 2 o 3")

    start = _parse_date(data.get("start_date")) or ad.start_date
    end   = _parse_date(data.get("end_date")) or ad.end_date
    if not start or not end or start > end:
        raise HTTPException(status_code=400, detail="Fechas de inicio y fin válidas son requeridas")

    ad.slot_position = slot
    ad.start_date    = start
    ad.end_date      = end
    ad.priority      = int(data.get("priority") or 0)
    ad.status        = "active"
    await db.commit()
    return await _ser_ad(ad, db)


@router.patch("/admin/{ad_id}/pause")
async def admin_pause(
    ad_id: int,
    current_user: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    ad = await db.get(Advertisement, ad_id)
    if not ad or ad.status != "active":
        raise HTTPException(status_code=400, detail="Solo se pueden pausar pautas activas")
    ad.status = "paused"
    await db.commit()
    return await _ser_ad(ad, db)


@router.patch("/admin/{ad_id}/expire")
async def admin_expire(
    ad_id: int,
    current_user: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    ad = await db.get(Advertisement, ad_id)
    if not ad:
        raise HTTPException(status_code=404, detail="Pauta no encontrada")
    ad.status = "expired"
    await db.commit()
    return {"ok": True}


@router.patch("/admin/payments/{payment_id}/verify")
async def admin_verify_payment(
    payment_id: int,
    data: dict = Body(...),
    current_user: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    pay = await db.get(AdPayment, payment_id)
    if not pay:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    action = data.get("action")  # "verified" | "rejected"
    if action not in ("verified", "rejected"):
        raise HTTPException(status_code=400, detail="action debe ser 'verified' o 'rejected'")
    pay.status      = action
    pay.notes       = (data.get("notes") or "").strip() or None
    pay.verified_by = current_user.id
    pay.verified_at = datetime.utcnow()
    await db.commit()
    return _ser_payment(pay)


@router.get("/admin/stats/summary")
async def admin_stats(
    current_user: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    counts = {}
    for st in ("pending", "approved", "active", "paused", "expired", "rejected"):
        r = await db.execute(select(func.count()).select_from(Advertisement).where(Advertisement.status == st))
        counts[st] = r.scalar() or 0
    return counts


@router.get("/admin/payments/list")
async def admin_payments_list(
    status: str = None,
    current_user: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    q = select(AdPayment).order_by(AdPayment.created_at.desc())
    if status:
        q = q.where(AdPayment.status == status)
    res = await db.execute(q)
    payments = res.scalars().all()
    result = []
    for pay in payments:
        ad = await db.get(Advertisement, pay.advertisement_id)
        company = await db.get(Company, pay.company_id)
        result.append({
            **_ser_payment(pay),
            "ad_title":    ad.title if ad else None,
            "company_name": company.name if company else None,
        })
    return result


@router.get("/admin/payments/report")
async def admin_payments_report(
    period: str = "month",   # day | month | year
    current_user: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    """Income summary grouped by period for verified payments."""
    if period == "day":
        trunc = func.date(AdPayment.created_at)
    elif period == "year":
        trunc = func.year(AdPayment.created_at)
    else:
        trunc = func.date_format(AdPayment.created_at, "%Y-%m")

    res = await db.execute(
        select(trunc.label("periodo"), func.sum(AdPayment.amount).label("total"), func.count().label("qty"))
        .where(AdPayment.status == "verified")
        .group_by(trunc)
        .order_by(trunc.desc())
        .limit(60)
    )
    return [{"periodo": str(r.periodo), "total": float(r.total or 0), "qty": r.qty} for r in res.all()]


# ── Utility ──────────────────────────────────────────────────────────────────

def _parse_date(val) -> date | None:
    if not val:
        return None
    try:
        if isinstance(val, date):
            return val
        return date.fromisoformat(str(val)[:10])
    except Exception:
        return None
