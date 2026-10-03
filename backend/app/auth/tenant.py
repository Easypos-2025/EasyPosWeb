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
import logging
import time
from contextvars import ContextVar
from typing import Optional

from sqlalchemy.orm.attributes import set_committed_value

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.user_model import User
from app.models.role_model import Role

logger = logging.getLogger(__name__)

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
    from app.services.error_log import record_security
    record_security("Acceso a empresa no permitida", {"empresa_propia": own, "empresa_solicitada": requested})
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


async def _requested_companies(request: Request) -> set:
    """company_id solicitados explícitamente por el navegador: query y cuerpo JSON.
    (El header X-Company-Id lo aplica apply_selected_company, que lo ignora si no hay acceso.)"""
    found = set()
    for raw in (request.query_params.get("company_id"),):
        if raw not in (None, ""):
            try:
                found.add(int(raw))
            except ValueError:
                raise HTTPException(status_code=400, detail="company_id inválido")
    if request.method in ("POST", "PUT", "PATCH", "DELETE") and \
            "application/json" in (request.headers.get("content-type") or ""):
        try:
            body = await request.json()          # Starlette lo deja en caché para el endpoint
        except Exception:
            body = None
        items = body if isinstance(body, list) else [body]
        for it in items:
            if isinstance(it, dict) and it.get("company_id") not in (None, ""):
                try:
                    found.add(int(it["company_id"]))
                except (TypeError, ValueError):
                    raise HTTPException(status_code=400, detail="company_id inválido")
    return found


async def tenant_guard(request: Request, db: AsyncSession = Depends(get_db)) -> None:
    """Dependencia de ROUTER: rechaza (403) cualquier company_id del navegador al que el
    usuario no tenga acceso. Uso: APIRouter(..., dependencies=[Depends(tenant_guard)]).
    No reemplaza la autenticación de cada ruta: si no hay token, la ruta responde 401."""
    requested = await _requested_companies(request)
    if not requested:
        return
    auth = request.headers.get("authorization") or ""
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    token = auth[7:].strip()
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    if payload.get("type") == "waiter" or (payload.get("company_id") and not payload.get("user_id")):
        own = int(payload.get("company_id") or 0)
        for cid in requested:
            check_company(own, frozenset({own}), cid)
        return

    user = None
    if payload.get("user_id"):
        user = await db.get(User, int(payload["user_id"]))
    elif payload.get("sub"):
        user = (await db.execute(select(User).where(User.email == payload["sub"]))).scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    own, allowed = await allowed_companies(db, user)
    for cid in requested:
        check_company(own, allowed, cid)


# ─── Empresa seleccionada en el topbar (header X-Company-Id) ─────────────────
# El frontend envía en TODA petición la empresa elegida en el selector del topbar.
# SelectedCompanyMiddleware la guarda aquí; la autenticación la aplica al usuario
# de esa petición SOLO si tiene acceso (ADMIN mismo NIT / SYSADMIN). Nunca se
# persiste en la tabla users.
_selected_company: ContextVar[Optional[int]] = ContextVar("selected_company", default=None)


class SelectedCompanyMiddleware:
    """Middleware ASGI puro: lee X-Company-Id y lo deja en el contexto de la petición."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)
        value = None
        for k, v in scope.get("headers") or []:
            if k == b"x-company-id":
                try:
                    value = int(v.decode().strip()) or None
                except ValueError:
                    value = None
                break
        token = _selected_company.set(value)
        try:
            await self.app(scope, receive, send)
        finally:
            _selected_company.reset(token)


async def apply_selected_company(db: AsyncSession, user: User) -> User:
    """Aplica al usuario (solo en memoria, para esta petición) la empresa del topbar
    si tiene acceso; si no, se ignora y queda su empresa propia."""
    from app.services.error_log import set_identity
    requested = _selected_company.get()
    if not requested or requested == user.company_id:
        set_identity(user_id=user.id, company_id=user.company_id)
        return user
    own, allowed = await allowed_companies(db, user)
    if allowed is None or requested in allowed:
        # set_committed_value: cambia el valor SIN marcar el objeto como modificado,
        # así un commit posterior nunca escribe este company_id en la tabla users.
        set_committed_value(user, "company_id", requested)
    else:
        logger.warning("X-Company-Id %s ignorado: usuario %s sin acceso", requested, user.id)
    set_identity(user_id=user.id, company_id=user.company_id)
    return user


def clear_cache(user_id: Optional[int] = None) -> None:
    if user_id is None:
        _allowed_cache.clear()
    else:
        _allowed_cache.pop(user_id, None)
