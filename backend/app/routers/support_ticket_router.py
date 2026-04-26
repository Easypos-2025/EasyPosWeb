import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.support_ticket_model import SupportTicket, TicketEvidence
from app.models.user_model import User
from app.models.role_model import Role
from app.models.company_model import Company
from app.models.user_session_model import UserSession
from app.auth.jwt_handler import decode_access_token

router = APIRouter(prefix="/support-tickets", tags=["SupportTickets"])

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads" / "tickets"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_BYTES = 10 * 1024 * 1024
CHUNK          = 256 * 1024

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".pdf", ".mp4", ".mov"}
IMG_EXT     = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXT   = {".mp4", ".mov"}

VALID_STATUSES   = ("abierto", "en_proceso", "resuelto", "cerrado")
VALID_PRIORITIES = ("baja", "media", "alta", "critica")


# ── Helpers ──────────────────────────────────────────────────────────────────
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


def _role_level(user: User, db: Session) -> str:
    """Returns 'sysadmin' | 'manager' (admin/auditor) | 'user'"""
    role = db.query(Role).filter(Role.id == user.role_id).first()
    if not role:
        return "user"
    if role.is_system:
        return "sysadmin"
    name = role.name.lower()
    if "admin" in name or "auditor" in name:
        return "manager"
    return "user"


def _ser(t: SupportTicket, user_name: str = "", company_name: str = "", ev_count: int = 0) -> dict:
    return {
        "id":            t.id,
        "company_id":    t.company_id,
        "company_name":  company_name,
        "user_id":       t.user_id,
        "user_name":     user_name,
        "title":         t.title,
        "description":   t.description,
        "status":        t.status,
        "priority":      t.priority,
        "evidence_count": ev_count,
        "created_at":    t.created_at.isoformat() if t.created_at else None,
        "updated_at":    t.updated_at.isoformat() if t.updated_at else None,
    }


def _ser_ev(ev: TicketEvidence) -> dict:
    return {
        "id":          ev.id,
        "ticket_id":   ev.ticket_id,
        "file_url":    ev.file_url,
        "file_type":   ev.file_type,
        "uploaded_at": ev.uploaded_at.isoformat() if ev.uploaded_at else None,
    }


def _enrich(t: SupportTicket, db: Session) -> dict:
    author  = db.query(User).filter(User.id == t.user_id).first()
    company = db.query(Company).filter(Company.id_company == t.company_id).first()
    ev_cnt  = db.query(TicketEvidence).filter(TicketEvidence.ticket_id == t.id).count()
    return _ser(
        t,
        user_name    = author.nombre  if author  else "Desconocido",
        company_name = company.name   if company else "",
        ev_count     = ev_cnt
    )


# ── GET /support-tickets ─────────────────────────────────────────────────────
@router.get("")
def list_tickets(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user  = _get_user(authorization, db)
    level = _role_level(user, db)

    query = db.query(SupportTicket)

    if level == "sysadmin":
        pass                                             # ve todos sin filtro
    elif level == "manager":
        query = query.filter(SupportTicket.company_id == user.company_id)
    else:
        query = query.filter(
            SupportTicket.company_id == user.company_id,
            SupportTicket.user_id    == user.id
        )

    tickets = query.order_by(SupportTicket.created_at.desc()).all()
    return [_enrich(t, db) for t in tickets]


# ── POST /support-tickets ────────────────────────────────────────────────────
@router.post("")
def create_ticket(
    data: dict,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user     = _get_user(authorization, db)
    title    = data.get("title", "").strip()
    desc     = data.get("description", "").strip()
    priority = data.get("priority", "media")

    if not title:
        raise HTTPException(status_code=400, detail="El título es obligatorio")
    if not desc:
        raise HTTPException(status_code=400, detail="La descripción es obligatoria")
    if priority not in VALID_PRIORITIES:
        priority = "media"

    t = SupportTicket(
        company_id  = user.company_id,
        user_id     = user.id,
        title       = title,
        description = desc,
        priority    = priority,
        status      = "abierto"
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return _enrich(t, db)


# ── PUT /support-tickets/{id} ────────────────────────────────────────────────
@router.put("/{ticket_id}")
def update_ticket(
    ticket_id: int,
    data: dict,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user  = _get_user(authorization, db)
    level = _role_level(user, db)

    t = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    # Acceso: sysadmin ve todo; manager ve su empresa; user solo el suyo
    if level == "user":
        if t.company_id != user.company_id or t.user_id != user.id:
            raise HTTPException(status_code=403, detail="Sin permiso")
    elif level == "manager":
        if t.company_id != user.company_id:
            raise HTTPException(status_code=403, detail="Sin permiso")

    # Campos editables por el creador
    if t.user_id == user.id or level in ("manager", "sysadmin"):
        if data.get("title", "").strip():
            t.title = data["title"].strip()
        if data.get("description", "").strip():
            t.description = data["description"].strip()
        if data.get("priority") in VALID_PRIORITIES:
            t.priority = data["priority"]

    # Estado solo para manager / sysadmin
    if level in ("manager", "sysadmin") and data.get("status") in VALID_STATUSES:
        t.status = data["status"]

    db.commit()
    db.refresh(t)
    return _enrich(t, db)


# ── DELETE /support-tickets/{id} ─────────────────────────────────────────────
@router.delete("/{ticket_id}")
def delete_ticket(
    ticket_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user  = _get_user(authorization, db)
    level = _role_level(user, db)

    t = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    if level == "user" and (t.company_id != user.company_id or t.user_id != user.id):
        raise HTTPException(status_code=403, detail="Sin permiso")
    if level == "manager" and t.company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Sin permiso")

    evidences = db.query(TicketEvidence).filter(TicketEvidence.ticket_id == t.id).all()
    for ev in evidences:
        fp = UPLOADS_DIR / Path(ev.file_url).name
        fp.unlink(missing_ok=True)

    db.delete(t)
    db.commit()
    return {"ok": True}


# ── GET /support-tickets/{id}/evidence ───────────────────────────────────────
@router.get("/{ticket_id}/evidence")
def list_evidence(
    ticket_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user  = _get_user(authorization, db)
    level = _role_level(user, db)

    t = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    if level == "user" and (t.company_id != user.company_id or t.user_id != user.id):
        raise HTTPException(status_code=403, detail="Sin acceso")
    if level == "manager" and t.company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Sin acceso")

    evs = db.query(TicketEvidence).filter(
        TicketEvidence.ticket_id == ticket_id
    ).order_by(TicketEvidence.uploaded_at.asc()).all()
    return [_ser_ev(ev) for ev in evs]


# ── POST /support-tickets/{id}/evidence ──────────────────────────────────────
@router.post("/{ticket_id}/evidence")
async def upload_evidence(
    ticket_id: int,
    file: UploadFile = File(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)

    t = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if t.company_id != user.company_id and _role_level(user, db) != "sysadmin":
        raise HTTPException(status_code=403, detail="Sin acceso")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=415, detail=f"Formato no permitido: {ext}")

    file_type = "image" if ext in IMG_EXT else "video" if ext in VIDEO_EXT else "document"
    filename  = f"{ticket_id}_{uuid.uuid4().hex}{ext}"
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

    ev = TicketEvidence(
        ticket_id = ticket_id,
        file_url  = f"/uploads/tickets/{filename}",
        file_type = file_type
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return _ser_ev(ev)


# ── DELETE /support-tickets/evidence/{id} ────────────────────────────────────
@router.delete("/evidence/{evidence_id}")
def delete_evidence(
    evidence_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user  = _get_user(authorization, db)
    level = _role_level(user, db)

    ev = db.query(TicketEvidence).filter(TicketEvidence.id == evidence_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")

    t = db.query(SupportTicket).filter(SupportTicket.id == ev.ticket_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    if level == "user" and (t.company_id != user.company_id or t.user_id != user.id):
        raise HTTPException(status_code=403, detail="Sin permiso")
    if level == "manager" and t.company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Sin permiso")

    fp = UPLOADS_DIR / Path(ev.file_url).name
    fp.unlink(missing_ok=True)

    db.delete(ev)
    db.commit()
    return {"ok": True}
