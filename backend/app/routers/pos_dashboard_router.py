from datetime import date, datetime, timezone, timedelta
from typing import Optional

_BOG = timezone(timedelta(hours=-5))
def _today() -> str:
    return datetime.now(_BOG).date().isoformat()

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.database import get_db
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.user_model import User

router = APIRouter(prefix="/api/pos-dashboard", tags=["POS Dashboard"])


# ─── Auth helper ──────────────────────────────────────────────────────────────

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
                WHERE c1.id = :uid AND c2.id = :oid AND c1.identification_number IS NOT NULL LIMIT 1"""),
        {"uid": user.company_id, "oid": override}
    )).fetchone()
    return override if row else user.company_id


# ─── KPIs ─────────────────────────────────────────────────────────────────────

@router.get("/kpis")
async def get_kpis(
    fecha: Optional[str] = None,
    company_id: Optional[int] = None,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid = await _resolve_cid(user, company_id, db)
    fecha = fecha or _today()
    today = _today()

    # Ventas Facturas (DIAN) — excluye propinas (tip + extra_tip)
    r_fact = (await db.execute(text("""
        SELECT
            COALESCE(SUM(cash_amount + credit_card_amount + debit_card_amount
                        + adjustment - discount - tip - extra_tip), 0) AS total,
            COUNT(*) AS cnt
        FROM pos_invoices
        WHERE company_id = :cid AND date = :fecha AND voided = 0
    """), {"cid": cid, "fecha": fecha})).mappings().one()

    # Ventas Recibos (no DIAN) — excluye propinas (tip + extra_tip)
    r_rec = (await db.execute(text("""
        SELECT
            COALESCE(SUM(cash_amount + credit_card_amount + debit_card_amount
                        + adjustment - discount - tip - extra_tip), 0) AS total,
            COUNT(*) AS cnt
        FROM pos_receipts
        WHERE company_id = :cid AND date = :fecha AND voided = 0
    """), {"cid": cid, "fecha": fecha})).mappings().one()

    # Comandas abiertas — siempre HOY (local, sin facturar)
    r_cmd = (await db.execute(text("""
        SELECT
            COALESCE(SUM(amount), 0) AS total,
            COUNT(*)                 AS cnt
        FROM pos_orders
        WHERE company_id = :cid
          AND date = :today
          AND invoice_number = '0'
          AND cancelled = 0
          AND delivery = 0
    """), {"cid": cid, "today": today})).mappings().one()

    # Plataforma / Delivery — siempre HOY (operativo en tiempo real)
    r_plat = (await db.execute(text("""
        SELECT
            COALESCE(SUM(amount), 0) AS total,
            COUNT(*)                 AS cnt
        FROM pos_orders
        WHERE company_id = :cid
          AND date = :today
          AND delivery = 1
          AND cancelled = 0
    """), {"cid": cid, "today": today})).mappings().one()

    # Estado de mesas (pos_tables_layout + pos_orders)
    r_mesas = (await db.execute(text("""
        SELECT
            COALESCE(SUM(CASE WHEN o.order_number IS NULL     THEN 1 ELSE 0 END), 0) AS libres,
            COALESCE(SUM(CASE WHEN o.order_number IS NOT NULL THEN 1 ELSE 0 END), 0) AS ocupadas,
            0 AS cuenta,
            COUNT(t.id) AS total
        FROM pos_tables_layout t
        LEFT JOIN pos_orders o
               ON o.table_id    = t.id
              AND o.company_id  = :cid
              AND o.date        = :today
              AND o.invoice_number = '0'
              AND o.cancelled   = 0
              AND o.delivery    = 0
        WHERE t.company_id = :cid AND t.active = 1
    """), {"cid": cid, "today": today})).mappings().one()

    # Alertas de stock crítico
    r_stock = (await db.execute(text("""
        SELECT COUNT(*) AS cnt
        FROM supply_items
        WHERE company_id=:cid AND is_active=1
          AND control_stock=1 AND min_stock > 0 AND stock_qty <= min_stock
    """), {"cid": cid})).mappings().one()

    return {
        "ventas_facturas":  {"total": int(r_fact["total"]), "count": int(r_fact["cnt"])},
        "ventas_recibos":   {"total": int(r_rec["total"]),  "count": int(r_rec["cnt"])},
        "comandas_abiertas":{"total": int(r_cmd["total"]),  "count": int(r_cmd["cnt"])},
        "plataforma":       {"total": int(r_plat["total"]), "count": int(r_plat["cnt"])},
        "mesas": {
            "libres":   int(r_mesas["libres"]),
            "ocupadas": int(r_mesas["ocupadas"]),
            "cuenta":   int(r_mesas["cuenta"]),
            "total":    int(r_mesas["total"]),
        },
        "stock_alertas": int(r_stock["cnt"]),
        "fecha": fecha,
        "today": today,
    }


# ─── Mesas (layout + estado libre/ocupada) ────────────────────────────────────

@router.get("/mesas")
async def get_mesas(
    company_id: Optional[int] = None,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid = await _resolve_cid(user, company_id, db)
    today = _today()

    rows = (await db.execute(text("""
        SELECT
            t.id, t.name, t.location, t.seats, t.zone_id,
            CASE WHEN o.order_number IS NOT NULL THEN 1 ELSE 0 END AS ocupada,
            o.order_number, o.amount, o.time AS hora_apertura,
            o.guests_count, w.name AS waiter_name
        FROM pos_tables_layout t
        LEFT JOIN pos_orders o
               ON o.table_id    = t.id
              AND o.company_id  = :cid
              AND o.date        = :today
              AND o.invoice_number = '0'
              AND o.cancelled   = 0
              AND o.delivery    = 0
        LEFT JOIN pos_waiters w ON w.id = o.waiter_id AND w.company_id = :cid
        WHERE t.company_id = :cid AND t.active = 1
        ORDER BY t.zone_id, t.name
    """), {"cid": cid, "today": today})).mappings().all()

    return [dict(r) for r in rows]


# ─── Meseros activos (para modal) ─────────────────────────────────────────────

@router.get("/meseros")
async def get_meseros(
    company_id: Optional[int] = None,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid = await _resolve_cid(user, company_id, db)

    rows = (await db.execute(text("""
        SELECT id, name FROM pos_waiters
        WHERE company_id = :cid AND status = 1
        ORDER BY name
    """), {"cid": cid})).mappings().all()

    return [dict(r) for r in rows]


# ─── Comandas abiertas hoy ────────────────────────────────────────────────────

@router.get("/abiertas")
async def get_abiertas(
    company_id: Optional[int] = None,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid = await _resolve_cid(user, company_id, db)
    today = _today()

    rows = (await db.execute(text("""
        SELECT
            o.order_number, o.table_name, o.table_id,
            o.time AS hora_apertura, o.amount, o.guests_count, o.notes,
            w.name AS waiter_name,
            COUNT(od.dish_id) AS item_count
        FROM pos_orders o
        LEFT JOIN pos_waiters w
               ON w.id = o.waiter_id AND w.company_id = :cid
        LEFT JOIN pos_order_details od
               ON od.order_number = o.order_number
              AND od.date         = o.date
              AND od.invoice_number = o.invoice_number
              AND od.company_id   = :cid
        WHERE o.company_id     = :cid
          AND o.date           = :today
          AND o.invoice_number = '0'
          AND o.cancelled      = 0
          AND o.delivery       = 0
        GROUP BY o.order_number, o.date, o.invoice_number,
                 o.table_name, o.table_id, o.time, o.amount,
                 o.guests_count, o.notes, w.name
        ORDER BY o.time ASC
    """), {"cid": cid, "today": today})).mappings().all()

    return [dict(r) for r in rows]


# ─── Comandas facturadas ──────────────────────────────────────────────────────

@router.get("/facturadas")
async def get_facturadas(
    fecha: Optional[str] = None,
    company_id: Optional[int] = None,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid = await _resolve_cid(user, company_id, db)
    fecha = fecha or _today()

    rows = (await db.execute(text("""
        SELECT
            o.order_number, o.invoice_number, o.table_name,
            o.time AS hora_cierre, o.amount, o.guests_count,
            w.name AS waiter_name
        FROM pos_orders o
        LEFT JOIN pos_waiters w
               ON w.id = o.waiter_id AND w.company_id = :cid
        WHERE o.company_id       = :cid
          AND o.date             = :fecha
          AND o.invoice_number  != '0'
          AND o.cancelled        = 0
          AND o.delivery         = 0
        ORDER BY o.time DESC
    """), {"cid": cid, "fecha": fecha})).mappings().all()

    return [dict(r) for r in rows]


# ─── Abrir mesa / pedido ──────────────────────────────────────────────────────

class AbrirMesaIn(BaseModel):
    table_id: int
    table_name: str
    waiter_id: Optional[int] = 0
    guests_count: Optional[int] = 0
    notes: Optional[str] = ""
    delivery: Optional[int] = 0   # 0=local, 1=plataforma/delivery


@router.post("/abrir-mesa")
async def abrir_mesa(
    data: AbrirMesaIn,
    company_id: Optional[int] = None,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid = await _resolve_cid(user, company_id, db)
    today = _today()
    now_time = datetime.now().strftime("%H:%M:%S")

    # Verificar que la mesa no esté ya abierta
    existing = (await db.execute(text("""
        SELECT order_number FROM pos_orders
        WHERE company_id = :cid AND table_id = :tid
          AND date = :today AND invoice_number = '0'
          AND cancelled = 0
        LIMIT 1
    """), {"cid": cid, "tid": data.table_id, "today": today})).fetchone()

    if existing:
        raise HTTPException(status_code=409, detail="La mesa ya tiene una comanda abierta")

    ts = int(datetime.now().timestamp() * 1000)
    order_number = f"WEB-{cid}-{ts}"

    await db.execute(text("""
        INSERT INTO pos_orders
            (order_number, date, invoice_number, table_name, time,
             waiter_id, cancelled, amount, notes, complimentary,
             guests_count, delivery, customer_id, table_id,
             synced, company_id, updated_at)
        VALUES
            (:order_number, :date, '0', :table_name, :time,
             :waiter_id, 0, 0, :notes, 0,
             :guests_count, :delivery, 0, :table_id,
             0, :company_id, NOW())
    """), {
        "order_number": order_number,
        "date":         today,
        "table_name":   data.table_name,
        "time":         now_time,
        "waiter_id":    data.waiter_id,
        "notes":        data.notes or "",
        "guests_count": data.guests_count,
        "delivery":     data.delivery,
        "table_id":     data.table_id,
        "company_id":   cid,
    })
    await db.commit()

    return {"ok": True, "order_number": order_number}


# ─── Últimas transacciones del día ────────────────────────────────────────────

@router.get("/ultimas-transacciones")
async def ultimas_transacciones(
    fecha: Optional[str] = None,
    company_id: Optional[int] = None,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid = await _resolve_cid(user, company_id, db)
    fecha = fecha or _today()

    rows = (await db.execute(text("""
        SELECT tipo, numero, hora, total, cliente
        FROM (
            SELECT 'Factura' AS tipo,
                   invoice_number AS numero,
                   time AS hora,
                   (cash_amount + credit_card_amount + debit_card_amount + adjustment - discount) AS total,
                   customer_id AS cliente
            FROM pos_invoices
            WHERE company_id=:cid AND date=:fecha AND voided=0
            UNION ALL
            SELECT 'Recibo' AS tipo,
                   receipt_number AS numero,
                   time AS hora,
                   (cash_amount + credit_card_amount + debit_card_amount + adjustment - discount) AS total,
                   customer_id AS cliente
            FROM pos_receipts
            WHERE company_id=:cid AND date=:fecha AND voided=0
        ) t
        ORDER BY hora DESC
        LIMIT 10
    """), {"cid": cid, "fecha": fecha})).mappings().all()

    return [dict(r) for r in rows]


# ─── Stock crítico ────────────────────────────────────────────────────────────

@router.get("/stock-alertas")
async def stock_alertas(
    company_id: Optional[int] = None,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid = await _resolve_cid(user, company_id, db)

    rows = (await db.execute(text("""
        SELECT s.id, s.name, s.stock_qty, s.min_stock, u.name AS unit_name
        FROM supply_items s
        LEFT JOIN measurement_units u ON u.id = s.unit_id
        WHERE s.company_id=:cid AND s.is_active=1
          AND s.control_stock=1 AND s.min_stock > 0
          AND s.stock_qty <= s.min_stock
        ORDER BY (s.stock_qty / s.min_stock) ASC
        LIMIT 10
    """), {"cid": cid})).mappings().all()

    return [dict(r) for r in rows]
