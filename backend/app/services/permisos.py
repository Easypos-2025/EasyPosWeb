"""
Control de Acceso por rol (equivalente web del "Control de Acceso" del escritorio).

Catálogo en access_permissions; habilitados por rol en role_access_permissions.
El rol del sistema (SYSADMIN) tiene todos.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role_model import Role
from app.models.user_model import User


async def _es_sistema(db: AsyncSession, user: User) -> bool:
    role = await db.get(Role, user.role_id) if user.role_id else None
    return bool(role and role.is_system)


async def permisos_usuario(db: AsyncSession, user: User) -> set[str]:
    if await _es_sistema(db, user):
        return set((await db.execute(text("SELECT perm_key FROM access_permissions WHERE is_active = 1"))).scalars().all())
    return set((await db.execute(text("""
        SELECT p.perm_key FROM role_access_permissions p
        JOIN access_permissions a ON a.perm_key = p.perm_key AND a.is_active = 1
        WHERE p.role_id = :rid
    """), {"rid": user.role_id or 0})).scalars().all())


async def tiene_permiso(db: AsyncSession, user: User, clave: str) -> bool:
    return clave in await permisos_usuario(db, user)
