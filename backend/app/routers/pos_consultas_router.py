import io
import json
from datetime import date, datetime, timezone, timedelta
from typing import Optional

_BOG = timezone(timedelta(hours=-5))
def _today() -> str:
    return datetime.now(_BOG).date().isoformat()

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.database import get_db
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.user_model import User
from app.utils.excel_ventas import build_ventas_excel
from app.routers.metricas_router import _query_export

from app.services import periodos as per

from pydantic import BaseModel

router = APIRouter(prefix="/api/pos-consultas", tags=["POS Consultas"])


# ─── Auth + company helper ─────────────────────────────────────────────────────

async def _get_user(authorization: str, db: AsyncSession) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido")
    result = await db.execute(
        select(UserSession).where(UserSession.token == token, UserSession.is_active == True)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=401, detail="Sesión inválida")
    uid = payload.get("user_id")
    user = await db.get(User, int(uid)) if uid else None
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not user.company_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asignada")
    from app.auth.tenant import apply_selected_company
    return await apply_selected_company(db, user)   # empresa del topbar (validada)


async def _resolve_cid(user: User, override: Optional[int], db: AsyncSession) -> int:
    """Empresa efectiva (CLAUDE.md §6): la propia, o la solicitada solo si el usuario tiene acceso
    (ADMIN → empresas de su mismo NIT; SYSADMIN → todas; otros roles → solo la suya). 403 si no."""
    from app.auth.tenant import resolve_company
    return await resolve_company(db, user, override)


# ─── 1. Lista de ventas ────────────────────────────────────────────────────────

@router.get("/ventas")
async def get_ventas(
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
    tipo: Optional[str] = "ambos",   # "factura" | "recibo" | "ambos"
    company_id: Optional[int] = None,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid = await _resolve_cid(user, company_id, db)
    hoy = _today()
    desde = desde or hoy
    hasta = hasta or hoy
    desde, hasta = await per.validar_rango(db, user, desde, hasta)

    rows = []

    if tipo in ("factura", "ambos"):
        fact_rows = (await db.execute(text("""
            SELECT
                i.invoice_number                            AS numero,
                i.date,
                i.time                                      AS hora,
                COALESCE(i.cash_amount, 0)
                  + COALESCE(i.credit_card_amount, 0)
                  + COALESCE(i.debit_card_amount, 0)
                  + COALESCE(i.adjustment, 0)
                  - COALESCE(i.discount, 0)                AS valor,
                COALESCE(i.tip, 0) + COALESCE(i.extra_tip, 0) AS propina,
                COALESCE(
                    (SELECT SUM(amount) FROM invoice_delivery_fees
                     WHERE invoice_number = i.invoice_number AND company_id = i.company_id), 0
                )                                          AS domicilio,
                COALESCE(o.table_name, '')                 AS mesa,
                COALESCE(o.order_number, '')               AS order_number,
                COALESCE(i.shift, '')                      AS turno,
                'factura'                                  AS tipo
            FROM pos_invoices i
            LEFT JOIN pos_orders o
                   ON o.invoice_number = i.invoice_number
                  AND o.company_id     = i.company_id
                  AND o.date           = i.date
                  AND o.delivery       = 0
            WHERE i.company_id = :cid
              AND i.date BETWEEN :desde AND :hasta
              AND i.voided = 0
            ORDER BY i.invoice_number DESC
            LIMIT 500
        """), {"cid": cid, "desde": desde, "hasta": hasta})).mappings().all()
        rows.extend([dict(row) for row in fact_rows])

    if tipo in ("recibo", "ambos"):
        rec_rows = (await db.execute(text("""
            SELECT
                rc.receipt_number                          AS numero,
                rc.date,
                rc.time                                    AS hora,
                COALESCE(rc.cash_amount, 0)
                  + COALESCE(rc.credit_card_amount, 0)
                  + COALESCE(rc.debit_card_amount, 0)
                  + COALESCE(rc.adjustment, 0)
                  - COALESCE(rc.discount, 0)              AS valor,
                COALESCE(rc.tip, 0) + COALESCE(rc.extra_tip, 0) AS propina,
                COALESCE(
                    (SELECT SUM(amount) FROM receipt_delivery_fees
                     WHERE invoice_number = rc.receipt_number AND company_id = rc.company_id), 0
                )                                         AS domicilio,
                COALESCE(ro.table_name, '')               AS mesa,
                COALESCE(ro.order_number, '')             AS order_number,
                COALESCE(rc.shift, '')                    AS turno,
                'recibo'                                  AS tipo
            FROM pos_receipts rc
            LEFT JOIN pos_receipt_orders ro
                   ON ro.receipt_number = rc.receipt_number
                  AND ro.company_id     = rc.company_id
                  AND ro.date           = rc.date
            WHERE rc.company_id = :cid
              AND rc.date BETWEEN :desde AND :hasta
              AND rc.voided = 0
            ORDER BY rc.receipt_number DESC
            LIMIT 500
        """), {"cid": cid, "desde": desde, "hasta": hasta})).mappings().all()
        rows.extend([dict(row) for row in rec_rows])

    # Sort merged list newest first by date+hora
    rows.sort(key=lambda x: (str(x["date"] or ""), str(x["hora"] or "")), reverse=True)
    return rows[:500]


# ─── Totales del periodo (sin límite de registros) ────────────────────────────
@router.get("/ventas-resumen")
async def get_ventas_resumen(
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
    tipo: Optional[str] = "ambos",
    company_id: Optional[int] = None,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid = await _resolve_cid(user, company_id, db)
    hoy = _today()
    desde, hasta = await per.validar_rango(db, user, desde or hoy, hasta or hoy)
    tot = {"registros": 0, "venta": 0.0, "propinas": 0.0, "domicilios": 0.0}
    fuentes = []
    if tipo in ("factura", "ambos"):
        fuentes.append(("pos_invoices", "invoice_number", "invoice_delivery_fees"))
    if tipo in ("recibo", "ambos"):
        fuentes.append(("pos_receipts", "receipt_number", "receipt_delivery_fees"))
    for tabla, num, dom in fuentes:
        r = (await db.execute(text(f"""
            SELECT COUNT(*) n,
                   COALESCE(SUM(COALESCE(x.cash_amount,0) + COALESCE(x.credit_card_amount,0)
                       + COALESCE(x.debit_card_amount,0) + COALESCE(x.adjustment,0) - COALESCE(x.discount,0)), 0) v,
                   COALESCE(SUM(COALESCE(x.tip,0) + COALESCE(x.extra_tip,0)), 0) p,
                   COALESCE((SELECT SUM(d.amount) FROM {dom} d
                             JOIN {tabla} y ON y.{num} = d.invoice_number AND y.company_id = d.company_id
                             WHERE d.company_id = :cid AND y.date BETWEEN :d AND :h AND y.voided = 0), 0) dm
            FROM {tabla} x
            WHERE x.company_id = :cid AND x.date BETWEEN :d AND :h AND x.voided = 0
        """), {"cid": cid, "d": desde, "h": hasta})).mappings().first()
        tot["registros"] += int(r["n"] or 0)
        tot["venta"] += float(r["v"] or 0)
        tot["propinas"] += float(r["p"] or 0)
        tot["domicilios"] += float(r["dm"] or 0)
    # Venta real = valor sin propinas ni domicilios (igual que la lista)
    tot["venta_real"] = tot["venta"] - tot["propinas"] - tot["domicilios"]
    return tot | {"desde": desde, "hasta": hasta}


class ImprimirVentasIn(BaseModel):
    desde: str
    hasta: str
    tipo: str = "ambos"
    printer_id: int
    raw: bool = False
    company_id: Optional[int] = None
    receipt_number: Optional[str] = None


@router.post("/imprimir")
async def imprimir_ventas(
    body: ImprimirVentasIn,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Tirilla del listado de ventas del periodo (mismos filtros y permisos de la consulta)."""
    from app.routers.pos_recibo_impresion_router import enviar_tirilla, _ascii, _money
    user = await _get_user(authorization, db)
    cid = await _resolve_cid(user, body.company_id, db)
    tipo = body.tipo if body.tipo in ("factura", "recibo", "ambos") else "ambos"

    async def datos():
        lista = await get_ventas(body.desde, body.hasta, tipo, body.company_id, authorization, db)
        tot = await get_ventas_resumen(body.desde, body.hasta, tipo, body.company_id, authorization, db)
        empresa = (await db.execute(text("SELECT name FROM companies WHERE id_company = :c"), {"c": cid})).scalar() or ""
        return {"empresa": empresa, "lista": lista, "tot": tot}

    def armar(d: dict, width: int = 32) -> bytes:
        ESC = b"\x1b"
        buf = bytearray(ESC + b"@")
        def line(t="", bold=False, center=False):
            buf.extend((ESC + b"E\x01" if bold else b"") + (ESC + b"a\x01" if center else ESC + b"a\x00")
                       + _ascii(t) + b"\n" + (ESC + b"E\x00" if bold else b""))
        def dl(a, b, bold=False):
            a = str(a)[: max(1, width - len(b) - 1)]
            line(a + " " * max(1, width - len(a) - len(b)) + b, bold=bold)
        t = d["tot"]
        line(d["empresa"], bold=True, center=True)
        line("CONSULTA DE VENTAS", bold=True, center=True)
        f = lambda x: f"{x[8:10]}/{x[5:7]}/{x[:4]}"
        line(f"{f(t['desde'])} al {f(t['hasta'])}", center=True)
        line({"factura": "Facturas", "recibo": "Recibos", "ambos": "Facturas y Recibos"}[tipo], center=True)
        line("-" * width)
        for r in d["lista"]:
            dl(f"{'FAC' if r['tipo'] == 'factura' else 'REC'} {r['numero']} {str(r['date'])[5:10]}", _money(r["valor"]))
        line("-" * width)
        dl("Registros", str(t["registros"]))
        dl("Venta Real", _money(t["venta_real"]), True)
        if t["propinas"]:
            dl("Propinas", _money(t["propinas"]))
        if t["domicilios"]:
            dl("Domicilios", _money(t["domicilios"]))
        dl("TOTAL", _money(t["venta"]), True)
        if t["registros"] > len(d["lista"]):
            line(f"(se listan {len(d['lista'])} de {t['registros']})", center=True)
        buf.extend(b"\n" * 4 + b"\x1dV\x42\x00")
        return bytes(buf)

    return await enviar_tirilla(db, cid, body.printer_id, body.raw, datos, armar=armar)


# ─── 2. Detalle de una venta (header + items) ─────────────────────────────────

@router.get("/venta-detalle/{tipo}/{numero}")
async def get_venta_detalle(
    tipo: str,
    numero: str,
    fecha: Optional[str] = None,
    company_id: Optional[int] = None,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid = await _resolve_cid(user, company_id, db)

    if tipo == "factura":
        # Header
        hdr = (await db.execute(text("""
            SELECT
                i.invoice_number                           AS numero,
                i.date,
                i.time                                     AS hora,
                COALESCE(i.cash_amount, 0)
                  + COALESCE(i.credit_card_amount, 0)
                  + COALESCE(i.debit_card_amount, 0)
                  + COALESCE(i.adjustment, 0)
                  - COALESCE(i.discount, 0)               AS total,
                COALESCE(i.cash_amount, 0)                AS efectivo,
                COALESCE(i.credit_card_amount, 0)         AS tarjeta_credito,
                COALESCE(i.debit_card_amount, 0)          AS tarjeta_debito,
                COALESCE(i.adjustment, 0)                 AS ajuste,
                COALESCE(i.discount, 0)                   AS descuento,
                COALESCE(i.shift, '')                     AS turno,
                COALESCE(o.table_name, '')                AS mesa,
                COALESCE(w.name, '')                      AS mesero,
                COALESCE(o.guests_count, 0)               AS comensales,
                COALESCE(o.order_number, '')              AS order_number
            FROM pos_invoices i
            LEFT JOIN pos_orders o
                   ON o.invoice_number = i.invoice_number
                  AND o.company_id     = i.company_id
                  AND o.date           = i.date
            LEFT JOIN pos_waiters w
                   ON w.id = o.waiter_id AND w.company_id = i.company_id
            WHERE i.company_id    = :cid
              AND i.invoice_number = :numero
            LIMIT 1
        """), {"cid": cid, "numero": numero})).mappings().one_or_none()

        if not hdr:
            raise HTTPException(status_code=404, detail="Factura no encontrada")

        items = (await db.execute(text("""
            SELECT
                od.dish_id,
                COALESCE(d.name, od.dish_id)              AS plato,
                od.quantity,
                COALESCE(d.price, 0)                      AS price,
                COALESCE(od.amount, 0)                    AS subtotal,
                od.item,
                COALESCE(od.notes, '')                    AS notes,
                COALESCE(od.changes, '')                  AS changes,
                od.custom_product
            FROM pos_order_details od
            LEFT JOIN pos_dishes d ON d.id = od.dish_id AND d.company_id = :cid
            WHERE od.company_id    = :cid
              AND od.invoice_number = :numero
              AND od.date          = :fecha
            ORDER BY od.item
        """), {"cid": cid, "numero": numero, "fecha": dict(hdr)["date"]})).mappings().all()

    elif tipo == "recibo":
        hdr = (await db.execute(text("""
            SELECT
                rc.receipt_number                         AS numero,
                rc.date,
                rc.time                                   AS hora,
                COALESCE(rc.cash_amount, 0)
                  + COALESCE(rc.credit_card_amount, 0)
                  + COALESCE(rc.debit_card_amount, 0)
                  + COALESCE(rc.adjustment, 0)
                  - COALESCE(rc.discount, 0)             AS total,
                COALESCE(rc.cash_amount, 0)               AS efectivo,
                COALESCE(rc.credit_card_amount, 0)        AS tarjeta_credito,
                COALESCE(rc.debit_card_amount, 0)         AS tarjeta_debito,
                COALESCE(rc.adjustment, 0)                AS ajuste,
                COALESCE(rc.discount, 0)                  AS descuento,
                COALESCE(rc.shift, '')                    AS turno,
                COALESCE(ro.table_name, '')               AS mesa,
                COALESCE(w.name, '')                      AS mesero,
                COALESCE(ro.guests_count, 0)              AS comensales,
                COALESCE(ro.order_number, '')             AS order_number
            FROM pos_receipts rc
            LEFT JOIN pos_receipt_orders ro
                   ON ro.receipt_number = rc.receipt_number
                  AND ro.company_id     = rc.company_id
                  AND ro.date           = rc.date
            LEFT JOIN pos_waiters w
                   ON w.id = ro.waiter_id AND w.company_id = rc.company_id
            WHERE rc.company_id    = :cid
              AND rc.receipt_number = :numero
            LIMIT 1
        """), {"cid": cid, "numero": numero})).mappings().one_or_none()

        if not hdr:
            raise HTTPException(status_code=404, detail="Recibo no encontrado")

        items = (await db.execute(text("""
            SELECT
                od.dish_id,
                CASE
                    WHEN d.name IS NOT NULL THEN d.name
                    WHEN od.dish_id = 0    THEN COALESCE(od.notes, '')
                    ELSE CAST(od.dish_id AS CHAR)
                END                                       AS plato,
                od.quantity,
                COALESCE(d.price, 0)                      AS price,
                COALESCE(od.amount, 0)                    AS subtotal,
                od.item,
                CASE WHEN od.dish_id = 0 THEN '' ELSE COALESCE(od.notes, '') END AS notes,
                COALESCE(od.changes, '')                  AS changes,
                od.custom_product
            FROM pos_receipt_order_details od
            LEFT JOIN pos_dishes d ON d.id = od.dish_id AND d.company_id = :cid AND od.dish_id > 0
            WHERE od.company_id     = :cid
              AND od.receipt_number  = :numero
              AND od.date           = :fecha
            ORDER BY od.item
        """), {"cid": cid, "numero": numero, "fecha": dict(hdr)["date"]})).mappings().all()

    else:
        raise HTTPException(status_code=400, detail="tipo debe ser 'factura' o 'recibo'")

    items_list = []
    for r in items:
        row = dict(r)
        assembly = []
        cp = row.pop("custom_product", None)
        if cp:
            try:
                assembly = json.loads(cp).get("assembly", [])
            except Exception:
                pass
        row["assembly"] = assembly
        items_list.append(row)

    # Para recibos: incluir órdenes de servicio vinculadas y formas de pago detalladas
    ordenes_servicio = []
    pagos_detalle = []
    if tipo == "recibo":
        so_rows = await db.execute(text("""
            SELECT DISTINCT
                so.id, so.numero_orden, so.placa_vehiculo, so.estado,
                COALESCE(c.name, '') AS cliente_nombre
            FROM pos_receipt_order_details rod
            JOIN service_orders so
                 ON so.id = CAST(rod.order_number AS UNSIGNED)
                AND so.company_id = :cid
            LEFT JOIN clients c ON c.id = so.client_id
            WHERE rod.receipt_number = :numero
              AND rod.company_id = :cid
              AND rod.order_number REGEXP '^[1-9][0-9]*$'
        """), {"cid": cid, "numero": numero})
        ordenes_servicio = [dict(r) for r in so_rows.mappings()]

        pm_rows = await db.execute(text("""
            SELECT pm.amount, COALESCE(pt.name, 'Pago') AS name
            FROM pos_receipt_payment_methods pm
            LEFT JOIN pos_payment_types pt
                   ON pt.id = pm.payment_method_id AND pt.company_id = pm.company_id
            WHERE pm.invoice_number = :numero AND pm.company_id = :cid
            ORDER BY pm.item
        """), {"cid": cid, "numero": numero})
        pagos_detalle = [{"amount": float(r.amount or 0), "name": r.name} for r in pm_rows]

    return {
        "header": dict(hdr),
        "items": items_list,
        "ordenes_servicio": ordenes_servicio,
        "pagos": pagos_detalle,
    }


# ─── 3. Insumos consumidos por línea de plato (modal VER) ─────────────────────

@router.get("/detalle-productos")
async def get_detalle_productos(
    tipo: str,                        # "factura" | "recibo"
    numero: str,
    fecha: str,
    dish_id: str,
    item: int,
    company_id: Optional[int] = None,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid = await _resolve_cid(user, company_id, db)

    if tipo == "factura":
        tabla = "pos_order_detail_products"
        col   = "invoice_number"
    elif tipo == "recibo":
        tabla = "pos_receipt_order_detail_products"
        col   = "invoice_number"
    else:
        raise HTTPException(status_code=400, detail="tipo debe ser 'factura' o 'recibo'")

    rows = (await db.execute(text(f"""
        SELECT
            dp.item_id,
            COALESCE(si.description, dp.item_id)          AS insumo,
            dp.quantity,
            COALESCE(mu.name, '')             AS unidad
        FROM {tabla} dp
        LEFT JOIN supply_items si
               ON si.id_item = dp.item_id AND si.company_id = :cid
        LEFT JOIN pos_measure_forms mu
               ON mu.id = si.unit_id AND mu.company_id = :cid
        WHERE dp.company_id  = :cid
          AND dp.{col}       = :numero
          AND dp.date        = :fecha
          AND dp.dish_id     = :dish_id
          AND dp.item        = :item
        ORDER BY dp.group_id, dp.item_id
    """), {
        "cid": cid,
        "numero": numero,
        "fecha": fecha,
        "dish_id": dish_id,
        "item": item,
    })).mappings().all()

    return [dict(r) for r in rows]


# ─── 4. Categorías de platos (dropdown para filtros) ─────────────────────────

@router.get("/categorias-platos")
async def get_categorias_platos(
    company_id: Optional[int] = None,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid  = await _resolve_cid(user, company_id, db)
    rows = (await db.execute(text(
        "SELECT id, name FROM pos_dish_categories WHERE company_id=:cid AND is_active=1 ORDER BY name"
    ), {"cid": cid})).mappings().all()
    return [dict(r) for r in rows]


# ─── 5. Ventas agrupadas por producto ─────────────────────────────────────────

@router.get("/ventas-producto")
async def get_ventas_producto(
    desde:      Optional[str] = None,
    hasta:      Optional[str] = None,
    tipo:       Optional[str] = "ambos",   # "factura" | "recibo" | "ambos"
    cat_id:     Optional[int] = None,
    company_id: Optional[int] = None,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid  = await _resolve_cid(user, company_id, db)
    hoy  = _today()
    d0   = desde or hoy
    d1   = hasta or hoy
    d0, d1 = await per.validar_rango(db, user, d0, d1)
    cat_filter = "AND dc.id = :cat_id" if cat_id else ""

    rows = []

    if tipo in ("factura", "ambos"):
        fact = (await db.execute(text(f"""
            SELECT
                COALESCE(dc.name, 'Sin categoría')         AS categoria,
                COALESCE(d.name, od.dish_id)               AS plato,
                SUM(od.quantity)                           AS cantidad,
                SUM(COALESCE(od.amount, 0))                AS total
            FROM pos_order_details od
            JOIN pos_invoices i
                ON i.invoice_number = od.invoice_number
               AND i.company_id     = od.company_id
               AND i.date           = od.date
               AND i.voided         = 0
            LEFT JOIN pos_dishes d
                ON d.id = od.dish_id AND d.company_id = od.company_id
            LEFT JOIN pos_dish_categories dc
                ON dc.id = d.category_id AND dc.company_id = od.company_id
            WHERE od.company_id = :cid
              AND od.date BETWEEN :d0 AND :d1
              {cat_filter}
            GROUP BY dc.name, d.id, d.name, od.dish_id
        """), {"cid": cid, "d0": d0, "d1": d1, **({"cat_id": cat_id} if cat_id else {})}
        )).mappings().all()
        rows.extend([dict(r) for r in fact])

    if tipo in ("recibo", "ambos"):
        recs = (await db.execute(text(f"""
            SELECT
                COALESCE(dc.name, 'Sin categoría')         AS categoria,
                COALESCE(d.name, od.dish_id)               AS plato,
                SUM(od.quantity)                           AS cantidad,
                SUM(COALESCE(od.amount, 0))                AS total
            FROM pos_receipt_order_details od
            JOIN pos_receipts rc
                ON rc.receipt_number = od.receipt_number
               AND rc.company_id     = od.company_id
               AND rc.date           = od.date
               AND rc.voided         = 0
            LEFT JOIN pos_dishes d
                ON d.id = od.dish_id AND d.company_id = od.company_id
            LEFT JOIN pos_dish_categories dc
                ON dc.id = d.category_id AND dc.company_id = od.company_id
            WHERE od.company_id = :cid
              AND od.date BETWEEN :d0 AND :d1
              {cat_filter}
            GROUP BY dc.name, d.id, d.name, od.dish_id
        """), {"cid": cid, "d0": d0, "d1": d1, **({"cat_id": cat_id} if cat_id else {})}
        )).mappings().all()
        rows.extend([dict(r) for r in recs])

    # Consolidar: mismo plato puede aparecer de facturas y recibos
    merged: dict[str, dict] = {}
    for r in rows:
        key = f"{r['categoria']}|{r['plato']}"
        if key in merged:
            merged[key]["cantidad"] += float(r["cantidad"] or 0)
            merged[key]["total"]    += float(r["total"]    or 0)
        else:
            merged[key] = {
                "categoria": r["categoria"],
                "plato":     r["plato"],
                "cantidad":  float(r["cantidad"] or 0),
                "total":     float(r["total"]    or 0),
            }

    result = sorted(merged.values(), key=lambda x: (x["categoria"] or "", -(x["total"] or 0)))
    return result


# ─── 6. Consumo de insumos agrupado por periodo ───────────────────────────────

@router.get("/ventas-insumo")
async def get_ventas_insumo(
    desde:      Optional[str] = None,
    hasta:      Optional[str] = None,
    tipo:       Optional[str] = "ambos",
    cat_id:     Optional[int] = None,
    company_id: Optional[int] = None,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid  = await _resolve_cid(user, company_id, db)
    hoy  = _today()
    d0   = desde or hoy
    d1   = hasta or hoy
    d0, d1 = await per.validar_rango(db, user, d0, d1)
    cat_filter = "AND dc.id = :cat_id" if cat_id else ""

    rows = []

    if tipo in ("factura", "ambos"):
        fact = (await db.execute(text(f"""
            SELECT
                COALESCE(dc.name, 'Sin categoría')         AS categoria_plato,
                COALESCE(d.name, dp.dish_id)               AS plato,
                dp.item_id,
                COALESCE(si.description, dp.item_id)       AS insumo,
                COALESCE(mu.name, '')                      AS unidad,
                SUM(dp.quantity)                           AS cantidad
            FROM pos_order_detail_products dp
            JOIN pos_invoices i
                ON i.invoice_number = dp.invoice_number
               AND i.company_id     = dp.company_id
               AND i.date           = dp.date
               AND i.voided         = 0
            LEFT JOIN pos_dishes d
                ON d.id = dp.dish_id AND d.company_id = dp.company_id
            LEFT JOIN pos_dish_categories dc
                ON dc.id = d.category_id AND dc.company_id = dp.company_id
            LEFT JOIN supply_items si
                ON si.id_item = dp.item_id AND si.company_id = dp.company_id
            LEFT JOIN pos_measure_forms mu
                ON mu.id = si.unit_id AND mu.company_id = dp.company_id
            WHERE dp.company_id = :cid
              AND dp.date BETWEEN :d0 AND :d1
              {cat_filter}
            GROUP BY dc.name, d.id, d.name, dp.dish_id, dp.item_id, si.description, mu.name
        """), {"cid": cid, "d0": d0, "d1": d1, **({"cat_id": cat_id} if cat_id else {})}
        )).mappings().all()
        rows.extend([dict(r) for r in fact])

    if tipo in ("recibo", "ambos"):
        recs = (await db.execute(text(f"""
            SELECT
                COALESCE(dc.name, 'Sin categoría')         AS categoria_plato,
                COALESCE(d.name, dp.dish_id)               AS plato,
                dp.item_id,
                COALESCE(si.description, dp.item_id)       AS insumo,
                COALESCE(mu.name, '')                      AS unidad,
                SUM(dp.quantity)                           AS cantidad
            FROM pos_receipt_order_detail_products dp
            JOIN pos_receipts rc
                ON rc.receipt_number = dp.invoice_number
               AND rc.company_id     = dp.company_id
               AND rc.date           = dp.date
               AND rc.voided         = 0
            LEFT JOIN pos_dishes d
                ON d.id = dp.dish_id AND d.company_id = dp.company_id
            LEFT JOIN pos_dish_categories dc
                ON dc.id = d.category_id AND dc.company_id = dp.company_id
            LEFT JOIN supply_items si
                ON si.id_item = dp.item_id AND si.company_id = dp.company_id
            LEFT JOIN pos_measure_forms mu
                ON mu.id = si.unit_id AND mu.company_id = dp.company_id
            WHERE dp.company_id = :cid
              AND dp.date BETWEEN :d0 AND :d1
              {cat_filter}
            GROUP BY dc.name, d.id, d.name, dp.dish_id, dp.item_id, si.description, mu.name
        """), {"cid": cid, "d0": d0, "d1": d1, **({"cat_id": cat_id} if cat_id else {})}
        )).mappings().all()
        rows.extend([dict(r) for r in recs])

    # Consolidar por insumo+plato+unidad
    merged: dict[str, dict] = {}
    for r in rows:
        key = f"{r['categoria_plato']}|{r['plato']}|{r['item_id']}|{r['insumo']}"
        if key in merged:
            merged[key]["cantidad"] += float(r["cantidad"] or 0)
        else:
            merged[key] = {
                "categoria_plato": r["categoria_plato"],
                "plato":           r["plato"],
                "insumo":          r["insumo"],
                "unidad":          r["unidad"],
                "cantidad":        float(r["cantidad"] or 0),
            }

    result = sorted(merged.values(), key=lambda x: (x["categoria_plato"] or "", x["plato"] or "", x["insumo"] or ""))
    return result


# ─── 7. Exportar a Excel ───────────────────────────────────────────────────────

@router.get("/export-excel")
async def export_excel(
    desde:      Optional[str] = None,
    hasta:      Optional[str] = None,
    tipo:       str           = "ambos",   # "factura" | "recibo" | "ambos"
    company_id: Optional[int] = None,
    authorization: str        = Header(None),
    db: AsyncSession          = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid  = await _resolve_cid(user, company_id, db)
    hoy  = _today()
    d0   = desde or hoy
    d1   = hasta or hoy
    d0, d1 = await per.validar_rango(db, user, d0, d1)

    # normalizar tipo: consultas usa "factura"/"recibo", export usa "facturas"/"recibos"
    tipo_exp = {"factura": "facturas", "recibo": "recibos", "ambos": "ambos"}.get(tipo, "ambos")

    enc, det, fp = await _query_export(db, cid, tipo_exp, d0, d1)
    xlsx_bytes   = build_ventas_excel(enc, det, fp)

    filename = f"ventas_{d0}_{d1}_{tipo_exp}.xlsx"
    return StreamingResponse(
        io.BytesIO(xlsx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
