from fastapi import APIRouter, Depends, Header, HTTPException, Body
from sqlalchemy import Column, Integer, DateTime, ForeignKey, text
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db, Base
from app.models.user_model import User
from app.models.task_model import Task
from app.models.role_model import Role
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession

router = APIRouter(prefix="/task-collaborators", tags=["TaskCollaborators"])


# ── Modelo inline (se crea la tabla vía migración en main.py) ──
class TaskCollaborator(Base):
    __tablename__ = "colaborador_tarea"
    __table_args__ = {"extend_existing": True}

    id          = Column(Integer, primary_key=True, autoincrement=True)
    task_id     = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)


# ── Helper: usuario autenticado ─────────────────────────────────
def _get_user(authorization: str, db: Session) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    session = db.query(UserSession).filter(
        UserSession.token == token, UserSession.is_active == True
    ).first()
    if not session or payload is None:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


def _role_name(user: User, db: Session) -> str:
    role = db.query(Role).filter(Role.id == user.role_id).first()
    return (role.name or "").lower() if role else ""


def _is_worker(user: User, db: Session) -> bool:
    return "worker" in _role_name(user, db)


def _can_manage(user: User, db: Session) -> bool:
    """Solo roles superiores (no worker) pueden asignar/quitar colaboradores."""
    return not _is_worker(user, db)


# ── GET: listar colaboradores de una tarea ───────────────────────
@router.get("/{task_id}")
def list_collaborators(
    task_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    _get_user(authorization, db)  # solo requiere autenticación
    rows = db.query(TaskCollaborator).filter(
        TaskCollaborator.task_id == task_id
    ).order_by(TaskCollaborator.assigned_at.asc()).all()

    result = []
    for r in rows:
        u = db.query(User).filter(User.id == r.user_id).first()
        if u:
            role = db.query(Role).filter(Role.id == u.role_id).first()
            result.append({
                "id":          r.id,
                "task_id":     r.task_id,
                "user_id":     r.user_id,
                "nombre":      u.nombre,
                "email":       u.email,
                "role":        role.name if role else "",
                "assigned_at": r.assigned_at.isoformat() if r.assigned_at else None,
            })
    return result


# ── POST: agregar colaborador ────────────────────────────────────
@router.post("/{task_id}")
def add_collaborator(
    task_id: int,
    data: dict = Body(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    requester = _get_user(authorization, db)
    if not _can_manage(requester, db):
        raise HTTPException(status_code=403, detail="Solo roles superiores pueden asignar colaboradores")

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=422, detail="user_id es requerido")

    collab_user = db.query(User).filter(User.id == user_id).first()
    if not collab_user:
        raise HTTPException(status_code=404, detail="Usuario colaborador no encontrado")

    # Evitar duplicados
    exists = db.query(TaskCollaborator).filter(
        TaskCollaborator.task_id == task_id,
        TaskCollaborator.user_id == user_id
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail="Este usuario ya es colaborador de la tarea")

    # No agregar al responsable principal como colaborador
    if task.assigned_to == user_id:
        raise HTTPException(status_code=409, detail="El responsable principal no puede ser colaborador")

    new = TaskCollaborator(
        task_id     = task_id,
        user_id     = user_id,
        assigned_by = requester.id,
        assigned_at = datetime.utcnow(),
    )
    db.add(new)
    db.commit()
    db.refresh(new)

    role = db.query(Role).filter(Role.id == collab_user.role_id).first()
    return {
        "id":          new.id,
        "task_id":     new.task_id,
        "user_id":     new.user_id,
        "nombre":      collab_user.nombre,
        "email":       collab_user.email,
        "role":        role.name if role else "",
        "assigned_at": new.assigned_at.isoformat(),
    }


# ── DELETE: quitar colaborador ───────────────────────────────────
@router.delete("/{task_id}/{user_id}")
def remove_collaborator(
    task_id: int,
    user_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    requester = _get_user(authorization, db)
    if not _can_manage(requester, db):
        raise HTTPException(status_code=403, detail="Solo roles superiores pueden quitar colaboradores")

    row = db.query(TaskCollaborator).filter(
        TaskCollaborator.task_id == task_id,
        TaskCollaborator.user_id == user_id
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Colaborador no encontrado en esta tarea")

    db.delete(row)
    db.commit()
    return {"detail": "Colaborador eliminado"}
