"""
Guardián de la Bodega Central (migración 042).

La bodega es una empresa marcada por SYSADMIN con company_configs.has_bodega_central = 1. Sus SEDES son las
empresas ACTIVAS con su mismo NIT. Es la única excepción en la que una empresa lee o escribe datos de otra,
así que todo pasa por aquí:

  · requiere_bodega  → la empresa efectiva de la petición (topbar validada por tenant) debe ser una bodega
                       y el usuario ADMIN o SYSADMIN. Si no: 403 con X-Error-Code BODEGA_NO_HABILITADA.
  · sedes_del_nit    → única lista válida de sedes destino/origen; se calcula siempre en el servidor.
  · exigir_sede      → un id de sede enviado por el navegador solo se acepta si está en esa lista.
"""
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.role_model import Role
from app.models.user_model import User


@dataclass
class Bodega:
    id: int
    nit: str
    user: User
    ip: str

    @property
    def usuario(self) -> str:
        return (self.user.nombre or self.user.email or f"usuario {self.user.id}")[:150]


def _no_habilitada(detalle: str) -> HTTPException:
    return HTTPException(status_code=403, detail=detalle, headers={"X-Error-Code": "BODEGA_NO_HABILITADA"})


async def es_bodega(db: AsyncSession, cid: int) -> bool:
    return bool((await db.execute(text(
        "SELECT 1 FROM company_configs WHERE company_id = :c AND COALESCE(has_bodega_central, 0) = 1 LIMIT 1"
    ), {"c": cid})).scalar())


async def requiere_bodega(request: Request, db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(get_current_user)) -> Bodega:
    role = await db.get(Role, current_user.role_id) if current_user.role_id else None
    if not (role and (role.is_system or "ADMIN" in (role.name or "").upper())):
        raise _no_habilitada("Solo el administrador puede operar la bodega central")
    cid = int(current_user.company_id or 0)
    if not cid or not await es_bodega(db, cid):
        raise _no_habilitada("La empresa seleccionada no está habilitada como bodega central")
    nit = (await db.execute(text(
        "SELECT identification_number FROM companies WHERE id_company = :c AND state = 1"
    ), {"c": cid})).scalar()
    if not (nit or "").strip():
        raise _no_habilitada("La bodega central no tiene NIT o está inactiva")
    ip = (request.headers.get("X-Forwarded-For") or (request.client.host if request.client else "") or "")
    return Bodega(id=cid, nit=str(nit).strip(), user=current_user, ip=ip.split(",")[0].strip()[:45])


async def sedes_del_nit(db: AsyncSession, bodega: Bodega) -> list[dict]:
    """Empresas activas con el mismo NIT de la bodega (sin ella ni otras bodegas), A-Z."""
    filas = (await db.execute(text("""
        SELECT c.id_company AS id, c.name AS nombre,
               EXISTS(SELECT 1 FROM company_local_agents a WHERE a.company_id = c.id_company AND a.activo = 1) AS con_escritorio
        FROM companies c
        LEFT JOIN company_configs cc ON cc.company_id = c.id_company
        WHERE c.identification_number = :nit AND c.state = 1 AND c.id_company <> :b
          AND COALESCE(cc.has_bodega_central, 0) = 0
        ORDER BY c.name
    """), {"nit": bodega.nit, "b": bodega.id})).mappings().all()
    return [{"id": int(f["id"]), "nombre": f["nombre"], "con_escritorio": bool(f["con_escritorio"])} for f in filas]


async def exigir_sede(db: AsyncSession, bodega: Bodega, sede_id: int) -> dict:
    for s in await sedes_del_nit(db, bodega):
        if s["id"] == int(sede_id or 0):
            return s
    from app.services.error_log import record_security
    record_security("Bodega central: sede fuera de su NIT", {"bodega": bodega.id, "sede_solicitada": sede_id})
    raise HTTPException(status_code=403, detail="La sede no pertenece a la bodega central")
