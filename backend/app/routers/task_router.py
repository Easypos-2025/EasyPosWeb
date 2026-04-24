from fastapi import APIRouter, Depends, Header, HTTPException, Body
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.task_model import Task
from app.models.task_status_model import TaskStatus
from app.models.user_model import User
from app.models.role_model import Role
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession

router = APIRouter(prefix="/tasks", tags=["Tasks"])


# ─── helper: usuario autenticado ───────────────────────────────
def _get_user(authorization: str, db: Session):
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


def _is_system(user, db):
    role = db.query(Role).filter(Role.id == user.role_id).first()
    return role.is_system if role else False


# ─── STATS para el dashboard ───────────────────────────────────
@router.get("/stats")
def get_task_stats(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)
    base = db.query(Task)
    if not _is_system(user, db):
        base = base.filter(Task.company_id == user.company_id)

    hoy = datetime.now()
    return {
        "total":      base.count(),
        "pendiente":  base.filter(Task.status_id == 1).count(),
        "asignada":   base.filter(Task.status_id == 2).count(),
        "progreso":   base.filter(Task.status_id == 3).count(),
        "revision":   base.filter(Task.status_id == 4).count(),
        "finalizada": base.filter(Task.status_id == 5).count(),
        "cancelada":  base.filter(Task.status_id == 6).count(),
        "atrasadas":  base.filter(
            Task.due_date < hoy,
            Task.status_id.notin_([5, 6])
        ).count(),
    }


# ─── MIS TAREAS (Task Leader) ──────────────────────────────────
@router.get("/my-tasks")
def get_my_tasks(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Tareas asignadas al usuario logueado (Task Leader view)."""
    user  = _get_user(authorization, db)
    tasks = db.query(Task).filter(Task.assigned_to == user.id)\
               .order_by(Task.due_date.asc()).all()
    return [_serialize(t) for t in tasks]


# ─── ACTUALIZAR AVANCE RÁPIDO ──────────────────────────────────
@router.patch("/{task_id}/progress")
def update_progress(
    task_id: int,
    data: dict = Body(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """Actualización rápida de avance y estado desde la vista Task Leader."""
    user = _get_user(authorization, db)
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    if task.assigned_to != user.id and not _is_system(user, db):
        raise HTTPException(status_code=403, detail="Solo el Task Leader asignado puede actualizar el avance")

    if "progress" in data:
        task.progress = max(0, min(100, int(data["progress"])))
    if "status_id" in data:
        task.status_id = data["status_id"]
        if data["status_id"] in [5, 6] and not task.closed_at:
            task.closed_at = datetime.now()

    db.commit()
    db.refresh(task)
    return _serialize(task)


# ─── GET ALL ───────────────────────────────────────────────────
@router.get("/")
def get_tasks(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)
    q = db.query(Task)
    if not _is_system(user, db):
        q = q.filter(Task.company_id == user.company_id)
    return [_serialize(t) for t in q.order_by(Task.created_at.desc()).all()]


# ─── GET BY ID ─────────────────────────────────────────────────
@router.get("/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return _serialize(task)


# ─── CREATE ────────────────────────────────────────────────────
@router.post("/")
def create_task(
    data: dict = Body(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)

    task = Task(
        company_id=        user.company_id,
        title=             data.get("title", "").strip(),
        description=       data.get("description", ""),
        asset_id=          data.get("asset_id") or None,
        status_id=         data.get("status_id", 1),
        assigned_to=       data.get("assigned_to") or None,
        worker_id=         data.get("worker_id") or None,
        progress=          int(data.get("progress", 0)),
        budget_labor_cost= float(data.get("budget_labor_cost", 0)),
        actual_labor_cost= float(data.get("actual_labor_cost", 0)),
        start_date=        _parse_date(data.get("start_date")),
        due_date=          _parse_date(data.get("due_date")),
        created_by=        user.id,
    )

    if not task.title:
        raise HTTPException(status_code=400, detail="El título es obligatorio")

    db.add(task)
    db.commit()
    db.refresh(task)
    return _serialize(task)


# ─── UPDATE ────────────────────────────────────────────────────
@router.put("/{task_id}")
def update_task(
    task_id: int,
    data: dict = Body(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user  = _get_user(authorization, db)
    task  = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    fields = [
        "title", "description", "asset_id", "status_id",
        "assigned_to", "worker_id", "progress",
        "budget_labor_cost", "actual_labor_cost",
    ]
    for f in fields:
        if f in data:
            setattr(task, f, data[f] or None if f.endswith("_id") else data[f])

    if "start_date" in data:
        task.start_date = _parse_date(data["start_date"])
    if "due_date" in data:
        task.due_date = _parse_date(data["due_date"])

    # Auto-cerrar si pasa a Finalizada o Cancelada
    if data.get("status_id") in [5, 6] and not task.closed_at:
        task.closed_at = datetime.now()

    db.commit()
    db.refresh(task)
    return _serialize(task)


# ─── DELETE ────────────────────────────────────────────────────
@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    db.delete(task)
    db.commit()
    return {"message": "Tarea eliminada"}


# ─── helpers ───────────────────────────────────────────────────
def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)[:10])
    except Exception:
        return None


def _serialize(t: Task):
    return {
        "id":                 t.id,
        "company_id":         t.company_id,
        "title":              t.title,
        "description":        t.description,
        "asset_id":           t.asset_id,
        "status_id":          t.status_id,
        "status_name":        t.status.name if t.status else "—",
        "assigned_to":        t.assigned_to,
        "worker_id":          t.worker_id,
        "progress":           t.progress,
        "budget_labor_cost":  t.budget_labor_cost,
        "actual_labor_cost":  t.actual_labor_cost,
        "start_date":         t.start_date.isoformat() if t.start_date else None,
        "due_date":           t.due_date.isoformat() if t.due_date else None,
        "closed_at":          t.closed_at.isoformat() if t.closed_at else None,
        "created_at":         t.created_at.isoformat() if t.created_at else None,
    }
