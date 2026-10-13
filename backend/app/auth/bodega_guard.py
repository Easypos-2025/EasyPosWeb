"""
Guardián de la Bodega Central (migración 042).

La bodega es una empresa marcada por SYSADMIN con company_configs.has_bodega_central = 1. Sus SEDES son las
empresas ACTIVAS con su mismo NIT. Es la única excepción en la que una empresa lee o escribe datos de otra,
así que todo pasa por aquí:

  · seccion_bodega(ruta) → la empresa efectiva de la petición (topbar validada por tenant) debe ser una bodega.
                       ADMIN/SYSADMIN entran siempre; los demás roles (ayudantes de la bodega) según su permiso en
                       ESA pantalla del menú Bodega Central (Productos, Importar, Enviar a sedes, Usuarios…):
                       ver para consultar, crear o editar para guardar. requiere_bodega = cualquier pantalla de la
                       bodega con permiso de ver (datos generales). Si no: 403 con X-Error-Code BODEGA_NO_HABILITADA.
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


RUTA_BODEGA = "/bodega-central"
_ESCRITURA = {"POST", "PUT", "PATCH", "DELETE"}


def es_admin_rol(role) -> bool:
    return bool(role) and (bool(role.is_system) or "ADMIN" in (role.name or "").upper())


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


async def _resolver(request: Request, db: AsyncSession, current_user: User, ruta) -> Bodega:
    role = await db.get(Role, current_user.role_id) if current_user.role_id else None
    if not role:
        raise _no_habilitada("Usuario sin rol")
    if not es_admin_rol(role):
        if ruta:
            filtro, params = "sm.route = :ruta", {"ruta": ruta}
        else:      # datos generales: basta ver alguna pantalla de la bodega
            filtro, params = "(sm.route = :base OR sm.route LIKE :pref)", {"base": RUTA_BODEGA, "pref": RUTA_BODEGA + "/%"}
        permiso = (await db.execute(text(f"""
            SELECT MAX(rm.can_view), MAX(rm.can_create), MAX(rm.can_edit) FROM role_modules rm
            JOIN system_modules sm ON sm.id = rm.module_id AND {filtro}
            WHERE rm.role_id = :r
        """), {"r": role.id, **params})).first()
        if not permiso or not permiso[0]:
            raise _no_habilitada("Su rol no tiene acceso a esta opción de la bodega central")
        if request.method in _ESCRITURA and not (permiso[1] or permiso[2]):
            raise _no_habilitada("Su rol solo puede consultar esta opción de la bodega central")
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


def seccion_bodega(ruta=None):
    """Dependencia por pantalla del menú Bodega Central (ruta = '/bodega-central/productos', …)."""
    async def _dep(request: Request, db: AsyncSession = Depends(get_db),
                   current_user: User = Depends(get_current_user)) -> Bodega:
        return await _resolver(request, db, current_user, ruta)
    _dep.ruta = ruta
    return _dep


# Pantallas (hijos del menú Bodega Central, migración 045)
SEC_PRODUCTOS = seccion_bodega(RUTA_BODEGA + "/productos")
SEC_IMPORTAR = seccion_bodega(RUTA_BODEGA + "/importar")
SEC_ENVIAR = seccion_bodega(RUTA_BODEGA + "/enviar")
SEC_USUARIOS = seccion_bodega(RUTA_BODEGA + "/usuarios")
SEC_MOVIMIENTOS = seccion_bodega(RUTA_BODEGA + "/movimientos")
requiere_bodega = seccion_bodega(None)


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


# ─── Sedes administradas por la bodega ───────────────────────────────────────
# Con una bodega activa en el NIT (aunque sea de una sola sede), los catálogos compartidos se crean y cambian
# SOLO en la bodega y se envían a las sedes. En la sede quedan de solo consulta, para todos los roles.

async def bodega_de_sede(db: AsyncSession, cid: int):
    """Bodega activa que administra a la empresa cid ({id, nombre}), o None (sin bodega o es la bodega)."""
    fila = (await db.execute(text("""
        SELECT b.id_company AS id, b.name AS nombre
        FROM companies s
        JOIN companies b ON b.identification_number = s.identification_number AND b.id_company <> s.id_company
                         AND b.state = 1
        JOIN company_configs cc ON cc.company_id = b.id_company AND COALESCE(cc.has_bodega_central, 0) = 1
        WHERE s.id_company = :c AND COALESCE(s.identification_number, '') <> ''
          AND NOT EXISTS (SELECT 1 FROM company_configs sc WHERE sc.company_id = s.id_company
                          AND COALESCE(sc.has_bodega_central, 0) = 1)
        ORDER BY b.id_company LIMIT 1
    """), {"c": int(cid or 0)})).mappings().first()
    return dict(fila) if fila else None


async def exigir_no_administrada(db: AsyncSession, cid: int, que: str) -> None:
    """403 ADMINISTRADO_POR_BODEGA si la empresa cid es una sede administrada por una bodega."""
    bodega = await bodega_de_sede(db, cid) if cid else None
    if bodega:
        raise HTTPException(
            status_code=403,
            detail=f"{que} los administra la bodega central «{bodega['nombre']}». Créelos o modifíquelos "
                   f"allá y envíelos a esta sede.",
            headers={"X-Error-Code": "ADMINISTRADO_POR_BODEGA"})


def bloqueo_bodega(que: str):
    """Dependencia de ROUTER: en una sede administrada por la bodega rechaza crear/editar/borrar (403
    ADMINISTRADO_POR_BODEGA). Las consultas siguen. La empresa se resuelve igual que la ruta."""
    async def _guard(request: Request, db: AsyncSession = Depends(get_db)) -> None:
        if request.method not in _ESCRITURA:
            return
        from app.auth.efectivo_guard import _empresa
        await exigir_no_administrada(db, await _empresa(request, db), que)
    return _guard
