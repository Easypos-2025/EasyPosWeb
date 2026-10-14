"""
Productos para comercio (vista /productos): almacén, droguería, ferretería, minimarket, estanco, fruver, lujos…

  Guarda en pos_dishes (la misma tabla de platos, la que vende el POS y usa el escritorio) con lo mínimo: sin
  impresoras, armado, variantes, menú del día ni receta. El producto se crea COMPLETO como Crear_Plato_Nuevo del
  escritorio (presentación UNIDAD con su proveedor, insumo con Id_Item = Id_Plato, existencia y relación 1:1),
  con el servicio de la Bodega Central (bodega_central.crear_producto).

  Empresa con escritorio: el producto nace con número provisional e inactivo y lo baja la sincronización del
  catálogo; la cantidad entra con la Factura de Proveedor (la baja el agente) o desde el escritorio.
  Empresa solo web: cantidad inicial y Replicar por IMEI (cargue unitario) al instante.

  GET  /api/productos                  productos con existencia, valor del inventario (lotes PEPS) y vencimiento
  GET  /api/productos/catalogos        categorías, proveedores, laboratorios, cargue unitario, escritorio, bodega
  POST /api/productos/laboratorios     crear laboratorio (droguerías)
  GET  /api/productos/{id}/lotes       lotes con existencia: compra, costo y vencimiento
  POST /api/productos                  crear
  PUT  /api/productos/{id}             editar (venta/mínimo/costo/IVA/stock mínimo bloqueados si una bodega administra)
  POST /api/productos/{id}/replicar    réplica por IMEI (cargue unitario, empresa solo web)
  POST /api/productos/{id}/estado      activar / desactivar
Permisos: pantalla /productos del rol (ver, crear, editar, borrar); ADMIN/SYSADMIN siempre.
"""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Annotated

from app.auth.bodega_guard import Bodega, bodega_de_sede, es_admin_rol, exigir_no_administrada
from app.auth.dependencies import get_current_user
from app.auth.tenant import tenant_guard
from app.database import get_db
from app.models.role_model import Role
from app.models.user_model import User
from app.services import bodega_central as bc
from app.services import lotes, sede_maestros, sede_pedidos

router = APIRouter(prefix="/api/productos", tags=["Productos"], dependencies=[Depends(tenant_guard)])

RUTA = "/productos"
PERFIL_DROGUERIA = 3
Money = Annotated[float, Field(ge=0, le=2_000_000_000)]


async def _permiso(db: AsyncSession, user: User, accion: str) -> None:
    rol = await db.get(Role, user.role_id) if user.role_id else None
    if es_admin_rol(rol):
        return
    ok = (await db.execute(text(f"""
        SELECT 1 FROM role_modules rm JOIN system_modules sm ON sm.id = rm.module_id AND sm.route = :r
        WHERE rm.role_id = :rol AND rm.can_{accion} = 1 LIMIT 1
    """), {"r": RUTA, "rol": user.role_id or 0})).scalar()
    if not ok:
        raise HTTPException(status_code=403, detail="Su rol no tiene permiso para esta acción en Productos")


async def _empresa(db: AsyncSession, user: User, request: Request) -> Bodega:
    """La empresa de la sesión (topbar validada) como 'Bodega' para reutilizar el servicio de productos."""
    cid = int(user.company_id or 0)
    nit = (await db.execute(text("SELECT identification_number FROM companies WHERE id_company = :c"), {"c": cid})).scalar()
    ip = (request.headers.get("X-Forwarded-For") or (request.client.host if request.client else "") or "")
    return Bodega(id=cid, nit=str(nit or "").strip(), user=user, ip=ip.split(",")[0].strip()[:45])


async def es_drogueria(db: AsyncSession, cid: int) -> bool:
    return int((await db.execute(text("SELECT business_profile_id FROM companies WHERE id_company = :c"),
                                 {"c": cid})).scalar() or 0) == PERFIL_DROGUERIA


@router.get("")
async def listar(request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await _permiso(db, user, "view")
    cid = int(user.company_id)
    filas = await bc.listar_productos(db, await _empresa(db, user, request))
    valor = await lotes.resumen_por_item(db, cid)
    labs = {int(p): n for p, n in (await db.execute(text("""
        SELECT li.posicion_insumo, l.nombre_laboratorio FROM laboratorio_insumo li
        JOIN laboratorios l ON l.company_id = li.company_id AND l.id_laboratorio = li.id_laboratorio
        WHERE li.company_id = :c
    """), {"c": cid})).all()}
    lab_ids = {int(p): int(i) for p, i in (await db.execute(text(
        "SELECT posicion_insumo, id_laboratorio FROM laboratorio_insumo WHERE company_id = :c"), {"c": cid})).all()}
    for f in filas:
        f["provisional"] = int(f["id"]) >= sede_maestros.ID_PROVISIONAL
        f.pop("sedes", None)
        v = valor.get(int(f["id"]))
        # sin lotes: el stock se valora al costo del producto
        f["valor_inventario"] = v["valor"] if v else max(f["stock"], 0) * f["product_cost"]
        f["lotes"] = v["lotes"] if v else 0
        f["vence"] = v["vence"] if v else None
        f["laboratorio"] = labs.get(int(f["id"]))
        f["id_laboratorio"] = lab_ids.get(int(f["id"]))
    return filas


@router.get("/catalogos")
async def catalogos(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await _permiso(db, user, "view")
    cid = int(user.company_id)
    categorias = (await db.execute(text(
        "SELECT id, name FROM pos_dish_categories WHERE company_id = :c AND is_active = 1 ORDER BY name"), {"c": cid})).mappings().all()
    proveedores = (await db.execute(text(
        "SELECT id_proveedor AS id, name FROM suppliers WHERE company_id = :c AND is_active = 1 "
        "AND id_proveedor IS NOT NULL ORDER BY name"), {"c": cid})).mappings().all()
    drogueria = await es_drogueria(db, cid)
    laboratorios = (await db.execute(text(
        "SELECT id_laboratorio AS id, nombre_laboratorio AS name FROM laboratorios WHERE company_id = :c AND activo = 1 "
        "ORDER BY nombre_laboratorio"), {"c": cid})).mappings().all() if drogueria else []
    return {"categorias": [dict(c) for c in categorias], "proveedores": [dict(p) for p in proveedores],
            "drogueria": drogueria, "laboratorios": [dict(x) for x in laboratorios],
            "cargue_unitario": await bc.cargue_unitario(db, cid),
            "con_escritorio": await sede_pedidos.tiene_sede(db, cid),
            "administrado_por": await bodega_de_sede(db, cid)}


class ProductoIn(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=250)]
    product_code: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=60)]] = ""
    category_id: Annotated[int, Field(ge=1)]
    id_proveedor: Optional[Annotated[int, Field(ge=0)]] = 0
    price: Annotated[int, Field(ge=0, le=2_000_000_000)] = 0
    wholesale_price: Money = 0             # precio mínimo (Precio_x_Mayor del escritorio)
    product_cost: Money = 0
    tax: Annotated[float, Field(ge=0, le=100)] = 0
    minimum_stock: Annotated[float, Field(ge=0, le=1_000_000)] = 0
    extra_print: bool = False              # desactivar al vender
    ask_product_description: bool = False
    cantidad_inicial: Annotated[int, Field(ge=0, le=1_000_000)] = 0
    fecha_vence: Optional[date] = None     # droguerías (vencimiento del lote inicial)
    id_laboratorio: Optional[Annotated[int, Field(ge=1)]] = None
    company_id: Optional[int] = None       # lo valida tenant_guard; no se usa


@router.post("", status_code=201)
async def crear(body: ProductoIn, request: Request, db: AsyncSession = Depends(get_db),
                user: User = Depends(get_current_user)):
    await _permiso(db, user, "create")
    emp = await _empresa(db, user, request)
    if body.wholesale_price and body.price and body.wholesale_price > body.price:
        raise HTTPException(status_code=422, detail="El precio mínimo no puede ser mayor que el precio de venta")
    con_escritorio = await sede_pedidos.tiene_sede(db, emp.id)
    unitario = await bc.cargue_unitario(db, emp.id)
    drogueria = await es_drogueria(db, emp.id)
    datos = body.model_dump(exclude={"company_id", "cantidad_inicial"})
    if not drogueria:
        datos["fecha_vence"], datos["id_laboratorio"] = None, None
    cantidad = body.cantidad_inicial
    if unitario:
        datos["extra_print"] = True
        cantidad = 1
    if con_escritorio and cantidad:
        cantidad = 0       # la cantidad entra con la Factura de Proveedor (la baja el agente) o desde el escritorio
    dish_id = await bc.crear_producto(db, emp.id, datos, con_escritorio=con_escritorio)
    if cantidad:
        prov = (await bc._producto(db, emp.id, dish_id))["id_proveedor"] or 0
        await bc.registrar_entrada(db, emp, dish_id, cantidad, prov, "Entrada al registrar producto",
                                   lote={"costo": float(body.product_cost or 0), "fecha_vence": datos.get("fecha_vence"),
                                         "id_proveedor": prov or None})
    await db.commit()
    return {"ok": True, "id": dish_id, "pendiente_escritorio": con_escritorio,
            "aviso": ("La cantidad se carga con la Factura de Proveedor o desde el escritorio."
                      if con_escritorio and (body.cantidad_inicial or unitario) else None)}


class ProductoUpdate(BaseModel):
    name: Optional[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=250)]] = None
    product_code: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=60)]] = None
    category_id: Optional[Annotated[int, Field(ge=1)]] = None
    id_proveedor: Optional[Annotated[int, Field(ge=0)]] = None
    price: Optional[Annotated[int, Field(ge=0, le=2_000_000_000)]] = None
    wholesale_price: Optional[Money] = None
    product_cost: Optional[Money] = None
    tax: Optional[Annotated[float, Field(ge=0, le=100)]] = None
    minimum_stock: Optional[Annotated[float, Field(ge=0, le=1_000_000)]] = None
    extra_print: Optional[bool] = None
    ask_product_description: Optional[bool] = None
    id_laboratorio: Optional[Annotated[int, Field(ge=0)]] = None     # 0 = sin laboratorio
    company_id: Optional[int] = None


@router.put("/{dish_id}")
async def editar(dish_id: int, body: ProductoUpdate, db: AsyncSession = Depends(get_db),
                 user: User = Depends(get_current_user)):
    await _permiso(db, user, "edit")
    cid = int(user.company_id)
    actual = (await db.execute(text(
        f"SELECT name, product_code, category_id, {', '.join(bc.CAMPOS_VALORES)} FROM pos_dishes "
        "WHERE company_id = :c AND id = :d"), {"c": cid, "d": dish_id})).mappings().first()
    if not actual:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    datos = body.model_dump(exclude_unset=True, exclude={"company_id"})

    # Venta, mínimo, costo, IVA y stock mínimo: los define la central si una bodega administra la empresa
    cambios = [{"campo": k, "nuevo": float(datos[k])} for k in bc.CAMPOS_VALORES
               if datos.get(k) is not None and round(float(datos[k]), 2) != round(float(actual[k] or 0), 2)]
    if cambios:
        await exigir_no_administrada(db, cid, "El precio de venta, el mínimo, el costo, el IVA y el stock mínimo")
        minimo = next((c["nuevo"] for c in cambios if c["campo"] == "wholesale_price"), float(actual["wholesale_price"] or 0))
        venta = next((c["nuevo"] for c in cambios if c["campo"] == "price"), float(actual["price"] or 0))
        if minimo and venta and minimo > venta:
            raise HTTPException(status_code=422, detail="El precio mínimo no puede ser mayor que el precio de venta")
        await bc._aplicar_valores(db, cid, dish_id, cambios)

    sets, params = [], {"c": cid, "d": dish_id}
    if datos.get("name") and datos["name"] != actual["name"]:
        if (await db.execute(text("SELECT 1 FROM pos_dishes WHERE company_id = :c AND name = :n AND id <> :d"),
                             {"c": cid, "n": datos["name"], "d": dish_id})).scalar():
            raise HTTPException(status_code=409, detail="Este nombre de producto ya se encuentra registrado")
        sets.append("name = :name"); params["name"] = datos["name"]
    if "product_code" in datos and datos["product_code"] is not None:
        codigo = bc.limpiar_codigo(datos["product_code"]) or f"WEB-{dish_id}"
        if codigo != (actual["product_code"] or ""):
            if await bc.codigos_usados(db, [cid], [codigo]):
                raise HTTPException(status_code=409, detail=f"El código {codigo} ya existe en otro producto")
            sets.append("product_code = :cod"); params["cod"] = codigo
    if datos.get("category_id") and int(datos["category_id"]) != int(actual["category_id"] or 0):
        params["cat"] = await bc.categoria_valida(db, cid, datos["category_id"])
        sets.append("category_id = :cat")
    if datos.get("extra_print") is not None:
        sets.append("extra_print = :ep"); params["ep"] = "1" if datos["extra_print"] else "0"
    if datos.get("ask_product_description") is not None:
        sets.append("ask_product_description = :apd"); params["apd"] = 1 if datos["ask_product_description"] else 0
    if sets:
        await db.execute(text(f"UPDATE pos_dishes SET {', '.join(sets)}, synced = 0, updated_at = NOW() "
                              "WHERE company_id = :c AND id = :d"), params)
        # el insumo del producto (almacén: 1 a 1) lleva el mismo nombre y código
        item = await _insumo_unico(db, cid, dish_id)
        if item and ("name" in params or "cod" in params or "cat" in params):
            nombre = params.get("name", actual["name"])
            codigo = params.get("cod", actual["product_code"])
            await db.execute(text("""
                UPDATE supply_items SET description = :n, code = :k, agrupar = COALESCE(:cat, agrupar), synced = 0
                WHERE company_id = :c AND id_item = :i
            """), {"n": bc.nombre_porcion(nombre), "k": codigo, "cat": params.get("cat"), "c": cid, "i": item})
            await db.execute(text("""
                UPDATE inventario_actual_porciones SET descripcion = :n, codigo_insumo = :k, enviada_mysql = 0
                WHERE company_id = :c AND id_item = :i
            """), {"n": bc.nombre_porcion(nombre), "k": codigo, "c": cid, "i": item})
    if datos.get("id_proveedor") is not None:
        prov = await bc.proveedor_valido(db, cid, datos["id_proveedor"], obligatorio=await bc.cargue_unitario(db, cid))
        await db.execute(text(
            "UPDATE pos_dish_products SET supplier_id = :p, synced = 0 WHERE company_id = :c AND dish_id = :d"),
            {"p": prov, "c": cid, "d": dish_id})
    if datos.get("id_laboratorio") is not None and await es_drogueria(db, cid):
        item = await _insumo_unico(db, cid, dish_id)
        if item:
            lab = await bc.laboratorio_valido(db, cid, datos["id_laboratorio"]) if datos["id_laboratorio"] else None
            await bc.asignar_laboratorio(db, cid, item, lab)
    await db.commit()
    return {"ok": True}


class LaboratorioIn(BaseModel):
    nombre: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=50)]
    company_id: Optional[int] = None


@router.post("/laboratorios", status_code=201)
async def crear_laboratorio(body: LaboratorioIn, db: AsyncSession = Depends(get_db),
                            user: User = Depends(get_current_user)):
    await _permiso(db, user, "create")
    cid = int(user.company_id)
    if not await es_drogueria(db, cid):
        raise HTTPException(status_code=409, detail="Los laboratorios son de las droguerías")
    nombre = body.nombre.upper()
    ya = (await db.execute(text(
        "SELECT id_laboratorio FROM laboratorios WHERE company_id = :c AND UPPER(TRIM(nombre_laboratorio)) = :n"),
        {"c": cid, "n": nombre})).scalar()
    if ya:
        await db.execute(text("UPDATE laboratorios SET activo = 1 WHERE company_id = :c AND id_laboratorio = :l"),
                         {"c": cid, "l": ya})
        await db.commit()
        return {"id": int(ya), "name": nombre}
    nuevo = await sede_maestros.siguiente_id(db, "laboratorios", "id_laboratorio", cid,
                                             await sede_pedidos.tiene_sede(db, cid))
    await db.execute(text("""
        INSERT INTO laboratorios (company_id, id_laboratorio, nombre_laboratorio, porcentaje, activo, synced)
        VALUES (:c, :l, :n, 0, 1, 0)
    """), {"c": cid, "l": nuevo, "n": nombre})
    await db.commit()
    return {"id": nuevo, "name": nombre}


@router.get("/{dish_id}/lotes")
async def lotes_producto(dish_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await _permiso(db, user, "view")
    cid = int(user.company_id)
    if not (await db.execute(text("SELECT 1 FROM pos_dishes WHERE company_id = :c AND id = :d"),
                             {"c": cid, "d": dish_id})).scalar():
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    item = await _insumo_unico(db, cid, dish_id) or dish_id
    return {"lotes": await lotes.lotes_de(db, cid, item), "drogueria": await es_drogueria(db, cid)}


async def _insumo_unico(db: AsyncSession, cid: int, dish_id: int):
    items = (await db.execute(text(
        "SELECT id_item FROM inventario_porciones_plato WHERE company_id = :c AND id_plato = :d"),
        {"c": cid, "d": dish_id})).scalars().all()
    return int(items[0]) if len(items) == 1 else None


class ReplicarIn(BaseModel):
    nombre_base: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]] = ""
    codigos: Annotated[List[Annotated[str, StringConstraints(strip_whitespace=True, max_length=60)]],
                       Field(min_length=1, max_length=bc.MAX_REPLICAS)]
    company_id: Optional[int] = None


@router.post("/{dish_id}/replicar", status_code=201)
async def replicar(dish_id: int, body: ReplicarIn, request: Request, db: AsyncSession = Depends(get_db),
                   user: User = Depends(get_current_user)):
    await _permiso(db, user, "create")
    emp = await _empresa(db, user, request)
    if await sede_pedidos.tiene_sede(db, emp.id):
        raise HTTPException(status_code=409, detail="Esta empresa trabaja con escritorio: los IMEI con su unidad se "
                                                    "registran con la Factura de Proveedor o desde el escritorio.")
    res = await bc.replicar(db, emp, dish_id, body.nombre_base or "", body.codigos, None, es_bodega=False)
    await db.commit()
    return res


class EstadoIn(BaseModel):
    activo: bool
    company_id: Optional[int] = None


@router.post("/{dish_id}/estado")
async def estado(dish_id: int, body: EstadoIn, db: AsyncSession = Depends(get_db),
                 user: User = Depends(get_current_user)):
    await _permiso(db, user, "delete" if not body.activo else "edit")
    cid = int(user.company_id)
    res = await db.execute(text(
        "UPDATE pos_dishes SET active = :a, synced = 0, updated_at = NOW() WHERE company_id = :c AND id = :d "
        "AND id < :prov"), {"a": 0 if body.activo else 1, "c": cid, "d": dish_id, "prov": bc.sede_maestros.ID_PROVISIONAL})
    if not res.rowcount:
        raise HTTPException(status_code=404, detail="Producto no encontrado (o aún no sincronizado con el escritorio)")
    await db.commit()
    return {"ok": True}
