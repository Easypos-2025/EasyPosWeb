from fastapi import APIRouter, Depends, Header, HTTPException, Body
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.database import get_db, Base
from app.models.user_model import User
from app.models.task_model import Task
from app.models.role_model import Role
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession

router = APIRouter(prefix="/task-collaborators", tags=["TaskCollaborators"])


class TaskCollaborator(Base):
    __tablename__ = "colaborador_tarea"
    __table_args__ = {"extend_existing": True}
    id          = Column(Integer, primary_key=True, autoincrement=True)
    task_id     = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)


async def _get_user(authorization: str, db: AsyncSession) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    result = await db.execute(select(UserSession).where(UserSession.token == token, UserSession.is_active == True))
    if not result.scalar_one_or_none() or payload is None:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    result = await db.execute(select(User).where(User.email == payload.get("sub")))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


async def _can_manage(user: User, db: AsyncSession) -> bool:
    result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = result.scalar_one_or_none()
    return "worker" not in (role.name or "").lower() if role else True


@router.get("/{task_id}")
async def list_collaborators(task_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_user(authorization, db)
    result = await db.execute(select(TaskCollaborator).where(TaskCollaborator.task_id == task_id).order_by(TaskCollaborator.assigned_at.asc()))
    rows = result.scalars().all()
    items = []
    for r in rows:
        u_result = await db.execute(select(User).where(User.id == r.user_id))
        u = u_result.scalar_one_or_none()
        if u:
            role_result = await db.execute(select(Role).where(Role.id == u.role_id))
            role = role_result.scalar_one_or_none()
            items.append({"id": r.id, "task_id": r.task_id, "user_id": r.user_id, "nombre": u.nombre,
                          "email": u.email, "role": role.name if role else "",
                          "assigned_at": r.assigned_at.isoformat() if r.assigned_at else None})
    return items


@router.post("/{task_id}")
async def add_collaborator(task_id: int, data: dict = Body(...), authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    requester = await _get_user(authorization, db)
    if not await _can_manage(requester, db):
        raise HTTPException(status_code=403, detail="Solo roles superiores pueden asignar colaboradores")
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=422, detail="user_id es requerido")
    result = await db.execute(select(User).where(User.id == user_id))
    collab_user = result.scalar_one_or_none()
    if not collab_user:
        raise HTTPException(status_code=404, detail="Usuario colaborador no encontrado")
    result = await db.execute(select(TaskCollaborator).where(TaskCollaborator.task_id == task_id, TaskCollaborator.user_id == user_id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Este usuario ya es colaborador de la tarea")
    if task.assigned_to == user_id:
        raise HTTPException(status_code=409, detail="El responsable principal no puede ser colaborador")
    new = TaskCollaborator(task_id=task_id, user_id=user_id, assigned_by=requester.id, assigned_at=datetime.utcnow())
    db.add(new)
    await db.commit()
    await db.refresh(new)
    result = await db.execute(select(Role).where(Role.id == collab_user.role_id))
    role = result.scalar_one_or_none()
    return {"id": new.id, "task_id": new.task_id, "user_id": new.user_id, "nombre": collab_user.nombre,
            "email": collab_user.email, "role": role.name if role else "",
            "assigned_at": new.assigned_at.isoformat()}


@router.delete("/{task_id}/{user_id}")
async def remove_collaborator(task_id: int, user_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    requester = await _get_user(authorization, db)
    if not await _can_manage(requester, db):
        raise HTTPException(status_code=403, detail="Solo roles superiores pueden quitar colaboradores")
    result = await db.execute(select(TaskCollaborator).where(TaskCollaborator.task_id == task_id, TaskCollaborator.user_id == user_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Colaborador no encontrado en esta tarea")
    await db.delete(row)
    await db.commit()
    return {"detail": "Colaborador eliminado"}
