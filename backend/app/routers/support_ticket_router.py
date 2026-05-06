import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.support_ticket_model import SupportTicket, TicketEvidence
from app.models.user_model import User
from app.models.role_model import Role
from app.models.company_model import Company
from app.models.user_session_model import UserSession
from app.auth.jwt_handler import decode_access_token
from app.utils.storage import upload_file

router = APIRouter(prefix="/support-tickets", tags=["SupportTickets"])

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads" / "tickets"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_BYTES = 10 * 1024 * 1024
CHUNK = 256 * 1024
ALLOWED_EXT  = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".pdf", ".mp4", ".mov"}
IMG_EXT      = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXT    = {".mp4", ".mov"}
VALID_STATUSES   = ("abierto", "en_proceso", "resuelto", "cerrado")
VALID_PRIORITIES = ("baja", "media", "alta", "critica")


async def _get_user(authorization: str, db: AsyncSession) -> User:
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
    return user


async def _role_level(user: User, db: AsyncSession) -> str:
    result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = result.scalar_one_or_none()
    if not role:
        return "user"
    if role.is_system:
        return "sysadmin"
    name = role.name.lower()
    if "admin" in name or "auditor" in name:
        return "manager"
    return "user"


def _ser(t: SupportTicket, user_name="", company_name="", ev_count=0):
    return {"id": t.id, "company_id": t.company_id, "company_name": company_name,
            "user_id": t.user_id, "user_name": user_name, "title": t.title,
            "description": t.description, "status": t.status, "priority": t.priority,
            "evidence_count": ev_count, "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None}

def _ser_ev(ev: TicketEvidence):
    return {"id": ev.id, "ticket_id": ev.ticket_id, "file_url": ev.file_url,
            "file_type": ev.file_type, "uploaded_at": ev.uploaded_at.isoformat() if ev.uploaded_at else None}


async def _enrich(t: SupportTicket, db: AsyncSession) -> dict:
    author_r = await db.execute(select(User).where(User.id == t.user_id))
    author = author_r.scalar_one_or_none()
    company_r = await db.execute(select(Company).where(Company.id_company == t.company_id))
    company = company_r.scalar_one_or_none()
    ev_cnt = (await db.execute(select(func.count()).select_from(TicketEvidence).where(TicketEvidence.ticket_id == t.id))).scalar()
    return _ser(t, user_name=author.nombre if author else "Desconocido",
                company_name=company.name if company else "", ev_count=ev_cnt)


@router.get("")
async def list_tickets(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    level = await _role_level(user, db)
    stmt = select(SupportTicket)
    if level == "manager":
        stmt = stmt.where(SupportTicket.company_id == user.company_id)
    elif level == "user":
        stmt = stmt.where(SupportTicket.company_id == user.company_id, SupportTicket.user_id == user.id)
    result = await db.execute(stmt.order_by(SupportTicket.created_at.desc()))
    return [await _enrich(t, db) for t in result.scalars().all()]


@router.post("")
async def create_ticket(data: dict, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    title = data.get("title", "").strip()
    desc = data.get("description", "").strip()
    priority = data.get("priority", "media")
    if not title:
        raise HTTPException(status_code=400, detail="El título es obligatorio")
    if not desc:
        raise HTTPException(status_code=400, detail="La descripción es obligatoria")
    if priority not in VALID_PRIORITIES:
        priority = "media"
    t = SupportTicket(company_id=user.company_id, user_id=user.id, title=title,
                      description=desc, priority=priority, status="abierto")
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return await _enrich(t, db)


@router.put("/{ticket_id}")
async def update_ticket(ticket_id: int, data: dict, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    level = await _role_level(user, db)
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if level == "user" and (t.company_id != user.company_id or t.user_id != user.id):
        raise HTTPException(status_code=403, detail="Sin permiso")
    elif level == "manager" and t.company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Sin permiso")
    if t.user_id == user.id or level in ("manager", "sysadmin"):
        if data.get("title", "").strip():
            t.title = data["title"].strip()
        if data.get("description", "").strip():
            t.description = data["description"].strip()
        if data.get("priority") in VALID_PRIORITIES:
            t.priority = data["priority"]
    if level in ("manager", "sysadmin") and data.get("status") in VALID_STATUSES:
        t.status = data["status"]
    await db.commit()
    await db.refresh(t)
    return await _enrich(t, db)


@router.delete("/{ticket_id}")
async def delete_ticket(ticket_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    level = await _role_level(user, db)
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if level == "user" and (t.company_id != user.company_id or t.user_id != user.id):
        raise HTTPException(status_code=403, detail="Sin permiso")
    if level == "manager" and t.company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Sin permiso")
    result = await db.execute(select(TicketEvidence).where(TicketEvidence.ticket_id == t.id))
    for ev in result.scalars().all():
        fp = UPLOADS_DIR / Path(ev.file_url).name
        fp.unlink(missing_ok=True)
    await db.delete(t)
    await db.commit()
    return {"ok": True}


@router.get("/{ticket_id}/evidence")
async def list_evidence(ticket_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    level = await _role_level(user, db)
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if level == "user" and (t.company_id != user.company_id or t.user_id != user.id):
        raise HTTPException(status_code=403, detail="Sin acceso")
    if level == "manager" and t.company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Sin acceso")
    result = await db.execute(select(TicketEvidence).where(TicketEvidence.ticket_id == ticket_id).order_by(TicketEvidence.uploaded_at.asc()))
    return [_ser_ev(ev) for ev in result.scalars().all()]


@router.post("/{ticket_id}/evidence")
async def upload_evidence(ticket_id: int, file: UploadFile = File(...), authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    level = await _role_level(user, db)
    if t.company_id != user.company_id and level != "sysadmin":
        raise HTTPException(status_code=403, detail="Sin acceso")
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=415, detail=f"Formato no permitido: {ext}")
    file_type = "image" if ext in IMG_EXT else "video" if ext in VIDEO_EXT else "document"
    filename = f"{ticket_id}_{uuid.uuid4().hex}{ext}"
    content = await file.read()
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="Archivo demasiado grande (máx 10 MB)")
    try:
        file_url = await upload_file(content, f"tickets/{filename}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error al guardar el archivo")
    ev = TicketEvidence(ticket_id=ticket_id, file_url=file_url, file_type=file_type)
    db.add(ev)
    await db.commit()
    await db.refresh(ev)
    return _ser_ev(ev)


@router.delete("/evidence/{evidence_id}")
async def delete_evidence(evidence_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    level = await _role_level(user, db)
    result = await db.execute(select(TicketEvidence).where(TicketEvidence.id == evidence_id))
    ev = result.scalar_one_or_none()
    if not ev:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ev.ticket_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    if level == "user" and (t.company_id != user.company_id or t.user_id != user.id):
        raise HTTPException(status_code=403, detail="Sin permiso")
    if level == "manager" and t.company_id != user.company_id:
        raise HTTPException(status_code=403, detail="Sin permiso")
    fp = UPLOADS_DIR / Path(ev.file_url).name
    fp.unlink(missing_ok=True)
    await db.delete(ev)
    await db.commit()
    return {"ok": True}
