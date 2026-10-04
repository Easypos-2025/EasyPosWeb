"""
Control de Acceso por rol (equivalente web del "Control de Acceso" del escritorio).

Catálogo en access_permissions; habilitados por rol en role_access_permissions.
El rol del sistema (SYSADMIN) tiene todos.
Los meseros-vendedores (meseros = pos_waiters, entran con PIN a la comanda / TPV) también tienen
rol (pos_waiters.role_id, de su misma empresa): sus acciones se validan igual que las de un usuario.
"""
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role_model import Role
from app.models.user_model import User


async def _es_sistema(db: AsyncSession, user: User) -> bool:
    role = await db.get(Role, user.role_id) if user.role_id else None
    return bool(role and role.is_system)


async def permisos_rol(db: AsyncSession, role_id: int) -> set[str]:
    return set((await db.execute(text("""
        SELECT p.perm_key FROM role_access_permissions p
        JOIN access_permissions a ON a.perm_key = p.perm_key AND a.is_active = 1
        WHERE p.role_id = :rid
    """), {"rid": int(role_id or 0)})).scalars().all())


async def permisos_usuario(db: AsyncSession, user: User) -> set[str]:
    if await _es_sistema(db, user):
        return set((await db.execute(text("SELECT perm_key FROM access_permissions WHERE is_active = 1"))).scalars().all())
    return await permisos_rol(db, user.role_id)


async def permisos_comanda(db: AsyncSession, payload: dict) -> set[str]:
    """Permisos de quien opera la comanda / TPV: mesero (token de mesero → rol del mesero, de su
    misma empresa) o usuario del sistema (rol del usuario)."""
    if payload.get("type") == "waiter" or not payload.get("user_id"):
        rid = (await db.execute(text("""
            SELECT w.role_id FROM pos_waiters w
            JOIN roles r ON r.id = w.role_id AND r.company_id = w.company_id
            WHERE w.id = :wid AND w.company_id = :cid
        """), {"wid": int(payload.get("waiter_id") or 0), "cid": int(payload.get("company_id") or 0)})).scalar()
        return await permisos_rol(db, rid) if rid else set()
    user = await db.get(User, int(payload["user_id"]))
    return await permisos_usuario(db, user) if user else set()


def exigir(permisos: set[str], clave: str, mensaje: str) -> None:
    """403 si el rol no tiene el permiso (Roles → Control de Acceso)."""
    if clave not in permisos:
        raise HTTPException(status_code=403, detail=mensaje)


async def tiene_permiso(db: AsyncSession, user: User, clave: str) -> bool:
    return clave in await permisos_usuario(db, user)
