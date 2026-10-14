"""
Factura de Proveedor (vista /compras/factura-proveedor, padre "Transaccional").

  Una factura completa por pantalla: proveedor, número de factura, fecha y líneas (producto, cantidad, valor
  unitario, % de descuento). Sin IVA. El costo nuevo de cada producto es el VALOR CON DESCUENTO (como el
  formulario de registro de precios del escritorio). Sin cuentas por pagar.

  Al guardar, cada línea:
    · entra al inventario (inventory_entries + stock) y crea su LOTE PEPS con ese costo (y vencimiento en droguerías);
    · actualiza el costo del producto (salvo que una bodega central lo administre: el costo lo define la central);
    · el caso especial de cargue unitario (celulares): una línea con IMEI crea un producto por cada IMEI, con el
      nombre "producto + IMEI", cantidad 1 y "desactivar al vender".
  Empresa con escritorio: la factura queda PENDIENTE y el agente la baja (inventario_porciones_precios, entrada
  manual tipificación 7 "REGISTRO PRECIOS", existencia y costo) cuando todos sus productos ya tienen número real.

  Anular: solo si ninguna unidad de la factura ha salido (los lotes siguen completos); devuelve el stock y el
  costo anterior. En el escritorio el agente la reversa (como "eliminar" del formulario del escritorio).
"""
from datetime import date
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.bodega_guard import Bodega, bodega_de_sede
from app.services import bodega_central as bc
from app.services import lotes, sede_maestros, sede_pedidos
from app.services.stock import apply_stock_move

MAX_LINEAS = 300
ESTADOS_ESCRITORIO = {"NO_APLICA": "Solo web", "PENDIENTE": "Pendiente de bajar al escritorio",
                      "APLICADA": "Aplicada en el escritorio", "ERROR": "Error en el escritorio",
                      "REVERSA": "Anulación pendiente en el escritorio", "REVERTIDA": "Anulada en el escritorio"}


def _r(v: float, n: int = 2) -> float:
    return round(float(v or 0) + 0.0, n)


async def _insumo(db: AsyncSession, cid: int, dish_id: int) -> Optional[int]:
    items = (await db.execute(text(
        "SELECT id_item FROM inventario_porciones_plato WHERE company_id = :c AND id_plato = :d"),
        {"c": cid, "d": dish_id})).scalars().all()
    if len(items) == 1:
        return int(items[0])
    return None


async def es_drogueria(db: AsyncSession, cid: int) -> bool:
    return int((await db.execute(text("SELECT business_profile_id FROM companies WHERE id_company = :c"),
                                 {"c": cid})).scalar() or 0) == 3


# ─── Productos para la factura ───────────────────────────────────────────────

async def productos(db: AsyncSession, cid: int) -> list[dict]:
    """Productos que se pueden comprar (un solo insumo) con su último costo registrado (fecha y proveedor)."""
    filas = (await db.execute(text("""
        SELECT d.id, d.name, d.product_code, d.price, d.product_cost, c.name AS categoria,
               COALESCE(d.active, 0) AS active, IF(COALESCE(d.extra_print, '0') = '1', 1, 0) AS unitario,
               COALESCE(iap.cantidad_actual, 0) AS stock
        FROM pos_dishes d
        JOIN inventario_porciones_plato ip ON ip.company_id = d.company_id AND ip.id_plato = d.id
        LEFT JOIN pos_dish_categories c ON c.company_id = d.company_id AND c.id = d.category_id
        LEFT JOIN inventario_actual_porciones iap ON iap.company_id = d.company_id AND iap.id_item = ip.id_item
        WHERE d.company_id = :c
        GROUP BY d.id
        HAVING COUNT(DISTINCT ip.id_item) = 1
        ORDER BY d.name
    """), {"c": cid})).mappings().all()
    ultimos = {int(f["dish_id"]): f for f in (await db.execute(text("""
        SELECT x.dish_id, x.valor_con_descuento, f.fecha, s.name AS proveedor
        FROM facturas_proveedor_detalle x
        JOIN facturas_proveedor f ON f.id = x.factura_id AND f.estado = 'ACTIVA'
        LEFT JOIN suppliers s ON s.company_id = f.company_id AND s.id_proveedor = f.id_proveedor
        WHERE x.company_id = :c AND x.id = (SELECT MAX(y.id) FROM facturas_proveedor_detalle y
                                            JOIN facturas_proveedor g ON g.id = y.factura_id AND g.estado = 'ACTIVA'
                                            WHERE y.company_id = x.company_id AND y.dish_id = x.dish_id)
    """), {"c": cid})).mappings().all()}
    out = []
    for f in filas:
        u = ultimos.get(int(f["id"]))
        out.append({"id": int(f["id"]), "name": f["name"], "product_code": f["product_code"],
                    "price": int(f["price"] or 0), "product_cost": float(f["product_cost"] or 0),
                    "categoria": f["categoria"], "activo": int(f["active"] or 0) == 0, "unitario": bool(f["unitario"]),
                    "stock": float(f["stock"] or 0),
                    "ultimo_costo": float(u["valor_con_descuento"]) if u else None,
                    "ultima_fecha": u["fecha"].isoformat() if u and u["fecha"] else None,
                    "ultimo_proveedor": u["proveedor"] if u else None})
    return out


# ─── Registrar ───────────────────────────────────────────────────────────────

async def crear(db: AsyncSession, emp: Bodega, d: dict) -> dict:
    cid = emp.id
    lineas = d.get("lineas") or []
    if not lineas:
        raise HTTPException(status_code=422, detail="Agregue al menos un producto a la factura")
    if len(lineas) > MAX_LINEAS:
        raise HTTPException(status_code=422, detail=f"Máximo {MAX_LINEAS} productos por factura")
    proveedor = await bc.proveedor_valido(db, cid, d.get("id_proveedor"), obligatorio=True)
    nro = (d.get("nro_factura") or "").strip().upper()[:40]
    if not nro:
        raise HTTPException(status_code=422, detail="Digite el número de la factura del proveedor")
    if (await db.execute(text("""
        SELECT 1 FROM facturas_proveedor WHERE company_id = :c AND id_proveedor = :p AND nro_factura = :n
          AND estado = 'ACTIVA' LIMIT 1
    """), {"c": cid, "p": proveedor, "n": nro})).scalar():
        raise HTTPException(status_code=409, detail=f"La factura {nro} de este proveedor ya está registrada")
    fecha = d.get("fecha") or date.today()
    if fecha > date.today():
        raise HTTPException(status_code=422, detail="La fecha de la factura no puede ser futura")
    drogueria = await es_drogueria(db, cid)
    unitario = await bc.cargue_unitario(db, cid)
    con_escritorio = await sede_pedidos.tiene_sede(db, cid)
    administrada = bool(await bodega_de_sede(db, cid))

    vistos, preparadas = set(), []
    for n, ln in enumerate(lineas, start=1):
        dish_id = int(ln["dish_id"])
        if dish_id in vistos:
            raise HTTPException(status_code=422, detail=f"Línea {n}: el producto está repetido en la factura")
        vistos.add(dish_id)
        prod = (await db.execute(text(
            "SELECT id, name, product_code, product_cost FROM pos_dishes WHERE company_id = :c AND id = :d"),
            {"c": cid, "d": dish_id})).mappings().first()
        if not prod:
            raise HTTPException(status_code=404, detail=f"Línea {n}: producto no encontrado")
        item = await _insumo(db, cid, dish_id)
        if not item:
            raise HTTPException(status_code=422, detail=f"Línea {n}: «{prod['name']}» lleva receta; "
                                                        "solo se compran productos que son su propio insumo")
        cantidad = float(ln["cantidad"])
        valor = float(ln["valor_unitario"])
        porc = float(ln.get("porc_descuento") or 0)
        con_desc = valor * (1 - porc / 100)
        vence = ln.get("fecha_vence") if drogueria else None
        if drogueria and not vence:
            raise HTTPException(status_code=422, detail=f"Línea {n}: «{prod['name']}» — digite la fecha de vencimiento del lote")
        imeis = [bc.limpiar_codigo(x) for x in (ln.get("imeis") or [])]
        if imeis:
            if not unitario:
                raise HTTPException(status_code=409, detail="Los IMEI por unidad solo aplican con el cargue unitario activo")
            if any(not x for x in imeis):
                raise HTTPException(status_code=422, detail=f"Línea {n}: hay IMEI vacíos")
            if len(imeis) != int(cantidad) or cantidad != int(cantidad):
                raise HTTPException(status_code=422, detail=f"Línea {n}: digite un IMEI por cada unidad ({int(cantidad)})")
        preparadas.append({"n": n, "prod": dict(prod), "item": item, "cantidad": cantidad, "valor": valor,
                           "porc": porc, "con_desc": con_desc, "vence": vence, "imeis": imeis})

    todos = [x for p in preparadas for x in p["imeis"]]
    repetidos = sorted({x for x in todos if todos.count(x) > 1})
    if repetidos:
        raise HTTPException(status_code=422, detail=f"IMEI repetidos en la factura: {', '.join(repetidos[:10])}")
    if todos:
        usados = await bc.codigos_usados(db, [cid], todos)
        if usados:
            raise HTTPException(status_code=409, detail=f"Estos IMEI ya existen como producto: {', '.join(list(usados)[:10])}")

    numero = int((await db.execute(text(
        "SELECT COALESCE(MAX(numero), 0) + 1 FROM facturas_proveedor WHERE company_id = :c FOR UPDATE"),
        {"c": cid})).scalar())
    subtotal = sum(p["valor"] * p["cantidad"] for p in preparadas)
    total = sum(p["con_desc"] * p["cantidad"] for p in preparadas)
    res = await db.execute(text("""
        INSERT INTO facturas_proveedor (company_id, numero, id_proveedor, nro_factura, fecha, observacion, subtotal,
                                        descuento, total, estado, escritorio_estado, usuario_id, usuario, ip)
        VALUES (:c, :num, :p, :n, :f, :obs, :sub, :desc, :tot, 'ACTIVA', :esc, :uid, :u, :ip)
    """), {"c": cid, "num": numero, "p": proveedor, "n": nro, "f": fecha.isoformat(),
           "obs": (d.get("observacion") or "").strip()[:255] or None, "sub": _r(subtotal), "desc": _r(subtotal - total),
           "tot": _r(total), "esc": "PENDIENTE" if con_escritorio else "NO_APLICA", "uid": emp.user.id,
           "u": emp.usuario, "ip": emp.ip})
    fid = int(res.lastrowid)
    obs = f"Factura proveedor {nro}"

    item_n = 0
    for p in preparadas:
        # Caso especial: un producto por cada IMEI (nombre + IMEI, cantidad 1, desactivar al vender)
        destinos = []
        if p["imeis"]:
            base = await bc._producto(db, cid, p["prod"]["id"])
            siguiente = await bc._nuevo_id(db, cid, con_escritorio)
            for imei in p["imeis"]:
                nuevo = await bc.crear_producto(db, cid, {
                    **base, "name": f"{base['name']} {imei}"[:250], "product_code": imei, "extra_print": 1,
                    "product_cost": p["con_desc"], "id_proveedor": proveedor, "fecha_vence": p["vence"],
                }, nuevo_id=siguiente, con_escritorio=con_escritorio)
                siguiente += 1
                destinos.append((nuevo, nuevo, f"{base['name']} {imei}"[:250], imei, 1.0, imei))
        else:
            destinos.append((p["prod"]["id"], p["item"], p["prod"]["name"], p["prod"]["product_code"], p["cantidad"], None))
        for dish_id, item, nombre, codigo, cantidad, imei in destinos:
            item_n += 1
            costo_anterior = 0.0 if imei else float((await db.execute(text(
                "SELECT product_cost FROM pos_dishes WHERE company_id = :c AND id = :d"), {"c": cid, "d": dish_id})).scalar() or 0)
            eid = await bc.registrar_entrada(db, emp, dish_id, cantidad, proveedor, obs, ref_tipo="factura_proveedor",
                                             fecha=fecha.isoformat(), item=item,
                                             lote={"costo": p["con_desc"], "fecha_vence": p["vence"], "origen": "FACTURA",
                                                   "id_proveedor": proveedor, "nro_factura": nro})
            lote_id = (await db.execute(text("""
                SELECT MAX(id) FROM inv_lotes WHERE company_id = :c AND id_item = :i AND origen = 'FACTURA' AND origen_id = :e
            """), {"c": cid, "i": item, "e": eid})).scalar()
            await db.execute(text("""
                INSERT INTO facturas_proveedor_detalle
                    (factura_id, company_id, item, dish_id, id_item, nombre, codigo, imei, cantidad, valor_unitario,
                     porc_descuento, valor_con_descuento, total, costo_anterior, fecha_vence, lote_id)
                VALUES (:f, :c, :n, :d, :i, :nom, :cod, :imei, :q, :v, :porc, :vd, :tot, :ca, :fv, :lote)
            """), {"f": fid, "c": cid, "n": item_n, "d": dish_id, "i": item, "nom": nombre, "cod": codigo, "imei": imei,
                   "q": cantidad, "v": p["valor"], "porc": p["porc"], "vd": p["con_desc"],
                   "tot": _r(p["con_desc"] * cantidad), "ca": costo_anterior, "fv": p["vence"], "lote": lote_id})
            if not administrada and round(costo_anterior, 4) != round(p["con_desc"], 4):
                await bc._aplicar_valores(db, cid, dish_id, [{"campo": "product_cost", "nuevo": p["con_desc"]}])
            await db.execute(text(
                "UPDATE supply_items SET valor_und_compra = :v, synced = 0 WHERE company_id = :c AND id_item = :i"),
                {"v": p["con_desc"], "c": cid, "i": item})
            if drogueria:
                await _vencimiento_proximo(db, cid, item)
    return {"ok": True, "id": fid, "numero": numero, "total": _r(total),
            "escritorio": "PENDIENTE" if con_escritorio else "NO_APLICA"}


async def _vencimiento_proximo(db: AsyncSession, cid: int, item: int) -> None:
    """Droguerías: la fecha de vencimiento del producto es la del lote con existencia que vence primero."""
    vence = (await db.execute(text(
        "SELECT MIN(fecha_vence) FROM inv_lotes WHERE company_id = :c AND id_item = :i AND cantidad_disponible > 0"),
        {"c": cid, "i": item})).scalar()
    if vence:
        await db.execute(text("UPDATE supply_items SET fecha_vence = :v, synced = 0 WHERE company_id = :c AND id_item = :i"),
                         {"v": vence, "c": cid, "i": item})
        await db.execute(text(
            "UPDATE inventario_actual_porciones SET fecha_vence = :v, enviada_mysql = 0 WHERE company_id = :c AND id_item = :i"),
            {"v": vence, "c": cid, "i": item})


# ─── Anular ──────────────────────────────────────────────────────────────────

async def anular(db: AsyncSession, emp: Bodega, fid: int, motivo: str) -> dict:
    cid = emp.id
    f = (await db.execute(text("SELECT * FROM facturas_proveedor WHERE id = :f AND company_id = :c FOR UPDATE"),
                          {"f": fid, "c": cid})).mappings().first()
    if not f:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    if f["estado"] != "ACTIVA":
        raise HTTPException(status_code=409, detail="La factura ya está anulada")
    motivo = (motivo or "").strip()
    if len(motivo) < 5:
        raise HTTPException(status_code=422, detail="Escriba el motivo de la anulación")
    lineas = (await db.execute(text(
        "SELECT * FROM facturas_proveedor_detalle WHERE factura_id = :f ORDER BY item"), {"f": fid})).mappings().all()
    # Solo si nada de lo que entró ha salido (vendido, trasladado o ajustado)
    for ln in lineas:
        lote = (await db.execute(text("SELECT cantidad_inicial, cantidad_disponible FROM inv_lotes WHERE id = :l FOR UPDATE"),
                                 {"l": ln["lote_id"]})).first() if ln["lote_id"] else None
        if lote and float(lote[1]) + lotes.CERO < float(lote[0]):
            raise HTTPException(status_code=409, detail=f"No se puede anular: ya salieron unidades de «{ln['nombre']}» "
                                                        "(vendidas o trasladadas). Registre una devolución al proveedor.")
    administrada = bool(await bodega_de_sede(db, cid))
    hoy = date.today().isoformat()
    for ln in lineas:
        res = await db.execute(text("""
            INSERT INTO inventory_exits (id_salida, id_item, id_proveedor, company_id, fecha, cantidad, cod_empleado,
                                         observacion, autorizada, synced, updated_at)
            VALUES ((SELECT COALESCE(MAX(id_salida), 0) + 1 FROM inventory_exits x2 WHERE x2.company_id = :c),
                    :i, :p, :c, :f, :q, :emp, :obs, 1, 0, NOW())
        """), {"c": cid, "i": ln["id_item"], "p": f["id_proveedor"], "f": hoy, "q": float(ln["cantidad"]),
               "emp": (emp.user.email or "")[:50], "obs": f"Anulación factura proveedor {f['nro_factura']}"[:255]})
        await db.flush()
        await apply_stock_move(db, cid, int(ln["id_item"]), -float(ln["cantidad"]), "exit", "factura_proveedor_anulada",
                               res.lastrowid, hoy, f"Anulación factura proveedor {f['nro_factura']}", emp.user.id,
                               lote={"solo_lote": ln["lote_id"]} if ln["lote_id"] else None)
        actual = float((await db.execute(text("SELECT product_cost FROM pos_dishes WHERE company_id = :c AND id = :d"),
                                         {"c": cid, "d": ln["dish_id"]})).scalar() or 0)
        if not administrada and round(actual, 4) == round(float(ln["valor_con_descuento"]), 4):
            await bc._aplicar_valores(db, cid, int(ln["dish_id"]),
                                      [{"campo": "product_cost", "nuevo": float(ln["costo_anterior"] or 0)}])
        if ln["imei"]:              # la unidad con IMEI no existió: el producto queda inactivo
            await db.execute(text("UPDATE pos_dishes SET active = 1, synced = 0, updated_at = NOW() "
                                  "WHERE company_id = :c AND id = :d"), {"c": cid, "d": ln["dish_id"]})
    # Con escritorio siempre REVERSA: el agente deshace solo lo que alcanzó a aplicar (lleva su propio registro),
    # así no queda nada a medias si la estaba bajando en ese momento.
    esc = "REVERSA" if f["escritorio_estado"] in ("PENDIENTE", "APLICADA") else f["escritorio_estado"]
    await db.execute(text("""
        UPDATE facturas_proveedor SET estado = 'ANULADA', anulada_en = NOW(), anulada_por = :u, anulada_motivo = :m,
               escritorio_estado = :e WHERE id = :f
    """), {"u": emp.usuario, "m": motivo[:255], "e": esc, "f": fid})
    return {"ok": True, "escritorio": esc}


# ─── Consultas ───────────────────────────────────────────────────────────────

async def listar(db: AsyncSession, cid: int, desde: Optional[date], hasta: Optional[date],
                 id_proveedor: Optional[int], texto: Optional[str]) -> list[dict]:
    cond, p = ["f.company_id = :c"], {"c": cid}
    if desde:
        cond.append("f.fecha >= :d"); p["d"] = desde.isoformat()
    if hasta:
        cond.append("f.fecha <= :h"); p["h"] = hasta.isoformat()
    if id_proveedor:
        cond.append("f.id_proveedor = :p"); p["p"] = int(id_proveedor)
    if texto:
        cond.append("(f.nro_factura LIKE :t OR EXISTS (SELECT 1 FROM facturas_proveedor_detalle x WHERE x.factura_id = f.id "
                    "AND (x.nombre LIKE :t OR x.codigo LIKE :t OR x.imei LIKE :t)))")
        p["t"] = f"%{texto.strip()[:60]}%"
    filas = (await db.execute(text(f"""
        SELECT f.id, f.numero, f.nro_factura, f.fecha, f.subtotal, f.descuento, f.total, f.estado, f.escritorio_estado,
               f.escritorio_error, f.usuario, f.observacion, s.name AS proveedor,
               (SELECT COUNT(*) FROM facturas_proveedor_detalle x WHERE x.factura_id = f.id) AS lineas
        FROM facturas_proveedor f
        LEFT JOIN suppliers s ON s.company_id = f.company_id AND s.id_proveedor = f.id_proveedor
        WHERE {' AND '.join(cond)}
        ORDER BY f.fecha DESC, f.numero DESC LIMIT 500
    """), p)).mappings().all()
    return [{**dict(f), "fecha": f["fecha"].isoformat(), "subtotal": float(f["subtotal"]), "descuento": float(f["descuento"]),
             "total": float(f["total"]), "escritorio_texto": ESTADOS_ESCRITORIO.get(f["escritorio_estado"], "")} for f in filas]


async def detalle(db: AsyncSession, cid: int, fid: int) -> dict:
    f = (await db.execute(text("""
        SELECT f.*, s.name AS proveedor, s.nit AS proveedor_nit FROM facturas_proveedor f
        LEFT JOIN suppliers s ON s.company_id = f.company_id AND s.id_proveedor = f.id_proveedor
        WHERE f.id = :f AND f.company_id = :c
    """), {"f": fid, "c": cid})).mappings().first()
    if not f:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    lineas = (await db.execute(text("""
        SELECT x.item, x.dish_id, x.nombre, x.codigo, x.imei, x.cantidad, x.valor_unitario, x.porc_descuento,
               x.valor_con_descuento, x.total, x.costo_anterior, x.fecha_vence, l.cantidad_disponible
        FROM facturas_proveedor_detalle x LEFT JOIN inv_lotes l ON l.id = x.lote_id
        WHERE x.factura_id = :f ORDER BY x.item
    """), {"f": fid})).mappings().all()
    cab = {k: f[k] for k in ("id", "numero", "nro_factura", "observacion", "estado", "escritorio_estado", "escritorio_error",
                             "usuario", "anulada_por", "anulada_motivo", "proveedor", "proveedor_nit")}
    return {**cab, "fecha": f["fecha"].isoformat(), "subtotal": float(f["subtotal"]), "descuento": float(f["descuento"]),
            "total": float(f["total"]), "creada": f["created_at"].isoformat(sep=" ", timespec="minutes"),
            "anulada_en": f["anulada_en"].isoformat(sep=" ", timespec="minutes") if f["anulada_en"] else None,
            "escritorio_texto": ESTADOS_ESCRITORIO.get(f["escritorio_estado"], ""),
            "lineas": [{**dict(x), "cantidad": float(x["cantidad"]), "valor_unitario": float(x["valor_unitario"]),
                        "porc_descuento": float(x["porc_descuento"]), "valor_con_descuento": float(x["valor_con_descuento"]),
                        "total": float(x["total"]), "costo_anterior": float(x["costo_anterior"]),
                        "fecha_vence": x["fecha_vence"].isoformat() if x["fecha_vence"] else None,
                        "disponible": float(x["cantidad_disponible"]) if x["cantidad_disponible"] is not None else None}
                       for x in lineas]}


# ─── Agente (empresa con escritorio) ─────────────────────────────────────────

async def tareas_agente(db: AsyncSession, cid: int) -> list[dict]:
    """Facturas por bajar (APLICAR) o por reversar (REVERSA). Una factura espera mientras algún producto o el
    proveedor aún tenga número provisional (no ha bajado con la sincronización del catálogo)."""
    facturas = (await db.execute(text("""
        SELECT f.id, f.numero, f.nro_factura, f.fecha, f.id_proveedor, f.observacion, f.escritorio_estado,
               f.escritorio_registro
        FROM facturas_proveedor f
        WHERE f.company_id = :c AND f.escritorio_estado IN ('PENDIENTE', 'REVERSA')
        ORDER BY f.id LIMIT 20
    """), {"c": cid})).mappings().all()
    out = []
    for f in facturas:
        lineas = (await db.execute(text("""
            SELECT x.item, x.dish_id, x.id_item, x.nombre, x.codigo, x.cantidad, x.valor_con_descuento, x.costo_anterior,
                   x.total, x.fecha_vence
            FROM facturas_proveedor_detalle x WHERE x.factura_id = :f ORDER BY x.item
        """), {"f": f["id"]})).mappings().all()
        if sede_maestros.es_provisional(f["id_proveedor"]) or any(
                sede_maestros.es_provisional(x["dish_id"]) or sede_maestros.es_provisional(x["id_item"]) for x in lineas):
            continue
        out.append({"id": int(f["id"]), "tarea": "APLICAR" if f["escritorio_estado"] == "PENDIENTE" else "REVERSA",
                    "numero": int(f["numero"]), "nro_factura": f["nro_factura"], "fecha": f["fecha"].isoformat(),
                    "id_proveedor": int(f["id_proveedor"]), "observacion": f["observacion"] or "",
                    "registro": f["escritorio_registro"],
                    "lineas": [{"item": int(x["item"]), "id_plato": int(x["dish_id"]), "id_item": int(x["id_item"]),
                                "nombre": x["nombre"], "codigo": x["codigo"] or "", "cantidad": float(x["cantidad"]),
                                "precio": float(x["valor_con_descuento"]), "precio_anterior": float(x["costo_anterior"]),
                                "total": float(x["total"]),
                                "fecha_vence": x["fecha_vence"].isoformat() if x["fecha_vence"] else None}
                               for x in lineas]})
    return out


async def resultado_agente(db: AsyncSession, cid: int, r: dict) -> dict:
    f = (await db.execute(text(
        "SELECT escritorio_estado FROM facturas_proveedor WHERE id = :f AND company_id = :c FOR UPDATE"),
        {"f": int(r["id"]), "c": cid})).scalar()
    if f is None:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    esperado = "PENDIENTE" if r["tarea"] == "APLICAR" else "REVERSA"
    if f != esperado:
        return {"ok": True, "ignorado": True}
    if r.get("ok"):
        nuevo = "APLICADA" if r["tarea"] == "APLICAR" else "REVERTIDA"
        await db.execute(text("""
            UPDATE facturas_proveedor SET escritorio_estado = :e, escritorio_registro = COALESCE(:reg, escritorio_registro),
                   escritorio_error = NULL, escritorio_en = NOW() WHERE id = :f
        """), {"e": nuevo, "reg": r.get("registro"), "f": int(r["id"])})
    else:
        # queda pendiente (se reintenta) con el error a la vista
        await db.execute(text(
            "UPDATE facturas_proveedor SET escritorio_error = :m, escritorio_en = NOW() WHERE id = :f"),
            {"m": (r.get("error") or "Error en el escritorio")[:255], "f": int(r["id"])})
    return {"ok": True}
