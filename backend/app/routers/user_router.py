from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete as sql_delete, update as sql_update
from sqlalchemy.exc import IntegrityError
from typing import Optional, Union

from app.database import get_db
from app.models.role_model import Role
from app.models.user_model import User
from app.schemas.user_schema import UserResponse, UserCreate, UserUpdate
from app.models.role_module_model import RoleModule
from app.models.system_module_model import SystemModule
from app.models.company_plan_model import CompanyPlan
from app.models.plan_model import Plan
from app.models.task_model import Task
from app.models.task_comment_model import TaskComment
from app.models.task_evidence_model import TaskEvidence
from app.models.task_material_model import TaskMaterial
from app.models.task_expense_model import TaskExpense
from app.models.task_purchase_model import TaskPurchase
from app.models.task_progress_report_model import TaskProgressReport
from app.models.novelty_model import Novelty, NoveltyEvidence, NoveltyReply
from app.models.support_ticket_model import SupportTicket, TicketEvidence
from app.models.user_session_model import UserSession
from app.models.user_notification_model import UserNotification
from app.models.invitation_model import InvitationToken
from passlib.context import CryptContext
from app.auth.dependencies import get_current_user
from app.services.plan_limits_service import check_limit


async def _cascade_delete_user(user_id: int, db: AsyncSession):
    """Elimina en cascada todos los registros asociados a un usuario (solo SYSADMIN)."""
    # Sesiones y tokens
    await db.execute(sql_delete(UserSession).where(UserSession.user_id == user_id))
    await db.execute(sql_delete(InvitationToken).where(InvitationToken.created_by == user_id))
    await db.execute(sql_delete(UserNotification).where(
        or_(UserNotification.sender_id == user_id, UserNotification.receiver_id == user_id)
    ))

    # Comentarios de tareas
    await db.execute(sql_delete(TaskComment).where(TaskComment.user_id == user_id))

    # Tareas (primero hijos, luego la tarea)
    task_ids_r = await db.execute(
        select(Task.id).where(or_(Task.created_by == user_id, Task.assigned_to == user_id))
    )
    task_ids = [r[0] for r in task_ids_r.all()]
    if task_ids:
        for child in (TaskEvidence, TaskMaterial, TaskExpense, TaskPurchase, TaskProgressReport):
            await db.execute(sql_delete(child).where(child.task_id.in_(task_ids)))
        await db.execute(sql_delete(Task).where(Task.id.in_(task_ids)))

    # Novedades (evidence y replies tienen CASCADE en BD)
    novelty_ids_r = await db.execute(select(Novelty.id).where(Novelty.user_id == user_id))
    novelty_ids = [r[0] for r in novelty_ids_r.all()]
    if novelty_ids:
        await db.execute(sql_delete(NoveltyEvidence).where(NoveltyEvidence.novelty_id.in_(novelty_ids)))
        await db.execute(sql_delete(NoveltyReply).where(NoveltyReply.novelty_id.in_(novelty_ids)))
        await db.execute(sql_delete(Novelty).where(Novelty.id.in_(novelty_ids)))
    await db.execute(sql_delete(NoveltyReply).where(NoveltyReply.user_id == user_id))

    # Tickets de soporte (ticket_evidence tiene CASCADE en BD)
    ticket_ids_r = await db.execute(select(SupportTicket.id).where(SupportTicket.user_id == user_id))
    ticket_ids = [r[0] for r in ticket_ids_r.all()]
    if ticket_ids:
        await db.execute(sql_delete(TicketEvidence).where(TicketEvidence.ticket_id.in_(ticket_ids)))
        await db.execute(sql_delete(SupportTicket).where(SupportTicket.id.in_(ticket_ids)))

router = APIRouter(prefix="/users", tags=["users"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def _get_plan_limit(company_id: int, db: AsyncSession):
    result = await db.execute(
        select(CompanyPlan)
        .where(CompanyPlan.company_id == company_id, CompanyPlan.is_active == True)
        .order_by(CompanyPlan.id.desc())
    )
    cp = result.scalar_one_or_none()
    if not cp:
        return 1, "Sin plan"
    plan = await db.get(Plan, cp.plan_id)
    return (plan.max_users if plan else 1), (plan.name if plan else "Sin plan")


@router.get("/plan-limit")
async def get_plan_limit(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    role = await db.get(Role, current_user.role_id)
    is_system = role.is_system if role else False
    if is_system:
        return {"current": 0, "max": -1, "plan_name": "SYSADMIN", "can_add": True}

    company_id = current_user.company_id
    max_users, plan_name = await _get_plan_limit(company_id, db)
    current_count = (await db.execute(select(func.count()).select_from(User).where(User.company_id == company_id))).scalar()
    return {"current": current_count, "max": max_users, "plan_name": plan_name, "can_add": (max_users == -1) or (current_count < max_users)}


@router.post("/", response_model=UserResponse)
async def crear_user(usuario: UserCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    role = await db.get(Role, current_user.role_id)
    if not (role and role.is_system):
        company_id = usuario.company_id or current_user.company_id
        await check_limit(company_id, "max_users", User, db)

    nuevo_usuario = User(nombre=usuario.nombre, email=usuario.email,
                         password_hash=pwd_context.hash(usuario.password),
                         role_id=usuario.role_id, company_id=usuario.company_id)
    try:
        db.add(nuevo_usuario)
        await db.commit()
        await db.refresh(nuevo_usuario)
        return nuevo_usuario
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="El email ya está registrado")


@router.get("/", response_model=list[UserResponse])
async def get_user_list(
    company_id: Optional[Union[int, str]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    role = await db.get(Role, current_user.role_id)
    if role and not role.is_system:
        result = await db.execute(select(User).where(User.company_id == current_user.company_id))
        return result.scalars().all()

    if isinstance(company_id, str) and company_id.lower() == "all":
        result = await db.execute(select(User))
        return result.scalars().all()

    cid = int(company_id) if company_id is not None else current_user.company_id
    result = await db.execute(select(User).where(User.company_id == cid))
    return result.scalars().all()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    usuario = await db.get(User, user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, data: UserUpdate, db: AsyncSession = Depends(get_db)):
    usuario = await db.get(User, user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(usuario, key, value)
    try:
        await db.commit()
        await db.refresh(usuario)
        return usuario
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="El email ya está registrado")


@router.get("/{user_id}/modules/")
async def get_user_modules(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    result = await db.execute(
        select(RoleModule)
        .join(SystemModule, RoleModule.module_id == SystemModule.id)
        .where(RoleModule.role_id == user.role_id, RoleModule.can_view == True, SystemModule.is_active == True)
    )
    role_modules = result.scalars().all()
    modules = [rm.module for rm in role_modules]

    module_dict = {m.id: {"id": m.id, "name": m.name, "route": m.route,
                           "icon": m.icon, "parent_id": m.parent_id, "children": []}
                   for m in modules}
    tree = []
    for m in module_dict.values():
        if m["parent_id"] and m["parent_id"] in module_dict:
            module_dict[m["parent_id"]]["children"].append(m)
        else:
            tree.append(m)
    return tree


@router.delete("/{id}")
async def delete_user(id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    caller_role = await db.get(Role, current_user.role_id)
    is_sysadmin = caller_role.is_system if caller_role else False

    user = await db.get(User, id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if is_sysadmin:
        # SYSADMIN: cascada completa para limpieza de datos de prueba
        await _cascade_delete_user(id, db)
        await db.delete(user)
        await db.commit()
        return {"message": "Usuario y todos sus datos eliminados"}

    # No-SYSADMIN: bloquear si tiene registros asociados
    bloqueos = []
    task_count = (await db.execute(
        select(func.count()).select_from(Task).where(
            or_(Task.created_by == id, Task.assigned_to == id)
        )
    )).scalar()
    if task_count:
        bloqueos.append(f"{task_count} tarea(s)")

    novelty_count = (await db.execute(
        select(func.count()).select_from(Novelty).where(Novelty.user_id == id)
    )).scalar()
    if novelty_count:
        bloqueos.append(f"{novelty_count} novedad(es)")

    ticket_count = (await db.execute(
        select(func.count()).select_from(SupportTicket).where(SupportTicket.user_id == id)
    )).scalar()
    if ticket_count:
        bloqueos.append(f"{ticket_count} ticket(s) de soporte")

    if bloqueos:
        raise HTTPException(
            status_code=409,
            detail=f"No se puede eliminar: el usuario tiene {', '.join(bloqueos)} asociado(s). Desactívalo para bloquear su acceso sin perder los registros."
        )

    try:
        await db.delete(user)
        await db.commit()
        return {"message": "Usuario eliminado"}
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar el usuario porque tiene registros asociados. Desactívalo para bloquear su acceso sin perder los datos."
        )
