"""
Resolución de empresa (tenant) — regla ÚNICA para decidir con qué company_id
puede trabajar una petición. Nunca se confía en un company_id enviado por el
navegador (header, query o body) sin validarlo aquí.

Reglas:
  - Token de MESERO  → solo la empresa de su token (firmado; no se puede alterar).
  - Usuario SYSADMIN → cualquier empresa.
  - Usuario ADMIN    → su empresa + las empresas con su mismo NIT
                       (igual que el selector de empresas del topbar).
  - Otros roles      → solo su empresa.
  Si se solicita una empresa fuera de lo permitido → 403.

Las empresas permitidas por usuario se guardan en memoria del servidor 60 s
para no consultar la BD en cada petición.
"""
import time
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.user_model import User
from app.models.role_model import Role

_CACHE_TTL = 60
_allowed_cache: dict = {}          # user_id → (expira, company_id propia, frozenset permitidas | None=todas)


def _is_admin(role: Optional[Role]) -> bool:
    return bool(role) and "ADMIN" in (role.name or "").upper()


async def allowed_companies(db: AsyncSession, user: User) -> tuple:
    """(empresa propia, set de empresas permitidas | None si es SYSADMIN)."""
    hit = _allowed_cache.get(user.id)
    if hit and hit[0] > time.monotonic():
        return hit[1], hit[2]

    role = await db.get(Role, user.role_id) if user.role_id else None
    own = int(user.company_id) if user.company_id else None
    if role and role.is_system:
        allowed = None
    elif _is_admin(role) and own:
        rows = (await db.execute(text("""
            SELECT c2.id_company
            FROM companies c1
            JOIN companies c2 ON c2.identification_number = c1.identification_number
            WHERE c1.id_company = :cid AND COALESCE(c1.identification_number, '') <> ''
        """), {"cid": own})).all()
        allowed = frozenset({own, *(int(r[0]) for r in rows)})
    else:
        allowed = frozenset({own}) if own else frozenset()

    _allowed_cache[user.id] = (time.monotonic() + _CACHE_TTL, own, allowed)
    return own, allowed


def check_company(own: Optional[int], allowed, requested: Optional[int]) -> int:
    """Devuelve la empresa efectiva o lanza 403 si la solicitada no está permitida."""
    if not requested:
        if not own:
            raise HTTPException(status_code=403, detail="Usuario sin empresa asignada")
        return own
    requested = int(requested)
    if allowed is None or requested in allowed:
        return requested
    raise HTTPException(status_code=403, detail="No tiene acceso a la empresa solicitada")


async def user_from_token(db: AsyncSession, token: str) -> User:
    """Usuario de un token de sesión (firma + sesión activa)."""
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    active = (await db.execute(select(UserSession).where(
        UserSession.token == token, UserSession.is_active == True))).scalar_one_or_none()
    if not active:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    uid = payload.get("user_id")
    user = await db.get(User, int(uid)) if uid else None
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user


async def resolve_company(db: AsyncSession, user: User, requested: Optional[int]) -> int:
    own, allowed = await allowed_companies(db, user)
    return check_company(own, allowed, requested)


def clear_cache(user_id: Optional[int] = None) -> None:
    if user_id is None:
        _allowed_cache.clear()
    else:
        _allowed_cache.pop(user_id, None)
