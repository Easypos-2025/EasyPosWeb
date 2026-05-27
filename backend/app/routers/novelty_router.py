import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.novelty_model import Novelty, NoveltyEvidence, NoveltyReply
from app.models.user_model import User
from app.models.role_model import Role
from app.models.user_session_model import UserSession
from app.auth.jwt_handler import decode_access_token
from app.utils.storage import upload_file

router = APIRouter(prefix="/novelties", tags=["Novelties"])

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads" / "novelties"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_BYTES = 10 * 1024 * 1024
CHUNK = 256 * 1024
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


async def _get_user(authorization: str, db: AsyncSession) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    result = await db.execute(select(UserSession).where(UserSession.token == token, UserSession.is_active == True))
    if not result.scalar_one_or_none() or not payload:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    uid = payload.get("user_id")
    user = await db.get(User, int(uid)) if uid else None
    if not user:
        result = await db.execute(select(User).where(User.email == payload.get("sub")))
        user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


async def _get_role(user: User, db: AsyncSession):
    result = await db.execute(select(Role).where(Role.id == user.role_id))
    return result.scalar_one_or_none()


async def _can_manage_all(user: User, db: AsyncSession) -> bool:
    role = await _get_role(user, db)
    if not role:
        return False
    if role.is_system:
        return True
    name = role.name.lower().strip()
    return name == "admin" or name == "auditor"


def _ser(n: Novelty, user_name="", evidence_count=0):
    return {"id": n.id, "company_id": n.company_id, "user_id": n.user_id, "user_name": user_name,
            "title": n.title, "description": n.description, "status": n.status,
            "evidence_count": evidence_count,
            "created_at": n.created_at.isoformat() if n.created_at else None,
            "updated_at": n.updated_at.isoformat() if n.updated_at else None}

def _ser_reply(r: NoveltyReply, user_name):
    return {"id": r.id, "novelty_id": r.novelty_id, "user_id": r.user_id, "user_name": user_name,
            "message": r.message, "created_at": r.created_at.isoformat() if r.created_at else None}

def _ser_ev(ev: NoveltyEvidence):
    return {"id": ev.id, "novelty_id": ev.novelty_id, "file_url": ev.file_url,
            "file_type": ev.file_type, "uploaded_at": ev.uploaded_at.isoformat() if ev.uploaded_at else None}


@router.get("/users-list")
async def list_novelty_users(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    if not await _can_manage_all(user, db):
        raise HTTPException(status_code=403, detail="Sin permiso")
    role = await _get_role(user, db)
    is_sys = role.is_system if role else False
    stmt = select(Novelty.user_id).distinct()
    if not is_sys:
        stmt = stmt.where(Novelty.company_id == user.company_id)
    result = await db.execute(stmt)
    ids = [r[0] for r in result.all()]
    result = await db.execute(select(User).where(User.id.in_(ids)).order_by(User.nombre))
    return [{"id": u.id, "nombre": u.nombre} for u in result.scalars().all()]


@router.get("")
async def list_novelties(
    filter_user_id: Optional[int] = Query(None), date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None), authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    can_all = await _can_manage_all(user, db)
    role = await _get_role(user, db)
    is_sys = role.is_system if role else False

    conds = []
    if not can_all:
        conds += [Novelty.company_id == user.company_id, Novelty.user_id == user.id]
    elif not is_sys:
        conds.append(Novelty.company_id == user.company_id)
    if can_all and filter_user_id:
        conds.append(Novelty.user_id == filter_user_id)
    if date_from:
        try:
            conds.append(Novelty.created_at >= datetime.fromisoformat(date_from[:10]))
        except ValueError:
            pass
    if date_to:
        try:
            conds.append(Novelty.created_at <= datetime.fromisoformat(date_to[:10]).replace(hour=23, minute=59, second=59))
        except ValueError:
            pass

    result = await db.execute(select(Novelty).where(*conds).order_by(Novelty.created_at.desc()))
    novelties = result.scalars().all()
    if not novelties:
        return []

    novelty_ids = [n.id for n in novelties]
    user_ids = {n.user_id for n in novelties}

    # Batch: todas las respuestas de estas novedades
    replies_r = await db.execute(
        select(NoveltyReply)
        .where(NoveltyReply.novelty_id.in_(novelty_ids))
        .order_by(NoveltyReply.created_at.asc())
    )
    all_replies = replies_r.scalars().all()
    user_ids.update(r.user_id for r in all_replies)

    # Batch: conteo de evidencias
    ev_rows = await db.execute(
        select(NoveltyEvidence.novelty_id, func.count().label("cnt"))
        .where(NoveltyEvidence.novelty_id.in_(novelty_ids))
        .group_by(NoveltyEvidence.novelty_id)
    )
    ev_counts = {r.novelty_id: r.cnt for r in ev_rows.all()}

    # Batch: todos los usuarios necesarios
    users_r = await db.execute(select(User).where(User.id.in_(list(user_ids))))
    users_map = {u.id: u.nombre for u in users_r.scalars().all()}

    # Agrupar respuestas por novedad
    replies_by_novelty: dict[int, list] = {}
    for r in all_replies:
        replies_by_novelty.setdefault(r.novelty_id, []).append(
            _ser_reply(r, users_map.get(r.user_id, "Desconocido"))
        )

    items = []
    for n in novelties:
        item = _ser(n, users_map.get(n.user_id, "Desconocido"), ev_counts.get(n.id, 0))
        item["replies"] = replies_by_novelty.get(n.id, [])
        items.append(item)
    return items


@router.post("")
async def create_novelty(data: dict, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    title = data.get("title", "").strip()
    desc = (data.get("description") or "").strip() or None
    if not title:
        raise HTTPException(status_code=400, detail="El título es obligatorio")
    n = Novelty(company_id=user.company_id, user_id=user.id, title=title, description=desc, status="pendiente")
    db.add(n)
    await db.commit()
    await db.refresh(n)
    return _ser(n, user.nombre, 0)


@router.put("/{novelty_id}")
async def update_novelty(novelty_id: int, data: dict, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    can_all = await _can_manage_all(user, db)
    result = await db.execute(select(Novelty).where(Novelty.id == novelty_id))
    n = result.scalar_one_or_none()
    if not n or (not (await _get_role(user, db)).is_system and n.company_id != user.company_id):
        raise HTTPException(status_code=404, detail="Novedad no encontrada")
    if not can_all and n.user_id != user.id:
        raise HTTPException(status_code=403, detail="Sin permiso para editar esta novedad")
    if data.get("title", "").strip():
        n.title = data["title"].strip()
    if data.get("description", "").strip():
        n.description = data["description"].strip()
    if can_all and "status" in data and data["status"] in ("pendiente", "revisada", "resuelta"):
        n.status = data["status"]
    await db.commit()
    await db.refresh(n)
    author_r = await db.execute(select(User).where(User.id == n.user_id))
    author = author_r.scalar_one_or_none()
    ev_count = (await db.execute(select(func.count()).select_from(NoveltyEvidence).where(NoveltyEvidence.novelty_id == n.id))).scalar()
    return _ser(n, author.nombre if author else "Desconocido", ev_count)


@router.delete("/{novelty_id}")
async def delete_novelty(novelty_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    can_all = await _can_manage_all(user, db)
    role = await _get_role(user, db)
    result = await db.execute(select(Novelty).where(Novelty.id == novelty_id))
    n = result.scalar_one_or_none()
    if not n or (not role.is_system and n.company_id != user.company_id):
        raise HTTPException(status_code=404, detail="Novedad no encontrada")
    if not can_all and n.user_id != user.id:
        raise HTTPException(status_code=403, detail="Sin permiso para eliminar esta novedad")
    result = await db.execute(select(NoveltyEvidence).where(NoveltyEvidence.novelty_id == n.id))
    for ev in result.scalars().all():
        fp = UPLOADS_DIR / Path(ev.file_url).name
        if fp.exists():
            fp.unlink()
    await db.delete(n)
    await db.commit()
    return {"ok": True}


@router.get("/{novelty_id}/evidence")
async def list_evidence(novelty_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    result = await db.execute(select(NoveltyEvidence).where(NoveltyEvidence.novelty_id == novelty_id).order_by(NoveltyEvidence.uploaded_at.asc()))
    return [_ser_ev(ev) for ev in result.scalars().all()]


@router.post("/{novelty_id}/evidence")
async def upload_evidence(novelty_id: int, file: UploadFile = File(...), authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=415, detail=f"Solo imágenes (jpg, png, webp, gif). Recibido: {ext}")
    filename = f"{novelty_id}_{uuid.uuid4().hex}{ext}"
    content = await file.read()
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="Archivo demasiado grande (máx 10 MB)")
    try:
        file_url = await upload_file(content, f"novelties/{filename}")
    except Exception:
        raise HTTPException(status_code=500, detail="Error al guardar el archivo")
    ev = NoveltyEvidence(novelty_id=novelty_id, file_url=file_url, file_type="image")
    db.add(ev)
    await db.commit()
    await db.refresh(ev)
    return _ser_ev(ev)


@router.get("/{novelty_id}/replies")
async def list_replies(novelty_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    result = await db.execute(select(NoveltyReply).where(NoveltyReply.novelty_id == novelty_id).order_by(NoveltyReply.created_at.asc()))
    replies = result.scalars().all()
    items = []
    for r in replies:
        author_r = await db.execute(select(User).where(User.id == r.user_id))
        author = author_r.scalar_one_or_none()
        items.append(_ser_reply(r, author.nombre if author else "Desconocido"))
    return items


@router.post("/{novelty_id}/replies")
async def create_reply(novelty_id: int, data: dict, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    if not await _can_manage_all(user, db):
        raise HTTPException(status_code=403, detail="Sin permiso para responder novedades")
    message = (data.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío")
    r = NoveltyReply(novelty_id=novelty_id, user_id=user.id, message=message)
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return _ser_reply(r, user.nombre)


@router.delete("/replies/{reply_id}")
async def delete_reply(reply_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    can_all = await _can_manage_all(user, db)
    result = await db.execute(select(NoveltyReply).where(NoveltyReply.id == reply_id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Respuesta no encontrada")
    if not can_all and r.user_id != user.id:
        raise HTTPException(status_code=403, detail="Sin permiso para eliminar esta respuesta")
    await db.delete(r)
    await db.commit()
    return {"ok": True}


@router.delete("/evidence/{evidence_id}")
async def delete_evidence(evidence_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    result = await db.execute(select(NoveltyEvidence).where(NoveltyEvidence.id == evidence_id))
    ev = result.scalar_one_or_none()
    if not ev:
        raise HTTPException(status_code=404, detail="Evidencia no encontrada")
    fp = UPLOADS_DIR / Path(ev.file_url).name
    fp.unlink(missing_ok=True)
    await db.delete(ev)
    await db.commit()
    return {"ok": True}
