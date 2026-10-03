"""
Cuadre de Caja — cálculo único (pantalla, impresión y cierre usan este mismo resultado).

Alcance de un cuadre = un conjunto de Id_Caja (pos_cash_register_closings = cajas_cierres;
el Id_Caja es `id_registro`, el mismo del escritorio):
  · todos   → todos los Id_Caja de la fecha
  · usuario → los Id_Caja de la fecha de ese cajero (Venta_Clientes = customer_sales)
  · caja    → un Id_Caja de la fecha
Los movimientos se amarran al Id_Caja, vengan del escritorio (sincronizados) o de la web:
recibos por caja_recibos.Id_Caja (closing_id), facturas por caja_facturas.Id_Caja,
gastos / compras / otros ingresos / otros egresos / vales por register_id.

Reglas de efectivo (como el escritorio):
  · Entra en efectivo la parte pagada con la forma de pago EFECTIVO (las demás son Otros) de la
    venta, la propina y el domicilio; en recibos con varias formas de pago se reparte en proporción.
  · Salen completas la propina y el domicilio: se les pagan en efectivo al mesero y al
    domiciliario aunque el cliente haya pagado con tarjeta.
  · Gastos, compras, otros egresos/ingresos y vales: efectivo = valor − lo pagado con otras
    formas de pago (pos_cash_movement_payments).
"""
from collections import OrderedDict
from typing import Optional

from sqlalchemy import bindparam, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.formas_pago import es_efectivo_sql

# Movimientos de dinero del turno: (clave, tabla, título, type_id en pos_cash_movement_payments, sentido)
MOVIMIENTOS = [
    ("otros_ingresos", "pos_other_incomes", "Otros Ingresos", 4, "entra"),
    ("gastos", "pos_expenses", "Gastos", 1, "sale"),
    ("compras", "pos_purchases", "Compras", 2, "sale"),
    ("vales", "pos_cash_advances", "Vales", 5, "sale"),
    ("otros_egresos", "pos_other_expenses", "Otros Egresos", 3, "sale"),
]


def _r(v: float) -> int:
    return int(round(v or 0))


def _in(sql: str, *names: str):
    return text(sql).bindparams(*(bindparam(n, expanding=True) for n in names))


async def turnos(db: AsyncSession, cid: int, fecha: str, modo: str,
                 user_id: Optional[int] = None, closing_id: Optional[int] = None) -> list[dict]:
    """Id_Caja de la fecha. `abierto` = Cierre 0 y es el mayor Id_Caja abierto de ese cajero
    (los demás Cierre 0 son registros viejos sin cerrar)."""
    from app.routers.pos_shift_router import _VIGENTE
    where, p = "c.company_id = :cid AND c.date = :f", {"cid": cid, "f": fecha}
    if modo == "usuario":
        where += " AND c.customer_sales = :uid"
        p["uid"] = int(user_id or 0)
    elif modo == "caja":
        where += " AND c.id_registro = :clid"
        p["clid"] = int(closing_id or 0)
    rows = (await db.execute(text(f"""
        SELECT c.id_registro AS id, c.register_number, c.base_amount, c.final_base,
               CASE WHEN {_VIGENTE} THEN 0 ELSE 1 END AS closed, c.synced,
               CAST(c.customer_sales AS SIGNED) AS user_id, c.opening_datetime, c.closing_datetime,
               COALESCE(r.name, CONCAT('Caja ', c.register_number)) AS caja_nombre,
               COALESCE(e.name, u.nombre, '') AS usuario
        FROM pos_cash_register_closings c
        LEFT JOIN pos_cash_registers r ON r.company_id = c.company_id AND r.id = c.register_number
        LEFT JOIN pos_employees e ON e.company_id = c.company_id AND e.id = CAST(c.customer_sales AS SIGNED)
        LEFT JOIN users u ON u.id = CAST(c.customer_sales AS SIGNED) AND u.company_id = c.company_id
        WHERE {where}
        ORDER BY c.id_registro
    """), p)).mappings().all()
    return [dict(r) | {"opening_datetime": str(r["opening_datetime"] or ""),
                       "closing_datetime": str(r["closing_datetime"] or ""),
                       "origen": "escritorio" if int(r["synced"] or 0) else "web"} for r in rows]


# Recibos y facturas tienen la misma estructura (escritorio y web):
#   caja_recibos / caja_facturas → encabezado → formas de pago → domicilios → detalle
FUENTES = {
    "recibos": {"caja": "pos_cash_register_receipts", "num": "receipt_number", "hdr": "pos_receipts",
                "pagos": "pos_receipt_payment_methods", "dom": "receipt_delivery_fees",
                "det": "pos_receipt_order_details", "det_num": "receipt_number", "det_amount": "amount",
                "custom": "od.custom_product"},
    "facturas": {"caja": "pos_cash_register_invoices", "num": "invoice_number", "hdr": "pos_invoices",
                 "pagos": "pos_invoice_payment_methods", "dom": "invoice_delivery_fees",
                 "det": "pos_invoice_details", "det_num": "invoice_number", "det_amount": "dish_amount",
                 "custom": "''"},
}


async def _documentos(db: AsyncSession, cid: int, ids: list[int], tipo: str) -> list[dict]:
    if not ids:
        return []
    f = FUENTES[tipo]
    rows = (await db.execute(_in(f"""
        SELECT cr.{f['num']} AS numero, cr.closing_id, cr.date,
               COALESCE(h.amount_without_tip, cr.amount, 0) venta, COALESCE(h.tip, 0) tip,
               COALESCE(h.cash_amount, cr.amount, 0) total, COALESCE(h.voided, 0) voided
        FROM {f['caja']} cr
        LEFT JOIN {f['hdr']} h ON h.company_id = cr.company_id AND h.{f['num']} = cr.{f['num']}
        WHERE cr.company_id = :cid AND cr.closing_id IN :ids
    """, "ids"), {"cid": cid, "ids": ids})).mappings().all()
    docs = {str(r["numero"]): {"receipt_number": str(r["numero"]), "venta": float(r["venta"] or 0),
                               "tip": float(r["tip"] or 0), "total": float(r["total"] or 0),
                               "voided": int(r["voided"] or 0), "pagos": [], "domicilio": 0.0,
                               "tipo": tipo} for r in rows}
    if not docs:
        return []
    nums = list(docs)
    for pm in (await db.execute(_in(f"""
        SELECT pm.invoice_number, pm.amount, COALESCE(pt.name, 'Pago') name, {es_efectivo_sql('pt')} cash
        FROM {f['pagos']} pm
        LEFT JOIN pos_payment_types pt ON pt.id = pm.payment_method_id AND pt.company_id = pm.company_id
        WHERE pm.company_id = :cid AND pm.invoice_number IN :nums
        ORDER BY pm.item
    """, "nums"), {"cid": cid, "nums": nums})).mappings().all():
        docs[str(pm["invoice_number"])]["pagos"].append(dict(pm))
    for d in (await db.execute(_in(f"""
        SELECT invoice_number, SUM(amount) amount FROM {f['dom']}
        WHERE company_id = :cid AND invoice_number IN :nums GROUP BY invoice_number
    """, "nums"), {"cid": cid, "nums": nums})).mappings().all():
        docs[str(d["invoice_number"])]["domicilio"] = float(d["amount"] or 0)
    return list(docs.values())


async def _movimientos(db: AsyncSession, cid: int, ids: list[int]) -> dict:
    out = {}
    if not ids:
        return {k: [] for k, *_ in MOVIMIENTOS}
    for clave, tabla, _titulo, tipo, _s in MOVIMIENTOS:
        concepto = "m.description" if tabla == "pos_cash_advances" else "COALESCE(c.description, m.detail, '')"
        join = "" if tabla == "pos_cash_advances" else \
            "LEFT JOIN pos_cash_concepts c ON c.company_id = m.company_id AND c.concept_id = m.concept_id"
        detalle = "m.description" if tabla == "pos_cash_advances" else "m.detail"
        rows = (await db.execute(_in(f"""
            SELECT m.id, m.date, m.amount, {concepto} AS concepto, {detalle} AS detalle,
                   COALESCE((SELECT SUM(mp.amount) FROM pos_cash_movement_payments mp
                             LEFT JOIN pos_payment_types pt ON pt.id = mp.payment_method_id AND pt.company_id = mp.company_id
                             WHERE mp.company_id = m.company_id AND mp.type_id = {tipo} AND mp.movement_id = m.id_registro
                               AND NOT {es_efectivo_sql('pt')}), 0) AS otros
            FROM {tabla} m {join}
            WHERE m.company_id = :cid AND m.register_id IN :ids
            ORDER BY m.id
        """, "ids"), {"cid": cid, "ids": ids})).mappings().all()
        out[clave] = [{"id": r["id"], "fecha": str(r["date"] or ""), "concepto": r["concepto"] or "",
                       "detalle": r["detalle"] or "", "valor": _r(r["amount"]),
                       "efectivo": _r(float(r["amount"] or 0) - float(r["otros"] or 0))} for r in rows]
    return out


async def calcular(db: AsyncSession, cid: int, fecha: str, modo: str, origen: str,
                   user_id: Optional[int] = None, closing_id: Optional[int] = None,
                   base_inicial: Optional[float] = None, base_final: Optional[float] = None) -> dict:
    ts = await turnos(db, cid, fecha, modo, user_id, closing_id)
    ids = [int(t["id"]) for t in ts]

    docs = []
    if origen in ("recibos", "ambos"):
        docs += await _documentos(db, cid, ids, "recibos")
    if origen in ("facturas", "ambos"):
        docs += await _documentos(db, cid, ids, "facturas")

    venta = venta_ef = tip = tip_ef = dom = dom_ef = 0.0
    formas: "OrderedDict[str, float]" = OrderedDict()
    cuentas, otros, anuladas, numeros = [], [], [], []
    validos = {"recibos": [], "facturas": []}
    for d in docs:
        num = d["receipt_number"]
        if int(d["voided"] or 0):
            anuladas.append({"numero": num, "valor": _r(d["total"])})
            continue
        pagado = sum(float(p["amount"] or 0) for p in d["pagos"])
        en_ef = sum(float(p["amount"] or 0) for p in d["pagos"] if int(p["cash"] or 0))
        f = (en_ef / pagado) if pagado else 1.0
        v, t, dm = float(d["venta"] or 0), float(d["tip"] or 0), float(d["domicilio"] or 0)
        venta += v; tip += t; dom += dm
        venta_ef += v * f; tip_ef += t * f; dom_ef += dm * f
        for p in d["pagos"]:
            formas[p["name"]] = formas.get(p["name"], 0.0) + float(p["amount"] or 0)
        cuentas.append({"numero": num, "valor": _r(d["total"])})
        numeros.append(num)
        validos[d["tipo"]].append(num)
        if any(not int(p["cash"] or 0) for p in d["pagos"]):
            otros.append({"numero": num, "valor": _r(d["total"]),
                          "formas": ", ".join(sorted({p["name"] for p in d["pagos"] if not int(p["cash"] or 0)}))})

    def _orden(n: str):
        return (0, int(n)) if str(n).isdigit() else (1, str(n))
    numeros.sort(key=_orden)
    for lst in (cuentas, otros, anuladas):
        lst.sort(key=lambda x: _orden(x["numero"]))

    movs = await _movimientos(db, cid, ids)

    # Bases: editables solo en un turno abierto (modo caja); si no, lo guardado en los turnos
    b_ini = sum(float(t["base_amount"] or 0) for t in ts)
    b_fin = sum(float(t["final_base"] if int(t["closed"] or 0) else t["base_amount"] or 0) for t in ts)
    editable = modo == "caja" and len(ts) == 1 and not int(ts[0]["closed"] or 0) and ts[0]["origen"] == "web"
    if editable:
        if base_inicial is not None:
            b_ini = float(base_inicial)
        b_fin = float(base_final) if base_final is not None else b_ini

    ef_mov = {k: sum(m["efectivo"] for m in movs[k]) for k in movs}
    entran = [{"clave": "base_inicial", "label": "Base Inicial", "valor": _r(b_ini), "fija": True},
              {"clave": "venta", "label": "Efectivo Venta", "valor": _r(venta_ef)},
              {"clave": "domicilio", "label": "Efectivo Domicilio", "valor": _r(dom_ef)},
              {"clave": "propina", "label": "Efectivo Propina", "valor": _r(tip_ef)},
              {"clave": "otros_ingresos", "label": "Efectivo Otros Ingresos", "valor": ef_mov["otros_ingresos"], "ver": True}]
    salen = [{"clave": "base_final", "label": "Base Final", "valor": _r(b_fin), "fija": True},
             {"clave": "gastos", "label": "Gastos Efectivo", "valor": ef_mov["gastos"], "ver": True},
             {"clave": "compras", "label": "Compras Efectivo", "valor": ef_mov["compras"], "ver": True},
             {"clave": "vales", "label": "Vales Efectivo", "valor": ef_mov["vales"], "ver": True},
             {"clave": "domicilio", "label": "Domicilios", "valor": _r(dom)},
             {"clave": "propina", "label": "Propinas", "valor": _r(tip)},
             {"clave": "otros_egresos", "label": "Otros Egresos Efectivo", "valor": ef_mov["otros_egresos"], "ver": True}]
    # Dinámicas: solo las filas con movimiento (las bases siempre)
    entran = [e for e in entran if e.get("fija") or e["valor"]]
    salen = [s for s in salen if s.get("fija") or s["valor"]]
    t_ent, t_sal = sum(e["valor"] for e in entran), sum(s["valor"] for s in salen)

    categorias = await ventas_por_categoria(db, cid, validos, detalle=False)

    return {
        "fecha": fecha, "modo": modo, "origen": origen,
        "turnos": ts, "editable_bases": editable,
        "venta": {"total": _r(venta), "efectivo": _r(venta_ef), "otros": _r(venta) - _r(venta_ef)},
        "domicilios": {"total": _r(dom), "efectivo": _r(dom_ef), "otros": _r(dom) - _r(dom_ef)},
        "propinas": {"total": _r(tip), "efectivo": _r(tip_ef), "otros": _r(tip) - _r(tip_ef)},
        "conteos": {"cuentas": len(cuentas), "otros": len(otros), "anuladas": len(anuladas),
                    "inicial": numeros[0] if numeros else "", "final": numeros[-1] if numeros else ""},
        "listas": {"cuentas": cuentas, "otros": otros, "anuladas": anuladas},
        "entran": entran, "salen": salen,
        "total_entran": t_ent, "total_salen": t_sal, "dinero_entregar": t_ent - t_sal,
        "formas_pago": [{"name": k, "valor": _r(v)} for k, v in formas.items() if _r(v)],
        "categorias": categorias,
        "movimientos": movs,
        "documentos": validos,
        "bases": {"inicial": _r(b_ini), "final": _r(b_fin)},
    }


async def ventas_por_categoria(db: AsyncSession, cid: int, documentos: dict, detalle: bool) -> list[dict]:
    """Venta por categoría (detalle=False) o lista de artículos vendidos agrupada por categoría.
    `documentos` = {"recibos": [números], "facturas": [números]} (solo los no anulados)."""
    partes, params = [], {"cid": cid}
    for tipo, nums in documentos.items():
        if not nums:
            continue
        f = FUENTES[tipo]
        params[f"n_{tipo}"] = list(nums)
        partes.append(f"""
            SELECT COALESCE(dc.name, 'SIN CATEGORÍA') categoria,
                   CASE WHEN COALESCE({f['custom']}, '') <> '' AND LEFT({f['custom']}, 1) <> '{{'
                        THEN {f['custom']} ELSE COALESCE(d.name, 'Producto') END producto,
                   od.quantity cantidad, od.{f['det_amount']} valor
            FROM {f['det']} od
            LEFT JOIN pos_dishes d ON d.id = od.dish_id AND d.company_id = od.company_id
            LEFT JOIN pos_dish_categories dc ON dc.id = d.category_id AND dc.company_id = od.company_id
            WHERE od.company_id = :cid AND od.{f['det_num']} IN :n_{tipo}""")
    if not partes:
        return []
    sql = ("SELECT categoria, producto, SUM(cantidad) cantidad, SUM(valor) valor FROM ("
           + " UNION ALL ".join(partes) + ") x GROUP BY categoria, producto ORDER BY categoria, producto")
    rows = (await db.execute(_in(sql, *[k for k in params if k.startswith("n_")]), params)).mappings().all()
    cats: "OrderedDict[str, dict]" = OrderedDict()
    for r in rows:
        c = cats.setdefault(r["categoria"], {"categoria": r["categoria"], "cantidad": 0.0, "valor": 0, "items": []})
        q = float(r["cantidad"] or 0)
        c["cantidad"] += q
        c["valor"] += _r(r["valor"])
        if detalle:
            c["items"].append({"producto": r["producto"], "cantidad": int(q) if q.is_integer() else q,
                               "valor": _r(r["valor"])})
    out = []
    for c in cats.values():
        c["cantidad"] = int(c["cantidad"]) if float(c["cantidad"]).is_integer() else c["cantidad"]
        if not detalle:
            c.pop("items")
        out.append(c)
    return out
