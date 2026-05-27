from fastapi import APIRouter, Depends, Header, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.task_comment_model import TaskComment
from app.models.task_model import Task
from app.models.user_model import User
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession

router = APIRouter(prefix="/task-comments", tags=["TaskComments"])


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


def _ser(c: TaskComment, task_title: str = None, sender_name: str = None):
    return {
        "id": c.id, "task_id": c.task_id, "task_title": task_title,
        "user_id": c.user_id, "sender_name": sender_name, "comment": c.comment,
        "is_notification": c.is_notification, "is_read": c.is_read,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


@router.get("/notifications/unread")
async def get_unread_notifications(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    result = await db.execute(
        select(TaskComment, Task, User)
        .join(Task, TaskComment.task_id == Task.id)
        .join(User, TaskComment.user_id == User.id, isouter=True)
        .where(Task.assigned_to == user.id, TaskComment.is_notification == True, TaskComment.is_read == False)
        .order_by(TaskComment.created_at.desc())
        .limit(30)
    )
    return [_ser(c, task_title=t.title, sender_name=u.nombre if u else None) for c, t, u in result.all()]


@router.get("/{task_id}")
async def get_comments(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TaskComment, User)
        .join(User, TaskComment.user_id == User.id, isouter=True)
        .where(TaskComment.task_id == task_id)
        .order_by(TaskComment.created_at.asc())
    )
    return [_ser(c, sender_name=u.nombre if u else None) for c, u in result.all()]


@router.post("/{task_id}")
async def add_comment(
    task_id: int,
    data: dict = Body(...),
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    text = data.get("comment", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="El comentario no puede estar vacío")
    c = TaskComment(task_id=task_id, user_id=user.id, comment=text,
                    is_notification=bool(data.get("is_notification", False)), is_read=False)
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return _ser(c, sender_name=user.nombre)


@router.patch("/{comment_id}/read")
async def mark_read(comment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskComment).where(TaskComment.id == comment_id))
    c = result.scalar_one_or_none()
    if c:
        c.is_read = True
        await db.commit()
    return {"ok": True}
