"""
Tablero de la Bodega Central (dashboard de la empresa bodega): una tarjeta por sede y los totales del grupo.

  Ventas de la fecha: recibos y facturas no anulados (misma fórmula del dashboard: efectivo + tarjetas − descuento
  − propinas). Turnos abiertos: la misma regla de Turnos de caja (de los Cierre = 0, el mayor Id_Caja de cada
  cajero). Tienda activa = escritorio conectado (agente con contacto en los últimos minutos).
  Traslados: pendientes = todos los que aún no se cargan (sin importar la fecha); aceptados = cargados en la fecha.
  Sedes con escritorio: sus datos llegan con la sincronización (pueden llevar unos minutos de atraso).
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.bodega_guard import Bodega, sedes_del_nit
from app.services.formas_pago import pago_vigente_sql

MINUTOS_EN_LINEA = 3
_TOTAL = "cash_amount + credit_card_amount + debit_card_amount - discount - tip - extra_tip"


def _iso(v):
    """datetime → ISO; algunas columnas del escritorio llegan como texto (se devuelven tal cual)."""
    if not v:
        return None
    return v.isoformat(timespec="minutes") if hasattr(v, "isoformat") else str(v).strip()[:19]


async def _ventas(db: AsyncSession, cid: int, fecha: str) -> dict:
    out = {}
    for clave, tabla in (("recibos", "pos_receipts"), ("facturas", "pos_invoices")):
        f = (await db.execute(text(
            f"SELECT COUNT(*) AS n, COALESCE(SUM({_TOTAL}), 0) AS t FROM {tabla} "
            "WHERE company_id = :c AND date = :f AND voided = 0"), {"c": cid, "f": fecha})).mappings().one()
        out[clave] = {"cantidad": int(f["n"] or 0), "total": float(f["t"] or 0)}
    out["total"] = out["recibos"]["total"] + out["facturas"]["total"]
    out["documentos"] = out["recibos"]["cantidad"] + out["facturas"]["cantidad"]
    return out


async def _turnos(db: AsyncSession, cid: int) -> list[dict]:
    from app.routers.pos_shift_router import _SELECT_CAJA, _VIGENTE
    filas = (await db.execute(text(f"{_SELECT_CAJA} WHERE c.company_id = :c AND {_VIGENTE} ORDER BY c.opening_datetime"),
                              {"c": cid})).mappings().all()
    return [{"caja": f["caja_nombre"], "cajero": f["cajero"] or f"Usuario {f['cajero_id']}",
             "abierto_en": _iso(f["opening_datetime"])} for f in filas]


async def _agente(db: AsyncSession, cid: int) -> dict:
    f = (await db.execute(text("""
        SELECT activo, ultimo_contacto, ultimo_contacto >= NOW() - INTERVAL :m MINUTE AS en_linea
        FROM company_local_agents WHERE company_id = :c ORDER BY activo DESC LIMIT 1
    """), {"c": cid, "m": MINUTOS_EN_LINEA})).mappings().first()
    if not f or not int(f["activo"] or 0):
        return {"con_escritorio": False, "en_linea": False, "ultimo_contacto": None}
    return {"con_escritorio": True, "en_linea": bool(f["en_linea"]), "ultimo_contacto": _iso(f["ultimo_contacto"])}


async def _traslados_cuenta(db: AsyncSession, bodega: Bodega, cid: int, fecha: str) -> dict:
    f = (await db.execute(text("""
        SELECT SUM(estado IN ('PENDIENTE_SALIDA', 'PENDIENTE_CARGUE')) AS pend,
               SUM(estado = 'CARGADO' AND DATE(cargado_en) = :f) AS carg
        FROM bc_traslados WHERE bodega_id = :b AND (origen_id = :c OR destino_id = :c)
    """), {"b": bodega.id, "c": cid, "f": fecha})).mappings().one()
    return {"pendientes": int(f["pend"] or 0), "aceptados": int(f["carg"] or 0)}


async def resumen_grupo(db: AsyncSession, bodega: Bodega, fecha: str) -> dict:
    sedes = []
    tot = {"recibos": {"cantidad": 0, "total": 0.0}, "facturas": {"cantidad": 0, "total": 0.0}, "total": 0.0}
    for s in await sedes_del_nit(db, bodega):
        v = await _ventas(db, s["id"], fecha)
        for k in ("recibos", "facturas"):
            tot[k]["cantidad"] += v[k]["cantidad"]
            tot[k]["total"] += v[k]["total"]
        tot["total"] += v["total"]
        sedes.append({"id": s["id"], "nombre": s["nombre"], "ventas": v, "turnos": await _turnos(db, s["id"]),
                      "agente": await _agente(db, s["id"]), "traslados": await _traslados_cuenta(db, bodega, s["id"], fecha)})
    pend_bodega = (await _traslados_cuenta(db, bodega, bodega.id, fecha))
    return {"fecha": fecha, "totales": tot, "sedes": sedes, "traslados_bodega": pend_bodega}


async def resumen_sede(db: AsyncSession, bodega: Bodega, sede: dict, fecha: str) -> dict:
    cid = sede["id"]
    ventas = await _ventas(db, cid, fecha)
    ventas["ticket_promedio"] = ventas["total"] / ventas["documentos"] if ventas["documentos"] else 0

    formas = {}
    for tabla, doc, num in (("pos_receipt_payment_methods", "pos_receipts", "receipt_number"),
                            ("pos_invoice_payment_methods", "pos_invoices", "invoice_number")):
        for f in (await db.execute(text(f"""
            SELECT COALESCE(pt.name, CONCAT('Forma ', pm.payment_method_id)) AS forma, SUM(pm.amount) AS total
            FROM {tabla} pm
            JOIN {doc} d ON d.company_id = pm.company_id AND d.{num} = pm.invoice_number AND d.date = :f AND d.voided = 0
            LEFT JOIN pos_payment_types pt ON pt.company_id = pm.company_id AND pt.id = pm.payment_method_id
            WHERE pm.company_id = :c AND {pago_vigente_sql('pm', tabla)}
            GROUP BY forma
        """), {"c": cid, "f": fecha})).mappings().all():
            formas[f["forma"]] = formas.get(f["forma"], 0) + float(f["total"] or 0)

    top = []
    for f in (await db.execute(text("""
        SELECT x.dish_id, COALESCE(p.name, CONCAT('Producto ', x.dish_id)) AS producto, SUM(x.cant) AS cantidad,
               SUM(x.valor) AS valor
        FROM (
            SELECT d.dish_id, d.quantity AS cant, d.quantity * d.amount AS valor FROM pos_receipt_order_details d
            JOIN pos_receipts r ON r.company_id = d.company_id AND r.receipt_number = d.receipt_number
                               AND r.date = d.date AND r.voided = 0
            WHERE d.company_id = :c AND d.date = :f
            UNION ALL
            SELECT d.dish_id, d.quantity, d.quantity * d.amount FROM pos_order_details d
            JOIN pos_invoices i ON i.company_id = d.company_id AND i.invoice_number = d.invoice_number
                               AND i.date = d.date AND i.voided = 0
            WHERE d.company_id = :c AND d.date = :f
        ) x
        LEFT JOIN pos_dishes p ON p.company_id = :c AND p.id = x.dish_id
        GROUP BY x.dish_id, producto
        ORDER BY cantidad DESC, valor DESC
        LIMIT 5
    """), {"c": cid, "f": fecha})).mappings().all():
        top.append({"producto": f["producto"], "cantidad": float(f["cantidad"] or 0), "valor": float(f["valor"] or 0)})

    from app.services import bodega_traslados as tr
    traslados = [t for t in await tr.listar(db, bodega, None, cid, None, None)
                 if t["estado"] in tr.ABIERTOS or (t["estado"] == "CARGADO" and (t["cargado_en"] or "")[:10] == fecha)]
    return {"fecha": fecha, "sede": {"id": cid, "nombre": sede["nombre"]}, "ventas": ventas,
            "formas_pago": sorted([{"forma": k, "total": v} for k, v in formas.items()], key=lambda x: -x["total"]),
            "turnos": await _turnos(db, cid), "agente": await _agente(db, cid), "top_productos": top,
            "traslados": traslados}
