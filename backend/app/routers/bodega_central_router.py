"""
Bodega Central (F0) — vista /bodega-central. Solo empresas marcadas por SYSADMIN (has_bodega_central) y
usuarios ADMIN/SYSADMIN (bodega_guard.requiere_bodega). Las sedes salen siempre de bodega_guard.sedes_del_nit.

  GET  /api/bodega-central                  bodega, sedes del NIT, cargue unitario, catálogos (categorías, proveedores)
  GET  /api/bodega-central/productos        productos con stock y estado por sede
  POST /api/bodega-central/productos        crear producto (+ cantidad inicial)
  POST /api/bodega-central/entradas         entrada manual de inventario a la bodega
  POST /api/bodega-central/replicar/{id}    réplica por IMEI (cargue unitario): un producto por código, cantidad 1
  POST /api/bodega-central/importar         copiar el catálogo de una sede con cantidad 0
  GET  /api/bodega-central/movimientos      kardex/auditoría de la bodega

Las operaciones de escritura reciben `clave` (idempotencia): repetirla no duplica nada.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Annotated

from app.auth.bodega_guard import Bodega, exigir_sede, requiere_bodega, sedes_del_nit
from app.auth.tenant import tenant_guard
from app.database import get_db
from app.services import bodega_central as svc

router = APIRouter(prefix="/api/bodega-central", tags=["Bodega Central"], dependencies=[Depends(tenant_guard)])

Clave = Optional[Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[A-Za-z0-9\-]{8,64}$")]]
Money = Annotated[float, Field(ge=0, le=2_000_000_000)]
Cant = Annotated[int, Field(ge=1, le=1_000_000)]


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
async def productos(db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(requiere_bodega)):
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
async def crear(body: ProductoIn, db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(requiere_bodega)):
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
async def entrada(body: EntradaIn, db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(requiere_bodega)):
    if await svc.clave_usada(db, bodega, body.clave):
        return {"ok": True, "repetida": True}
    prod = await svc._producto(db, bodega.id, body.dish_id)          # 404 si no es de la bodega
    if str(prod["extra_print"] or "0") == "1" and await svc.cargue_unitario(db, bodega.id):
        raise HTTPException(status_code=409, detail="Un producto de cargue unitario (IMEI) no recibe más "
                                                    "cantidades: use Replicar para registrar más unidades")
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
                   bodega: Bodega = Depends(requiere_bodega)):
    res = await svc.replicar(db, bodega, dish_id, body.nombre_base or "", body.codigos, body.clave)
    await db.commit()
    return res


class ImportarIn(BaseModel):
    sede_id: Annotated[int, Field(ge=1)]
    clave: Clave = None
    company_id: Optional[int] = None


@router.post("/importar")
async def importar(body: ImportarIn, db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(requiere_bodega)):
    sede = await exigir_sede(db, bodega, body.sede_id)
    res = await svc.importar_catalogo(db, bodega, sede, body.clave)
    await db.commit()
    return res


@router.get("/movimientos")
async def movimientos(db: AsyncSession = Depends(get_db), bodega: Bodega = Depends(requiere_bodega)):
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
