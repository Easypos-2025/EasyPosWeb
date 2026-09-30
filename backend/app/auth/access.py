"""
Control de acceso por registro (CLAUDE.md §6).

Valida que un id recibido del navegador pertenezca a la empresa efectiva del
usuario antes de usarlo. Si no pertenece se responde 404 (no se revela que
el registro existe en otra empresa). SYSADMIN accede a cualquier empresa.
"""
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role_model import Role
from app.models.user_model import User
from app.models.task_model import Task
from app.models.asset_model import Asset
from app.models.novelty_model import Novelty
from app.models.worker_model import Worker


async def is_sysadmin(db: AsyncSession, user: User) -> bool:
    role: Optional[Role] = await db.get(Role, user.role_id) if user.role_id else None
    return bool(role and role.is_system)


async def ensure_task(db: AsyncSession, user: User, task_id: int) -> Task:
    task = await db.get(Task, task_id)
    if not task or (task.company_id != user.company_id and not await is_sysadmin(db, user)):
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return task


async def ensure_asset(db: AsyncSession, user: User, asset_id: int) -> Asset:
    asset = await db.get(Asset, asset_id)
    if not asset or (asset.company_id != user.company_id and not await is_sysadmin(db, user)):
        raise HTTPException(status_code=404, detail="Activo no encontrado")
    return asset


async def ensure_novelty(db: AsyncSession, user: User, novelty_id: int) -> Novelty:
    nov = await db.get(Novelty, novelty_id)
    if not nov or (nov.company_id != user.company_id and not await is_sysadmin(db, user)):
        raise HTTPException(status_code=404, detail="Novedad no encontrada")
    return nov


async def ensure_task_refs(db: AsyncSession, company_id: int, asset_id=None,
                           assigned_to=None, worker_id=None) -> None:
    """Propiedad, usuario asignado y trabajador de una tarea deben ser de su empresa."""
    if asset_id:
        a = await db.get(Asset, int(asset_id))
        if not a or a.company_id != company_id:
            raise HTTPException(status_code=400, detail="El activo no pertenece a la empresa")
    if assigned_to:
        u = await db.get(User, int(assigned_to))
        if not u or u.company_id != company_id:
            raise HTTPException(status_code=400, detail="El usuario asignado no pertenece a la empresa")
    if worker_id:
        w = await db.get(Worker, int(worker_id))
        # company_id NULL = trabajador heredado sin empresa (datos antiguos)
        if not w or (w.company_id is not None and w.company_id != company_id):
            raise HTTPException(status_code=400, detail="El trabajador no pertenece a la empresa")
