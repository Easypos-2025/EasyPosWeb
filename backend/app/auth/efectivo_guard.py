"""
Guardián de la forma de pago EFECTIVO (CLAUDE.md §8.10).

Sin exactamente una forma de pago Default y Activa (= EFECTIVO) no se registra nada ni se genera
ningún reporte: responde 409 con el header X-Error-Code: EFECTIVO_NO_CONFIGURADO y el frontend
muestra la ventana que explica cómo corregirlo (EfectivoNoConfiguradoModal).

Uso (dependencia de ROUTER, como tenant_guard):
    APIRouter(..., dependencies=[Depends(tenant_guard), Depends(efectivo_guard())])
    efectivo_guard(solo_escritura=True)  → solo POST/PUT/PATCH/DELETE (las consultas siguen)
    efectivo_guard(excluir=("/auth/",))  → rutas que no se bloquean (contienen ese texto)
La empresa se resuelve igual que la ruta: mesero → la de su token; usuario → la seleccionada en el
topbar (X-Company-Id) si tiene acceso, si no la propia. Sin token no hace nada (la ruta responde 401).
"""
from typing import Optional

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import decode_access_token
from app.auth import tenant
from app.database import get_db
from app.services.formas_pago import exigir_efectivo

_LECTURA = {"GET", "HEAD", "OPTIONS"}


async def _empresa(request: Request, db: AsyncSession) -> Optional[int]:
    auth = request.headers.get("authorization") or ""
    if not auth.lower().startswith("bearer "):
        return None
    token = auth[7:].strip()
    payload = decode_access_token(token)
    if not payload:
        return None
    if payload.get("type") == "waiter" or (payload.get("company_id") and not payload.get("user_id")):
        return int(payload.get("company_id") or 0) or None
    user = await tenant.user_from_token(db, token)
    own, allowed = await tenant.allowed_companies(db, user)
    try:
        pedida = int(request.headers.get("x-company-id") or 0)
    except ValueError:
        pedida = 0
    if pedida and (allowed is None or pedida in allowed):
        return pedida
    return own


def efectivo_guard(solo_escritura: bool = False, excluir: tuple = ()):
    async def _guard(request: Request, db: AsyncSession = Depends(get_db)) -> None:
        if request.method == "OPTIONS" or (solo_escritura and request.method in _LECTURA):
            return
        if any(e in request.url.path for e in excluir):
            return
        cid = await _empresa(request, db)
        if cid:
            await exigir_efectivo(db, cid)
    return _guard
