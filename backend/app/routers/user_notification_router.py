from fastapi import APIRouter, Depends, Header, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user_notification_model import UserNotification
from app.models.user_model import User
from app.models.user_session_model import UserSession
from app.auth.jwt_handler import decode_access_token

router = APIRouter(prefix="/user-notifications", tags=["UserNotifications"])


def _get_user(authorization: str, db: Session):
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


def _ser(n: UserNotification, sender_name: str = None, receiver_name: str = None):
    return {
        "id":            n.id,
        "sender_id":     n.sender_id,
        "sender_name":   sender_name,
        "receiver_id":   n.receiver_id,
        "receiver_name": receiver_name,
        "title":         n.title,
        "message":       n.message,
        "is_read":       n.is_read,
        "created_at":    n.created_at.isoformat() if n.created_at else None,
    }


@router.get("/inbox/count")
def inbox_count(authorization: str = Header(None), db: Session = Depends(get_db)):
    user  = _get_user(authorization, db)
    count = db.query(UserNotification).filter(
        UserNotification.receiver_id == user.id,
        UserNotification.is_read     == False,
    ).count()
    return {"count": count}


@router.get("/inbox")
def inbox(authorization: str = Header(None), db: Session = Depends(get_db)):
    user = _get_user(authorization, db)
    rows = (
        db.query(UserNotification, User)
        .join(User, UserNotification.sender_id == User.id)
        .filter(UserNotification.receiver_id == user.id)
        .order_by(UserNotification.created_at.desc())
        .limit(50)
        .all()
    )
    return [_ser(n, sender_name=u.nombre) for n, u in rows]


@router.get("/outbox")
def outbox(authorization: str = Header(None), db: Session = Depends(get_db)):
    user = _get_user(authorization, db)
    rows = (
        db.query(UserNotification, User)
        .join(User, UserNotification.receiver_id == User.id)
        .filter(UserNotification.sender_id == user.id)
        .order_by(UserNotification.created_at.desc())
        .limit(50)
        .all()
    )
    return [_ser(n, receiver_name=u.nombre) for n, u in rows]


@router.get("/recipients")
def list_recipients(authorization: str = Header(None), db: Session = Depends(get_db)):
    """Usuarios de la misma empresa disponibles como destinatarios."""
    me = _get_user(authorization, db)
    users = (
        db.query(User)
        .filter(User.company_id == me.company_id, User.is_active == True, User.id != me.id)
        .order_by(User.nombre)
        .all()
    )
    return [{"id": u.id, "nombre": u.nombre, "email": u.email} for u in users]


@router.post("/send")
def send_notification(
    data: dict = Body(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    sender = _get_user(authorization, db)

    receiver_id = data.get("receiver_id")
    title       = (data.get("title") or "").strip()
    message     = (data.get("message") or "").strip()

    if not receiver_id or not title or not message:
        raise HTTPException(status_code=400, detail="receiver_id, title y message son requeridos")

    receiver = db.query(User).filter(User.id == receiver_id, User.is_active == True).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Destinatario no encontrado")

    n = UserNotification(
        sender_id=sender.id,
        receiver_id=receiver.id,
        title=title,
        message=message,
        is_read=False,
    )
    db.add(n)
    db.commit()
    db.refresh(n)
    return _ser(n, sender_name=sender.nombre, receiver_name=receiver.nombre)


@router.patch("/{notif_id}/read")
def mark_read(notif_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = _get_user(authorization, db)
    n    = db.query(UserNotification).filter(
        UserNotification.id == notif_id,
        UserNotification.receiver_id == user.id,
    ).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    n.is_read = True
    db.commit()
    return {"ok": True}


@router.delete("/{notif_id}")
def delete_notification(notif_id: int, authorization: str = Header(None), db: Session = Depends(get_db)):
    user = _get_user(authorization, db)
    n    = db.query(UserNotification).filter(
        UserNotification.id == notif_id,
        UserNotification.sender_id == user.id,
    ).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    db.delete(n)
    db.commit()
    return {"ok": True}
