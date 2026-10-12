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


async def crear_producto(db: AsyncSession, cid: int, d: dict) -> int:
    """d: name, product_code, price, wholesale_price (precio mínimo), product_cost, tax, minimum_stock,
    category_id, id_proveedor, extra_print (desactivar al vender), ask_product_description.
    Valida categoría y proveedor; no hace commit."""
    unitario = await cargue_unitario(db, cid)
    categoria = await categoria_valida(db, cid, d.get("category_id"))
    proveedor = await proveedor_valido(db, cid, d.get("id_proveedor"), obligatorio=unitario)
    codigo = limpiar_codigo(d.get("product_code"))
    nombre = (d.get("name") or "").strip()[:250]
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
    nuevo = await _nuevo_id(db, cid)
    codigo = codigo or f"BC-{nuevo}"
    unidad = await asegurar_unidad(db, cid)

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
    for codigo in limpios:
        nuevo = await crear_producto(db, bodega.id, {
            **base, "name": f"{nombre_base} {codigo}"[:250], "product_code": codigo, "extra_print": 1,
        })
        await registrar_entrada(db, bodega, nuevo, 1, base["id_proveedor"] or 0,
                                f"Réplica de {base['product_code'] or base['id']}")
        await movimiento(db, bodega, "REPLICA", nuevo, 1, f"Réplica de {base['name']}"[:255],
                         referencia=str(dish_id), clave=clave)
        creados.append({"id": nuevo, "codigo": codigo})
    return {"ok": True, "repetida": False, "creados": creados}


# ─── Importar el catálogo de una sede (cantidad 0) ───────────────────────────

async def _mapa_categorias(db: AsyncSession, bodega_id: int, sede_id: int) -> dict:
    propias = {(f[1] or "").strip().upper(): int(f[0]) for f in (await db.execute(text(
        "SELECT id, name FROM pos_dish_categories WHERE company_id = :c"), {"c": bodega_id})).all()}
    mapa = {}
    for f in (await db.execute(text(
            "SELECT id, name, percentage FROM pos_dish_categories WHERE company_id = :s"), {"s": sede_id})).all():
        nombre = (f[1] or "").strip()[:100] or f"CATEGORIA {f[0]}"
        llave = nombre.upper()
        if llave not in propias:
            nuevo = await sede_maestros.siguiente_id(db, "pos_dish_categories", "id", bodega_id, False)
            await db.execute(text("""
                INSERT INTO pos_dish_categories (id, company_id, parent_category_id, name, percentage, is_active, synced)
                VALUES (:id, :c, 0, :n, :p, 1, 0)
            """), {"id": nuevo, "c": bodega_id, "n": nombre, "p": f[2] or 0})
            propias[llave] = nuevo
        mapa[int(f[0])] = propias[llave]
    return mapa


async def _mapa_proveedores(db: AsyncSession, bodega_id: int, sede_id: int) -> dict:
    propios = {}
    for f in (await db.execute(text(
            "SELECT id_proveedor, name, nit FROM suppliers WHERE company_id = :c AND id_proveedor IS NOT NULL"),
            {"c": bodega_id})).all():
        propios[((f[2] or "").strip(), (f[1] or "").strip().upper())] = int(f[0])
    mapa = {}
    for f in (await db.execute(text("""
            SELECT id_proveedor, name, nit, contact_name, email, phone, telefono_celular, address
            FROM suppliers WHERE company_id = :s AND id_proveedor IS NOT NULL"""), {"s": sede_id})).mappings().all():
        llave = ((f["nit"] or "").strip(), (f["name"] or "").strip().upper())
        if llave not in propios:
            nuevo = await sede_maestros.siguiente_id(db, "suppliers", "id_proveedor", bodega_id, False)
            await db.execute(text("""
                INSERT INTO suppliers (company_id, id_proveedor, name, nit, contact_name, email, phone,
                                       telefono_celular, address, is_active, synced, created_at)
                VALUES (:c, :p, :n, :nit, :cn, :e, :ph, :cel, :a, 1, 0, NOW())
            """), {"c": bodega_id, "p": nuevo, "n": (f["name"] or "SIN NOMBRE")[:150], "nit": f["nit"],
                   "cn": f["contact_name"], "e": f["email"], "ph": f["phone"], "cel": f["telefono_celular"],
                   "a": f["address"]})
            propios[llave] = nuevo
        mapa[int(f["id_proveedor"])] = propios[llave]
    return mapa


async def importar_catalogo(db: AsyncSession, bodega: Bodega, sede: dict, clave: Optional[str]) -> dict:
    """Copia a la bodega los productos VISIBLES de la sede (active = 0) con cantidad 0. Los que ya existen
    en la bodega por código se vinculan; los que no tienen código se omiten (el código es la llave con la sede)."""
    if await clave_usada(db, bodega, clave):
        return {"ok": True, "repetida": True}
    sede_id = sede["id"]
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

    categorias = await _mapa_categorias(db, bodega.id, sede_id)
    proveedores = await _mapa_proveedores(db, bodega.id, sede_id)
    varios = await asegurar_varios(db, bodega.id)
    existentes = {(f[0] or "").strip(): int(f[1]) for f in (await db.execute(text(
        "SELECT product_code, id FROM pos_dishes WHERE company_id = :c AND COALESCE(product_code, '') <> ''"),
        {"c": bodega.id})).all()}
    nombres = {(f[0] or "").strip().upper() for f in (await db.execute(text(
        "SELECT name FROM pos_dishes WHERE company_id = :c"), {"c": bodega.id})).all()}

    creados = vinculados = sin_codigo = omitidos = 0
    for p in productos:
        codigo = (p["product_code"] or "").strip().replace("'", "-").replace(",", "-")
        if not codigo or not RE_CODIGO.match(codigo):
            sin_codigo += 1
            continue
        if codigo in existentes:
            dish_id = existentes[codigo]
            vinculados += 1
        else:
            nombre = (p["name"] or "").strip()
            if not nombre or nombre.upper() in nombres:
                omitidos += 1
                continue
            dish_id = await crear_producto(db, bodega.id, {
                "name": nombre, "product_code": codigo, "price": p["price"], "tax": p["tax"],
                "wholesale_price": p["wholesale_price"], "product_cost": p["product_cost"],
                "minimum_stock": p["minimum_stock"], "extra_print": str(p["extra_print"] or "0") == "1",
                "ask_product_description": p["ask_product_description"],
                "category_id": categorias.get(int(p["category_id"] or 0)) or await _categoria_general(db, bodega.id),
                "id_proveedor": proveedores.get(int(p["proveedor"] or 0)) or varios,
            })
            existentes[codigo] = dish_id
            nombres.add(nombre.upper())
            creados += 1
        await db.execute(text("""
            INSERT INTO bc_producto_sede (bodega_id, dish_id, sede_id, sede_dish_id, estado)
            VALUES (:b, :d, :s, :sd, 'VINCULADO')
            ON DUPLICATE KEY UPDATE sede_dish_id = VALUES(sede_dish_id), estado = 'VINCULADO', error = NULL
        """), {"b": bodega.id, "d": dish_id, "s": sede_id, "sd": int(p["id"])})

    resumen = {"creados": creados, "vinculados": vinculados, "sin_codigo": sin_codigo, "omitidos": omitidos}
    await movimiento(db, bodega, "IMPORTACION", None, 0,
                     f"Catálogo de {sede['nombre']}: {creados} creados, {vinculados} vinculados, "
                     f"{sin_codigo} sin código, {omitidos} omitidos", sede_id=sede_id, clave=clave)
    return {"ok": True, "repetida": False, **resumen}


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
