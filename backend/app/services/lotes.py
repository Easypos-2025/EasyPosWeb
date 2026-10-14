"""
Costeo del inventario por lotes — PEPS (primero en entrar, primero en salir).

  Cada entrada al inventario crea un LOTE con su costo unitario (y su fecha de vencimiento en droguerías):
  Factura de Proveedor (costo = valor con descuento), entradas manuales, traslados (el lote llega con el costo
  con que salió del origen), ajustes de inventario físico. Cada salida (venta, salida manual, traslado, físico)
  gasta los lotes del más viejo al más nuevo y deja en inv_lote_consumos cuánto salió de cada lote y a qué costo:
  con eso la utilidad y el inventario valorizado salen exactos (4 ventiladores a $30.000 y 2 a $32.000).

  El stock que ya existía antes de los lotes entra como un lote SALDO_INICIAL al costo actual del producto, la
  primera vez que el artículo se mueve. Si una salida no encuentra lotes (stock en negativo) se costea al costo
  actual del producto (consumo sin lote).

  Solo aplica a los insumos con control de stock (supply_items.control_stock = 1), igual que apply_stock_move.
  No hace commit: va en la misma transacción del movimiento.
"""
from datetime import date
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

CERO = 0.00005


def _fecha(f) -> str:
    if not f:
        return date.today().isoformat()
    return str(f)[:10]


async def _insumo(db: AsyncSession, cid: int, id_item: int) -> Optional[dict]:
    fila = (await db.execute(text("""
        SELECT si.control_stock, si.cost_price, COALESCE(iap.cantidad_actual, 0) AS cantidad
        FROM supply_items si
        LEFT JOIN inventario_actual_porciones iap ON iap.company_id = si.company_id AND iap.id_item = si.id_item
        WHERE si.company_id = :c AND si.id_item = :i LIMIT 1
    """), {"c": cid, "i": id_item})).mappings().first()
    return dict(fila) if fila else None


async def _disponible(db: AsyncSession, cid: int, id_item: int) -> float:
    return float((await db.execute(text(
        "SELECT COALESCE(SUM(cantidad_disponible), 0) FROM inv_lotes WHERE company_id = :c AND id_item = :i"),
        {"c": cid, "i": id_item})).scalar() or 0)


async def _saldo_inicial(db: AsyncSession, cid: int, id_item: int, cantidad: float, costo: float) -> None:
    """La primera vez que el artículo se mueve, su stock previo queda como un lote al costo actual."""
    if cantidad <= CERO:
        return
    if (await db.execute(text("SELECT 1 FROM inv_lotes WHERE company_id = :c AND id_item = :i LIMIT 1"),
                         {"c": cid, "i": id_item})).scalar():
        return
    await crear_lote(db, cid, id_item, cantidad, costo, "SALDO_INICIAL")


async def crear_lote(db: AsyncSession, cid: int, id_item: int, cantidad: float, costo: float, origen: str,
                     origen_id: Optional[int] = None, fecha=None, fecha_vence=None, id_proveedor: Optional[int] = None,
                     nro_factura: Optional[str] = None) -> int:
    res = await db.execute(text("""
        INSERT INTO inv_lotes (company_id, id_item, fecha, origen, origen_id, costo_unitario, cantidad_inicial,
                               cantidad_disponible, fecha_vence, id_proveedor, nro_factura)
        VALUES (:c, :i, :f, :o, :oid, :costo, :q, :q, :fv, :p, :nf)
    """), {"c": cid, "i": id_item, "f": _fecha(fecha), "o": origen[:20], "oid": origen_id, "costo": float(costo or 0),
           "q": float(cantidad), "fv": fecha_vence or None, "p": id_proveedor, "nf": (nro_factura or None) and str(nro_factura)[:40]})
    return int(res.lastrowid)


async def _consumir(db: AsyncSession, cid: int, id_item: int, cantidad: float, costo_actual: float, ref_tipo: str,
                    ref_id: Optional[int], fecha, clave: Optional[str], solo_lote: Optional[int] = None) -> list[dict]:
    """Gasta `cantidad` de los lotes (PEPS). Devuelve [{lote_id, cantidad, costo, fecha_vence}]."""
    filtro = " AND id = :lote" if solo_lote else ""
    lotes = (await db.execute(text(f"""
        SELECT id, cantidad_disponible, costo_unitario, fecha_vence FROM inv_lotes
        WHERE company_id = :c AND id_item = :i AND cantidad_disponible > 0{filtro}
        ORDER BY fecha, id FOR UPDATE
    """), {"c": cid, "i": id_item, "lote": solo_lote})).mappings().all()
    pendiente, salidas = float(cantidad), []
    for lt in lotes:
        if pendiente <= CERO:
            break
        toma = min(pendiente, float(lt["cantidad_disponible"]))
        await db.execute(text("UPDATE inv_lotes SET cantidad_disponible = cantidad_disponible - :q WHERE id = :id"),
                         {"q": toma, "id": lt["id"]})
        salidas.append({"lote_id": int(lt["id"]), "cantidad": toma, "costo": float(lt["costo_unitario"] or 0),
                        "fecha_vence": lt["fecha_vence"]})
        pendiente -= toma
    if pendiente > CERO:
        salidas.append({"lote_id": None, "cantidad": pendiente, "costo": float(costo_actual or 0), "fecha_vence": None})
    for s in salidas:
        await db.execute(text("""
            INSERT INTO inv_lote_consumos (company_id, lote_id, id_item, fecha, cantidad, costo_unitario, ref_tipo,
                                           ref_id, clave)
            VALUES (:c, :l, :i, :f, :q, :costo, :rt, :rid, :k)
        """), {"c": cid, "l": s["lote_id"], "i": id_item, "f": _fecha(fecha), "q": s["cantidad"], "costo": s["costo"],
               "rt": (ref_tipo or "salida")[:30], "rid": ref_id, "k": clave})
    return salidas


async def registrar(db: AsyncSession, cid: int, id_item: int, qty: float, ref_tipo: str, ref_id: Optional[int] = None,
                    fecha=None, cantidad_antes: Optional[float] = None, costo: Optional[float] = None,
                    origen: Optional[str] = None, fecha_vence=None, id_proveedor: Optional[int] = None,
                    nro_factura: Optional[str] = None, clave: Optional[str] = None,
                    copiar_de: Optional[tuple] = None, solo_lote: Optional[int] = None) -> list[dict]:
    """Movimiento de `qty` (+ entrada, − salida) en los lotes del artículo. Llamarlo ANTES de cambiar
    inventario_actual_porciones (o pasar cantidad_antes).
      costo / fecha_vence / id_proveedor / nro_factura: datos del lote de una entrada (Factura de Proveedor).
      copiar_de = (empresa, clave): la entrada toma los costos de lo que salió del origen con esa clave (traslados).
      clave: marca los consumos de una salida para que el destino de un traslado copie su costo.
    Devuelve lo consumido (salidas) o [] (entradas)."""
    info = await _insumo(db, cid, id_item)
    if not info or not info["control_stock"] or abs(qty) <= CERO:
        return []
    costo_actual = float(info["cost_price"] or 0)
    antes = float(info["cantidad"] if cantidad_antes is None else cantidad_antes)
    await _saldo_inicial(db, cid, id_item, antes, costo_actual)

    if qty < 0:
        return await _consumir(db, cid, id_item, -qty, costo_actual, ref_tipo, ref_id, fecha, clave, solo_lote)

    origen = (origen or {"traslado_bodega": "TRASLADO", "physical": "AJUSTE"}.get(ref_tipo, "ENTRADA"))
    if copiar_de:
        empresa, clave_origen = copiar_de
        restante = float(qty)
        filas = (await db.execute(text("""
            SELECT c.costo_unitario, l.fecha_vence, SUM(c.cantidad) AS cantidad
            FROM inv_lote_consumos c LEFT JOIN inv_lotes l ON l.id = c.lote_id
            WHERE c.company_id = :c AND c.clave = :k GROUP BY c.costo_unitario, l.fecha_vence ORDER BY MIN(c.id)
        """), {"c": empresa, "k": clave_origen})).mappings().all()
        for f in filas:
            if restante <= CERO:
                break
            q = min(restante, float(f["cantidad"] or 0))
            if q > CERO:
                await crear_lote(db, cid, id_item, q, float(f["costo_unitario"] or 0), origen, ref_id, fecha,
                                 f["fecha_vence"], id_proveedor, nro_factura)
                restante -= q
        if restante > CERO:
            await crear_lote(db, cid, id_item, restante, costo if costo is not None else costo_actual, origen, ref_id,
                             fecha, fecha_vence, id_proveedor, nro_factura)
        return []
    await crear_lote(db, cid, id_item, qty, costo if costo is not None else costo_actual, origen, ref_id, fecha,
                     fecha_vence, id_proveedor, nro_factura)
    return []


async def ajustar_fisico(db: AsyncSession, cid: int, id_item: int, cantidad_nueva: float, cantidad_antes: float,
                         ref_id: Optional[int], fecha) -> None:
    """Inventario físico: los lotes quedan sumando lo contado (faltante → se gasta PEPS; sobrante → lote AJUSTE)."""
    info = await _insumo(db, cid, id_item)
    if not info or not info["control_stock"]:
        return
    costo_actual = float(info["cost_price"] or 0)
    await _saldo_inicial(db, cid, id_item, cantidad_antes, costo_actual)
    diferencia = float(cantidad_nueva) - await _disponible(db, cid, id_item)
    if diferencia > CERO:
        await crear_lote(db, cid, id_item, diferencia, costo_actual, "AJUSTE", ref_id, fecha)
    elif diferencia < -CERO:
        await _consumir(db, cid, id_item, -diferencia, costo_actual, "physical", ref_id, fecha, None)


# ─── Consultas ───────────────────────────────────────────────────────────────

async def lotes_de(db: AsyncSession, cid: int, id_item: int, solo_disponibles: bool = True) -> list[dict]:
    filas = (await db.execute(text(f"""
        SELECT l.id, l.fecha, l.origen, l.costo_unitario, l.cantidad_inicial, l.cantidad_disponible, l.fecha_vence,
               l.nro_factura, s.name AS proveedor
        FROM inv_lotes l
        LEFT JOIN suppliers s ON s.company_id = l.company_id AND s.id_proveedor = l.id_proveedor
        WHERE l.company_id = :c AND l.id_item = :i {"AND l.cantidad_disponible > 0" if solo_disponibles else ""}
        ORDER BY l.fecha, l.id
    """), {"c": cid, "i": id_item})).mappings().all()
    return [{"id": int(f["id"]), "fecha": f["fecha"].isoformat() if f["fecha"] else None, "origen": f["origen"],
             "costo": float(f["costo_unitario"] or 0), "cantidad_inicial": float(f["cantidad_inicial"] or 0),
             "disponible": float(f["cantidad_disponible"] or 0),
             "vence": f["fecha_vence"].isoformat() if f["fecha_vence"] else None,
             "nro_factura": f["nro_factura"], "proveedor": f["proveedor"]} for f in filas]


async def resumen_por_item(db: AsyncSession, cid: int) -> dict:
    """{id_item: {valor, lotes, vence_proximo}} de los lotes con existencia (inventario valorizado)."""
    filas = (await db.execute(text("""
        SELECT id_item, SUM(cantidad_disponible * costo_unitario) AS valor, COUNT(*) AS lotes, MIN(fecha_vence) AS vence
        FROM inv_lotes WHERE company_id = :c AND cantidad_disponible > 0 GROUP BY id_item
    """), {"c": cid})).mappings().all()
    return {int(f["id_item"]): {"valor": float(f["valor"] or 0), "lotes": int(f["lotes"] or 0),
                                "vence": f["vence"].isoformat() if f["vence"] else None} for f in filas}
