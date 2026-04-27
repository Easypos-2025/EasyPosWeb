import uuid
from pathlib import Path
from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.novelty_model import Novelty, NoveltyEvidence
from app.models.user_model import User
from app.models.role_model import Role
from app.models.user_session_model import UserSession
from app.auth.jwt_handler import decode_access_token

router = APIRouter(prefix="/novelties", tags=["Novelties"])

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads" / "novelties"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB
CHUNK = 256 * 1024                  # 256 KB

# Solo imágenes para evidencias de novedades
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
IMG_EXT     = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


# ── Auth helper ─────────────────────────────────────────────────────────────
def _get_user(authorization: str, db: Session) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token   = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    session = db.query(UserSession).filter(
        UserSession.token == token, UserSession.is_active == True
    ).first()
    if not session or not payload:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


def _can_manage_all(user: User, db: Session) -> bool:
    role = db.query(Role).filter(Role.id == user.role_id).first()
    if not role:
        return False
    if role.is_system:
        return True
    name = role.name.lower()
    return "admin" in name or "auditor" in name


# ── Serializers ──────────────────────────────────────────────────────────────
def _ser(n: Novelty, user_name: str = "", evidence_count: int = 0) -> dict:
    return {
        "id":             n.id,
        "company_id":     n.company_id,
        "user_id":        n.user_id,
        "user_name":      user_name,
        "title":          n.title,
        "description":    n.description,
        "status":         n.status,
        "evidence_count": evidence_count,
        "created_at":     n.created_at.isoformat() if n.created_at else None,
        "updated_at":     n.updated_at.isoformat() if n.updated_at else None,
    }


def _ser_ev(ev: NoveltyEvidence) -> dict:
    return {
        "id":          ev.id,
        "novelty_id":  ev.novelty_id,
        "file_url":    ev.file_url,
        "file_type":   ev.file_type,
        "uploaded_at": ev.uploaded_at.isoformat() if ev.uploaded_at else None,
    }


# ── GET /novelties/users-list (solo SYSADMIN/Admin) ─────────────────────────
@router.get("/users-list")
def list_novelty_users(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user    = _get_user(authorization, db)
    can_all = _can_manage_all(user, db)
    if not can_all:
        raise HTTPException(status_code=403, detail="Sin permiso")

    user_ids = (
        db.query(Novelty.user_id)
        .filter(Novelty.company_id == user.company_id)
        .distinct()
        .all()
    )
    ids = [r[0] for r in user_ids]
    users = db.query(User).filter(User.id.in_(ids)).order_by(User.nombre).all()
    return [{"id": u.id, "nombre": u.nombre} for u in users]


# ── GET /novelties ───────────────────────────────────────────────────────────
@router.get("")
def list_novelties(
    filter_user_id: Optional[int] = Query(None),
    date_from:      Optional[str] = Query(None),
    date_to:        Optional[str] = Query(None),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user    = _get_user(authorization, db)
    can_all = _can_manage_all(user, db)

    query = db.query(Novelty).filter(Novelty.company_id == user.company_id)
    if not can_all:
        query = query.filter(Novelty.user_id == user.id)
    elif filter_user_id:
        query = query.filter(Novelty.user_id == filter_user_id)

    if date_from:
        try:
            df = datetime.fromisoformat(date_from[:10])
            query = query.filter(Novelty.created_at >= df)
        except ValueError:
            pass
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to[:10]).replace(hour=23, minute=59, second=59)
            query = query.filter(Novelty.created_at <= dt)
        except ValueError:
            pass

    novelties = query.order_by(Novelty.created_at.desc()).all()

    result = []
    for n in novelties:
        author    = db.query(User).filter(User.id == n.user_id).first()
        ev_count  = db.query(NoveltyEvidence).filter(NoveltyEvidence.novelty_id == n.id).count()
        result.append(_ser(n, author.nombre if author else "Desconocido", ev_count))
    return result


# ── POST /novelties ──────────────────────────────────────────────────────────
@router.post("")
def create_novelty(
    data: dict,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user  = _get_user(authorization, db)
    title = data.get("title", "").strip()
    desc  = data.get("description", "").strip()

    if not title:
        raise HTTPException(status_code=400, detail="El título es obligatorio")
    if not desc:
        raise HTTPException(status_code=400, detail="La descripción es obligatoria")

    n = Novelty(
        company_id=user.company_id,
        user_id=user.id,
        title=title,
        description=desc,
        status="pendiente"
    )
    db.add(n)
    db.commit()
    db.refresh(n)
    return _ser(n, user.nombre, 0)


# ── PUT /novelties/{id} ──────────────────────────────────────────────────────
@router.put("/{novelty_id}")
def update_novelty(
    novelty_id: int,
    data: dict,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user    = _get_user(authorization, db)
    can_all = _can_manage_all(user, db)

    n = db.query(Novelty).filter(
        Novelty.id == novelty_id,
        Novelty.company_id == user.company_id
    ).first()
    if not n:
        raise HTTPException(status_code=404, detail="Novedad no encontrada")
    if not can_all and n.user_id != user.id:
        raise HTTPException(status_code=403, detail="Sin permiso para editar esta novedad")

    if data.get("title", "").strip():
        n.title = data["title"].strip()
    if data.get("description", "").strip():
        n.description = data["description"].strip()

    if can_all and "status" in data:
        if data["status"] in ("pendiente", "revisada", "resuelta"):
            n.status = data["status"]

    db.commit()
    db.refresh(n)
    author   = db.query(User).filter(User.id == n.user_id).first()
    ev_count = db.query(NoveltyEvidence).filter(NoveltyEvidence.novelty_id == n.id).count()
    return _ser(n, author.nombre if author else "Desconocido", ev_count)


# ── DELETE /novelties/{id} ───────────────────────────────────────────────────
@router.delete("/{novelty_id}")
def delete_novelty(
    novelty_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user    = _get_user(authorization, db)
    can_all = _can_manage_all(user, db)

    n = db.query(Novelty).filter(
        Novelty.id == novelty_id,
        Novelty.company_id == user.company_id
    ).first()
    if not n:
        raise HTTPException(status_code=404, detail="Novedad no encontrada")
    if not can_all and n.user_id != user.id:
        raise HTTPException(status_code=403, detail="Sin permiso para eliminar esta novedad")

    # Eliminar archivos del disco
    evidences = db.query(NoveltyEvidence).filter(NoveltyEvidence.novelty_id == n.id).all()
    for ev in evidences:
        fp = UPLOADS_DIR / Path(ev.file_url).name
        if fp.exists():
            fp.unlink()

    db.delete(n)
    db.commit()
    return {"ok": True}


# ── GET /novelties/{id}/evidence ─────────────────────────────────────────────
@router.get("/{novelty_id}/evidence")
def list_evidence(
    novelty_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)
    n    = db.query(Novelty).filter(
        Novelty.id == novelty_id,
        Novelty.company_id == user.company_id
    ).first()
    if not n:
        raise HTTPException(status_code=404, detail="Novedad no encontrada")

    evs = db.query(NoveltyEvidence).filter(
        NoveltyEvidence.novelty_id == novelty_id
    ).order_by(NoveltyEvidence.uploaded_at.asc()).all()
    return [_ser_ev(ev) for ev in evs]


# ── POST /novelties/{id}/evidence ────────────────────────────────────────────
@router.post("/{novelty_id}/evidence")
async def upload_evidence(
    novelty_id: int,
    file: UploadFile = File(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)
    n    = db.query(Novelty).filter(
        Novelty.id == novelty_id,
        Novelty.company_id == user.company_id
    ).first()
    if not n:
        raise HTTPException(status_code=404, detail="Novedad no encontrada")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(
            status_code=415,
            detail=f"Solo se permiten imágenes (jpg, jpeg, png, webp, gif). Formato recibido: {ext}"
        )

    file_type = "image"

    filename  = f"{novelty_id}_{uuid.uuid4().hex}{ext}"
    file_path = UPLOADS_DIR / filename
    total     = 0

    try:
        with open(file_path, "wb") as f:
            while True:
                chunk = await file.read(CHUNK)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_FILE_BYTES:
                    f.close()
                    file_path.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail="Archivo demasiado grande (máx 10 MB)")
                f.write(chunk)
    except HTTPException:
        raise
    except Exception:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Error al guardar el archivo")

    ev = NoveltyEvidence(
        novelty_id=novelty_id,
        file_url=f"/uploads/novelties/{filename}",
        file_type=file_type
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return _ser_ev(ev)


# ── DELETE /novelties/evidence/{evidence_id} ─────────────────────────────────
@router.delete("/evidence/{evidence_id}")
def delete_evidence(
    evidence_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)

    ev = db.query(NoveltyEvidence).filter(NoveltyEvidence.id == evidence_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")

    n = db.query(Novelty).filter(
        Novelty.id == ev.novelty_id,
        Novelty.company_id == user.company_id
    ).first()
    if not n:
        raise HTTPException(status_code=403, detail="Sin acceso")

    fp = UPLOADS_DIR / Path(ev.file_url).name
    fp.unlink(missing_ok=True)

    db.delete(ev)
    db.commit()
    return {"ok": True}
