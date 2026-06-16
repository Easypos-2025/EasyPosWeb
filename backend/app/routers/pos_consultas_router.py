import json
from datetime import date, datetime, timezone, timedelta
from typing import Optional

_BOG = timezone(timedelta(hours=-5))
def _today() -> str:
    return datetime.now(_BOG).date().isoformat()

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.database import get_db
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.user_model import User

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
        result = await db.execute(select(User).where(User.email == payload.get("sub")))
        user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not user.company_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asignada")
    return user


async def _resolve_cid(user: User, override: Optional[int], db: AsyncSession) -> int:
    """SYSADMIN puede ver cualquier empresa; usuario normal puede ver empresas con el mismo NIT."""
    if not override:
        return user.company_id
    if user.role and user.role.is_system:
        return override
    row = (await db.execute(
        text("""SELECT 1 FROM companies c1
                JOIN companies c2 ON c1.identification_number = c2.identification_number
                WHERE c1.id_company = :uid AND c2.id_company = :oid AND c1.identification_number IS NOT NULL LIMIT 1"""),
        {"uid": user.company_id, "oid": override}
    )).fetchone()
    return override if row else user.company_id


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
    rows.sort(key=lambda x: (x["date"], x["hora"]), reverse=True)
    return rows[:500]


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
                COALESCE(d.name, od.dish_id)              AS plato,
                od.quantity,
                COALESCE(d.price, 0)                      AS price,
                COALESCE(od.amount, 0)                    AS subtotal,
                od.item,
                COALESCE(od.notes, '')                    AS notes,
                COALESCE(od.changes, '')                  AS changes,
                od.custom_product
            FROM pos_receipt_order_details od
            LEFT JOIN pos_dishes d ON d.id = od.dish_id AND d.company_id = :cid
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

    return {
        "header": dict(hdr),
        "items": items_list,
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
