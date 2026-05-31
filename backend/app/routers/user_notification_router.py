from fastapi import APIRouter, Depends, Header, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.user_notification_model import UserNotification
from app.models.user_model import User
from app.models.role_model import Role
from app.models.company_model import Company
from app.models.user_session_model import UserSession
from app.auth.jwt_handler import decode_access_token

router = APIRouter(prefix="/user-notifications", tags=["UserNotifications"])


async def _get_user(authorization: str, db: AsyncSession):
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


def _ser(n: UserNotification, sender_name: str = None, receiver_name: str = None, company_name: str = None):
    return {"id": n.id, "sender_id": n.sender_id, "sender_name": sender_name,
            "receiver_id": n.receiver_id, "receiver_name": receiver_name,
            "title": n.title, "message": n.message, "is_read": n.is_read,
            "company_name": company_name,
            "created_at": n.created_at.isoformat() if n.created_at else None}


_SYSTEM_ACCESS_TITLES = ("Entrada al sistema", "Salida del sistema")

async def _is_sysadmin(user: User, db: AsyncSession) -> bool:
    role = await db.get(Role, user.role_id)
    return bool(role and role.is_system)


@router.get("/inbox/count")
async def inbox_count(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    sysadmin = await _is_sysadmin(user, db)
    q = (
        select(func.count()).select_from(UserNotification)
        .where(
            UserNotification.is_read == False,
            UserNotification.title.notin_(_SYSTEM_ACCESS_TITLES),
        )
    )
    if not sysadmin:
        q = q.where(UserNotification.receiver_id == user.id)
    count = (await db.execute(q)).scalar()
    return {"count": count}


@router.get("/inbox")
async def inbox(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    sysadmin = await _is_sysadmin(user, db)
    q = (
        select(UserNotification, User, Company)
        .join(User, UserNotification.sender_id == User.id)
        .outerjoin(Company, User.company_id == Company.id_company)
        .order_by(UserNotification.created_at.desc())
    )
    if sysadmin:
        q = q.limit(200)
    else:
        q = q.where(UserNotification.receiver_id == user.id).limit(50)
    result = await db.execute(q)
    return [_ser(n, sender_name=u.nombre, company_name=c.name if c else None) for n, u, c in result.all()]


@router.get("/outbox")
async def outbox(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    result = await db.execute(
        select(UserNotification, User)
        .join(User, UserNotification.receiver_id == User.id)
        .where(UserNotification.sender_id == user.id)
        .order_by(UserNotification.created_at.desc())
        .limit(50)
    )
    return [_ser(n, receiver_name=u.nombre) for n, u in result.all()]


@router.get("/recipients")
async def list_recipients(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    me = await _get_user(authorization, db)
    result = await db.execute(
        select(User).where(User.company_id == me.company_id, User.is_active == True, User.id != me.id).order_by(User.nombre)
    )
    return [{"id": u.id, "nombre": u.nombre, "email": u.email} for u in result.scalars().all()]


@router.post("/send")
async def send_notification(data: dict = Body(...), authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    sender = await _get_user(authorization, db)
    receiver_id = data.get("receiver_id")
    title   = (data.get("title") or "").strip()
    message = (data.get("message") or "").strip()
    if not receiver_id or not title or not message:
        raise HTTPException(status_code=400, detail="receiver_id, title y message son requeridos")
    result = await db.execute(select(User).where(User.id == receiver_id, User.is_active == True))
    receiver = result.scalar_one_or_none()
    if not receiver:
        raise HTTPException(status_code=404, detail="Destinatario no encontrado")
    n = UserNotification(sender_id=sender.id, receiver_id=receiver.id, title=title, message=message, is_read=False)
    db.add(n)
    await db.commit()
    await db.refresh(n)
    return _ser(n, sender_name=sender.nombre, receiver_name=receiver.nombre)


@router.patch("/{notif_id}/read")
async def mark_read(notif_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    result = await db.execute(select(UserNotification).where(UserNotification.id == notif_id, UserNotification.receiver_id == user.id))
    n = result.scalar_one_or_none()
    if not n:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    n.is_read = True
    await db.commit()
    return {"ok": True}


@router.delete("/{notif_id}")
async def delete_notification(notif_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    result = await db.execute(select(UserNotification).where(UserNotification.id == notif_id, UserNotification.sender_id == user.id))
    n = result.scalar_one_or_none()
    if not n:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    await db.delete(n)
    await db.commit()
    return {"ok": True}
