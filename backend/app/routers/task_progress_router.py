from fastapi import APIRouter, Depends, Header, HTTPException, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.task_progress_report_model import TaskProgressReport
from app.models.task_model import Task
from app.models.asset_model import Asset
from app.models.task_status_model import TaskStatus
from app.models.user_model import User
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession

router = APIRouter(prefix="/task-progress", tags=["TaskProgress"])


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


def _ser(r: TaskProgressReport):
    return {"id": r.id, "task_id": r.task_id, "progress_percent": r.progress_percent,
            "description": r.description, "created_by": r.created_by,
            "created_at": r.created_at.isoformat() if r.created_at else None}


@router.get("/{task_id:int}")
async def get_reports(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskProgressReport).where(TaskProgressReport.task_id == task_id).order_by(TaskProgressReport.created_at.asc()))
    return [_ser(r) for r in result.scalars().all()]


@router.post("/{task_id:int}")
async def add_report(task_id: int, data: dict = Body(...), authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    desc = data.get("description", "").strip()
    if not desc:
        raise HTTPException(status_code=400, detail="La descripción del reporte es obligatoria")
    r = TaskProgressReport(task_id=task_id, progress_percent=int(data.get("progress_percent", 0)),
                           description=desc, created_by=user.id)
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return _ser(r)


@router.delete("/{report_id:int}")
async def delete_report(report_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_user(authorization, db)
    result = await db.execute(select(TaskProgressReport).where(TaskProgressReport.id == report_id))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    await db.delete(r)
    await db.commit()
    return {"message": "Reporte eliminado"}


# ── Historial de un activo ──────────────────────────────────────
asset_history_router = APIRouter(prefix="/assets", tags=["AssetHistory"])


@asset_history_router.get("/{asset_id}/history")
async def get_asset_history(asset_id: int, status_id: int = None, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Activo no encontrado")

    conds = [Task.asset_id == asset_id]
    if status_id:
        conds.append(Task.status_id == status_id)
    result = await db.execute(select(Task).where(*conds).order_by(Task.created_at.desc()))
    tasks = result.scalars().all()

    status_result = await db.execute(select(TaskStatus))
    statuses = {s.id: s.name for s in status_result.scalars().all()}
    user_result = await db.execute(select(User))
    users = {u.id: u.nombre for u in user_result.scalars().all()}

    return {
        "asset": {"id": asset.id, "name": asset.name, "location": asset.location},
        "tasks": [{"id": t.id, "title": t.title, "description": t.description,
                   "status_id": t.status_id, "status_name": statuses.get(t.status_id, "—"),
                   "assigned_to": t.assigned_to,
                   "assigned_name": users.get(t.assigned_to, "—") if t.assigned_to else "—",
                   "progress": t.progress, "budget": t.budget_labor_cost, "actual_cost": t.actual_labor_cost,
                   "start_date": t.start_date.isoformat() if t.start_date else None,
                   "due_date": t.due_date.isoformat() if t.due_date else None,
                   "closed_at": t.closed_at.isoformat() if t.closed_at else None,
                   "created_at": t.created_at.isoformat() if t.created_at else None}
                  for t in tasks]
    }
