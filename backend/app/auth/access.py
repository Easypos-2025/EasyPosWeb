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
