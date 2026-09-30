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
from app.models.password_reset_token import PasswordResetToken
from passlib.context import CryptContext
from app.auth.dependencies import get_current_user
from app.auth import tenant
from app.services.plan_limits_service import check_limit


async def _cascade_delete_user(user_id: int, db: AsyncSession):
    """Elimina en cascada todos los registros asociados a un usuario (solo SYSADMIN)."""
    # Sesiones y tokens
    await db.execute(sql_delete(PasswordResetToken).where(PasswordResetToken.user_id == user_id))
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


# ── Control de acceso (CLAUDE.md §6) ─────────────────────────────────────────
# Gestionar usuarios: SYSADMIN o rol ADMIN, y solo dentro de sus empresas permitidas
# (ADMIN = su empresa + mismo NIT). Nadie que no sea SYSADMIN puede asignar un rol
# de sistema, tocar un usuario SYSADMIN ni cambiar su propio rol o empresa.

async def _caller(db: AsyncSession, user: User) -> tuple:
    """(es_sysadmin, es_admin, empresas permitidas | None=todas)."""
    role = await db.get(Role, user.role_id) if user.role_id else None
    is_sys = bool(role and role.is_system)
    _, allowed = await tenant.allowed_companies(db, user)
    return is_sys, tenant._is_admin(role), allowed


async def _target_user(db: AsyncSession, user_id: int, allowed) -> User:
    """Usuario destino dentro de las empresas permitidas; 404 si no."""
    target = await db.get(User, user_id)
    if not target or (allowed is not None and target.company_id not in allowed):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return target


async def _is_system_user(db: AsyncSession, u: User) -> bool:
    role = await db.get(Role, u.role_id) if u.role_id else None
    return bool(role and role.is_system)


async def _check_role_assignable(db: AsyncSession, role_id: int, company_id: Optional[int],
                                 is_sys: bool, allowed) -> None:
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=400, detail="Rol no válido")
    if is_sys:
        return
    if role.is_system:
        raise HTTPException(status_code=403, detail="No puede asignar un rol de sistema")
    # Roles propios de una empresa solo se asignan dentro de esa empresa (0/NULL = rol global)
    if role.company_id and role.company_id != company_id and role.company_id not in (allowed or ()):
        raise HTTPException(status_code=403, detail="El rol no pertenece a la empresa")


@router.get("/plan-limit")
async def get_plan_limit(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    role = await db.get(Role, current_user.role_id)
    is_system = role.is_system if role else False
    if is_system:
        return {"current": 0, "max": -1, "plan_name": "SYSADMIN", "can_add": True}

    company_id = current_user.company_id

    # Usa get_limits que respeta CompanyPlanLimits (overrides por asociado) con fallback al Plan
    from app.services.plan_limits_service import get_limits
    limits = await get_limits(company_id, db)
    max_users = limits.get("max_users", 1)

    # Nombre del plan activo
    cp_res = await db.execute(
        select(CompanyPlan).where(CompanyPlan.company_id == company_id, CompanyPlan.is_active == True)
        .order_by(CompanyPlan.id.desc())
    )
    cp = cp_res.scalar_one_or_none()
    plan_name = "Sin plan"
    if cp:
        plan = await db.get(Plan, cp.plan_id)
        plan_name = plan.name if plan else "Sin plan"

    current_count = (await db.execute(
        select(func.count()).select_from(User).where(User.company_id == company_id)
    )).scalar() or 0

    return {
        "current":  current_count,
        "max":      max_users,
        "plan_name": plan_name,
        "can_add":  (max_users == -1) or (current_count < max_users),
    }


@router.post("/", response_model=UserResponse)
async def crear_user(usuario: UserCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    is_sys, is_admin, allowed = await _caller(db, current_user)
    if not (is_sys or is_admin):
        raise HTTPException(status_code=403, detail="Solo un administrador puede crear usuarios")

    company_id = tenant.check_company(current_user.company_id, allowed, usuario.company_id)
    await _check_role_assignable(db, usuario.role_id, company_id, is_sys, allowed)
    if not is_sys:
        await check_limit(company_id, "max_users", User, db)

    nuevo_usuario = User(nombre=usuario.nombre, email=usuario.email,
                         password_hash=pwd_context.hash(usuario.password),
                         role_id=usuario.role_id, company_id=company_id)
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
async def get_user(user_id: int, db: AsyncSession = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    _, _, allowed = await _caller(db, current_user)
    return await _target_user(db, user_id, allowed)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, data: UserUpdate, db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    is_sys, is_admin, allowed = await _caller(db, current_user)
    is_self = user_id == current_user.id
    if not (is_sys or is_admin or is_self):
        raise HTTPException(status_code=403, detail="Solo un administrador puede modificar usuarios")

    usuario = await _target_user(db, user_id, allowed)
    changes = data.dict(exclude_unset=True)

    if not is_sys:
        if await _is_system_user(db, usuario):
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        # El formulario reenvía todos los campos: solo se valida lo que realmente cambia
        changed = {k for k, v in changes.items() if getattr(usuario, k, None) != v}
        if "is_test_account" in changed:
            raise HTTPException(status_code=403, detail="Solo SYSADMIN puede cambiar la cuenta de prueba")
        if is_self and changed & {"role_id", "company_id", "is_active"}:
            raise HTTPException(status_code=403, detail="No puede cambiar su propio rol, empresa o estado")
        if not is_admin and changed - {"nombre", "email"}:
            raise HTTPException(status_code=403, detail="Solo un administrador puede cambiar esos datos")
        changes = {k: v for k, v in changes.items() if k in changed}

    if "company_id" in changes:
        changes["company_id"] = tenant.check_company(current_user.company_id, allowed, changes["company_id"])
    if "role_id" in changes:
        await _check_role_assignable(db, changes["role_id"], changes.get("company_id", usuario.company_id),
                                     is_sys, allowed)

    for key, value in changes.items():
        setattr(usuario, key, value)
    try:
        await db.commit()
        await db.refresh(usuario)
        return usuario
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="El email ya está registrado")


@router.get("/{user_id}/modules/")
async def get_user_modules(user_id: int, db: AsyncSession = Depends(get_db),
                           current_user: User = Depends(get_current_user)):
    _, _, allowed = await _caller(db, current_user)
    user = await _target_user(db, user_id, allowed)

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
    is_sysadmin, is_admin, allowed = await _caller(db, current_user)
    if not (is_sysadmin or is_admin):
        raise HTTPException(status_code=403, detail="Solo un administrador puede eliminar usuarios")
    if id == current_user.id:
        raise HTTPException(status_code=400, detail="No puede eliminar su propio usuario")

    user = await _target_user(db, id, allowed)
    if not is_sysadmin and await _is_system_user(db, user):
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
