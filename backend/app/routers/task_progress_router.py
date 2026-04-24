from fastapi import APIRouter, Depends, Header, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.task_progress_report_model import TaskProgressReport
from app.models.task_model import Task
from app.models.asset_model import Asset
from app.models.task_status_model import TaskStatus
from app.models.user_model import User
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession

router = APIRouter(prefix="/task-progress", tags=["TaskProgress"])


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


# ── Reportes de avance de una tarea ─────────────────────────────
@router.get("/{task_id}")
def get_reports(task_id: int, db: Session = Depends(get_db)):
    items = db.query(TaskProgressReport)\
               .filter(TaskProgressReport.task_id == task_id)\
               .order_by(TaskProgressReport.created_at.asc()).all()
    return [_ser(r) for r in items]


@router.post("/{task_id}")
def add_report(
    task_id: int,
    data: dict = Body(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)
    desc = data.get("description", "").strip()
    if not desc:
        raise HTTPException(status_code=400, detail="La descripción del reporte es obligatoria")

    r = TaskProgressReport(
        task_id=          task_id,
        progress_percent= int(data.get("progress_percent", 0)),
        description=      desc,
        created_by=       user.id,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return _ser(r)


@router.delete("/{report_id}")
def delete_report(
    report_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    _get_user(authorization, db)
    r = db.query(TaskProgressReport).filter(TaskProgressReport.id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    db.delete(r)
    db.commit()
    return {"message": "Reporte eliminado"}


# ── Historial de un activo (todas sus tareas) ───────────────────
asset_history_router = APIRouter(prefix="/assets", tags=["AssetHistory"])


@asset_history_router.get("/{asset_id}/history")
def get_asset_history(
    asset_id:   int,
    status_id:  int = None,
    db: Session = Depends(get_db)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Activo no encontrado")

    q = db.query(Task).filter(Task.asset_id == asset_id)
    if status_id:
        q = q.filter(Task.status_id == status_id)

    tasks = q.order_by(Task.created_at.desc()).all()

    statuses = {s.id: s.name for s in db.query(TaskStatus).all()}
    users    = {u.id: u.nombre for u in db.query(User).all()}

    return {
        "asset": {"id": asset.id, "name": asset.name, "location": asset.location},
        "tasks": [
            {
                "id":          t.id,
                "title":       t.title,
                "description": t.description,
                "status_id":   t.status_id,
                "status_name": statuses.get(t.status_id, "—"),
                "assigned_to": t.assigned_to,
                "assigned_name": users.get(t.assigned_to, "—") if t.assigned_to else "—",
                "progress":    t.progress,
                "budget":      t.budget_labor_cost,
                "actual_cost": t.actual_labor_cost,
                "start_date":  t.start_date.isoformat() if t.start_date else None,
                "due_date":    t.due_date.isoformat() if t.due_date else None,
                "closed_at":   t.closed_at.isoformat() if t.closed_at else None,
                "created_at":  t.created_at.isoformat() if t.created_at else None,
            }
            for t in tasks
        ]
    }


def _ser(r: TaskProgressReport):
    return {
        "id":               r.id,
        "task_id":          r.task_id,
        "progress_percent": r.progress_percent,
        "description":      r.description,
        "created_by":       r.created_by,
        "created_at":       r.created_at.isoformat() if r.created_at else None,
    }
