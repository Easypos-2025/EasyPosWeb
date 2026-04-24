from fastapi import APIRouter, Depends, Header, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.task_comment_model import TaskComment
from app.models.user_model import User
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession

router = APIRouter(prefix="/task-comments", tags=["TaskComments"])


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


@router.get("/{task_id}")
def get_comments(task_id: int, db: Session = Depends(get_db)):
    items = db.query(TaskComment).filter(
        TaskComment.task_id == task_id
    ).order_by(TaskComment.created_at.asc()).all()
    return [_ser(c) for c in items]


@router.post("/{task_id}")
def add_comment(
    task_id: int,
    data: dict = Body(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)
    text = data.get("comment", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="El comentario no puede estar vacío")

    c = TaskComment(
        task_id=         task_id,
        user_id=         user.id,
        comment=         text,
        is_notification= bool(data.get("is_notification", False)),
        is_read=         False,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return _ser(c)


@router.patch("/{comment_id}/read")
def mark_read(comment_id: int, db: Session = Depends(get_db)):
    c = db.query(TaskComment).filter(TaskComment.id == comment_id).first()
    if c:
        c.is_read = True
        db.commit()
    return {"ok": True}


@router.get("/notifications/unread")
def get_unread_notifications(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Notificaciones no leídas para el Task Leader logueado (para el SidebarRight)."""
    user  = _get_user(authorization, db)
    items = db.query(TaskComment).join(
        __import__("app.models.task_model", fromlist=["Task"]).Task,
        TaskComment.task_id == __import__("app.models.task_model", fromlist=["Task"]).Task.id
    ).filter(
        __import__("app.models.task_model", fromlist=["Task"]).Task.assigned_to == user.id,
        TaskComment.is_notification == True,
        TaskComment.is_read == False
    ).order_by(TaskComment.created_at.desc()).limit(20).all()
    return [_ser(c) for c in items]


def _ser(c: TaskComment):
    return {
        "id":              c.id,
        "task_id":         c.task_id,
        "user_id":         c.user_id,
        "comment":         c.comment,
        "is_notification": c.is_notification,
        "is_read":         c.is_read,
        "created_at":      c.created_at.isoformat() if c.created_at else None,
    }
