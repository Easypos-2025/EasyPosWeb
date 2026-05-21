from fastapi import APIRouter, Depends, Header, HTTPException, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date, delete as sql_delete
from datetime import datetime, date
from typing import Optional

from app.database import get_db
from app.models.task_model import Task
from app.models.task_status_model import TaskStatus
from app.models.asset_model import Asset
from app.models.user_model import User
from app.models.worker_model import Worker
from app.models.role_model import Role
from app.models.role_module_model import RoleModule
from app.models.system_module_model import SystemModule
from app.models.task_material_model import TaskMaterial
from app.models.task_expense_model import TaskExpense
from app.models.task_purchase_model import TaskPurchase
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.services.plan_limits_service import check_limit, get_limits
from app.models.task_evidence_model import TaskEvidence
from app.models.task_material_model import TaskMaterial
from app.models.task_expense_model import TaskExpense
from app.models.task_comment_model import TaskComment
from app.models.task_progress_report_model import TaskProgressReport
from app.models.task_purchase_model import TaskPurchase

router = APIRouter(prefix="/tasks", tags=["Tasks"])
COMPLETAR_ROUTE = "/tasks/completar-info"


async def _can_view_all_tasks(user: User, db: AsyncSession) -> bool:
    """True si el rol puede ver todas las tareas (no filtrar por usuario)."""
    role = await db.get(Role, user.role_id)
    if role and role.is_system:
        return True
    result = await db.execute(
        select(RoleModule)
        .join(SystemModule, SystemModule.id == RoleModule.module_id)
        .where(RoleModule.role_id == user.role_id, SystemModule.route == COMPLETAR_ROUTE)
    )
    perm = result.scalar_one_or_none()
    return bool(perm.can_view_all) if perm else False


async def _get_user(authorization: str, db: AsyncSession):
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


async def _get_role(user: User, db: AsyncSession):
    result = await db.execute(select(Role).where(Role.id == user.role_id))
    return result.scalar_one_or_none()


async def _status_map(db: AsyncSession) -> dict:
    result = await db.execute(select(TaskStatus))
    return {s.id: s.name for s in result.scalars().all()}


async def _worker_map(db: AsyncSession) -> dict:
    result = await db.execute(select(Worker))
    return {w.id: w.name for w in result.scalars().all()}


async def _user_map(db: AsyncSession) -> dict:
    result = await db.execute(select(User))
    return {u.id: u.nombre for u in result.scalars().all()}


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)[:10])
    except Exception:
        return None


def _serialize(t: Task, status_names=None, worker_names=None, user_names=None) -> dict:
    sname = (status_names or {}).get(t.status_id, "—") if t.status_id else "—"
    return {
        "id": t.id, "company_id": t.company_id, "title": t.title, "description": t.description,
        "asset_id": t.asset_id, "status_id": t.status_id, "status_name": sname,
        "assigned_to": t.assigned_to,
        "assigned_to_name": (user_names or {}).get(t.assigned_to) if t.assigned_to else None,
        "worker_id": t.worker_id,
        "worker_name": (worker_names or {}).get(t.worker_id) if t.worker_id else None,
        "progress": t.progress or 0,
        "budget_labor_cost": t.budget_labor_cost or 0, "actual_labor_cost": t.actual_labor_cost or 0,
        "start_date": t.start_date.isoformat()[:10] if t.start_date else None,
        "due_date": t.due_date.isoformat()[:10] if t.due_date else None,
        "closed_at": t.closed_at.isoformat() if t.closed_at else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    }


@router.get("/stats")
async def get_task_stats(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    role = await _get_role(user, db)
    role_name = (role.name or "").lower() if role else ""
    is_sys = role.is_system if role else False
    can_see_all = is_sys or "admin" in role_name or "auditor" in role_name

    base_conds = []
    if not is_sys:
        base_conds.append(Task.company_id == user.company_id)
    if not can_see_all:
        base_conds.append(Task.assigned_to == user.id)

    async def cnt(*extra):
        return (await db.execute(select(func.count()).select_from(Task).where(*base_conds, *extra))).scalar()

    hoy = datetime.now()
    return {
        "total":           await cnt(),
        "pendiente":       await cnt(Task.status_id == 1),
        "asignada":        await cnt(Task.status_id == 2),
        "progreso":        await cnt(Task.status_id == 3),
        "revision":        await cnt(Task.status_id == 4),
        "finalizada":      await cnt(Task.status_id == 5),
        "cancelada":       await cnt(Task.status_id == 6),
        "atrasadas":       await cnt(Task.due_date < hoy, Task.status_id.notin_([5, 6])),
        "sin_ejecutor":    await cnt(Task.worker_id == None, Task.status_id.notin_([5, 6])),
        "sin_asignar":     await cnt(Task.status_id == 1, Task.assigned_to == None),
        "info_incompleta": await cnt(Task.status_id == 2, (Task.worker_id == None) | (Task.due_date == None)),
    }


@router.get("/incomplete-info")
async def get_incomplete_tasks(
    mine: bool = Query(False),
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    sm = await _status_map(db)
    wm = await _worker_map(db)
    um = await _user_map(db)

    role = await _get_role(user, db)
    is_sys = role.is_system if role else False

    # Si no tiene can_view_all, forzar filtro por usuario asignado
    view_all = is_sys or await _can_view_all_tasks(user, db)
    filter_by_user = mine or not view_all

    base_conds = [] if is_sys else [Task.company_id == user.company_id]
    if filter_by_user:
        base_conds.append(Task.assigned_to == user.id)

    # Sin can_view_all no tiene sentido mostrar tareas sin asignar (assigned_to es None)
    if not view_all:
        sin_asignar = []
    else:
        r1 = await db.execute(select(Task).where(*base_conds, Task.status_id == 1, Task.assigned_to == None))
        sin_asignar = [_serialize(t, sm, wm, um) for t in r1.scalars().all()]

    r2 = await db.execute(select(Task).where(*base_conds, Task.status_id == 2, (Task.worker_id == None) | (Task.due_date == None)))

    return {
        "sin_asignar":     sin_asignar,
        "info_incompleta": [_serialize(t, sm, wm, um) for t in r2.scalars().all()],
    }


@router.get("/report")
async def get_task_report(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    """Tareas con costo calculado = materiales + gastos + compras, ordenadas por start_date asc."""
    user = await _get_user(authorization, db)
    role = await _get_role(user, db)
    is_sys = role.is_system if role else False

    sm = await _status_map(db)
    wm = await _worker_map(db)
    um = await _user_map(db)

    conds = [] if is_sys else [Task.company_id == user.company_id]
    result = await db.execute(
        select(Task).where(*conds)
        .order_by(Task.start_date.is_(None), Task.start_date.asc())
    )
    tasks = result.scalars().all()
    task_ids = [t.id for t in tasks]

    if task_ids:
        mat_res   = await db.execute(select(TaskMaterial.task_id, func.sum(TaskMaterial.unit_cost * TaskMaterial.quantity)).where(TaskMaterial.task_id.in_(task_ids)).group_by(TaskMaterial.task_id))
        exp_res   = await db.execute(select(TaskExpense.task_id,  func.sum(TaskExpense.amount)).where(TaskExpense.task_id.in_(task_ids)).group_by(TaskExpense.task_id))
        purch_res = await db.execute(select(TaskPurchase.task_id, func.sum(TaskPurchase.amount)).where(TaskPurchase.task_id.in_(task_ids)).group_by(TaskPurchase.task_id))
        mat_costs   = {r[0]: float(r[1] or 0) for r in mat_res.all()}
        exp_costs   = {r[0]: float(r[1] or 0) for r in exp_res.all()}
        purch_costs = {r[0]: float(r[1] or 0) for r in purch_res.all()}
    else:
        mat_costs = exp_costs = purch_costs = {}

    rows = []
    for t in tasks:
        base = _serialize(t, sm, wm, um)
        base["calculated_cost"] = (mat_costs.get(t.id, 0) + exp_costs.get(t.id, 0) + purch_costs.get(t.id, 0))
        rows.append(base)
    return rows


@router.get("/users-list")
async def get_users_for_tasks(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    result = await db.execute(select(User).where(User.company_id == user.company_id).order_by(User.nombre))
    return [{"id": u.id, "nombre": u.nombre, "email": u.email} for u in result.scalars().all()]


@router.get("/assets-list")
async def get_assets_for_tasks(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_user(authorization, db)
    result = await db.execute(select(Asset).order_by(Asset.name))
    return [{"id": a.id, "name": a.name} for a in result.scalars().all()]


@router.get("/my-tasks")
async def get_my_tasks(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    sm = await _status_map(db)
    wm = await _worker_map(db)
    um = await _user_map(db)
    result = await db.execute(
        select(Task).where(Task.assigned_to == user.id).order_by(Task.due_date.is_(None), Task.due_date.asc())
    )
    return [_serialize(t, sm, wm, um) for t in result.scalars().all()]


@router.patch("/{task_id:int}/progress")
async def update_progress(
    task_id: int,
    data: dict = Body(...),
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    role = await _get_role(user, db)
    is_sys = role.is_system if role else False
    if task.assigned_to != user.id and not is_sys:
        raise HTTPException(status_code=403, detail="Solo el Task Leader asignado puede actualizar el avance")

    if "progress" in data:
        task.progress = max(0, min(100, int(data["progress"])))
    if "status_id" in data:
        task.status_id = data["status_id"]
        if data["status_id"] in [5, 6] and not task.closed_at:
            task.closed_at = datetime.now()

    await db.commit()
    await db.refresh(task)
    sm = await _status_map(db)
    wm = await _worker_map(db)
    um = await _user_map(db)
    return _serialize(task, sm, wm, um)


@router.get("/")
async def get_tasks(
    status_id: Optional[int] = Query(None),
    worker_id: Optional[int] = Query(None),
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    sm = await _status_map(db)
    wm = await _worker_map(db)
    um = await _user_map(db)
    role = await _get_role(user, db)
    role_name = (role.name or "").lower() if role else ""
    is_sys = role.is_system if role else False
    can_see_all = is_sys or "admin" in role_name or "auditor" in role_name

    conds = []
    if not is_sys:
        conds.append(Task.company_id == user.company_id)
    if not can_see_all:
        conds.append(Task.assigned_to == user.id)
    if status_id is not None:
        conds.append(Task.status_id == status_id)
    if worker_id is not None:
        conds.append(Task.worker_id == worker_id)

    result = await db.execute(select(Task).where(*conds).order_by(Task.created_at.desc()))
    return [_serialize(t, sm, wm, um) for t in result.scalars().all()]


@router.get("/{task_id:int}")
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    sm = await _status_map(db)
    wm = await _worker_map(db)
    um = await _user_map(db)
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return _serialize(task, sm, wm, um)


@router.post("/")
async def create_task(
    data: dict = Body(...),
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    await check_limit(user.company_id, "max_tasks", Task, db)

    # Verificar límite diario de creación de tareas
    limits = await get_limits(user.company_id, db)
    max_daily = limits.get("max_daily_tasks", -1)
    if max_daily != -1:
        today = date.today()
        daily_count = (await db.execute(
            select(func.count()).select_from(Task)
            .where(Task.company_id == user.company_id,
                   cast(Task.created_at, Date) == today)
        )).scalar() or 0
        if daily_count >= max_daily:
            raise HTTPException(
                status_code=403,
                detail=f"Límite de {max_daily} tareas diarias alcanzado en tu plan. Actualiza tu plan para crear más."
            )

    task = Task(
        company_id=user.company_id, title=data.get("title", "").strip(),
        description=data.get("description", ""), asset_id=data.get("asset_id") or None,
        status_id=data.get("status_id", 1), assigned_to=data.get("assigned_to") or None,
        worker_id=data.get("worker_id") or None, progress=int(data.get("progress", 0)),
        budget_labor_cost=float(data.get("budget_labor_cost", 0)),
        actual_labor_cost=float(data.get("actual_labor_cost", 0)),
        start_date=_parse_date(data.get("start_date")), due_date=_parse_date(data.get("due_date")),
        created_by=user.id,
    )
    if not task.title:
        raise HTTPException(status_code=400, detail="El título es obligatorio")
    try:
        db.add(task)
        await db.commit()
        await db.refresh(task)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear tarea: {str(e)}")
    sm = await _status_map(db)
    wm = await _worker_map(db)
    um = await _user_map(db)
    return _serialize(task, sm, wm, um)


@router.put("/{task_id:int}")
async def update_task(
    task_id: int,
    data: dict = Body(...),
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    await _get_user(authorization, db)
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    for f in ["title", "description", "asset_id", "status_id", "assigned_to", "worker_id",
              "progress", "budget_labor_cost", "actual_labor_cost"]:
        if f in data:
            setattr(task, f, data[f] or None if f.endswith("_id") else data[f])
    if "start_date" in data:
        task.start_date = _parse_date(data["start_date"])
    if "due_date" in data:
        task.due_date = _parse_date(data["due_date"])
    if data.get("status_id") in [5, 6] and not task.closed_at:
        task.closed_at = datetime.now()

    try:
        await db.commit()
        await db.refresh(task)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar tarea: {str(e)}")

    sm = await _status_map(db)
    wm = await _worker_map(db)
    um = await _user_map(db)
    return _serialize(task, sm, wm, um)


@router.delete("/{task_id:int}")
async def delete_task(task_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_user(authorization, db)
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    for child_model in (TaskEvidence, TaskMaterial, TaskExpense,
                        TaskComment, TaskProgressReport, TaskPurchase):
        await db.execute(sql_delete(child_model).where(child_model.task_id == task_id))
    await db.delete(task)
    await db.commit()
    return {"message": "Tarea eliminada"}
