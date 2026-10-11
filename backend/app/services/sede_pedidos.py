"""
Pedidos web hacia el escritorio (empresas con Agente Local activo).

En esas empresas "Enviar a cocina" NO envía: crea un LOTE pendiente (pos_sede_lotes / _items) con la
foto exacta de los ítems y sus precios. El agente de la sede lo baja, el cajero lo acepta o lo rechaza
(form VB6 o panel de la mini-app) y el agente lo pasa a los temporales del escritorio, que imprime.

  · Nada pasa sin intervención humana (pedido nuevo y productos agregados).
  · Ítem en lote pendiente: Sede_Pendiente = 1 en temp_detalle_comanda_parcial (datatemppos de la web):
    bloqueado, no sale en cocina (sin Hora_Plato) ni se cobra en la web.
  · APLICADO: el ítem queda enviado normal (Sede_Pendiente = 0, Impreso = 1, Hora_Plato).
  · RECHAZADO: los ítems salen del pedido en la nube (solo quedan en el histórico del lote); si era un
    pedido nuevo y no le queda nada, el pedido se elimina y la mesa queda libre.
  · Los lotes nunca se borran (histórico para reclamos).

La columna Sede_Pendiente solo se consulta en empresas con sede: las empresas solo web no dependen de ella.
"""
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_BOG = timezone(timedelta(hours=-5))         # misma hora que la comanda web (Hora_Plato)
ESTADOS_ABIERTOS = ("PENDIENTE", "RECIBIDO", "ACEPTADO", "ERROR")
MAX_ITEMS_LOTE = 200


async def envia_a_escritorio(db: AsyncSession, cid: int, order_number: Optional[str] = None) -> bool:
    """¿Lo que se envíe de este pedido pasa por la caja del escritorio?
    Sí cuando la empresa tiene Agente Local activo y su admin dejó "Enviar los pedidos web al
    escritorio" (company_configs.pedidos_web_escritorio) o cuando el pedido ya tiene algo enviado a
    la caja (un pedido no queda partido si el admin cambia la opción en pleno servicio)."""
    if not await tiene_sede(db, cid):
        return False
    activa = (await db.execute(text(
        "SELECT pedidos_web_escritorio FROM company_configs WHERE company_id = :c LIMIT 1"), {"c": cid})).scalar()
    if activa is None or int(activa):
        return True
    return bool(order_number) and bool((await db.execute(text(
        "SELECT 1 FROM pos_sede_lotes WHERE company_id = :c AND nro_pedido = :on LIMIT 1"),
        {"c": cid, "on": order_number})).scalar())


async def tiene_sede(db: AsyncSession, cid: int) -> bool:
    """La empresa tiene Agente Local activo: sus pedidos web pasan por la caja del escritorio."""
    return bool((await db.execute(text(
        "SELECT 1 FROM company_local_agents WHERE company_id = :c AND activo = 1 LIMIT 1"
    ), {"c": cid})).scalar())


def _hora(valor) -> str:
    return str(valor or "")[:20]


async def crear_lote(db: AsyncSession, db_temp: AsyncSession, cid: int, order_number: str, fecha,
                     es_nuevo: bool, enviado_por: Optional[str]) -> dict:
    """Crea el lote con los ítems aún no enviados (Salio = 0) y los deja pendientes.
    No hace commit: lo hace quien llama (los dos commits van juntos al final)."""
    orden = (await db_temp.execute(text("""
        SELECT Nro_Pedido, Mesa, Mesero, Id_Cliente, Nro_Comenzales FROM temp_comanda
        WHERE Nro_Pedido = :on AND company_id = :cid AND Nro_Factura = '0' AND Cancelado = 0 LIMIT 1
    """), {"on": order_number, "cid": cid})).mappings().first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    filas = (await db_temp.execute(text("""
        SELECT Item, Id_Plato, Descripcion, Cantidad, Valor, Novedad, Cambios, Producto_Personalizado
        FROM temp_detalle_comanda_parcial
        WHERE Nro_pedido = :on AND company_id = :cid AND Nro_Factura = '0' AND Mostrar = 1
          AND Salio = 0 AND Sede_Pendiente = 0
        ORDER BY Item
    """), {"on": order_number, "cid": cid})).mappings().all()
    if not filas:
        return {"lote_id": None, "items": 0}
    if len(filas) > MAX_ITEMS_LOTE:
        raise HTTPException(status_code=422, detail=f"El envío supera {MAX_ITEMS_LOTE} productos. Envíelo por partes.")

    items = [int(f["Item"]) for f in filas]
    ph = ", ".join(f":i{n}" for n in range(len(items)))
    pi = {f"i{n}": v for n, v in enumerate(items)}
    insumos: dict = {}
    for r in (await db_temp.execute(text(f"""
        SELECT Item, Id_Grupo, Id_Item, Cantidad, Posicion, Valor_Adicional_Armar
        FROM temp_plato_producto_parcial
        WHERE Nro_Pedido = :on AND company_id = :cid AND Item IN ({ph})
    """), {"on": order_number, "cid": cid, **pi})).mappings().all():
        insumos.setdefault(int(r["Item"]), []).append({
            "g": int(r["Id_Grupo"] or 0), "i": int(r["Id_Item"] or 0), "c": float(r["Cantidad"] or 0),
            "p": int(r["Posicion"] or 0), "v": float(r["Valor_Adicional_Armar"] or 0)})
    novedades: dict = {}
    for r in (await db_temp.execute(text(f"""
        SELECT Item, Cod_Categoria, Id_Novedad, Novedad FROM temp_novedades_plato_pedido
        WHERE Nro_Pedido = :on AND company_id = :cid AND Item IN ({ph})
    """), {"on": order_number, "cid": cid, **pi})).mappings().all():
        novedades.setdefault(int(r["Item"]), []).append({
            "cat": int(r["Cod_Categoria"] or 0), "id": int(r["Id_Novedad"] or 0), "txt": str(r["Novedad"] or "")[:250]})

    mesero = int(orden["Mesero"] or 0)
    nombre_mesero = (await db.execute(text(
        "SELECT name FROM pos_waiters WHERE id = :w AND company_id = :c"), {"w": mesero, "c": cid})).scalar()
    id_mesa = 0
    partes = order_number.split("-")
    if order_number.startswith("WEB-") and len(partes) >= 3 and partes[2].isdigit():
        id_mesa = int(partes[2])
    total = sum(int(f["Valor"] or 0) for f in filas)

    lote_id = (await db.execute(text("""
        INSERT INTO pos_sede_lotes
            (company_id, nro_pedido, tipo, canal, id_mesa, mesa, mesero, mesero_nombre, id_cliente, comensales,
             total, items, estado, enviado_por)
        VALUES (:c, :on, :tipo, 'MESA', :idm, :mesa, :mes, :mesn, :cli, :com, :tot, :n, 'PENDIENTE', :por)
    """), {"c": cid, "on": order_number, "tipo": "NUEVO" if es_nuevo else "AGREGAR", "idm": id_mesa,
           "mesa": (orden["Mesa"] or "")[:200], "mes": mesero, "mesn": (nombre_mesero or "")[:150] or None,
           "cli": int(orden["Id_Cliente"] or 1) or 1, "com": max(1, int(orden["Nro_Comenzales"] or 1)),
           "tot": total, "n": len(filas), "por": (enviado_por or "")[:150] or None})).lastrowid

    for f in filas:
        it = int(f["Item"])
        await db.execute(text("""
            INSERT INTO pos_sede_lote_items
                (lote_id, company_id, item, id_plato, descripcion, cantidad, valor, novedad, cambios,
                 producto_personalizado, insumos, novedades)
            VALUES (:l, :c, :it, :p, :d, :q, :v, :nov, :cam, :pp, :ins, :novs)
        """), {"l": lote_id, "c": cid, "it": it, "p": int(f["Id_Plato"]), "d": (f["Descripcion"] or "")[:255] or None,
               "q": float(f["Cantidad"] or 1), "v": int(f["Valor"] or 0), "nov": (f["Novedad"] or "")[:255] or None,
               "cam": (f["Cambios"] or "")[:255] or None, "pp": (f["Producto_Personalizado"] or "")[:1000] or None,
               "ins": json.dumps(insumos.get(it, [])), "novs": json.dumps(novedades.get(it, []))})

    await db_temp.execute(text(f"""
        UPDATE temp_detalle_comanda_parcial SET Salio = 1, Sede_Pendiente = 1
        WHERE Nro_pedido = :on AND company_id = :cid AND Nro_Factura = '0' AND Item IN ({ph})
    """), {"on": order_number, "cid": cid, **pi})
    if es_nuevo:
        await db_temp.execute(text(
            "UPDATE temp_comanda SET Salio = 1 WHERE Nro_Pedido = :on AND company_id = :cid"),
            {"on": order_number, "cid": cid})
    return {"lote_id": lote_id, "items": len(filas)}


async def item_pendiente(db_temp: AsyncSession, cid: int, order_number: str, item: int) -> bool:
    return bool((await db_temp.execute(text("""
        SELECT MAX(Sede_Pendiente) FROM temp_detalle_comanda_parcial
        WHERE Nro_pedido = :on AND company_id = :cid AND Item = :it AND Nro_Factura = '0'
    """), {"on": order_number, "cid": cid, "it": item})).scalar())


async def items_pendientes(db_temp: AsyncSession, cid: int, order_number: str) -> set:
    filas = (await db_temp.execute(text("""
        SELECT Item FROM temp_detalle_comanda_parcial
        WHERE Nro_pedido = :on AND company_id = :cid AND Nro_Factura = '0' AND Sede_Pendiente = 1
    """), {"on": order_number, "cid": cid})).all()
    return {int(f[0]) for f in filas}


async def pedidos_pendientes_caja(db: AsyncSession, cid: int) -> set:
    """Pedidos con algo enviado desde la web que la caja aún no ha aceptado (para las tarjetas de mesa).
    Lee solo pos_sede_lotes (easyposweb): no depende de la columna Sede_Pendiente."""
    filas = (await db.execute(text("""
        SELECT DISTINCT nro_pedido FROM pos_sede_lotes
        WHERE company_id = :c AND estado IN ('PENDIENTE','RECIBIDO','ACEPTADO','ERROR')
    """), {"c": cid})).all()
    return {f[0] for f in filas}


async def rechazos_recientes(db: AsyncSession, cid: int, order_number: str) -> list:
    filas = (await db.execute(text("""
        SELECT id, tipo, items, total, motivo, procesado_por, procesado_en FROM pos_sede_lotes
        WHERE company_id = :c AND nro_pedido = :on AND estado = 'RECHAZADO'
          AND procesado_en >= NOW() - INTERVAL 12 HOUR
        ORDER BY id DESC LIMIT 5
    """), {"c": cid, "on": order_number})).mappings().all()
    return [{"lote": int(f["id"]), "tipo": f["tipo"], "items": int(f["items"]), "total": int(f["total"]),
             "motivo": f["motivo"], "por": f["procesado_por"],
             "fecha": f["procesado_en"].isoformat(timespec="minutes") if f["procesado_en"] else None} for f in filas]


# ───────────────────────────── resultado desde la sede ─────────────────────────────

async def _items_lote(db: AsyncSession, lote_id: int) -> list:
    return [int(r[0]) for r in (await db.execute(text(
        "SELECT item FROM pos_sede_lote_items WHERE lote_id = :l"), {"l": lote_id})).all()]


async def aplicar_en_nube(db: AsyncSession, db_temp: AsyncSession, lote: dict) -> None:
    """La sede ya lo pasó a sus temporales: en la web queda enviado normal."""
    items = await _items_lote(db, lote["id"])
    if not items:
        return
    ph = ", ".join(f":i{n}" for n in range(len(items)))
    await db_temp.execute(text(f"""
        UPDATE temp_detalle_comanda_parcial
        SET Sede_Pendiente = 0, Impreso = 1, Hora_Plato = :h
        WHERE Nro_pedido = :on AND company_id = :cid AND Nro_Factura = '0' AND Item IN ({ph})
    """), {"h": datetime.now(_BOG).strftime("%Y-%m-%d %H:%M:%S"), "on": lote["nro_pedido"], "cid": lote["company_id"],
           **{f"i{n}": v for n, v in enumerate(items)}})


async def rechazar_en_nube(db: AsyncSession, db_temp: AsyncSession, lote: dict) -> None:
    """Los ítems salen del pedido en la nube (quedan solo en el histórico del lote)."""
    cid, on = lote["company_id"], lote["nro_pedido"]
    items = await _items_lote(db, lote["id"])
    if items:
        ph = ", ".join(f":i{n}" for n in range(len(items)))
        p = {"on": on, "cid": cid, **{f"i{n}": v for n, v in enumerate(items)}}
        for tabla, col in (("temp_plato_producto_parcial", "Nro_Pedido"), ("temp_novedades_plato_pedido", "Nro_Pedido"),
                           ("temp_detalle_comanda_parcial", "Nro_pedido")):
            extra = " AND Sede_Pendiente = 1" if tabla == "temp_detalle_comanda_parcial" else ""
            await db_temp.execute(text(
                f"DELETE FROM {tabla} WHERE {col} = :on AND company_id = :cid AND Item IN ({ph}){extra}"), p)
    quedan = (await db_temp.execute(text("""
        SELECT COUNT(*) FROM temp_detalle_comanda_parcial
        WHERE Nro_pedido = :on AND company_id = :cid AND Nro_Factura = '0'
    """), {"on": on, "cid": cid})).scalar() or 0
    if lote["tipo"] == "NUEVO" and not quedan:
        await db_temp.execute(text(
            "DELETE FROM temp_comanda WHERE Nro_Pedido = :on AND company_id = :cid AND Nro_Factura = '0'"),
            {"on": on, "cid": cid})
    else:
        await db_temp.execute(text("""
            UPDATE temp_comanda tc SET tc.Valor = (
                SELECT COALESCE(SUM(d.Valor), 0) FROM temp_detalle_comanda_parcial d
                WHERE d.Nro_pedido = tc.Nro_Pedido AND d.company_id = tc.company_id
                  AND d.Nro_Factura = '0' AND d.Mostrar = 1)
            WHERE tc.Nro_Pedido = :on AND tc.company_id = :cid
        """), {"on": on, "cid": cid})
