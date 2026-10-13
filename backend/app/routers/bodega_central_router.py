"""
Bodega Central (F0) — vista /bodega-central. Solo empresas marcadas por SYSADMIN (has_bodega_central) y
usuarios ADMIN/SYSADMIN (bodega_guard.requiere_bodega). Las sedes salen siempre de bodega_guard.sedes_del_nit.

  GET  /api/bodega-central                  bodega, sedes del NIT, cargue unitario, catálogos (categorías, proveedores)
  GET  /api/bodega-central/productos        productos con stock y estado por sede
  POST /api/bodega-central/productos        crear producto (+ cantidad inicial)
  POST /api/bodega-central/entradas         entrada manual de inventario a la bodega
  POST /api/bodega-central/replicar/{id}    réplica por IMEI (cargue unitario): un producto por código, cantidad 1
  GET  /api/bodega-central/resumen-sede/{id} cuántos registros tiene la sede de cada dato importable
  POST /api/bodega-central/importar         copiar de una sede los datos escogidos (productos con cantidad 0)
  GET  /api/bodega-central/movimientos      kardex/auditoría de la bodega
  GET  /api/bodega-central/enviar/{tipo}    proveedores / categorías / roles de la bodega que se pueden enviar a las sedes
  POST /api/bodega-central/enviar           enviar los escogidos a las sedes marcadas (crea o sobrescribe)
  GET  /api/bodega-central/administrado     (cualquier usuario) ¿una bodega administra la empresa actual?
  GET  /api/bodega-central/usuarios         personas (por correo) de la bodega y sus sedes, con rol y estado por empresa
  GET  /api/bodega-central/roles-empresas   roles de cada empresa del grupo (para invitar / asignar)
  POST /api/bodega-central/invitar          link de invitación a varias empresas, con un rol por empresa
  POST /api/bodega-central/usuarios/asignar agregar a otra empresa (misma contraseña) o cambiar el rol allí
  POST /api/bodega-central/usuarios/estado  activar / desactivar a la persona en una empresa
  GET  /api/bodega-central/valores/productos       productos de la bodega para actualizar valores
  POST /api/bodega-central/valores/vista-previa    por sede: valor actual → nuevo (regla del cero), sin guardar
  POST /api/bodega-central/valores/enviar          aplica venta, mínimo, costo, IVA y stock mínimo en las sedes
  GET  /api/bodega-central/valores/listas          listas de precios por cliente de la bodega
  POST /api/bodega-central/valores/listas/enviar   envía esas listas (cliente por cédula; se crea si no existe)
  GET  /api/bodega-central/traslados/productos?origen_id=  productos del origen con su stock
  POST /api/bodega-central/traslados                crear traslados (uno por destino); automático en empresas web
  GET  /api/bodega-central/traslados                listado (estado, empresa, desde, hasta)
  GET  /api/bodega-central/traslados/{id}           detalle con la novedad de cada artículo
  POST /api/bodega-central/traslados/{id}/anular    anular lo que aún no se cargó (motivo obligatorio)
  GET  /api/bodega-central/tablero?fecha=           tarjetas del dashboard: ventas, turnos, escritorio y traslados por sede
  GET  /api/bodega-central/tablero/sede/{id}?fecha= resumen completo de una sede

Las operaciones de escritura reciben `clave` (idempotencia): repetirla no duplica nada.
Si la base de datos está ocupada (otra empresa sincronizando), se responde 409 con un mensaje para reintentar
en lugar de un error 500.
"""
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Annotated

from app.auth.bodega_guard import (Bodega, SEC_ENVIAR, SEC_IMPORTAR, SEC_MOVIMIENTOS, SEC_PRODUCTOS, SEC_USUARIOS,
                                   SEC_TRASLADOS, SEC_VALORES,
                                   bodega_de_sede, exigir_sede, requiere_bodega, sedes_del_nit)
from app.auth.dependencies import get_current_user
from app.models.user_model import User
from app.auth.tenant import tenant_guard
from app.database import get_db
from app.services import bodega_central as svc

router = APIRouter(prefix="/api/bodega-central", tags=["Bodega Central"], dependencies=[Depends(tenant_guard)])

Clave = Optional[Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[A-Za-z0-9\-]{8,64}$")]]
Money = Annotated[float, Field(ge=0, le=2_000_000_000)]
Cant = Annotated[int, Field(ge=1, le=1_000_000)]
_BLOQUEO = (1205, 1213)          # lock wait timeout, deadlock


@asynccontextmanager
async def _escritura(db: AsyncSession):
    """Bloqueo momentáneo de la base de datos → 409 amable (deshace todo lo de la operación)."""
    try:
        yield
    except OperationalError as e:
        if getattr(e.orig, "args", [None])[0] not in _BLOQUEO:
            raise
        await db.rollback()
        raise HTTPException(status_code=409, detail="La base de datos está ocupada en este momento (una sede está "
                                                    "sincronizando). No se guardó nada: intente de nuevo en un minuto.",
                            headers={"X-Error-Code": "BD_OCUPADA"})


@router.get("")
async def resumen(db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(requiere_bodega)):
    nombre = (await db.execute(text("SELECT name FROM companies WHERE id_company = :c"), {"c": bodega.id})).scalar()
    categorias = (await db.execute(text(
        "SELECT id, name FROM pos_dish_categories WHERE company_id = :c AND is_active = 1 ORDER BY name"
    ), {"c": bodega.id})).mappings().all()
    proveedores = (await db.execute(text(
        "SELECT id_proveedor AS id, name FROM suppliers WHERE company_id = :c AND is_active = 1 "
        "AND id_proveedor IS NOT NULL ORDER BY name"
    ), {"c": bodega.id})).mappings().all()
    return {
        "bodega": {"id": bodega.id, "nombre": nombre, "nit": bodega.nit},
        "sedes": await sedes_del_nit(db, bodega),
        "cargue_unitario": await svc.cargue_unitario(db, bodega.id),
        "categorias": [dict(c) for c in categorias],
        "proveedores": [dict(p) for p in proveedores],
    }


@router.get("/productos")
async def productos(db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(SEC_PRODUCTOS)):
    return await svc.listar_productos(db, bodega)


class ProductoIn(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=250)]
    product_code: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=60)]] = ""
    category_id: Annotated[int, Field(ge=1)]
    id_proveedor: Optional[Annotated[int, Field(ge=0)]] = 0
    price: Annotated[int, Field(ge=0, le=2_000_000_000)] = 0
    wholesale_price: Money = 0          # precio mínimo (Precio_x_Mayor del escritorio)
    product_cost: Money = 0
    tax: Annotated[float, Field(ge=0, le=100)] = 0
    minimum_stock: Annotated[float, Field(ge=0, le=1_000_000)] = 0
    extra_print: bool = False           # desactivar al vender
    ask_product_description: bool = False
    cantidad_inicial: Annotated[int, Field(ge=0, le=1_000_000)] = 0
    clave: Clave = None
    company_id: Optional[int] = None    # lo valida tenant_guard; no se usa


@router.post("/productos", status_code=201)
async def crear(body: ProductoIn, db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(SEC_PRODUCTOS)):
    if await svc.clave_usada(db, bodega, body.clave):
        return {"ok": True, "repetida": True}
    if body.wholesale_price and body.price and body.wholesale_price > body.price:
        raise HTTPException(status_code=422, detail="El precio mínimo no puede ser mayor que el precio de venta")
    unitario = await svc.cargue_unitario(db, bodega.id)
    datos = body.model_dump(exclude={"clave", "company_id", "cantidad_inicial"})
    cantidad = body.cantidad_inicial
    if unitario:
        datos["extra_print"] = True      # cada unidad es única: se desactiva al venderse
        cantidad = 1                     # Crear_Plato_Nuevo: entra con cantidad 1 al registrarlo
    async with _escritura(db):
        dish_id = await svc.crear_producto(db, bodega.id, datos)
        if cantidad:
            proveedor = (await svc._producto(db, bodega.id, dish_id))["id_proveedor"] or 0
            await svc.registrar_entrada(db, bodega, dish_id, cantidad, proveedor,
                                        "Entrada manual al registrar producto")
        await svc.movimiento(db, bodega, "CREACION", dish_id, cantidad, body.name, clave=body.clave)
        await db.commit()
    return {"ok": True, "id": dish_id}


class EntradaIn(BaseModel):
    dish_id: Annotated[int, Field(ge=1)]
    cantidad: Cant
    observacion: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]] = ""
    clave: Clave = None
    company_id: Optional[int] = None


@router.post("/entradas", status_code=201)
async def entrada(body: EntradaIn, db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(SEC_PRODUCTOS)):
    if await svc.clave_usada(db, bodega, body.clave):
        return {"ok": True, "repetida": True}
    prod = await svc._producto(db, bodega.id, body.dish_id)          # 404 si no es de la bodega
    if str(prod["extra_print"] or "0") == "1" and await svc.cargue_unitario(db, bodega.id):
        raise HTTPException(status_code=409, detail="Un producto de cargue unitario (IMEI) no recibe más "
                                                    "cantidades: use Replicar para registrar más unidades")
    async with _escritura(db):
        eid = await svc.registrar_entrada(db, bodega, body.dish_id, body.cantidad, prod["id_proveedor"] or 0,
                                          body.observacion or "Entrada manual bodega")
        await svc.movimiento(db, bodega, "ENTRADA", body.dish_id, body.cantidad, body.observacion or "",
                             referencia=str(eid), clave=body.clave)
        await db.commit()
    return {"ok": True, "id": eid}


class ReplicarIn(BaseModel):
    nombre_base: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]] = ""
    codigos: Annotated[List[Annotated[str, StringConstraints(strip_whitespace=True, max_length=60)]],
                       Field(min_length=1, max_length=svc.MAX_REPLICAS)]
    clave: Clave = None
    company_id: Optional[int] = None


@router.post("/replicar/{dish_id}", status_code=201)
async def replicar(dish_id: int, body: ReplicarIn, db: AsyncSession = Depends(get_db),
                   bodega: Bodega = Depends(SEC_PRODUCTOS)):
    async with _escritura(db):
        res = await svc.replicar(db, bodega, dish_id, body.nombre_base or "", body.codigos, body.clave)
        await db.commit()
    return res


@router.get("/resumen-sede/{sede_id}")
async def resumen_importar(sede_id: int, db: AsyncSession = Depends(get_db),
                           bodega: Bodega = Depends(SEC_IMPORTAR)):
    await exigir_sede(db, bodega, sede_id)
    return await svc.resumen_sede(db, sede_id)


class ImportarIn(BaseModel):
    sede_id: Annotated[int, Field(ge=1)]
    datos: Annotated[List[Annotated[str, StringConstraints(max_length=30)]], Field(min_length=1, max_length=10)]
    clave: Clave = None
    company_id: Optional[int] = None


@router.post("/importar")
async def importar(body: ImportarIn, db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(SEC_IMPORTAR)):
    invalidos = [d for d in body.datos if d not in svc.DATOS_IMPORTAR]
    if invalidos:
        raise HTTPException(status_code=422, detail="Dato a importar no válido")
    sede = await exigir_sede(db, bodega, body.sede_id)
    async with _escritura(db):
        res = await svc.importar_catalogo(db, bodega, sede, body.datos, body.clave)
        await db.commit()
    return res


@router.get("/movimientos")
async def movimientos(db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(SEC_MOVIMIENTOS)):
    filas = (await db.execute(text("""
        SELECT m.id, m.tipo, m.dish_id, d.name AS producto, d.product_code AS codigo, m.cantidad,
               m.sede_id, c.name AS sede, m.detalle, m.usuario, m.created_at
        FROM bc_movimientos m
        LEFT JOIN pos_dishes d ON d.company_id = m.bodega_id AND d.id = m.dish_id
        LEFT JOIN companies c ON c.id_company = m.sede_id
        WHERE m.bodega_id = :b
        ORDER BY m.id DESC
        LIMIT 300
    """), {"b": bodega.id})).mappings().all()
    return [{**dict(f), "cantidad": float(f["cantidad"] or 0),
             "created_at": f["created_at"].isoformat(timespec="minutes") if f["created_at"] else None} for f in filas]


# ─── Enviar a sedes (administración central) ─────────────────────────────────

@router.get("/administrado")
async def administrado(company_id: Optional[int] = Query(None, ge=1), db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    """Las pantallas de catálogos compartidos lo consultan para quedar de solo consulta en una sede.
    company_id: la empresa escogida en la pantalla (roles de SYSADMIN); se valida con tenant (403 si es ajena)."""
    from app.auth import tenant
    cid = await tenant.resolve_company(db, current_user, company_id) if company_id else current_user.company_id
    bodega = await bodega_de_sede(db, cid)
    return {"administrado_por": bodega}


@router.get("/enviar/{tipo}")
async def catalogo_envio(tipo: str, db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(SEC_ENVIAR)):
    if tipo == "roles":
        return await svc.catalogo_roles(db, bodega)
    if tipo == "formas_pago":
        return await svc.catalogo_formas_pago(db, bodega)
    if tipo not in svc.CATALOGOS_ENVIO:
        raise HTTPException(status_code=404, detail="Dato no válido")
    return await svc.catalogo_bodega(db, bodega, tipo)


class EnviarIn(BaseModel):
    tipo: Annotated[str, StringConstraints(max_length=30)]
    ids: Annotated[List[Annotated[int, Field(ge=0)]], Field(min_length=1, max_length=svc.MAX_ENVIO)]
    sedes: Annotated[List[Annotated[int, Field(ge=1)]], Field(min_length=1, max_length=50)]
    clave: Clave = None
    company_id: Optional[int] = None


@router.post("/enviar")
async def enviar(body: EnviarIn, db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(SEC_ENVIAR)):
    sedes = [await exigir_sede(db, bodega, s) for s in sorted(set(body.sedes))]     # 403 si alguna es ajena
    async with _escritura(db):
        if body.tipo == "roles":
            res = await svc.enviar_roles(db, bodega, body.ids, sedes, body.clave)
        elif body.tipo == "formas_pago":
            res = await svc.enviar_formas_pago(db, bodega, body.ids, sedes, body.clave)
        else:
            res = await svc.enviar_a_sedes(db, bodega, body.tipo, body.ids, sedes, body.clave)
        await db.commit()
    return res


# ─── Usuarios del grupo ──────────────────────────────────────────────────────

@router.get("/usuarios")
async def usuarios(db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(SEC_USUARIOS)):
    return await svc.usuarios_grupo(db, bodega)


@router.get("/roles-empresas")
async def roles_empresas(db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(SEC_USUARIOS)):
    return await svc.roles_empresas(db, bodega)


class AsignacionIn(BaseModel):
    empresa_id: Annotated[int, Field(ge=1)]
    role_id: Annotated[int, Field(ge=1)]


class InvitarIn(BaseModel):
    asignaciones: Annotated[List[AsignacionIn], Field(min_length=1, max_length=50)]
    company_id: Optional[int] = None


@router.post("/invitar", status_code=201)
async def invitar(body: InvitarIn, db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(SEC_USUARIOS)):
    async with _escritura(db):
        res = await svc.invitar(db, bodega, [{"company_id": a.empresa_id, "role_id": a.role_id}
                                             for a in body.asignaciones])
        await db.commit()
    return res


class AsignarIn(BaseModel):
    # "empresa_id" (no company_id): lo valida la bodega contra su grupo, no el tenant del usuario (un ayudante
    # de la bodega solo tiene acceso a la bodega, pero sí puede dar acceso a sus sedes)
    email: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=100,
                                            pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]
    empresa_id: Annotated[int, Field(ge=1)]
    role_id: Annotated[int, Field(ge=1)]


@router.post("/usuarios/asignar")
async def asignar(body: AsignarIn, db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(SEC_USUARIOS)):
    async with _escritura(db):
        res = await svc.asignar_empresa(db, bodega, body.email, body.empresa_id, body.role_id)
        await db.commit()
    return res


class EstadoIn(BaseModel):
    user_id: Annotated[int, Field(ge=1)]
    activo: bool


@router.post("/usuarios/estado")
async def estado(body: EstadoIn, db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(SEC_USUARIOS)):
    async with _escritura(db):
        res = await svc.cambiar_estado(db, bodega, body.user_id, body.activo)
        await db.commit()
    return res


# ─── Actualizar valores en sede ──────────────────────────────────────────────

class ValoresIn(BaseModel):
    ids: Annotated[List[Annotated[int, Field(ge=1)]], Field(min_length=1, max_length=svc.MAX_ENVIO)]
    sedes: Annotated[List[Annotated[int, Field(ge=1)]], Field(min_length=1, max_length=50)]
    clave: Clave = None
    company_id: Optional[int] = None


@router.get("/valores/productos")
async def valores_productos(db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(SEC_VALORES)):
    return await svc.listar_productos(db, bodega)


@router.post("/valores/vista-previa")
async def valores_vista_previa(body: ValoresIn, db: AsyncSession = Depends(get_db),
                               bodega: Bodega = Depends(SEC_VALORES)):
    sedes = [await exigir_sede(db, bodega, s) for s in sorted(set(body.sedes))]
    # Sin commit: la sesión se cierra y descarta todo (la vista previa no guarda nada, ni vínculos nuevos)
    return await svc.vista_previa_valores(db, bodega, body.ids, sedes)


@router.post("/valores/enviar")
async def valores_enviar(body: ValoresIn, db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(SEC_VALORES)):
    sedes = [await exigir_sede(db, bodega, s) for s in sorted(set(body.sedes))]
    async with _escritura(db):
        res = await svc.enviar_valores(db, bodega, body.ids, sedes, body.clave)
        await db.commit()
    return res


@router.get("/valores/listas")
async def valores_listas(db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(SEC_VALORES)):
    return await svc.listas_bodega(db, bodega)


@router.post("/valores/listas/enviar")
async def valores_listas_enviar(body: ValoresIn, db: AsyncSession = Depends(get_db),
                                bodega: Bodega = Depends(SEC_VALORES)):
    sedes = [await exigir_sede(db, bodega, s) for s in sorted(set(body.sedes))]
    async with _escritura(db):
        res = await svc.enviar_listas(db, bodega, body.ids, sedes, body.clave)
        await db.commit()
    return res


# ─── Traslados ───────────────────────────────────────────────────────────────
from app.services import bodega_traslados as tras_svc


async def _empresa_grupo(db: AsyncSession, bodega: Bodega, cid: int) -> int:
    if int(cid) not in await svc.empresas_grupo(db, bodega):
        from app.services.error_log import record_security
        record_security("Bodega central: empresa fuera de su NIT", {"bodega": bodega.id, "empresa": cid})
        raise HTTPException(status_code=403, detail="La empresa no pertenece a la bodega central")
    return int(cid)


@router.get("/traslados/productos")
async def traslados_productos(origen_id: int = Query(..., ge=1), db: AsyncSession = Depends(get_db),
                              bodega: Bodega = Depends(SEC_TRASLADOS)):
    return await tras_svc.productos_origen(db, await _empresa_grupo(db, bodega, origen_id))


class DestinoIn(BaseModel):
    empresa_id: Annotated[int, Field(ge=1)]
    cantidad: Annotated[float, Field(ge=0, le=1_000_000)]


class LineaIn(BaseModel):
    dish_id: Annotated[int, Field(ge=1)]
    destinos: Annotated[List[DestinoIn], Field(min_length=1, max_length=50)]


class TrasladoIn(BaseModel):
    origen_id: Annotated[int, Field(ge=1)]
    lineas: Annotated[List[LineaIn], Field(min_length=1, max_length=tras_svc.MAX_LINEAS)]
    observacion: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]] = ""
    clave: Clave = None


@router.post("/traslados", status_code=201)
async def traslados_crear(body: TrasladoIn, db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(SEC_TRASLADOS)):
    async with _escritura(db):
        res = await tras_svc.crear_traslados(db, bodega, body.origen_id, [l.model_dump() for l in body.lineas],
                                             body.observacion or "", body.clave)
        await db.commit()
    return res


@router.get("/traslados")
async def traslados_listar(estado: Optional[str] = Query(None, pattern=r"^[A-Z_]{4,20}$"),
                           empresa: Optional[int] = Query(None, ge=1),
                           desde: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
                           hasta: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
                           db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(SEC_TRASLADOS)):
    if empresa:
        await _empresa_grupo(db, bodega, empresa)
    return await tras_svc.listar(db, bodega, estado, empresa, desde, hasta)


@router.get("/traslados/{tid}")
async def traslados_detalle(tid: int, db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(SEC_TRASLADOS)):
    return await tras_svc.detalle(db, bodega, tid)


class AnularIn(BaseModel):
    motivo: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=255)]


@router.post("/traslados/{tid}/anular")
async def traslados_anular(tid: int, body: AnularIn, db: AsyncSession = Depends(get_db),
                           bodega: Bodega = Depends(SEC_TRASLADOS)):
    async with _escritura(db):
        res = await tras_svc.anular(db, bodega, tid, body.motivo)
        await db.commit()
    return res


# ─── Tablero (dashboard de la bodega) ────────────────────────────────────────
from app.services import bodega_dashboard as tablero_svc


def _fecha_o_hoy(fecha: Optional[str]) -> str:
    from datetime import datetime, timedelta, timezone
    return fecha or datetime.now(timezone(timedelta(hours=-5))).date().isoformat()


@router.get("/tablero")
async def tablero(fecha: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
                  db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(requiere_bodega)):
    return await tablero_svc.resumen_grupo(db, bodega, _fecha_o_hoy(fecha))


@router.get("/tablero/sede/{sede_id}")
async def tablero_sede(sede_id: int, fecha: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
                       db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(requiere_bodega)):
    sede = await exigir_sede(db, bodega, sede_id)
    return await tablero_svc.resumen_sede(db, bodega, sede, _fecha_o_hoy(fecha))
