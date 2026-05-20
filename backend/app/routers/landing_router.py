import asyncio
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header, Body
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.utils.sse import _sse_subscribers, sse_generator, notify_landing_changed

# Aliases para no romper código interno que use los nombres viejos
_sse_generator = sse_generator
_notify_landing_changed = notify_landing_changed

from app.database import get_db
from app.utils.storage import upload_file
from app.models.landing_section_model import LandingSection
from app.models.plan_feature_model import PlanFeature
from app.models.landing_contact_model import LandingContact
from app.models.business_profile_model import BusinessProfile
from app.models.plan_model import Plan
from app.models.user_model import User
from app.models.role_model import Role
from app.models.user_session_model import UserSession
from app.auth.jwt_handler import decode_access_token
from app.utils.email_service import send_contact_email

router = APIRouter(prefix="/landing", tags=["Landing"])

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads" / "landing"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


async def _get_sysadmin(authorization: str, db: AsyncSession):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    result = await db.execute(select(UserSession).where(UserSession.token == token, UserSession.is_active == True))
    if not result.scalar_one_or_none() or not payload:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    result = await db.execute(select(User).where(User.email == payload.get("sub")))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = result.scalar_one_or_none()
    if not role or not role.is_system:
        raise HTTPException(status_code=403, detail="Solo SYSADMIN")
    return user


def _ser_section(s):
    return {"id": s.id, "section_key": s.section_key, "title": s.title, "subtitle": s.subtitle,
            "body_text": s.body_text, "cta_text": s.cta_text, "cta_url": s.cta_url,
            "image_url": s.image_url, "is_active": s.is_active, "order_index": s.order_index,
            "section_type": s.section_type}

def _ser_feature(f):
    return {"id": f.id, "category": f.category, "feature_name": f.feature_name,
            "val_free": f.val_free, "val_basic": f.val_basic, "val_standard": f.val_standard,
            "val_premium": f.val_premium, "order_index": f.order_index, "is_active": f.is_active}

def _ser_contact(c):
    return {"id": c.id, "name": c.name, "email": c.email, "phone": c.phone,
            "company": c.company, "message": c.message, "is_read": c.is_read, "created_at": str(c.created_at)}

def _ser_profile(p):
    return {"id": p.id, "name": p.name, "description": p.description,
            "landing_description": p.landing_description, "image_url": p.image_url,
            "icon": p.icon, "color_accent": p.color_accent, "is_active": p.is_active,
            "show_in_landing": p.show_in_landing}


_NO_CACHE = {"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"}


@router.get("/sections")
async def get_sections(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LandingSection).where(LandingSection.is_active == True).order_by(LandingSection.order_index))
    return JSONResponse(content=[_ser_section(s) for s in result.scalars().all()], headers=_NO_CACHE)


@router.get("/profiles")
async def get_profiles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BusinessProfile).where(BusinessProfile.is_active == True, BusinessProfile.show_in_landing == True))
    return JSONResponse(content=[_ser_profile(p) for p in result.scalars().all()], headers=_NO_CACHE)


@router.get("/plans")
async def get_plans_with_features(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Plan).where(Plan.is_active == True).order_by(Plan.id))
    plans = result.scalars().all()
    result = await db.execute(select(PlanFeature).where(PlanFeature.is_active == True).order_by(PlanFeature.category, PlanFeature.order_index))
    features = result.scalars().all()
    categories = {}
    for f in features:
        categories.setdefault(f.category, []).append(_ser_feature(f))
    LIMIT_FIELDS = [
        "max_users", "max_products", "max_categories", "max_workers",
        "max_clients", "max_bodega_items", "max_assets", "max_waiters",
        "max_tasks", "max_daily_invoices", "max_daily_receipts", "max_daily_tasks",
    ]

    def _plan_ser(p):
        base = {"id": p.id, "name": p.name, "price": p.price}
        for f in LIMIT_FIELDS:
            base[f] = getattr(p, f, -1)
        return base

    return JSONResponse(content={
        "plans": [_plan_ser(p) for p in plans],
        "feature_groups": [{"category": cat, "features": feats} for cat, feats in categories.items()],
    }, headers=_NO_CACHE)


@router.get("/events")
async def landing_events():
    queue: asyncio.Queue = asyncio.Queue(maxsize=20)
    _sse_subscribers.add(queue)
    return StreamingResponse(_sse_generator(queue), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/contact")
async def submit_contact(data: dict = Body(...), db: AsyncSession = Depends(get_db)):
    name    = (data.get("name") or "").strip()
    email   = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()
    if not name or not email or not message:
        raise HTTPException(status_code=400, detail="Nombre, email y mensaje son obligatorios")
    contact = LandingContact(name=name, email=email, phone=data.get("phone", ""),
                             company=data.get("company", ""), message=message)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    try:
        send_contact_email(name=name, email=email, message=message,
                           phone=data.get("phone", ""), company=data.get("company", ""))
    except Exception as e:
        print("WARN: email contacto:", e)
    return {"message": "Mensaje recibido. Te contactaremos pronto."}


@router.get("/admin/sections")
async def admin_get_sections(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_sysadmin(authorization, db)
    result = await db.execute(select(LandingSection).order_by(LandingSection.order_index))
    return [_ser_section(s) for s in result.scalars().all()]


@router.post("/admin/sections")
async def admin_create_section(data: dict = Body(...), authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_sysadmin(authorization, db)
    key = (data.get("section_key") or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="section_key es obligatorio")
    result = await db.execute(select(LandingSection).where(LandingSection.section_key == key))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya existe una sección con esa clave")
    section = LandingSection(section_key=key, title=data.get("title", ""), subtitle=data.get("subtitle", ""),
                             body_text=data.get("body_text", ""), cta_text=data.get("cta_text", ""),
                             cta_url=data.get("cta_url", ""), image_url=data.get("image_url", ""),
                             is_active=data.get("is_active", True), order_index=data.get("order_index", 0),
                             section_type=data.get("section_type", "general"))
    db.add(section)
    await db.commit()
    await db.refresh(section)
    _notify_landing_changed()
    return _ser_section(section)


@router.put("/admin/sections/{section_key}")
async def admin_update_section(section_key: str, data: dict = Body(...), authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_sysadmin(authorization, db)
    result = await db.execute(select(LandingSection).where(LandingSection.section_key == section_key))
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail="Sección no encontrada")
    for field in ["title", "subtitle", "body_text", "cta_text", "cta_url", "image_url", "is_active", "order_index", "section_type"]:
        if field in data:
            setattr(section, field, data[field])
    await db.commit()
    await db.refresh(section)
    _notify_landing_changed()
    return _ser_section(section)


@router.delete("/admin/sections/{section_key}")
async def admin_delete_section(section_key: str, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_sysadmin(authorization, db)
    result = await db.execute(select(LandingSection).where(LandingSection.section_key == section_key))
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail="Sección no encontrada")
    await db.delete(section)
    await db.commit()
    _notify_landing_changed()
    return {"message": "Sección eliminada"}


@router.get("/admin/profiles")
async def admin_get_profiles(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_sysadmin(authorization, db)
    result = await db.execute(select(BusinessProfile))
    return [_ser_profile(p) for p in result.scalars().all()]


@router.put("/admin/profiles/{profile_id}")
async def admin_update_profile(profile_id: int, data: dict = Body(...), authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_sysadmin(authorization, db)
    result = await db.execute(select(BusinessProfile).where(BusinessProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    for field in ["image_url", "landing_description", "icon", "color_accent", "show_in_landing", "is_active"]:
        if field in data:
            setattr(profile, field, data[field])
    await db.commit()
    await db.refresh(profile)
    _notify_landing_changed()
    return _ser_profile(profile)


@router.get("/admin/plan-features")
async def admin_get_features(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_sysadmin(authorization, db)
    result = await db.execute(select(PlanFeature).order_by(PlanFeature.category, PlanFeature.order_index))
    return [_ser_feature(f) for f in result.scalars().all()]


@router.post("/admin/plan-features")
async def admin_create_feature(data: dict = Body(...), authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_sysadmin(authorization, db)
    if not data.get("feature_name") or not data.get("category"):
        raise HTTPException(status_code=400, detail="feature_name y category son obligatorios")
    feature = PlanFeature(category=data["category"], feature_name=data["feature_name"],
                          val_free=data.get("val_free"), val_basic=data.get("val_basic"),
                          val_standard=data.get("val_standard"), val_premium=data.get("val_premium"),
                          order_index=data.get("order_index", 0), is_active=data.get("is_active", True))
    db.add(feature)
    await db.commit()
    await db.refresh(feature)
    _notify_landing_changed()
    return _ser_feature(feature)


@router.put("/admin/plan-features/{feature_id}")
async def admin_update_feature(feature_id: int, data: dict = Body(...), authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_sysadmin(authorization, db)
    result = await db.execute(select(PlanFeature).where(PlanFeature.id == feature_id))
    feature = result.scalar_one_or_none()
    if not feature:
        raise HTTPException(status_code=404, detail="Feature no encontrada")
    for field in ["category", "feature_name", "val_free", "val_basic", "val_standard", "val_premium", "order_index", "is_active"]:
        if field in data:
            setattr(feature, field, data[field])
    await db.commit()
    await db.refresh(feature)
    _notify_landing_changed()
    return _ser_feature(feature)


@router.delete("/admin/plan-features/{feature_id}")
async def admin_delete_feature(feature_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_sysadmin(authorization, db)
    result = await db.execute(select(PlanFeature).where(PlanFeature.id == feature_id))
    feature = result.scalar_one_or_none()
    if not feature:
        raise HTTPException(status_code=404, detail="Feature no encontrada")
    await db.delete(feature)
    await db.commit()
    _notify_landing_changed()
    return {"message": "Feature eliminada"}


@router.get("/admin/contacts")
async def admin_get_contacts(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_sysadmin(authorization, db)
    result = await db.execute(select(LandingContact).order_by(LandingContact.created_at.desc()))
    return [_ser_contact(c) for c in result.scalars().all()]


@router.put("/admin/contacts/{contact_id}/read")
async def admin_mark_read(contact_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_sysadmin(authorization, db)
    result = await db.execute(select(LandingContact).where(LandingContact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    contact.is_read = True
    await db.commit()
    return {"message": "Marcado como leído"}


@router.post("/admin/upload")
async def admin_upload_image(file: UploadFile = File(...), authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_sysadmin(authorization, db)
    ext = Path(file.filename).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".svg"}:
        raise HTTPException(status_code=400, detail="Formato no permitido. Use JPG, PNG, WEBP o SVG")
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="La imagen no puede superar 5 MB")
    filename = f"{uuid.uuid4().hex}{ext}"
    url = await upload_file(contents, f"landing/{filename}")
    return {"url": url}
