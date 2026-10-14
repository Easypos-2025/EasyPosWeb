"""
Factura de Proveedor (vista /compras/factura-proveedor, bajo "Transaccional"). Ver app/services/factura_proveedor.py.

  GET  /api/factura-proveedor/catalogos      proveedores, droguería, cargue unitario, escritorio
  GET  /api/factura-proveedor/productos      productos que se pueden comprar con su último costo
  GET  /api/factura-proveedor                consulta (fecha, proveedor, número o producto)
  GET  /api/factura-proveedor/{id}           detalle
  POST /api/factura-proveedor                registrar la factura completa
  POST /api/factura-proveedor/{id}/anular    anular con motivo (solo si no ha salido nada de lo que entró)
Permisos: pantalla /compras/factura-proveedor del rol (ver, crear, borrar = anular); ADMIN/SYSADMIN siempre.
La empresa es la de la sesión (topbar validada); nunca la del navegador.
"""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Annotated

from app.auth.bodega_guard import Bodega, es_admin_rol
from app.auth.dependencies import get_current_user
from app.auth.tenant import tenant_guard
from app.database import get_db
from app.models.role_model import Role
from app.models.user_model import User
from app.services import bodega_central as bc
from app.services import factura_proveedor as fp
from app.services import sede_pedidos

router = APIRouter(prefix="/api/factura-proveedor", tags=["Factura de Proveedor"], dependencies=[Depends(tenant_guard)])

RUTA = "/compras/factura-proveedor"
Codigo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]


async def _permiso(db: AsyncSession, user: User, accion: str) -> None:
    rol = await db.get(Role, user.role_id) if user.role_id else None
    if es_admin_rol(rol):
        return
    ok = (await db.execute(text(f"""
        SELECT 1 FROM role_modules rm JOIN system_modules sm ON sm.id = rm.module_id AND sm.route = :r
        WHERE rm.role_id = :rol AND rm.can_{accion} = 1 LIMIT 1
    """), {"r": RUTA, "rol": user.role_id or 0})).scalar()
    if not ok:
        raise HTTPException(status_code=403, detail="Su rol no tiene permiso para esta acción en Factura de Proveedor")


def _empresa(user: User, request: Request) -> Bodega:
    ip = (request.headers.get("X-Forwarded-For") or (request.client.host if request.client else "") or "")
    return Bodega(id=int(user.company_id), nit="", user=user, ip=ip.split(",")[0].strip()[:45])


@router.get("/catalogos")
async def catalogos(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await _permiso(db, user, "view")
    cid = int(user.company_id)
    proveedores = (await db.execute(text(
        "SELECT id_proveedor AS id, name, nit FROM suppliers WHERE company_id = :c AND is_active = 1 "
        "AND id_proveedor IS NOT NULL ORDER BY name"), {"c": cid})).mappings().all()
    return {"proveedores": [dict(p) for p in proveedores], "drogueria": await fp.es_drogueria(db, cid),
            "cargue_unitario": await bc.cargue_unitario(db, cid),
            "con_escritorio": await sede_pedidos.tiene_sede(db, cid)}


@router.get("/productos")
async def productos(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await _permiso(db, user, "view")
    return await fp.productos(db, int(user.company_id))


@router.get("")
async def listar(desde: Optional[date] = None, hasta: Optional[date] = None,
                 id_proveedor: Optional[int] = Query(default=None, ge=1),
                 texto: Optional[str] = Query(default=None, max_length=60),
                 db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await _permiso(db, user, "view")
    return await fp.listar(db, int(user.company_id), desde, hasta, id_proveedor, texto)


@router.get("/{fid}")
async def detalle(fid: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await _permiso(db, user, "view")
    return await fp.detalle(db, int(user.company_id), fid)


class LineaIn(BaseModel):
    dish_id: Annotated[int, Field(ge=1)]
    cantidad: Annotated[float, Field(gt=0, le=1_000_000)]
    valor_unitario: Annotated[float, Field(ge=0, le=2_000_000_000)]
    porc_descuento: Annotated[float, Field(ge=0, le=100)] = 0
    fecha_vence: Optional[date] = None
    imeis: Optional[Annotated[List[Codigo], Field(max_length=bc.MAX_REPLICAS)]] = None


class FacturaIn(BaseModel):
    id_proveedor: Annotated[int, Field(ge=1)]
    nro_factura: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]
    fecha: date
    observacion: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]] = None
    lineas: Annotated[List[LineaIn], Field(min_length=1, max_length=fp.MAX_LINEAS)]
    company_id: Optional[int] = None       # lo valida tenant_guard; no se usa


@router.post("", status_code=201)
async def crear(body: FacturaIn, request: Request, db: AsyncSession = Depends(get_db),
                user: User = Depends(get_current_user)):
    await _permiso(db, user, "create")
    res = await fp.crear(db, _empresa(user, request), body.model_dump(exclude={"company_id"}))
    await db.commit()
    return res


class AnularIn(BaseModel):
    motivo: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=255)]
    company_id: Optional[int] = None


@router.post("/{fid}/anular")
async def anular(fid: int, body: AnularIn, request: Request, db: AsyncSession = Depends(get_db),
                 user: User = Depends(get_current_user)):
    await _permiso(db, user, "delete")
    res = await fp.anular(db, _empresa(user, request), fid, body.motivo)
    await db.commit()
    return res
