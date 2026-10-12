"""
Bodega Central (F0): catálogo y stock de la bodega, réplica por IMEI e importación del catálogo de una sede.

La bodega existe solo en la web: su catálogo es el de su empresa (pos_dishes) y su stock el de su
inventario_actual_porciones. Un producto se crea igual que en Crear_Plato_Nuevo del escritorio:
  platos            → pos_dishes                (precio = lista Default, active 0 = visible, convención VB6)
  plato_producto    → pos_dish_products         (presentación UNIDAD con su proveedor; nunca sin proveedor)
  inventario_porciones / inventario_actual_porciones → supply_items / inventario_actual_porciones
                      (Id_Grupo = 1, Id_Item = Id_Plato)
  inventario_porciones_plato                    (el plato descuenta 1 de su insumo)
Las cantidades entran por inventory_entries (kardex), así el recálculo de stock las respeta.

Cargue unitario (configuracion_sede.cargar_1_inventario_automatico, cliente especial): cada unidad es un
producto propio (Codigo_Producto = IMEI), exige proveedor, entra con cantidad 1 y se desactiva al venderse.
"""
import re
from datetime import date
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.bodega_guard import Bodega, sedes_del_nit
from app.services import listas_precios, sede_maestros
from app.services.stock import apply_stock_move

ID_GRUPO = 1
MAX_REPLICAS = 200
MAX_IMPORTAR = 5000
PROVEEDOR_DEFAULT = "VARIOS"
MEDIDA_DEFAULT = "UNIDAD"
RE_CODIGO = re.compile(r"^[A-Za-z0-9/\-._ ]{1,60}$")


def limpiar_codigo(valor: Optional[str]) -> str:
    """Como el escritorio (comilla y coma → guion) y solo caracteres seguros."""
    codigo = (valor or "").strip().replace("'", "-").replace(",", "-")
    if codigo and not RE_CODIGO.match(codigo):
        raise HTTPException(status_code=422, detail=f"Código inválido: {codigo[:60]}. Use letras, números, / - . _")
    return codigo


# ─── Catálogos base de la bodega ──────────────────────────────────────────────

async def cargue_unitario(db: AsyncSession, cid: int) -> bool:
    return bool((await db.execute(text(
        "SELECT COALESCE(cargar_1_inventario_automatico, 0) FROM configuracion_sede WHERE company_id = :c"
    ), {"c": cid})).scalar())


async def asegurar_unidad(db: AsyncSession, cid: int) -> int:
    fila = (await db.execute(text(
        "SELECT id FROM pos_measure_forms WHERE company_id = :c AND UPPER(name) = :n ORDER BY id LIMIT 1"
    ), {"c": cid, "n": MEDIDA_DEFAULT})).scalar()
    if fila:
        return int(fila)
    nuevo = await sede_maestros.siguiente_id(db, "pos_measure_forms", "id", cid, False)
    await db.execute(text(
        "INSERT INTO pos_measure_forms (id, company_id, name, is_active, synced) VALUES (:id, :c, :n, 1, 0)"
    ), {"id": nuevo, "c": cid, "n": MEDIDA_DEFAULT})
    return nuevo


async def asegurar_varios(db: AsyncSession, cid: int) -> int:
    """Proveedor VARIOS (default de todo producto sin proveedor). Devuelve su id_proveedor."""
    fila = (await db.execute(text(
        "SELECT id_proveedor FROM suppliers WHERE company_id = :c AND UPPER(TRIM(name)) = :n "
        "AND id_proveedor IS NOT NULL ORDER BY is_active DESC, id_proveedor LIMIT 1"
    ), {"c": cid, "n": PROVEEDOR_DEFAULT})).scalar()
    if fila:
        await db.execute(text(
            "UPDATE suppliers SET is_active = 1 WHERE company_id = :c AND id_proveedor = :p AND is_active = 0"
        ), {"c": cid, "p": fila})
        return int(fila)
    nuevo = await sede_maestros.siguiente_id(db, "suppliers", "id_proveedor", cid, False)
    await db.execute(text("""
        INSERT INTO suppliers (company_id, id_proveedor, name, is_active, synced, created_at)
        VALUES (:c, :p, :n, 1, 0, NOW())
    """), {"c": cid, "p": nuevo, "n": PROVEEDOR_DEFAULT})
    return nuevo


async def proveedor_valido(db: AsyncSession, cid: int, id_proveedor: Optional[int], obligatorio: bool) -> int:
    if not id_proveedor:
        if obligatorio:
            raise HTTPException(status_code=422, detail="Debe seleccionar el proveedor del producto")
        return await asegurar_varios(db, cid)
    ok = (await db.execute(text(
        "SELECT 1 FROM suppliers WHERE company_id = :c AND id_proveedor = :p AND is_active = 1"
    ), {"c": cid, "p": int(id_proveedor)})).scalar()
    if not ok:
        raise HTTPException(status_code=400, detail="Proveedor no válido para esta empresa")
    return int(id_proveedor)


async def categoria_valida(db: AsyncSession, cid: int, category_id: Optional[int]) -> int:
    if not category_id:
        raise HTTPException(status_code=422, detail="Debe escoger una categoría para el producto")
    ok = (await db.execute(text(
        "SELECT 1 FROM pos_dish_categories WHERE id = :id AND company_id = :c"
    ), {"id": int(category_id), "c": cid})).scalar()
    if not ok:
        raise HTTPException(status_code=400, detail="Categoría no válida para esta empresa")
    return int(category_id)


async def codigos_usados(db: AsyncSession, empresas: list[int], codigos: list[str]) -> dict:
    """{código: nombre de la empresa donde ya existe} entre las empresas dadas."""
    codigos = [c for c in {c.strip() for c in codigos} if c]
    if not codigos or not empresas:
        return {}
    pe = ", ".join(f":e{i}" for i in range(len(empresas)))
    pc = ", ".join(f":k{i}" for i in range(len(codigos)))
    filas = (await db.execute(text(f"""
        SELECT d.product_code, c.name FROM pos_dishes d JOIN companies c ON c.id_company = d.company_id
        WHERE d.company_id IN ({pe}) AND d.product_code IN ({pc})
    """), {**{f"e{i}": v for i, v in enumerate(empresas)}, **{f"k{i}": v for i, v in enumerate(codigos)}})).all()
    return {f[0]: f[1] for f in filas}


# ─── Producto ────────────────────────────────────────────────────────────────

async def _nuevo_id(db: AsyncSession, cid: int) -> int:
    """Id del plato = Id_Item de su insumo (como el escritorio): el mayor de los dos consecutivos."""
    from app.services.supply_keys import next_id_item
    return max(await sede_maestros.siguiente_id_plato(db, cid, False), await next_id_item(db, cid))


async def crear_producto(db: AsyncSession, cid: int, d: dict, nuevo_id: Optional[int] = None,
                         unidad: Optional[int] = None, validado: bool = False) -> int:
    """d: name, product_code, price, wholesale_price (precio mínimo), product_cost, tax, minimum_stock,
    category_id, id_proveedor, extra_print (desactivar al vender), ask_product_description.
    Valida categoría, proveedor, código y nombre; no hace commit.
    La importación ya validó todo y numera en bloque: pasa nuevo_id, unidad y validado=True."""
    codigo = limpiar_codigo(d.get("product_code"))
    nombre = (d.get("name") or "").strip()[:250]
    if validado:
        categoria, proveedor = int(d["category_id"]), int(d["id_proveedor"])
    else:
        unitario = await cargue_unitario(db, cid)
        categoria = await categoria_valida(db, cid, d.get("category_id"))
        proveedor = await proveedor_valido(db, cid, d.get("id_proveedor"), obligatorio=unitario)
        if not nombre:
            raise HTTPException(status_code=422, detail="El nombre del producto es obligatorio")
        if codigo and await codigos_usados(db, [cid], [codigo]):
            raise HTTPException(status_code=409, detail=f"El código {codigo} ya existe en otro producto de la bodega")
        if (await db.execute(text(
            "SELECT 1 FROM pos_dishes WHERE company_id = :c AND name = :n LIMIT 1"), {"c": cid, "n": nombre})).scalar():
            raise HTTPException(status_code=409, detail="Este nombre de producto ya se encuentra registrado")

    precio = int(d.get("price") or 0)
    costo = float(d.get("product_cost") or 0)
    stock_min = float(d.get("minimum_stock") or 0)
    nuevo = nuevo_id or await _nuevo_id(db, cid)
    codigo = codigo or f"BC-{nuevo}"
    unidad = unidad or await asegurar_unidad(db, cid)

    await db.execute(text("""
        INSERT INTO pos_dishes
            (id, company_id, name, product_code, price, preparation_time, active, category_id, `procedure`,
             description, printer, extra_print, pre_preparation, offer, offer_priority, tax, wholesale_price,
             product_cost, minimum_stock, ask_sale_price, ask_product_description, synced, updated_at)
        VALUES (:id, :c, :n, :cod, :p, 0, 0, :cat, '', '', 'Caja', :ep, 0, 0, 0, :tax, :minimo,
                :costo, :smin, 0, :apd, 0, NOW())
    """), {"id": nuevo, "c": cid, "n": nombre, "cod": codigo, "p": precio, "cat": categoria,
           "ep": "1" if d.get("extra_print") else "0", "tax": float(d.get("tax") or 0),
           "minimo": float(d.get("wholesale_price") or 0), "costo": costo, "smin": stock_min,
           "apd": 1 if d.get("ask_product_description") else 0})
    await listas_precios.plato_a_default(db, cid, nuevo, 0, precio)
    await db.execute(text("""
        INSERT INTO pos_dish_products (company_id, dish_id, supplier_id, measure_id, minimum_units,
                                       presentation_value, description, active, synced)
        VALUES (:c, :id, :sup, :mid, 1, :pv, :desc, 0, 0)
    """), {"c": cid, "id": nuevo, "sup": proveedor, "mid": unidad, "pv": precio, "desc": MEDIDA_DEFAULT})
    await db.execute(text("""
        INSERT INTO supply_items
            (company_id, code, description, unit_id, cost_price, stock_qty, min_stock, waste_pct, control_stock,
             is_active, id_grupo, id_item, posicion, agrupar, unit_uso_id, und_min_utilizadas, synced)
        VALUES (:c, :cod, :n, :u, :costo, 0, :smin, 0, 1, 1, :g, :id, :id, :cat, :u, 1, 0)
    """), {"c": cid, "cod": codigo, "n": nombre, "u": unidad, "costo": costo, "smin": stock_min,
           "g": ID_GRUPO, "id": nuevo, "cat": categoria})
    await db.execute(text("""
        INSERT INTO inventario_actual_porciones
            (company_id, id_grupo, id_item, codigo_insumo, descripcion, costo, und_compra, und_min_utilizadas,
             agrupar, controlar, und_uso, cantidad_actual, stock_minimo, enviada_mysql)
        VALUES (:c, :g, :id, :cod, :n, :costo, :u, 1, :cat, 1, :u, 0, :smin, 0)
        ON DUPLICATE KEY UPDATE codigo_insumo = VALUES(codigo_insumo), descripcion = VALUES(descripcion)
    """), {"c": cid, "g": ID_GRUPO, "id": nuevo, "cod": codigo, "n": nombre, "costo": costo, "u": unidad,
           "cat": categoria, "smin": stock_min})
    await db.execute(text("""
        INSERT IGNORE INTO inventario_porciones_plato
            (company_id, id_plato, id_grupo, id_item, cantidad, unidad_minima, porciones_a_desccontar, posicion,
             opcion_cambiar, enviada_mysql)
        VALUES (:c, :id, :g, :id, 1, 1, 1, :id, 0, 0)
    """), {"c": cid, "id": nuevo, "g": ID_GRUPO})
    return nuevo


async def _producto(db: AsyncSession, cid: int, dish_id: int) -> dict:
    fila = (await db.execute(text("""
        SELECT d.id, d.name, d.product_code, d.price, d.category_id, d.tax, d.wholesale_price, d.product_cost,
               d.minimum_stock, d.extra_print, d.ask_product_description,
               (SELECT dp.supplier_id FROM pos_dish_products dp
                WHERE dp.company_id = d.company_id AND dp.dish_id = d.id ORDER BY dp.supplier_id DESC LIMIT 1) AS id_proveedor
        FROM pos_dishes d WHERE d.company_id = :c AND d.id = :id
    """), {"c": cid, "id": int(dish_id)})).mappings().first()
    if not fila:
        raise HTTPException(status_code=404, detail="Producto no encontrado en la bodega")
    return dict(fila)


# ─── Movimientos (kardex de la bodega) ───────────────────────────────────────

async def clave_usada(db: AsyncSession, bodega: Bodega, clave: Optional[str]) -> bool:
    if not clave:
        return False
    return bool((await db.execute(text(
        "SELECT 1 FROM bc_movimientos WHERE bodega_id = :b AND clave = :k LIMIT 1"
    ), {"b": bodega.id, "k": clave})).scalar())


async def movimiento(db: AsyncSession, bodega: Bodega, tipo: str, dish_id: Optional[int], cantidad: float = 0,
                     detalle: str = "", referencia: Optional[str] = None, sede_id: Optional[int] = None,
                     clave: Optional[str] = None) -> None:
    await db.execute(text("""
        INSERT INTO bc_movimientos (bodega_id, tipo, dish_id, cantidad, sede_id, referencia, detalle, clave,
                                    usuario_id, usuario, ip)
        VALUES (:b, :t, :d, :q, :s, :r, :det, :k, :uid, :u, :ip)
    """), {"b": bodega.id, "t": tipo, "d": dish_id, "q": cantidad, "s": sede_id, "r": referencia,
           "det": (detalle or "")[:255], "k": clave, "uid": bodega.user.id, "u": bodega.usuario, "ip": bodega.ip})


async def registrar_entrada(db: AsyncSession, bodega: Bodega, dish_id: int, cantidad: float,
                            id_proveedor: int, observacion: str) -> int:
    """Entrada al inventario de la bodega (inventory_entries + stock). Devuelve el id de la entrada."""
    hoy = date.today().isoformat()
    res = await db.execute(text("""
        INSERT INTO inventory_entries
            (id_entrada, id_item, id_proveedor, company_id, fecha, cantidad, cod_empleado, observacion,
             autorizada, synced, updated_at)
        VALUES ((SELECT COALESCE(MAX(id_entrada), 0) + 1 FROM inventory_entries ie2 WHERE ie2.company_id = :c),
                :item, :prov, :c, :f, :q, :emp, :obs, 1, 0, NOW())
    """), {"c": bodega.id, "item": dish_id, "prov": int(id_proveedor or 0), "f": hoy, "q": cantidad,
           "emp": (bodega.user.email or "")[:50], "obs": (observacion or "")[:255]})
    eid = res.lastrowid
    await db.flush()
    await apply_stock_move(db, bodega.id, dish_id, cantidad, "entry", "bodega_central", eid, hoy,
                           f"Bodega central — {observacion or 'entrada'}", bodega.user.id)
    return eid


# ─── Réplica por IMEI (Modificar_Plato_Nuevo → "Replicar Producto") ──────────

async def replicar(db: AsyncSession, bodega: Bodega, dish_id: int, nombre_base: str, codigos: list[str],
                   clave: Optional[str]) -> dict:
    if not await cargue_unitario(db, bodega.id):
        raise HTTPException(status_code=409, detail="Replicar solo está disponible con el cargue unitario activo "
                                                    "(Configuración Sede)")
    if await clave_usada(db, bodega, clave):
        return {"ok": True, "repetida": True, "creados": []}
    if not codigos:
        raise HTTPException(status_code=422, detail="Digite al menos un código")
    if len(codigos) > MAX_REPLICAS:
        raise HTTPException(status_code=422, detail=f"Máximo {MAX_REPLICAS} réplicas por vez")
    limpios = [limpiar_codigo(c) for c in codigos]
    if any(not c for c in limpios):
        raise HTTPException(status_code=422, detail="Hay códigos vacíos")
    repetidos = sorted({c for c in limpios if limpios.count(c) > 1})
    if repetidos:
        raise HTTPException(status_code=422, detail=f"Códigos repetidos en la lista: {', '.join(repetidos[:10])}")
    empresas = [bodega.id] + [s["id"] for s in await sedes_del_nit(db, bodega)]
    usados = await codigos_usados(db, empresas, limpios)
    if usados:
        detalle = "; ".join(f"{k} ({v})" for k, v in list(usados.items())[:10])
        raise HTTPException(status_code=409, detail=f"Estos códigos ya existen: {detalle}")

    base = await _producto(db, bodega.id, dish_id)
    nombre_base = ((nombre_base or "").strip() or base["name"])[:200]
    creados = []
    siguiente = await _nuevo_id(db, bodega.id)                  # una sola vez; luego se numera en bloque
    for codigo in limpios:
        nuevo = await crear_producto(db, bodega.id, {
            **base, "name": f"{nombre_base} {codigo}"[:250], "product_code": codigo, "extra_print": 1,
        }, nuevo_id=siguiente)
        siguiente += 1
        await registrar_entrada(db, bodega, nuevo, 1, base["id_proveedor"] or 0,
                                f"Réplica de {base['product_code'] or base['id']}")
        await movimiento(db, bodega, "REPLICA", nuevo, 1, f"Réplica de {base['name']}"[:255],
                         referencia=str(dish_id), clave=clave)
        creados.append({"id": nuevo, "codigo": codigo})
    return {"ok": True, "repetida": False, "creados": creados}


# ─── Importar datos de una sede (productos con cantidad 0) ───────────────────
# El admin escoge qué datos traer. Lo que ya existe en la bodega no se duplica: categorías y unidades se buscan
# por nombre, proveedores por NIT + nombre, productos por código y clientes por cédula (sin cédula, por nombre).
# Productos arrastra las categorías y el proveedor que usa, aunque no estén marcados.

DATOS_IMPORTAR = {
    "categorias": "Categorías de productos",
    "categorias_insumos": "Categorías de insumos",
    "medidas": "Unidades de medida",
    "proveedores": "Proveedores",
    "productos": "Productos",
    "clientes": "Clientes",
}
_COLS_CLIENTE = ("cedula", "nombres", "apellidos", "direccion", "telefono", "barrio", "mail", "dia_cumple",
                 "mes_cumple", "edad", "ocupacion", "porc_descuento", "observaciones", "fecha_aniversario",
                 "fecha_grado", "empresa", "tarjeta_fiel", "cod_barrio", "referencia")


def _cuenta() -> dict:
    return {"creados": 0, "existentes": 0, "omitidos": 0}


async def resumen_sede(db: AsyncSession, sede_id: int) -> list[dict]:
    """Cuántos registros tiene la sede de cada dato importable."""
    p = {"s": sede_id, "prov": sede_maestros.ID_PROVISIONAL}

    async def n(sql: str) -> int:
        return int((await db.execute(text(sql), p)).scalar() or 0)

    prod = (await db.execute(text("""
        SELECT COUNT(*), COALESCE(SUM(COALESCE(TRIM(product_code), '') <> ''), 0)
        FROM pos_dishes WHERE company_id = :s AND COALESCE(active, 0) = 0 AND id < :prov
    """), p)).first()
    conteos = {
        "categorias": await n("SELECT COUNT(*) FROM pos_dish_categories WHERE company_id = :s"),
        "categorias_insumos": await n("SELECT COUNT(*) FROM pos_product_categories WHERE company_id = :s"),
        "medidas": await n("SELECT COUNT(*) FROM pos_measure_forms WHERE company_id = :s"),
        "proveedores": await n("SELECT COUNT(*) FROM suppliers WHERE company_id = :s AND id_proveedor IS NOT NULL"),
        "productos": int(prod[1] or 0),
        "clientes": await n("SELECT COUNT(*) FROM clientes WHERE company_id = :s"),
    }
    out = []
    for k, v in DATOS_IMPORTAR.items():
        fila = {"clave": k, "nombre": v, "registros": conteos[k]}
        if k == "productos":
            fila["sin_codigo"] = int(prod[0] or 0) - int(prod[1] or 0)
        out.append(fila)
    return out


async def _por_nombre(db: AsyncSession, tabla: str, bodega_id: int, sede_id: int, columnas: tuple,
                      solo_ids: Optional[set], cuenta: dict) -> dict:
    """Catálogo con llave (id, company_id) que se empata por nombre: {id en la sede: id en la bodega}.
    solo_ids = traer solo esos (los que usan los productos); None = todos."""
    propias = {(f[1] or "").strip().upper(): int(f[0]) for f in (await db.execute(text(
        f"SELECT id, name FROM {tabla} WHERE company_id = :c"), {"c": bodega_id})).all()}
    extra = "".join(f", {c}" for c in columnas)
    filas = (await db.execute(text(
        f"SELECT id, name{extra} FROM {tabla} WHERE company_id = :s ORDER BY id"), {"s": sede_id})).mappings().all()
    siguiente = None
    mapa = {}
    for f in filas:
        if solo_ids is not None and int(f["id"]) not in solo_ids:
            continue
        nombre = (f["name"] or "").strip()[:100]
        if not nombre:
            cuenta["omitidos"] += 1
            continue
        llave = nombre.upper()
        if llave in propias:
            cuenta["existentes"] += 1
        else:
            if siguiente is None:
                siguiente = await sede_maestros.siguiente_id(db, tabla, "id", bodega_id, False)
            cols = ", ".join(("id", "company_id", "name", "synced") + columnas)
            vals = ", ".join((":id", ":c", ":n", "0") + tuple(f":{c}" for c in columnas))
            await db.execute(text(f"INSERT INTO {tabla} ({cols}) VALUES ({vals})"),
                             {"id": siguiente, "c": bodega_id, "n": nombre, **{c: f[c] for c in columnas}})
            propias[llave] = siguiente
            siguiente += 1
            cuenta["creados"] += 1
        mapa[int(f["id"])] = propias[llave]
    return mapa


async def _proveedores(db: AsyncSession, bodega_id: int, sede_id: int, solo_ids: Optional[set], cuenta: dict) -> dict:
    propios = {((f[2] or "").strip(), (f[1] or "").strip().upper()): int(f[0]) for f in (await db.execute(text(
        "SELECT id_proveedor, name, nit FROM suppliers WHERE company_id = :c AND id_proveedor IS NOT NULL"),
        {"c": bodega_id})).all()}
    filas = (await db.execute(text("""
        SELECT id_proveedor, name, nit, contact_name, email, phone, telefono_celular, address, notes
        FROM suppliers WHERE company_id = :s AND id_proveedor IS NOT NULL ORDER BY id_proveedor"""),
        {"s": sede_id})).mappings().all()
    siguiente = None
    mapa = {}
    for f in filas:
        if solo_ids is not None and int(f["id_proveedor"]) not in solo_ids:
            continue
        nombre = (f["name"] or "").strip()[:150]
        if not nombre:
            cuenta["omitidos"] += 1
            continue
        llave = ((f["nit"] or "").strip(), nombre.upper())
        if llave in propios:
            cuenta["existentes"] += 1
        else:
            if siguiente is None:
                siguiente = await sede_maestros.siguiente_id(db, "suppliers", "id_proveedor", bodega_id, False)
            await db.execute(text("""
                INSERT INTO suppliers (company_id, id_proveedor, name, nit, contact_name, email, phone,
                                       telefono_celular, address, notes, is_active, synced, created_at)
                VALUES (:c, :p, :n, :nit, :cn, :e, :ph, :cel, :a, :notes, 1, 0, NOW())
            """), {"c": bodega_id, "p": siguiente, "n": nombre, "nit": f["nit"], "cn": f["contact_name"],
                   "e": f["email"], "ph": f["phone"], "cel": f["telefono_celular"], "a": f["address"],
                   "notes": f["notes"]})
            propios[llave] = siguiente
            siguiente += 1
            cuenta["creados"] += 1
        mapa[int(f["id_proveedor"])] = propios[llave]
    return mapa


async def _clientes(db: AsyncSession, bodega_id: int, sede_id: int, cuenta: dict) -> None:
    """Conserva el Id_Cliente de la sede si está libre en la bodega (el Consumidor Final sigue siendo el 1)."""
    propios = (await db.execute(text(
        "SELECT id_cliente, TRIM(COALESCE(cedula, '')) AS ced, "
        "UPPER(TRIM(CONCAT_WS(' ', nombres, apellidos))) AS nom FROM clientes WHERE company_id = :c"
    ), {"c": bodega_id})).mappings().all()
    ids = {int(f["id_cliente"]) for f in propios}
    cedulas = {f["ced"] for f in propios if f["ced"]}
    nombres = {f["nom"] for f in propios if not f["ced"] and f["nom"]}
    siguiente = max(ids | {1}) + 1
    filas = (await db.execute(text(
        f"SELECT id_cliente, {', '.join(_COLS_CLIENTE)} FROM clientes WHERE company_id = :s ORDER BY id_cliente"),
        {"s": sede_id})).mappings().all()
    for f in filas:
        ced = (f["cedula"] or "").strip()
        nom = " ".join(x for x in ((f["nombres"] or "").strip(), (f["apellidos"] or "").strip()) if x).upper()
        if not ced and not nom:
            cuenta["omitidos"] += 1
            continue
        if (ced and ced in cedulas) or (not ced and nom in nombres):
            cuenta["existentes"] += 1
            continue
        id_cli = int(f["id_cliente"])
        if id_cli in ids or id_cli < 1:
            id_cli, siguiente = siguiente, siguiente + 1
        await db.execute(text(f"""
            INSERT INTO clientes (company_id, id_cliente, {', '.join(_COLS_CLIENTE)}, enviada_mysql)
            VALUES (:c, :id, {', '.join(':' + k for k in _COLS_CLIENTE)}, 0)
        """), {"c": bodega_id, "id": id_cli, **{k: f[k] for k in _COLS_CLIENTE}})
        ids.add(id_cli)
        siguiente = max(siguiente, id_cli + 1)
        if ced:
            cedulas.add(ced)
        else:
            nombres.add(nom)
        cuenta["creados"] += 1


async def importar_catalogo(db: AsyncSession, bodega: Bodega, sede: dict, datos: list,
                            clave: Optional[str]) -> dict:
    """Importa los datos escogidos de la sede. Productos entran con cantidad 0 y quedan vinculados a la sede;
    los que no tienen código se omiten (el código es la llave con la sede)."""
    escogidos = set(datos or [])
    datos = [d for d in DATOS_IMPORTAR if d in escogidos]
    if not datos:
        raise HTTPException(status_code=422, detail="Escoja al menos un dato para importar")
    if await clave_usada(db, bodega, clave):
        return {"ok": True, "repetida": True, "resultado": []}
    sede_id = sede["id"]
    res = {d: _cuenta() for d in datos}
    con_productos = "productos" in datos

    productos = []
    if con_productos:
        productos = (await db.execute(text("""
            SELECT d.id, d.name, d.product_code, d.price, d.category_id, d.tax, d.wholesale_price, d.product_cost,
                   d.minimum_stock, d.extra_print, d.ask_product_description,
                   (SELECT dp.supplier_id FROM pos_dish_products dp
                    WHERE dp.company_id = d.company_id AND dp.dish_id = d.id ORDER BY dp.supplier_id DESC LIMIT 1) AS proveedor
            FROM pos_dishes d
            WHERE d.company_id = :s AND COALESCE(d.active, 0) = 0 AND d.id < :prov
            ORDER BY d.name
            LIMIT :lim
        """), {"s": sede_id, "prov": sede_maestros.ID_PROVISIONAL, "lim": MAX_IMPORTAR + 1})).mappings().all()
        if len(productos) > MAX_IMPORTAR:
            raise HTTPException(status_code=422, detail=f"La sede tiene más de {MAX_IMPORTAR} productos; contacte soporte")

    # Catálogos completos si se marcaron; si no, solo lo que usan los productos (arrastre, no se reporta).
    arrastre = _cuenta()
    categorias = {}
    if "categorias" in datos or con_productos:
        completo = "categorias" in datos
        categorias = await _por_nombre(db, "pos_dish_categories", bodega.id, sede_id, ("percentage", "is_active"),
                                       None if completo else {int(p["category_id"] or 0) for p in productos},
                                       res["categorias"] if completo else arrastre)
    if "categorias_insumos" in datos:
        await _por_nombre(db, "pos_product_categories", bodega.id, sede_id,
                          ("percentage", "is_active", "require_selection", "print_assembly_changes_only"),
                          None, res["categorias_insumos"])
    if "medidas" in datos:
        await _por_nombre(db, "pos_measure_forms", bodega.id, sede_id, ("is_active",), None, res["medidas"])
    proveedores = {}
    if "proveedores" in datos or con_productos:
        completo = "proveedores" in datos
        proveedores = await _proveedores(db, bodega.id, sede_id,
                                         None if completo else {int(p["proveedor"] or 0) for p in productos},
                                         res["proveedores"] if completo else arrastre)
    if "clientes" in datos:
        await _clientes(db, bodega.id, sede_id, res["clientes"])

    if con_productos:
        cuenta = res["productos"]
        varios = await asegurar_varios(db, bodega.id)
        unidad = await asegurar_unidad(db, bodega.id)
        general = None
        existentes = {(f[0] or "").strip(): int(f[1]) for f in (await db.execute(text(
            "SELECT product_code, id FROM pos_dishes WHERE company_id = :c AND COALESCE(product_code, '') <> ''"),
            {"c": bodega.id})).all()}
        nombres = {(f[0] or "").strip().upper() for f in (await db.execute(text(
            "SELECT name FROM pos_dishes WHERE company_id = :c"), {"c": bodega.id})).all()}
        siguiente = None
        for p in productos:
            codigo = (p["product_code"] or "").strip().replace("'", "-").replace(",", "-")
            if not codigo or not RE_CODIGO.match(codigo):
                cuenta["omitidos"] += 1
                continue
            if codigo in existentes:
                dish_id = existentes[codigo]
                cuenta["existentes"] += 1
            else:
                nombre = (p["name"] or "").strip()[:250]
                if not nombre or nombre.upper() in nombres:
                    cuenta["omitidos"] += 1
                    continue
                categoria = categorias.get(int(p["category_id"] or 0))
                if not categoria:
                    general = general or await _categoria_general(db, bodega.id)
                    categoria = general
                if siguiente is None:
                    siguiente = await _nuevo_id(db, bodega.id)        # una sola vez; luego se numera en bloque
                dish_id = await crear_producto(db, bodega.id, {
                    "name": nombre, "product_code": codigo, "price": p["price"], "tax": p["tax"],
                    "wholesale_price": p["wholesale_price"], "product_cost": p["product_cost"],
                    "minimum_stock": p["minimum_stock"], "extra_print": str(p["extra_print"] or "0") == "1",
                    "ask_product_description": p["ask_product_description"], "category_id": categoria,
                    "id_proveedor": proveedores.get(int(p["proveedor"] or 0)) or varios,
                }, nuevo_id=siguiente, unidad=unidad, validado=True)
                siguiente += 1
                existentes[codigo] = dish_id
                nombres.add(nombre.upper())
                cuenta["creados"] += 1
            await db.execute(text("""
                INSERT INTO bc_producto_sede (bodega_id, dish_id, sede_id, sede_dish_id, estado)
                VALUES (:b, :d, :s, :sd, 'VINCULADO')
                ON DUPLICATE KEY UPDATE sede_dish_id = VALUES(sede_dish_id), estado = 'VINCULADO', error = NULL
            """), {"b": bodega.id, "d": dish_id, "s": sede_id, "sd": int(p["id"])})

    resultado = [{"clave": d, "nombre": DATOS_IMPORTAR[d], **res[d]} for d in datos]
    texto = "; ".join(f"{r['nombre']}: {r['creados']} nuevos, {r['existentes']} ya estaban" for r in resultado)
    await movimiento(db, bodega, "IMPORTACION", None, 0, f"{sede['nombre']} — {texto}", sede_id=sede_id, clave=clave)
    return {"ok": True, "repetida": False, "resultado": resultado}


async def _categoria_general(db: AsyncSession, cid: int) -> int:
    fila = (await db.execute(text(
        "SELECT id FROM pos_dish_categories WHERE company_id = :c AND UPPER(name) = 'GENERAL' LIMIT 1"
    ), {"c": cid})).scalar()
    if fila:
        return int(fila)
    nuevo = await sede_maestros.siguiente_id(db, "pos_dish_categories", "id", cid, False)
    await db.execute(text("""
        INSERT INTO pos_dish_categories (id, company_id, parent_category_id, name, is_active, synced)
        VALUES (:id, :c, 0, 'GENERAL', 1, 0)
    """), {"id": nuevo, "c": cid})
    return nuevo


# ─── Enviar a sedes (administración central) ─────────────────────────────────
# Con bodega activa, proveedores y categorías se crean y cambian SOLO en la bodega (bloqueo_bodega en las sedes)
# y se envían a las sedes marcadas. En la sede: si ya existe (proveedor por NIT, o por nombre si no tiene NIT;
# categoría por nombre) se SOBRESCRIBE con lo de la bodega; si no, se crea. Lo enviado queda synced = 0 para que
# la sincronización del catálogo lo baje al escritorio (en sedes con escritorio nace con número provisional).

MAX_ENVIO = 2000
CATALOGOS_ENVIO = {
    "proveedores": {
        "nombre": "Proveedores", "tabla": "suppliers", "llave": "id_proveedor", "nombre_col": "name",
        "columnas": ("name", "nit", "contact_name", "email", "phone", "telefono_celular", "address", "notes",
                     "is_active"),
    },
    "categorias": {
        "nombre": "Categorías de productos", "tabla": "pos_dish_categories", "llave": "id", "nombre_col": "name",
        "columnas": ("name", "percentage", "is_active"),
    },
    "categorias_insumos": {
        "nombre": "Categorías de insumos", "tabla": "pos_product_categories", "llave": "id", "nombre_col": "name",
        "columnas": ("name", "percentage", "is_active", "require_selection", "print_assembly_changes_only"),
    },
}


async def catalogo_bodega(db: AsyncSession, bodega: Bodega, tipo: str) -> list[dict]:
    """Registros de la bodega que se pueden enviar, A-Z, con en cuántas sedes existe ya cada uno."""
    cfg = CATALOGOS_ENVIO[tipo]
    cols = ", ".join(cfg["columnas"])
    filas = (await db.execute(text(
        f"SELECT {cfg['llave']} AS id, {cols} FROM {cfg['tabla']} WHERE company_id = :b AND {cfg['llave']} IS NOT NULL "
        f"ORDER BY {cfg['nombre_col']}"), {"b": bodega.id})).mappings().all()
    out = []
    for f in filas:
        r = {k: (float(v) if k == "percentage" and v is not None else v) for k, v in dict(f).items()}
        r["is_active"] = int(r.get("is_active") or 0)
        out.append(r)
    return out


async def _registro_sede(db: AsyncSession, cfg: dict, sede_id: int, fila: dict):
    """Llave del mismo registro en la sede, o None."""
    if cfg["tabla"] == "suppliers" and (fila.get("nit") or "").strip():
        llave = (await db.execute(text(
            "SELECT id_proveedor FROM suppliers WHERE company_id = :s AND TRIM(nit) = :nit "
            "AND id_proveedor IS NOT NULL ORDER BY id_proveedor LIMIT 1"),
            {"s": sede_id, "nit": fila["nit"].strip()})).scalar()
        if llave is not None:
            return llave
    return (await db.execute(text(
        f"SELECT {cfg['llave']} FROM {cfg['tabla']} WHERE company_id = :s AND {cfg['llave']} IS NOT NULL "
        f"AND UPPER(TRIM({cfg['nombre_col']})) = :n ORDER BY {cfg['llave']} LIMIT 1"),
        {"s": sede_id, "n": (fila[cfg["nombre_col"]] or "").strip().upper()})).scalar()


async def enviar_a_sedes(db: AsyncSession, bodega: Bodega, tipo: str, ids: list[int], sedes: list[dict],
                         clave: Optional[str]) -> dict:
    from app.services import sede_pedidos
    if tipo not in CATALOGOS_ENVIO:
        raise HTTPException(status_code=422, detail="Dato a enviar no válido")
    if not ids or not sedes:
        raise HTTPException(status_code=422, detail="Escoja los registros y las sedes a las que se envían")
    if len(ids) > MAX_ENVIO:
        raise HTTPException(status_code=422, detail=f"Máximo {MAX_ENVIO} registros por envío")
    if await clave_usada(db, bodega, clave):
        return {"ok": True, "repetida": True, "resultado": []}
    cfg = CATALOGOS_ENVIO[tipo]
    cols = cfg["columnas"]
    pi = ", ".join(f":i{n}" for n in range(len(ids)))
    filas = (await db.execute(text(
        f"SELECT {cfg['llave']} AS _id, {', '.join(cols)} FROM {cfg['tabla']} "
        f"WHERE company_id = :b AND {cfg['llave']} IN ({pi}) ORDER BY {cfg['nombre_col']}"),
        {"b": bodega.id, **{f"i{n}": int(v) for n, v in enumerate(ids)}})).mappings().all()
    if len(filas) != len(set(int(i) for i in ids)):
        raise HTTPException(status_code=404, detail="Hay registros que no son de la bodega")

    resultado = []
    for sede in sedes:
        con_escritorio = await sede_pedidos.tiene_sede(db, sede["id"])
        cuenta = {"sede_id": sede["id"], "sede": sede["nombre"], "creados": 0, "actualizados": 0}
        for f in filas:
            datos = {c: f[c] for c in cols}
            datos[cfg["nombre_col"]] = (datos[cfg["nombre_col"]] or "").strip()
            llave = await _registro_sede(db, cfg, sede["id"], datos)
            if llave is not None:
                sets = ", ".join(f"{c} = :{c}" for c in cols)
                await db.execute(text(
                    f"UPDATE {cfg['tabla']} SET {sets}, synced = 0 WHERE company_id = :s AND {cfg['llave']} = :k"),
                    {**datos, "s": sede["id"], "k": llave})
                cuenta["actualizados"] += 1
            else:
                nuevo = await sede_maestros.siguiente_id(db, cfg["tabla"], cfg["llave"], sede["id"], con_escritorio)
                extra = ", created_at" if cfg["tabla"] == "suppliers" else ""
                await db.execute(text(
                    f"INSERT INTO {cfg['tabla']} (company_id, {cfg['llave']}, {', '.join(cols)}, synced{extra}) "
                    f"VALUES (:s, :k, {', '.join(':' + c for c in cols)}, 0{', NOW()' if extra else ''})"),
                    {**datos, "s": sede["id"], "k": nuevo})
                cuenta["creados"] += 1
        resultado.append(cuenta)
        await movimiento(db, bodega, "ENVIO", None, 0,
                         f"{cfg['nombre']} → {sede['nombre']}: {cuenta['creados']} nuevos, "
                         f"{cuenta['actualizados']} actualizados", sede_id=sede["id"], clave=clave)
    return {"ok": True, "repetida": False, "resultado": resultado}


# ─── Enviar roles con sus permisos ───────────────────────────────────────────
# El rol se arma en la bodega (pantallas visibles + Control de Acceso) y se copia a las sedes por NOMBRE: si la sede
# ya tiene un rol con ese nombre queda con los permisos de la bodega; si no, se crea. El rol ADMIN (nombre con
# "ADMIN") nunca se envía ni se toca en la sede. Las pantallas exclusivas de SYSADMIN nunca viajan.
# Un usuario que no es Admin (ayudante de la bodega) no puede enviar un rol con más permisos que el suyo.

def _es_rol_admin(nombre: str) -> bool:
    return "ADMIN" in (nombre or "").upper()


async def _permisos_rol(db: AsyncSession, role_id: int) -> tuple[dict, set]:
    """({module_id: (ver, ver_todo, crear, editar, borrar)}, {perm_key})"""
    modulos = {int(f[0]): tuple(int(bool(x)) for x in f[1:]) for f in (await db.execute(text("""
        SELECT rm.module_id, rm.can_view, rm.can_view_all, rm.can_create, rm.can_edit, rm.can_delete
        FROM role_modules rm JOIN system_modules sm ON sm.id = rm.module_id AND sm.is_sysadmin = 0
        WHERE rm.role_id = :r
    """), {"r": role_id})).all()}
    claves = set((await db.execute(text(
        "SELECT perm_key FROM role_access_permissions WHERE role_id = :r"), {"r": role_id})).scalars().all())
    return modulos, claves


async def catalogo_roles(db: AsyncSession, bodega: Bodega) -> list[dict]:
    filas = (await db.execute(text("""
        SELECT r.id, r.name, r.description, r.access_type,
               (SELECT COUNT(*) FROM role_modules rm WHERE rm.role_id = r.id AND rm.can_view = 1) AS pantallas,
               (SELECT COUNT(*) FROM role_access_permissions ra WHERE ra.role_id = r.id) AS permisos
        FROM roles r WHERE r.company_id = :b AND COALESCE(r.is_system, 0) = 0
        ORDER BY r.name
    """), {"b": bodega.id})).mappings().all()
    return [{**dict(f), "is_active": 1, "es_admin": _es_rol_admin(f["name"]),
             "nit": f"{f['pantallas']} pantallas · {f['permisos']} permisos"} for f in filas]


async def _exigir_no_escalar(db: AsyncSession, bodega: Bodega, modulos: dict, claves: set, nombre: str) -> None:
    from app.models.role_model import Role
    rol_propio = await db.get(Role, bodega.user.role_id) if bodega.user.role_id else None
    if rol_propio and (rol_propio.is_system or _es_rol_admin(rol_propio.name)):
        return
    mis_mod, mis_claves = await _permisos_rol(db, rol_propio.id) if rol_propio else ({}, set())
    for mid, flags in modulos.items():
        propios = mis_mod.get(mid, (0, 0, 0, 0, 0))
        if any(f and not p for f, p in zip(flags, propios)):
            raise HTTPException(status_code=403, detail=f"El rol «{nombre}» tiene permisos que su propio rol no tiene")
    if claves - mis_claves:
        raise HTTPException(status_code=403, detail=f"El rol «{nombre}» tiene permisos que su propio rol no tiene")


async def enviar_roles(db: AsyncSession, bodega: Bodega, ids: list[int], sedes: list[dict],
                       clave: Optional[str]) -> dict:
    from app.services.plan_limits_service import check_limit
    from app.models.role_model import Role
    if await clave_usada(db, bodega, clave):
        return {"ok": True, "repetida": True, "resultado": []}
    pi = ", ".join(f":i{n}" for n in range(len(ids)))
    roles = (await db.execute(text(
        f"SELECT id, name, description, access_type, home_route FROM roles "
        f"WHERE company_id = :b AND COALESCE(is_system, 0) = 0 AND id IN ({pi}) ORDER BY name"),
        {"b": bodega.id, **{f"i{n}": int(v) for n, v in enumerate(ids)}})).mappings().all()
    if len(roles) != len(set(int(i) for i in ids)):
        raise HTTPException(status_code=404, detail="Hay roles que no son de la bodega")
    admins = [r["name"] for r in roles if _es_rol_admin(r["name"])]
    if admins:
        raise HTTPException(status_code=422, detail="El rol ADMIN no se envía: cada sede conserva el suyo")
    paquetes = []
    for r in roles:
        modulos, claves = await _permisos_rol(db, r["id"])
        await _exigir_no_escalar(db, bodega, modulos, claves, r["name"])
        paquetes.append((r, modulos, claves))

    resultado = []
    for sede in sedes:
        cuenta = {"sede_id": sede["id"], "sede": sede["nombre"], "creados": 0, "actualizados": 0, "errores": []}
        for r, modulos, claves in paquetes:
            nombre = (r["name"] or "").strip()
            destino = (await db.execute(text(
                "SELECT id FROM roles WHERE company_id = :s AND UPPER(TRIM(name)) = :n AND COALESCE(is_system, 0) = 0 "
                "ORDER BY id LIMIT 1"), {"s": sede["id"], "n": nombre.upper()})).scalar()
            if destino is None:
                try:
                    await check_limit(sede["id"], "max_roles", Role, db)
                except HTTPException as e:
                    cuenta["errores"].append(f"{nombre}: {e.detail}")
                    continue
                res = await db.execute(text("""
                    INSERT INTO roles (name, description, company_id, is_system, home_route, access_type)
                    VALUES (:n, :d, :s, 0, :h, :t)
                """), {"n": nombre, "d": r["description"] or "", "s": sede["id"], "h": r["home_route"],
                       "t": r["access_type"] or "interno"})
                destino = res.lastrowid
                cuenta["creados"] += 1
            else:
                await db.execute(text(
                    "UPDATE roles SET description = :d, home_route = :h, access_type = :t WHERE id = :id"),
                    {"d": r["description"] or "", "h": r["home_route"], "t": r["access_type"] or "interno",
                     "id": destino})
                cuenta["actualizados"] += 1
            await db.execute(text("DELETE FROM role_modules WHERE role_id = :r"), {"r": destino})
            for mid, (v, va, c, e, b) in modulos.items():
                await db.execute(text("""
                    INSERT INTO role_modules (role_id, module_id, can_view, can_view_all, can_create, can_edit, can_delete)
                    VALUES (:r, :m, :v, :va, :c, :e, :b)
                """), {"r": destino, "m": mid, "v": v, "va": va, "c": c, "e": e, "b": b})
            await db.execute(text("DELETE FROM role_access_permissions WHERE role_id = :r"), {"r": destino})
            for k in sorted(claves):
                await db.execute(text("INSERT INTO role_access_permissions (role_id, perm_key) VALUES (:r, :k)"),
                                 {"r": destino, "k": k})
        resultado.append(cuenta)
        await movimiento(db, bodega, "ENVIO", None, 0,
                         f"Roles → {sede['nombre']}: {cuenta['creados']} nuevos, {cuenta['actualizados']} actualizados"
                         + (f", {len(cuenta['errores'])} sin enviar" if cuenta["errores"] else ""),
                         sede_id=sede["id"], clave=clave)
    return {"ok": True, "repetida": False, "resultado": resultado}


# ─── Usuarios del grupo (bodega + sedes) ─────────────────────────────────────
# Una persona = un correo. Tiene una fila en users por cada empresa donde trabaja, con su rol en esa empresa y
# UNA sola contraseña para todas. Desde la bodega: invitar (link) a varias empresas con rol por empresa, agregar
# a otra empresa a quien ya existe, cambiarle el rol y activar/desactivar por empresa. Un ayudante (no Admin) no
# asigna roles con más permisos que el suyo ni toca usuarios administradores.

async def empresas_grupo(db: AsyncSession, bodega: Bodega) -> dict:
    """{company_id: nombre} de la bodega y sus sedes (la bodega primero)."""
    nombre = (await db.execute(text("SELECT name FROM companies WHERE id_company = :b"), {"b": bodega.id})).scalar()
    out = {bodega.id: nombre or "Bodega"}
    for s in await sedes_del_nit(db, bodega):
        out[s["id"]] = s["nombre"]
    return out


async def roles_empresas(db: AsyncSession, bodega: Bodega) -> list[dict]:
    grupo = await empresas_grupo(db, bodega)
    pe = ", ".join(f":e{n}" for n in range(len(grupo)))
    filas = (await db.execute(text(
        f"SELECT id, name, company_id FROM roles WHERE company_id IN ({pe}) AND COALESCE(is_system, 0) = 0 ORDER BY name"),
        {f"e{n}": c for n, c in enumerate(grupo)})).mappings().all()
    out = []
    for cid, nombre in grupo.items():
        out.append({"company_id": cid, "nombre": nombre, "es_bodega": cid == bodega.id,
                    "roles": [{"id": f["id"], "name": f["name"], "es_admin": _es_rol_admin(f["name"])}
                              for f in filas if f["company_id"] == cid]})
    return out


async def usuarios_grupo(db: AsyncSession, bodega: Bodega) -> list[dict]:
    grupo = await empresas_grupo(db, bodega)
    pe = ", ".join(f":e{n}" for n in range(len(grupo)))
    filas = (await db.execute(text(f"""
        SELECT u.id, u.nombre, LOWER(TRIM(u.email)) AS email, u.company_id, u.is_active, u.role_id, r.name AS rol
        FROM users u LEFT JOIN roles r ON r.id = u.role_id
        WHERE u.company_id IN ({pe}) AND COALESCE(r.is_system, 0) = 0
        ORDER BY u.nombre
    """), {f"e{n}": c for n, c in enumerate(grupo)})).mappings().all()
    personas: dict = {}
    for f in filas:
        p = personas.setdefault(f["email"], {"email": f["email"], "nombre": f["nombre"], "empresas": []})
        p["empresas"].append({"user_id": f["id"], "company_id": f["company_id"], "empresa": grupo[f["company_id"]],
                              "role_id": f["role_id"], "rol": f["rol"], "activo": bool(f["is_active"]),
                              "es_bodega": f["company_id"] == bodega.id, "yo": f["id"] == bodega.user.id})
    for p in personas.values():
        p["empresas"].sort(key=lambda e: (not e["es_bodega"], e["empresa"]))
    return sorted(personas.values(), key=lambda p: (p["nombre"] or p["email"]).upper())


async def _rol_asignable(db: AsyncSession, bodega: Bodega, company_id: int, role_id: int):
    """El rol existe en esa empresa del grupo y el que asigna no escala permisos. Devuelve el rol."""
    from app.models.role_model import Role
    if company_id not in await empresas_grupo(db, bodega):
        from app.services.error_log import record_security
        record_security("Bodega central: empresa fuera de su NIT", {"bodega": bodega.id, "empresa": company_id})
        raise HTTPException(status_code=403, detail="La empresa no pertenece a la bodega central")
    rol = await db.get(Role, int(role_id))
    if not rol or rol.company_id != company_id or rol.is_system:
        raise HTTPException(status_code=400, detail="Rol no válido para esa empresa")
    propio = await db.get(Role, bodega.user.role_id) if bodega.user.role_id else None
    if not (propio and (propio.is_system or _es_rol_admin(propio.name))):
        if _es_rol_admin(rol.name):
            raise HTTPException(status_code=403, detail="Solo un administrador puede asignar el rol administrador")
        modulos, claves = await _permisos_rol(db, rol.id)
        await _exigir_no_escalar(db, bodega, modulos, claves, rol.name)
    return rol


async def invitar(db: AsyncSession, bodega: Bodega, asignaciones: list[dict]) -> dict:
    """Crea UNA invitación (link de 48 h) para la bodega y/o varias sedes, con un rol por empresa."""
    import uuid
    from datetime import datetime, timedelta
    from app.models.invitation_model import InvitationToken
    from app.models.user_model import User
    from app.services.plan_limits_service import check_limit
    vistas = set()
    roles = []
    for a in asignaciones:
        cid = int(a["company_id"])
        if cid in vistas:
            raise HTTPException(status_code=422, detail="Hay empresas repetidas en la invitación")
        vistas.add(cid)
        rol = await _rol_asignable(db, bodega, cid, int(a["role_id"]))
        await _limite_usuarios(db, bodega, cid)
        roles.append((cid, rol))
    primero = roles[0]
    inv = InvitationToken(token=uuid.uuid4().hex, company_id=primero[0], role_id=primero[1].id,
                          created_by=bodega.user.id, expires_at=datetime.utcnow() + timedelta(hours=48))
    db.add(inv)
    await db.flush()
    for cid, rol in roles:
        await db.execute(text(
            "INSERT INTO invitation_token_sedes (invitation_id, company_id, role_id) VALUES (:i, :c, :r)"),
            {"i": inv.id, "c": cid, "r": rol.id})
    grupo = await empresas_grupo(db, bodega)
    await movimiento(db, bodega, "USUARIOS", None, 0,
                     "Invitación: " + ", ".join(f"{grupo[c]} ({r.name})" for c, r in roles))
    return {"ok": True, "token": inv.token, "expires_at": inv.expires_at.isoformat()}


async def _filas_correo(db: AsyncSession, email: str) -> list:
    return (await db.execute(text(
        "SELECT id, company_id, nombre, password_hash FROM users WHERE LOWER(TRIM(email)) = :e ORDER BY id"),
        {"e": email.strip().lower()})).mappings().all()


async def asignar_empresa(db: AsyncSession, bodega: Bodega, email: str, company_id: int, role_id: int) -> dict:
    """Agrega a otra empresa del grupo a una persona que ya existe (misma contraseña), o le cambia el rol allí."""
    from app.models.user_model import User
    from app.services.plan_limits_service import check_limit
    grupo = await empresas_grupo(db, bodega)
    filas = await _filas_correo(db, email)
    if not filas or any(f["company_id"] not in grupo for f in filas):
        # nunca se toca a una persona que también trabaja en empresas ajenas al grupo
        raise HTTPException(status_code=404, detail="Usuario no encontrado en las empresas de la bodega")
    rol = await _rol_asignable(db, bodega, int(company_id), int(role_id))
    existente = next((f for f in filas if f["company_id"] == int(company_id)), None)
    if existente:
        await _exigir_puede_tocar(db, bodega, existente["id"])
        await db.execute(text("UPDATE users SET role_id = :r, is_active = 1 WHERE id = :id"),
                         {"r": rol.id, "id": existente["id"]})
        accion = "rol actualizado"
    else:
        await _limite_usuarios(db, bodega, int(company_id))
        base = filas[0]
        await db.execute(text("""
            INSERT INTO users (nombre, email, password_hash, role_id, company_id, is_active)
            VALUES (:n, :e, :h, :r, :c, 1)
        """), {"n": base["nombre"], "e": email.strip().lower(), "h": base["password_hash"], "r": rol.id,
               "c": int(company_id)})
        accion = "agregado"
    await movimiento(db, bodega, "USUARIOS", None, 0, f"{email} → {grupo[int(company_id)]} ({rol.name}): {accion}")
    return {"ok": True, "accion": accion}


async def _limite_usuarios(db: AsyncSession, bodega: Bodega, cid: int) -> None:
    """Límite de usuarios del plan de ESA empresa; el mensaje dice cuál, porque se invita a varias a la vez."""
    from app.models.user_model import User
    from app.services.plan_limits_service import check_limit
    try:
        await check_limit(cid, "max_users", User, db)
    except HTTPException as e:
        nombre = (await empresas_grupo(db, bodega)).get(cid, "La empresa")
        raise HTTPException(status_code=e.status_code, detail=f"{nombre}: {e.detail}")


async def _exigir_puede_tocar(db: AsyncSession, bodega: Bodega, user_id: int) -> None:
    from app.models.role_model import Role
    if int(user_id) == bodega.user.id:
        raise HTTPException(status_code=400, detail="No puede cambiar su propio acceso")
    propio = await db.get(Role, bodega.user.role_id) if bodega.user.role_id else None
    if propio and (propio.is_system or _es_rol_admin(propio.name)):
        return
    rol_destino = (await db.execute(text(
        "SELECT r.name FROM users u JOIN roles r ON r.id = u.role_id WHERE u.id = :u"), {"u": user_id})).scalar()
    if _es_rol_admin(rol_destino or ""):
        raise HTTPException(status_code=403, detail="Solo un administrador puede cambiar a otro administrador")


async def cambiar_estado(db: AsyncSession, bodega: Bodega, user_id: int, activo: bool) -> dict:
    grupo = await empresas_grupo(db, bodega)
    fila = (await db.execute(text(
        "SELECT u.id, u.email, u.company_id, COALESCE(r.is_system, 0) AS sis FROM users u "
        "LEFT JOIN roles r ON r.id = u.role_id WHERE u.id = :u"), {"u": int(user_id)})).mappings().first()
    if not fila or fila["company_id"] not in grupo or fila["sis"]:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en las empresas de la bodega")
    await _exigir_puede_tocar(db, bodega, fila["id"])
    await db.execute(text("UPDATE users SET is_active = :a WHERE id = :u"), {"a": 1 if activo else 0, "u": fila["id"]})
    if not activo:      # se cierran sus sesiones abiertas en esa empresa
        await db.execute(text("UPDATE user_sessions SET is_active = 0 WHERE user_id = :u"), {"u": fila["id"]})
    await movimiento(db, bodega, "USUARIOS", None, 0,
                     f"{fila['email']} en {grupo[fila['company_id']]}: {'activado' if activo else 'desactivado'}")
    return {"ok": True}


# ─── Consultas ───────────────────────────────────────────────────────────────

async def listar_productos(db: AsyncSession, bodega: Bodega) -> list[dict]:
    filas = (await db.execute(text("""
        SELECT d.id, d.name, d.product_code, d.price, d.wholesale_price, d.product_cost, d.tax, d.minimum_stock,
               d.category_id, c.name AS categoria, COALESCE(d.active, 0) AS active,
               IF(COALESCE(d.extra_print, '0') = '1', 1, 0) AS extra_print,
               COALESCE(iap.cantidad_actual, 0) AS stock,
               (SELECT dp.supplier_id FROM pos_dish_products dp
                WHERE dp.company_id = d.company_id AND dp.dish_id = d.id ORDER BY dp.supplier_id DESC LIMIT 1) AS id_proveedor
        FROM pos_dishes d
        LEFT JOIN pos_dish_categories c ON c.id = d.category_id AND c.company_id = d.company_id
        LEFT JOIN inventario_actual_porciones iap ON iap.company_id = d.company_id AND iap.id_item = d.id
        WHERE d.company_id = :b
        ORDER BY d.name
    """), {"b": bodega.id})).mappings().all()
    sedes = {s["id"]: s["nombre"] for s in await sedes_del_nit(db, bodega)}
    estados: dict = {}
    for f in (await db.execute(text(
            "SELECT dish_id, sede_id, estado FROM bc_producto_sede WHERE bodega_id = :b"), {"b": bodega.id})).all():
        if int(f[1]) in sedes:
            estados.setdefault(int(f[0]), []).append({"sede_id": int(f[1]), "sede": sedes[int(f[1])], "estado": f[2]})
    proveedores = {int(f[0]): f[1] for f in (await db.execute(text(
        "SELECT id_proveedor, name FROM suppliers WHERE company_id = :b AND id_proveedor IS NOT NULL"),
        {"b": bodega.id})).all()}
    out = []
    for f in filas:
        r = dict(f)
        r["price"] = int(r["price"] or 0)
        for k in ("wholesale_price", "product_cost", "tax", "minimum_stock", "stock"):
            r[k] = float(r[k] or 0)
        r["proveedor"] = proveedores.get(int(r["id_proveedor"] or 0), "")
        r["sedes"] = sorted(estados.get(int(r["id"]), []), key=lambda s: s["sede"])
        out.append(r)
    return out
