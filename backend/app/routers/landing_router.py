import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
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


# ──────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────

def _get_sysadmin(authorization: str, db: Session):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    session = db.query(UserSession).filter(
        UserSession.token == token, UserSession.is_active == True
    ).first()
    if not session or not payload:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    role = db.query(Role).filter(Role.id == user.role_id).first()
    if not role or not role.is_system:
        raise HTTPException(status_code=403, detail="Solo SYSADMIN")
    return user


def _ser_section(s: LandingSection):
    return {
        "id":           s.id,
        "section_key":  s.section_key,
        "title":        s.title,
        "subtitle":     s.subtitle,
        "body_text":    s.body_text,
        "cta_text":     s.cta_text,
        "cta_url":      s.cta_url,
        "image_url":    s.image_url,
        "is_active":    s.is_active,
        "order_index":  s.order_index,
        "section_type": s.section_type,
    }


def _ser_feature(f: PlanFeature):
    return {
        "id":           f.id,
        "category":     f.category,
        "feature_name": f.feature_name,
        "val_free":     f.val_free,
        "val_basic":    f.val_basic,
        "val_standard": f.val_standard,
        "val_premium":  f.val_premium,
        "order_index":  f.order_index,
        "is_active":    f.is_active,
    }


def _ser_contact(c: LandingContact):
    return {
        "id":         c.id,
        "name":       c.name,
        "email":      c.email,
        "phone":      c.phone,
        "company":    c.company,
        "message":    c.message,
        "is_read":    c.is_read,
        "created_at": str(c.created_at),
    }


def _ser_profile(p: BusinessProfile):
    return {
        "id":                  p.id,
        "name":                p.name,
        "description":         p.description,
        "landing_description": p.landing_description,
        "image_url":           p.image_url,
        "icon":                p.icon,
        "color_accent":        p.color_accent,
        "is_active":           p.is_active,
        "show_in_landing":     p.show_in_landing,
    }


# ══════════════════════════════════════════════════════
# ENDPOINTS PÚBLICOS (sin autenticación)
# ══════════════════════════════════════════════════════

_NO_CACHE = {"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"}


@router.get("/sections")
def get_sections(db: Session = Depends(get_db)):
    sections = (
        db.query(LandingSection)
        .filter(LandingSection.is_active == True)
        .order_by(LandingSection.order_index)
        .all()
    )
    return JSONResponse(content=[_ser_section(s) for s in sections], headers=_NO_CACHE)


@router.get("/profiles")
def get_profiles(db: Session = Depends(get_db)):
    profiles = (
        db.query(BusinessProfile)
        .filter(
            BusinessProfile.is_active == True,
            BusinessProfile.show_in_landing == True,
        )
        .all()
    )
    return JSONResponse(content=[_ser_profile(p) for p in profiles], headers=_NO_CACHE)


@router.get("/plans")
def get_plans_with_features(db: Session = Depends(get_db)):
    plans = db.query(Plan).filter(Plan.is_active == True).order_by(Plan.id).all()
    features = (
        db.query(PlanFeature)
        .filter(PlanFeature.is_active == True)
        .order_by(PlanFeature.category, PlanFeature.order_index)
        .all()
    )

    categories = {}
    for f in features:
        if f.category not in categories:
            categories[f.category] = []
        categories[f.category].append(_ser_feature(f))

    return JSONResponse(
        content={
            "plans": [
                {"id": p.id, "name": p.name, "price": p.price}
                for p in plans
            ],
            "feature_groups": [
                {"category": cat, "features": feats}
                for cat, feats in categories.items()
            ],
        },
        headers=_NO_CACHE,
    )


@router.post("/contact")
def submit_contact(data: dict = Body(...), db: Session = Depends(get_db)):
    name    = (data.get("name") or "").strip()
    email   = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()

    if not name or not email or not message:
        raise HTTPException(status_code=400, detail="Nombre, email y mensaje son obligatorios")

    contact = LandingContact(
        name    = name,
        email   = email,
        phone   = data.get("phone", ""),
        company = data.get("company", ""),
        message = message,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)

    try:
        send_contact_email(name=name, email=email, message=message,
                           phone=data.get("phone", ""), company=data.get("company", ""))
    except Exception as e:
        print("WARN: No se pudo enviar email de contacto:", e)

    return {"message": "Mensaje recibido. Te contactaremos pronto."}


# ══════════════════════════════════════════════════════
# ENDPOINTS ADMIN — solo SYSADMIN
# ══════════════════════════════════════════════════════

# ── SECCIONES ──────────────────────────────────────────

@router.get("/admin/sections")
def admin_get_sections(authorization: str = Header(None), db: Session = Depends(get_db)):
    _get_sysadmin(authorization, db)
    sections = db.query(LandingSection).order_by(LandingSection.order_index).all()
    return [_ser_section(s) for s in sections]


@router.post("/admin/sections")
def admin_create_section(
    data: dict = Body(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    _get_sysadmin(authorization, db)
    key = (data.get("section_key") or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="section_key es obligatorio")
    if db.query(LandingSection).filter(LandingSection.section_key == key).first():
        raise HTTPException(status_code=400, detail="Ya existe una sección con esa clave")

    section = LandingSection(
        section_key  = key,
        title        = data.get("title", ""),
        subtitle     = data.get("subtitle", ""),
        body_text    = data.get("body_text", ""),
        cta_text     = data.get("cta_text", ""),
        cta_url      = data.get("cta_url", ""),
        image_url    = data.get("image_url", ""),
        is_active    = data.get("is_active", True),
        order_index  = data.get("order_index", 0),
        section_type = data.get("section_type", "general"),
    )
    db.add(section)
    db.commit()
    db.refresh(section)
    return _ser_section(section)


@router.put("/admin/sections/{section_key}")
def admin_update_section(
    section_key: str,
    data: dict = Body(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    _get_sysadmin(authorization, db)
    section = db.query(LandingSection).filter(LandingSection.section_key == section_key).first()
    if not section:
        raise HTTPException(status_code=404, detail="Sección no encontrada")

    for field in ["title", "subtitle", "body_text", "cta_text", "cta_url",
                  "image_url", "is_active", "order_index", "section_type"]:
        if field in data:
            setattr(section, field, data[field])

    db.commit()
    db.refresh(section)
    return _ser_section(section)


@router.delete("/admin/sections/{section_key}")
def admin_delete_section(
    section_key: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    _get_sysadmin(authorization, db)
    section = db.query(LandingSection).filter(LandingSection.section_key == section_key).first()
    if not section:
        raise HTTPException(status_code=404, detail="Sección no encontrada")
    db.delete(section)
    db.commit()
    return {"message": "Sección eliminada"}


# ── PERFILES (campos landing) ──────────────────────────

@router.get("/admin/profiles")
def admin_get_profiles(authorization: str = Header(None), db: Session = Depends(get_db)):
    _get_sysadmin(authorization, db)
    profiles = db.query(BusinessProfile).all()
    return [_ser_profile(p) for p in profiles]


@router.put("/admin/profiles/{profile_id}")
def admin_update_profile(
    profile_id: int,
    data: dict = Body(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    _get_sysadmin(authorization, db)
    profile = db.query(BusinessProfile).filter(BusinessProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    for field in ["image_url", "landing_description", "icon", "color_accent", "show_in_landing"]:
        if field in data:
            setattr(profile, field, data[field])

    db.commit()
    db.refresh(profile)
    return _ser_profile(profile)


# ── PLAN FEATURES ──────────────────────────────────────

@router.get("/admin/plan-features")
def admin_get_features(authorization: str = Header(None), db: Session = Depends(get_db)):
    _get_sysadmin(authorization, db)
    features = db.query(PlanFeature).order_by(PlanFeature.category, PlanFeature.order_index).all()
    return [_ser_feature(f) for f in features]


@router.post("/admin/plan-features")
def admin_create_feature(
    data: dict = Body(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    _get_sysadmin(authorization, db)
    if not data.get("feature_name") or not data.get("category"):
        raise HTTPException(status_code=400, detail="feature_name y category son obligatorios")

    feature = PlanFeature(
        category     = data["category"],
        feature_name = data["feature_name"],
        val_free     = data.get("val_free"),
        val_basic    = data.get("val_basic"),
        val_standard = data.get("val_standard"),
        val_premium  = data.get("val_premium"),
        order_index  = data.get("order_index", 0),
        is_active    = data.get("is_active", True),
    )
    db.add(feature)
    db.commit()
    db.refresh(feature)
    return _ser_feature(feature)


@router.put("/admin/plan-features/{feature_id}")
def admin_update_feature(
    feature_id: int,
    data: dict = Body(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    _get_sysadmin(authorization, db)
    feature = db.query(PlanFeature).filter(PlanFeature.id == feature_id).first()
    if not feature:
        raise HTTPException(status_code=404, detail="Feature no encontrada")

    for field in ["category", "feature_name", "val_free", "val_basic",
                  "val_standard", "val_premium", "order_index", "is_active"]:
        if field in data:
            setattr(feature, field, data[field])

    db.commit()
    db.refresh(feature)
    return _ser_feature(feature)


@router.delete("/admin/plan-features/{feature_id}")
def admin_delete_feature(
    feature_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    _get_sysadmin(authorization, db)
    feature = db.query(PlanFeature).filter(PlanFeature.id == feature_id).first()
    if not feature:
        raise HTTPException(status_code=404, detail="Feature no encontrada")
    db.delete(feature)
    db.commit()
    return {"message": "Feature eliminada"}


# ── CONTACTOS ─────────────────────────────────────────

@router.get("/admin/contacts")
def admin_get_contacts(authorization: str = Header(None), db: Session = Depends(get_db)):
    _get_sysadmin(authorization, db)
    contacts = db.query(LandingContact).order_by(LandingContact.created_at.desc()).all()
    return [_ser_contact(c) for c in contacts]


@router.put("/admin/contacts/{contact_id}/read")
def admin_mark_read(
    contact_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    _get_sysadmin(authorization, db)
    contact = db.query(LandingContact).filter(LandingContact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    contact.is_read = True
    db.commit()
    return {"message": "Marcado como leído"}


# ── UPLOAD IMAGEN ─────────────────────────────────────

@router.post("/admin/upload")
async def admin_upload_image(
    file: UploadFile = File(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    _get_sysadmin(authorization, db)

    allowed = {".jpg", ".jpeg", ".png", ".webp", ".svg"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail="Formato no permitido. Use JPG, PNG, WEBP o SVG")

    filename = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOADS_DIR / filename

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="La imagen no puede superar 5 MB")

    with open(dest, "wb") as f:
        f.write(contents)

    return {"url": f"/uploads/landing/{filename}"}
