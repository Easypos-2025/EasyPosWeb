import os
from typing import List, Optional
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db, get_datatemppos_db
from app.services.plan_limits_service import get_limits

router = APIRouter(prefix="/api/pos", tags=["POS Sync"])

POS_API_KEY = os.getenv("POS_API_KEY", "easypos-sync-key-2024")


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != POS_API_KEY:
        raise HTTPException(status_code=401, detail="API Key inválida")


async def _daily_remaining(company_id: int, limit_field: str, table: str, db) -> int:
    """
    Devuelve cuántos registros nuevos puede crear hoy la empresa para la tabla dada.
    -1 = ilimitado. 0 = límite alcanzado.
    """
    limits = await get_limits(company_id, db)
    max_val = limits.get(limit_field, -1)
    if max_val == -1:
        return -1
    today = date.today().isoformat()
    row = (await db.execute(
        text(f"SELECT COUNT(*) FROM {table} WHERE company_id=:cid AND date=:today"),
        {"cid": company_id, "today": today},
    )).scalar() or 0
    return max(0, max_val - row)


async def _exists_in_table(table: str, pk_col: str, pk_val: str, company_id: int, db) -> bool:
    row = (await db.execute(
        text(f"SELECT 1 FROM {table} WHERE {pk_col}=:pk AND company_id=:cid LIMIT 1"),
        {"pk": pk_val, "cid": company_id},
    )).fetchone()
    return row is not None


# ─────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────
class InvoiceIn(BaseModel):
    invoice_number: str
    company_id: int
    date: Optional[str] = None
    cash_amount: Optional[int] = 0
    discount: Optional[int] = 0
    customer_id: Optional[int] = 0
    employee_id: Optional[int] = 0
    voided: Optional[int] = 0
    paid_vat: Optional[int] = 0
    adjustment: Optional[int] = 0
    credit_card_amount: Optional[int] = 0
    debit_card_amount: Optional[int] = 0
    tip: Optional[int] = 0
    shift: Optional[int] = 0
    time: Optional[str] = None
    time_text: Optional[str] = None
    extra_tip: Optional[int] = 0
    amount_without_tip: Optional[int] = 0
    analyzed: Optional[int] = 0
    currency_type_id: Optional[int] = 0
    foreign_amount: Optional[float] = 0
    manual_invoice: Optional[int] = 0
    resolution_id: Optional[int] = 0
    reservation_invoice: Optional[str] = "0"
    delivery_invoice: Optional[int] = 0


# ─────────────────────────────────────────
# TEST
# ─────────────────────────────────────────
@router.get("/test/users")
async def get_users(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    result = await db.execute(
        text("SELECT id, nombre, email, company_id, is_active FROM users ORDER BY id")
    )
    rows = result.mappings().all()
    return {"total": len(rows), "users": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# ORDERS / COMANDAS — pos_orders + pos_receipt_orders
# ═════════════════════════════════════════

class OrderIn(BaseModel):
    order_number:  str
    date:          str
    invoice_number: Optional[str] = "0"
    company_id:    int
    table_name:    Optional[str]  = ""
    time:          Optional[str]  = None
    waiter_id:     Optional[int]  = 0
    cancelled:     Optional[int]  = 0
    amount:        Optional[int]  = 0
    notes:         Optional[str]  = ""
    complimentary: Optional[int]  = 0
    guests_count:  Optional[int]  = 0
    delivery:      Optional[int]  = 0
    customer_id:   Optional[int]  = 0
    table_id:      Optional[int]  = 0


@router.post("/sync/push/orders")
async def push_orders(
    orders: List[OrderIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for o in orders:
        key = f"{o.order_number}|{o.date}|{o.invoice_number}"
        try:
            await db.execute(text("""
                INSERT INTO pos_orders
                    (order_number, date, invoice_number, table_name, time,
                     waiter_id, cancelled, amount, notes, complimentary,
                     guests_count, delivery, customer_id, table_id,
                     synced, company_id, updated_at)
                VALUES
                    (:order_number, :date, :invoice_number, :table_name, :time,
                     :waiter_id, :cancelled, :amount, :notes, :complimentary,
                     :guests_count, :delivery, :customer_id, :table_id,
                     1, :company_id, NOW())
                ON DUPLICATE KEY UPDATE
                    table_name    = VALUES(table_name),
                    invoice_number= VALUES(invoice_number),
                    cancelled     = VALUES(cancelled),
                    amount        = VALUES(amount),
                    waiter_id     = VALUES(waiter_id),
                    synced        = 1,
                    updated_at    = NOW()
            """), o.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(orders), "total_saved": len(saved), "total_failed": len(failed)}


class ReceiptOrderIn(BaseModel):
    order_number:  str
    date:          str
    receipt_number: Optional[str] = "0"
    company_id:    int
    table_name:    Optional[str]  = ""
    time:          Optional[str]  = None
    waiter_id:     Optional[int]  = 0
    cancelled:     Optional[int]  = 0
    amount:        Optional[int]  = 0
    notes:         Optional[str]  = ""
    complimentary: Optional[int]  = 0
    guests_count:  Optional[int]  = 0
    delivery:      Optional[int]  = 0
    customer_id:   Optional[int]  = 0
    table_id:      Optional[int]  = 0


@router.post("/sync/push/receipt-orders")
async def push_receipt_orders(
    orders: List[ReceiptOrderIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for o in orders:
        key = f"{o.order_number}|{o.date}|{o.receipt_number}"
        try:
            await db.execute(text("""
                INSERT INTO pos_receipt_orders
                    (order_number, date, receipt_number, table_name, time,
                     waiter_id, cancelled, amount, notes, complimentary,
                     guests_count, delivery, customer_id, table_id,
                     synced, company_id, updated_at)
                VALUES
                    (:order_number, :date, :receipt_number, :table_name, :time,
                     :waiter_id, :cancelled, :amount, :notes, :complimentary,
                     :guests_count, :delivery, :customer_id, :table_id,
                     1, :company_id, NOW())
                ON DUPLICATE KEY UPDATE
                    table_name     = VALUES(table_name),
                    receipt_number = VALUES(receipt_number),
                    cancelled      = VALUES(cancelled),
                    amount         = VALUES(amount),
                    waiter_id      = VALUES(waiter_id),
                    synced         = 1,
                    updated_at     = NOW()
            """), o.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(orders), "total_saved": len(saved), "total_failed": len(failed)}


# ─────────────────────────────────────────
# PUSH — VB6 envía facturas al servidor
# ─────────────────────────────────────────
@router.post("/sync/push/invoices")
async def push_invoices(
    invoices: List[InvoiceIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved = []
    failed = []

    # Agrupamos por company_id para calcular slots restantes una sola vez por empresa
    company_remaining: dict[int, int] = {}

    for inv in invoices:
        cid = inv.company_id
        is_existing = await _exists_in_table("pos_invoices", "invoice_number", inv.invoice_number, cid, db)

        if not is_existing:
            if cid not in company_remaining:
                company_remaining[cid] = await _daily_remaining(cid, "max_daily_invoices", "pos_invoices", db)
            if company_remaining[cid] == 0:
                failed.append({"invoice_number": inv.invoice_number,
                               "error": "Límite diario de facturas alcanzado en tu plan"})
                continue
            if company_remaining[cid] > 0:
                company_remaining[cid] -= 1

        try:
            await db.execute(text("""
                INSERT INTO pos_invoices (
                    invoice_number, company_id, date, cash_amount, discount,
                    customer_id, employee_id, voided, paid_vat, adjustment,
                    credit_card_amount, debit_card_amount, tip, shift,
                    time, time_text, extra_tip, amount_without_tip, analyzed,
                    currency_type_id, foreign_amount, manual_invoice, resolution_id,
                    reservation_invoice, delivery_invoice, synced, updated_at
                ) VALUES (
                    :invoice_number, :company_id, :date, :cash_amount, :discount,
                    :customer_id, :employee_id, :voided, :paid_vat, :adjustment,
                    :credit_card_amount, :debit_card_amount, :tip, :shift,
                    :time, :time_text, :extra_tip, :amount_without_tip, :analyzed,
                    :currency_type_id, :foreign_amount, :manual_invoice, :resolution_id,
                    :reservation_invoice, :delivery_invoice, 1, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    cash_amount        = VALUES(cash_amount),
                    discount           = VALUES(discount),
                    customer_id        = VALUES(customer_id),
                    employee_id        = VALUES(employee_id),
                    voided             = VALUES(voided),
                    credit_card_amount = VALUES(credit_card_amount),
                    debit_card_amount  = VALUES(debit_card_amount),
                    tip                = VALUES(tip),
                    extra_tip          = VALUES(extra_tip),
                    amount_without_tip = VALUES(amount_without_tip),
                    currency_type_id   = VALUES(currency_type_id),
                    delivery_invoice   = VALUES(delivery_invoice),
                    synced             = 1,
                    updated_at         = NOW()
            """), inv.dict())
            saved.append(inv.invoice_number)
        except Exception as e:
            failed.append({"invoice_number": inv.invoice_number, "error": str(e)})

    await db.commit()

    return {
        "saved": saved,
        "failed": failed,
        "total_sent": len(invoices),
        "total_saved": len(saved),
        "total_failed": len(failed),
    }

 
# ─────────────────────────────────────────
# PULL — VB6 pide facturas desde el servidor
# ─────────────────────────────────────────
@router.get("/sync/pull/invoices")
async def pull_invoices(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM pos_invoices WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 500"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "invoices": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# ORDERS (comanda)
# ═════════════════════════════════════════
class OrderIn(BaseModel):
    order_number: str
    date: str
    invoice_number: str
    company_id: int
    table_name: Optional[str] = "0"
    time: Optional[str] = None
    waiter_id: Optional[int] = 0
    cancelled: Optional[int] = 0
    amount: Optional[int] = 0
    notes: Optional[str] = None
    complimentary: Optional[int] = 0
    guests_count: Optional[int] = 0
    delivery: Optional[int] = 0
    customer_id: Optional[int] = 0
    table_id: Optional[int] = 0


@router.post("/sync/push/orders")
async def push_orders(
    orders: List[OrderIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for o in orders:
        try:
            await db.execute(text("""
                INSERT INTO pos_orders (
                    order_number, date, invoice_number, company_id,
                    table_name, time, waiter_id, cancelled, amount,
                    notes, complimentary, guests_count, delivery,
                    customer_id, table_id, synced, updated_at
                ) VALUES (
                    :order_number, :date, :invoice_number, :company_id,
                    :table_name, :time, :waiter_id, :cancelled, :amount,
                    :notes, :complimentary, :guests_count, :delivery,
                    :customer_id, :table_id, 1, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    waiter_id    = VALUES(waiter_id),
                    cancelled    = VALUES(cancelled),
                    amount       = VALUES(amount),
                    notes        = VALUES(notes),
                    customer_id  = VALUES(customer_id),
                    table_id     = VALUES(table_id),
                    synced       = 1,
                    updated_at   = NOW()
            """), o.dict())
            saved.append(o.order_number)
        except Exception as e:
            failed.append({"order_number": o.order_number, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(orders), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/orders")
async def pull_orders(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM pos_orders WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 500"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "orders": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# ORDER DETAILS (detalle_comanda)
# ═════════════════════════════════════════
class OrderDetailIn(BaseModel):
    order_number: str
    date: str
    invoice_number: str
    dish_id: int
    item: int
    depends_on: int
    company_id: int
    quantity: Optional[float] = 0
    amount: Optional[int] = 0
    notes: Optional[str] = None
    complimentary: Optional[int] = 0
    dish_discount_pct: Optional[float] = 0
    general_discount_pct: Optional[float] = 0
    seat_number: Optional[int] = 0
    changes: Optional[str] = None
    dish_time: Optional[str] = None
    pays_tax: Optional[int] = 0
    tax: Optional[float] = 0
    original_tax: Optional[float] = 0
    pays_dish: Optional[int] = 0
    custom_product: Optional[str] = None


@router.post("/sync/push/order-details")
async def push_order_details(
    details: List[OrderDetailIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for d in details:
        key = f"{d.order_number}|{d.date}|{d.invoice_number}|{d.dish_id}|{d.item}|{d.depends_on}"
        try:
            await db.execute(text("""
                INSERT INTO pos_order_details (
                    order_number, date, invoice_number, dish_id, item, depends_on, company_id,
                    quantity, amount, notes, complimentary, dish_discount_pct,
                    general_discount_pct, seat_number, changes, dish_time,
                    pays_tax, tax, original_tax, pays_dish, custom_product,
                    synced, updated_at
                ) VALUES (
                    :order_number, :date, :invoice_number, :dish_id, :item, :depends_on, :company_id,
                    :quantity, :amount, :notes, :complimentary, :dish_discount_pct,
                    :general_discount_pct, :seat_number, :changes, :dish_time,
                    :pays_tax, :tax, :original_tax, :pays_dish, :custom_product,
                    1, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    quantity             = VALUES(quantity),
                    amount               = VALUES(amount),
                    notes                = VALUES(notes),
                    dish_discount_pct    = VALUES(dish_discount_pct),
                    general_discount_pct = VALUES(general_discount_pct),
                    pays_tax             = VALUES(pays_tax),
                    tax                  = VALUES(tax),
                    synced               = 1,
                    updated_at           = NOW()
            """), d.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(details), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/order-details")
async def pull_order_details(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM pos_order_details WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 1000"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "order_details": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# RECEIPTS (recibos) — misma normalización que invoices
# ═════════════════════════════════════════
class ReceiptIn(BaseModel):
    invoice_number: str            # VB6 envía invoice_number; DB columna = receipt_number
    company_id: int
    date: Optional[str] = None
    cash_amount: Optional[int] = 0
    discount: Optional[int] = 0
    customer_id: Optional[int] = 0
    employee_id: Optional[int] = 0
    voided: Optional[int] = 0
    paid_vat: Optional[int] = 0
    adjustment: Optional[int] = 0
    credit_card_amount: Optional[int] = 0
    debit_card_amount: Optional[int] = 0
    tip: Optional[int] = 0
    shift: Optional[int] = 0
    time: Optional[str] = None
    time_text: Optional[str] = None
    extra_tip: Optional[int] = 0
    amount_without_tip: Optional[int] = 0
    analyzed: Optional[int] = 0
    currency_type_id: Optional[int] = 0
    foreign_amount: Optional[float] = 0
    manual_receipt: Optional[int] = 0
    resolution_id: Optional[int] = 0
    reservation_receipt: Optional[str] = "0"
    delivery_invoice: Optional[int] = 0   # VB6 envía delivery_invoice; DB columna = delivery_receipt


@router.post("/sync/push/receipts")
async def push_receipts(
    receipts: List[ReceiptIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    company_remaining: dict[int, int] = {}

    for r in receipts:
        cid = r.company_id
        is_existing = await _exists_in_table("pos_receipts", "receipt_number", r.invoice_number, cid, db)

        if not is_existing:
            if cid not in company_remaining:
                company_remaining[cid] = await _daily_remaining(cid, "max_daily_receipts", "pos_receipts", db)
            if company_remaining[cid] == 0:
                failed.append({"invoice_number": r.invoice_number,
                               "error": "Límite diario de recibos alcanzado en tu plan"})
                continue
            if company_remaining[cid] > 0:
                company_remaining[cid] -= 1

        try:
            await db.execute(text("""
                INSERT INTO pos_receipts (
                    receipt_number, company_id, date, cash_amount, discount,
                    customer_id, employee_id, voided, paid_vat, adjustment,
                    credit_card_amount, debit_card_amount, tip, shift,
                    time, time_text, extra_tip, amount_without_tip, analyzed,
                    currency_type, foreign_amount, manual_receipt, resolution_id,
                    reservation_receipt, delivery_receipt, synced, updated_at
                ) VALUES (
                    :invoice_number, :company_id, :date, :cash_amount, :discount,
                    :customer_id, :employee_id, :voided, :paid_vat, :adjustment,
                    :credit_card_amount, :debit_card_amount, :tip, :shift,
                    :time, :time_text, :extra_tip, :amount_without_tip, :analyzed,
                    :currency_type_id, :foreign_amount, :manual_receipt, :resolution_id,
                    :reservation_receipt, :delivery_invoice, 1, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    cash_amount        = VALUES(cash_amount),
                    discount           = VALUES(discount),
                    customer_id        = VALUES(customer_id),
                    employee_id        = VALUES(employee_id),
                    voided             = VALUES(voided),
                    credit_card_amount = VALUES(credit_card_amount),
                    debit_card_amount  = VALUES(debit_card_amount),
                    tip                = VALUES(tip),
                    extra_tip          = VALUES(extra_tip),
                    amount_without_tip = VALUES(amount_without_tip),
                    currency_type      = VALUES(currency_type),
                    delivery_receipt   = VALUES(delivery_receipt),
                    synced             = 1,
                    updated_at         = NOW()
            """), r.dict())
            saved.append(r.invoice_number)
        except Exception as e:
            failed.append({"invoice_number": r.invoice_number, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(receipts), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/receipts")
async def pull_receipts(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM pos_receipts WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 500"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "receipts": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# DISHES (platos)
# ═════════════════════════════════════════
class DishIn(BaseModel):
    id: int
    company_id: int
    name: Optional[str] = None
    product_code: Optional[str] = None
    price: Optional[int] = 0
    preparation_time: Optional[int] = 0
    active: Optional[int] = 0
    category_id: Optional[int] = 0
    photo_path: Optional[str] = None
    description: Optional[str] = None
    printer: Optional[str] = None
    comment: Optional[str] = None
    extra_print: Optional[str] = None
    printer_2: Optional[str] = None
    pre_preparation: Optional[int] = 0
    offer: Optional[int] = 0
    offer_priority: Optional[int] = 0
    tax: Optional[float] = 0
    wholesale_price: Optional[float] = 0
    product_cost: Optional[float] = 0
    minimum_stock: Optional[float] = 0
    procedure: Optional[str] = None
    ask_sale_price: Optional[int] = 0
    ask_product_description: Optional[int] = 0


@router.post("/sync/push/dishes")
async def push_dishes(
    dishes: List[DishIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for d in dishes:
        try:
            await db.execute(text("""
                INSERT INTO pos_dishes (
                    id, company_id, name, product_code, price, preparation_time,
                    active, category_id, photo_path, `procedure`, description,
                    printer, comment, extra_print, printer_2, pre_preparation,
                    offer, offer_priority, tax, wholesale_price, product_cost,
                    minimum_stock, ask_sale_price, ask_product_description, synced, updated_at
                ) VALUES (
                    :id, :company_id, :name, :product_code, :price, :preparation_time,
                    :active, :category_id, :photo_path, :procedure, :description,
                    :printer, :comment, :extra_print, :printer_2, :pre_preparation,
                    :offer, :offer_priority, :tax, :wholesale_price, :product_cost,
                    :minimum_stock, :ask_sale_price, :ask_product_description, 1, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    name                      = VALUES(name),
                    product_code              = VALUES(product_code),
                    price                     = VALUES(price),
                    preparation_time          = VALUES(preparation_time),
                    active                    = VALUES(active),
                    category_id               = VALUES(category_id),
                    photo_path                = VALUES(photo_path),
                    `procedure`               = VALUES(`procedure`),
                    description               = VALUES(description),
                    printer                   = VALUES(printer),
                    comment                   = VALUES(comment),
                    extra_print               = VALUES(extra_print),
                    printer_2                 = VALUES(printer_2),
                    pre_preparation           = VALUES(pre_preparation),
                    offer                     = VALUES(offer),
                    offer_priority            = VALUES(offer_priority),
                    tax                       = VALUES(tax),
                    wholesale_price           = VALUES(wholesale_price),
                    product_cost              = VALUES(product_cost),
                    minimum_stock             = VALUES(minimum_stock),
                    ask_sale_price            = VALUES(ask_sale_price),
                    ask_product_description   = VALUES(ask_product_description),
                    synced                    = 1,
                    updated_at                = NOW()
            """), d.dict())
            saved.append(d.id)
        except Exception as e:
            failed.append({"id": d.id, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(dishes), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/dishes")
async def pull_dishes(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM pos_dishes WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 500"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "dishes": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# ZONES (zonas_asientos)
# ═════════════════════════════════════════
class ZoneIn(BaseModel):
    id: int
    company_id: int
    branch_id: Optional[int] = 1       # Id_Sede en VB6
    name: Optional[str] = None          # Ubicacion
    seats_count: Optional[int] = 0      # Nro_Asientos
    is_active: Optional[int] = 1        # Activa
    dynamic_zone: Optional[int] = 0     # Zona_Dinamica
    color: Optional[str] = "#1d4ed8"    # Color
    height: Optional[int] = 0           # Altura


@router.post("/sync/push/zones")
async def push_zones(
    zones: List[ZoneIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for z in zones:
        try:
            await db.execute(text("""
                INSERT INTO pos_zones (
                    id, company_id, branch_id, name, seats_count, is_active,
                    dynamic_zone, color, height, synced, updated_at
                ) VALUES (
                    :id, :company_id, :branch_id, :name, :seats_count, :is_active,
                    :dynamic_zone, :color, :height, 1, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    branch_id    = VALUES(branch_id),
                    name         = VALUES(name),
                    seats_count  = VALUES(seats_count),
                    is_active    = VALUES(is_active),
                    dynamic_zone = VALUES(dynamic_zone),
                    color        = VALUES(color),
                    height       = VALUES(height),
                    synced       = 1,
                    updated_at   = NOW()
            """), z.dict())
            saved.append(z.id)
        except Exception as e:
            failed.append({"id": z.id, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(zones), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/zones")
async def pull_zones(
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    rows = (await db.execute(text(
        "SELECT * FROM pos_zones WHERE company_id = :cid ORDER BY id"
    ), {"cid": company_id})).mappings().all()
    return {"total": len(rows), "zones": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# EMPLOYEES (empleados)
# ═════════════════════════════════════════
class EmployeeIn(BaseModel):
    id: int
    company_id: int
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    login: str
    password: str
    status: Optional[int] = 0
    employee_type: Optional[int] = 0
    personal_skin: Optional[int] = 0


@router.post("/sync/push/employees")
async def push_employees(
    employees: List[EmployeeIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for e in employees:
        try:
            await db.execute(text("""
                INSERT INTO pos_employees (
                    id, company_id, name, phone, address, login, password,
                    status, employee_type, personal_skin, synced, updated_at
                ) VALUES (
                    :id, :company_id, :name, :phone, :address, :login, :password,
                    :status, :employee_type, :personal_skin, 1, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    name          = VALUES(name),
                    phone         = VALUES(phone),
                    address       = VALUES(address),
                    login         = VALUES(login),
                    password      = VALUES(password),
                    status        = VALUES(status),
                    employee_type = VALUES(employee_type),
                    synced        = 1,
                    updated_at    = NOW()
            """), e.dict())
            saved.append(e.id)
        except Exception as e2:
            failed.append({"id": e.id, "error": str(e2)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(employees), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/employees")
async def pull_employees(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM pos_employees WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 500"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "employees": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# WAITERS (meseros)
# ═════════════════════════════════════════
class WaiterIn(BaseModel):
    id: int
    company_id: int
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    password: Optional[str] = None
    status: Optional[int] = 0
    employee_type: Optional[int] = 0


@router.post("/sync/push/waiters")
async def push_waiters(
    waiters: List[WaiterIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []

    # Agrupar por company_id para calcular slots disponibles una vez
    company_slots: dict[int, int] = {}

    for w in waiters:
        cid = w.company_id
        is_existing = await _exists_in_table("pos_waiters", "id", str(w.id), cid, db)

        if not is_existing:
            if cid not in company_slots:
                limits = await get_limits(cid, db)
                max_w = limits.get("max_waiters", -1)
                if max_w == -1:
                    company_slots[cid] = -1
                else:
                    active_count = (await db.execute(
                        text("SELECT COUNT(*) FROM pos_waiters WHERE company_id=:cid AND plan_blocked=0"),
                        {"cid": cid},
                    )).scalar() or 0
                    company_slots[cid] = max(0, max_w - active_count)

            if company_slots[cid] == 0:
                failed.append({"id": w.id,
                               "error": "Límite de meseros/cajeros POS alcanzado en tu plan"})
                continue
            if company_slots[cid] > 0:
                company_slots[cid] -= 1

        try:
            await db.execute(text("""
                INSERT INTO pos_waiters (
                    id, company_id, name, phone, address, password,
                    status, employee_type, synced, updated_at
                ) VALUES (
                    :id, :company_id, :name, :phone, :address, :password,
                    :status, :employee_type, 1, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    name          = VALUES(name),
                    phone         = VALUES(phone),
                    address       = VALUES(address),
                    password      = VALUES(password),
                    status        = VALUES(status),
                    employee_type = VALUES(employee_type),
                    synced        = 1,
                    updated_at    = NOW()
            """), w.dict())
            saved.append(w.id)
        except Exception as e:
            failed.append({"id": w.id, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(waiters), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/waiters")
async def pull_waiters(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM pos_waiters WHERE company_id = :company_id AND plan_blocked = 0"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 500"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "waiters": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# TABLES (mesas)
# ═════════════════════════════════════════
class TableIn(BaseModel):
    id: int
    company_id: int
    zone_id: Optional[int] = 0
    name: str
    capacity: Optional[int] = 0
    is_active: Optional[int] = 0


@router.post("/sync/push/tables")
async def push_tables(
    tables: List[TableIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for t in tables:
        try:
            await db.execute(text("""
                INSERT INTO pos_tables_layout (
                    id, company_id, zone_id, name, seats, active,
                    branch_id, customer_id, dynamic_zone, location,
                    synced, updated_at
                ) VALUES (
                    :id, :company_id, :zone_id, :name, :capacity, :is_active,
                    0, 0, 0, '',
                    1, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    name       = VALUES(name),
                    seats      = VALUES(seats),
                    zone_id    = VALUES(zone_id),
                    synced     = 1,
                    updated_at = NOW()
            """), t.dict())
            saved.append(t.id)
        except Exception as e:
            failed.append({"id": t.id, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(tables), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/tables")
async def pull_tables(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM pos_tables_layout WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 500"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "tables": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# INVOICE DETAILS (detalle_factura)
# ═════════════════════════════════════════
class InvoiceDetailIn(BaseModel):
    invoice_number: str
    order_number: str
    date: str
    dish_id: int
    item: int
    depends_on: int
    company_id: int
    quantity: Optional[float] = 0
    notes: Optional[str] = None
    dish_amount: Optional[int] = 0
    complimentary: Optional[int] = 0
    discount_pct: Optional[float] = 0


@router.post("/sync/push/invoice-details")
async def push_invoice_details(
    details: List[InvoiceDetailIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for d in details:
        key = f"{d.invoice_number}|{d.order_number}|{d.date}|{d.dish_id}|{d.item}|{d.depends_on}"
        try:
            await db.execute(text("""
                INSERT INTO pos_invoice_details (
                    invoice_number, order_number, date, dish_id, item, depends_on, company_id,
                    quantity, notes, dish_amount, complimentary, discount_pct,
                    synced, updated_at
                ) VALUES (
                    :invoice_number, :order_number, :date, :dish_id, :item, :depends_on, :company_id,
                    :quantity, :notes, :dish_amount, :complimentary, :discount_pct,
                    1, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    quantity     = VALUES(quantity),
                    notes        = VALUES(notes),
                    dish_amount  = VALUES(dish_amount),
                    complimentary= VALUES(complimentary),
                    discount_pct = VALUES(discount_pct),
                    synced       = 1,
                    updated_at   = NOW()
            """), d.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(details), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/invoice-details")
async def pull_invoice_details(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM pos_invoice_details WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 1000"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "invoice_details": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# INVOICE PAYMENT METHODS (factura_forma_pago)
# ═════════════════════════════════════════
class InvoicePaymentIn(BaseModel):
    item: int
    payment_method_id: int
    card_id: int
    invoice_number: str
    company_id: int
    amount: Optional[float] = 0
    date: Optional[str] = None
    authorization: Optional[float] = 0
    notes: Optional[str] = None
    delivery_amount: Optional[float] = 0
    prefix: Optional[str] = None
    fac_pe: Optional[str] = None
    order_number: Optional[str] = None


@router.post("/sync/push/invoice-payments")
async def push_invoice_payments(
    payments: List[InvoicePaymentIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for p in payments:
        key = f"{p.item}|{p.payment_method_id}|{p.card_id}|{p.invoice_number}"
        try:
            await db.execute(text("""
                INSERT INTO pos_invoice_payment_methods (
                    item, payment_method_id, card_id, invoice_number, company_id,
                    amount, date, authorization, notes, delivery_amount,
                    prefix, fac_pe, order_number, synced, updated_at
                ) VALUES (
                    :item, :payment_method_id, :card_id, :invoice_number, :company_id,
                    :amount, :date, :authorization, :notes, :delivery_amount,
                    :prefix, :fac_pe, :order_number, 1, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    amount          = VALUES(amount),
                    authorization   = VALUES(authorization),
                    notes           = VALUES(notes),
                    delivery_amount = VALUES(delivery_amount),
                    synced          = 1,
                    updated_at      = NOW()
            """), p.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(payments), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/invoice-payments")
async def pull_invoice_payments(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM pos_invoice_payment_methods WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 1000"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "invoice_payments": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# RECEIPT ORDERS (recibos_comanda)
# ═════════════════════════════════════════
class ReceiptOrderIn(BaseModel):
    order_number: str
    date: str
    receipt_number: str
    company_id: int
    table_name: Optional[str] = "0"
    time: Optional[str] = None
    waiter_id: Optional[int] = 0
    cancelled: Optional[int] = 0
    amount: Optional[int] = 0
    notes: Optional[str] = None
    complimentary: Optional[int] = 0
    guests_count: Optional[int] = 0
    delivery: Optional[int] = 0
    customer_id: Optional[int] = 0
    table_id: Optional[int] = 0


@router.post("/sync/push/receipt-orders")
async def push_receipt_orders(
    orders: List[ReceiptOrderIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for o in orders:
        key = f"{o.order_number}|{o.date}|{o.receipt_number}"
        try:
            await db.execute(text("""
                INSERT INTO pos_receipt_orders (
                    order_number, date, receipt_number, company_id,
                    table_name, time, waiter_id, cancelled, amount,
                    notes, complimentary, guests_count, delivery,
                    customer_id, table_id, synced, updated_at
                ) VALUES (
                    :order_number, :date, :receipt_number, :company_id,
                    :table_name, :time, :waiter_id, :cancelled, :amount,
                    :notes, :complimentary, :guests_count, :delivery,
                    :customer_id, :table_id, 1, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    waiter_id   = VALUES(waiter_id),
                    cancelled   = VALUES(cancelled),
                    amount      = VALUES(amount),
                    notes       = VALUES(notes),
                    customer_id = VALUES(customer_id),
                    synced      = 1,
                    updated_at  = NOW()
            """), o.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(orders), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/receipt-orders")
async def pull_receipt_orders(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM pos_receipt_orders WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 500"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "receipt_orders": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# RECEIPT ORDER DETAILS (recibos_detalle_comanda)
# ═════════════════════════════════════════
class ReceiptOrderDetailIn(BaseModel):
    order_number: str
    date: str
    receipt_number: str
    dish_id: int
    item: int
    depends_on: int
    company_id: int
    quantity: Optional[float] = 0
    amount: Optional[int] = 0
    notes: Optional[str] = None
    complimentary: Optional[int] = 0
    dish_discount_pct: Optional[float] = 0
    general_discount_pct: Optional[float] = 0
    seat_number: Optional[int] = 0
    changes: Optional[str] = None
    dish_time: Optional[str] = None
    pays_tax: Optional[int] = 0
    tax: Optional[float] = 0
    original_tax: Optional[float] = 0
    pays_dish: Optional[int] = 0
    custom_product: Optional[str] = None


@router.post("/sync/push/receipt-order-details")
async def push_receipt_order_details(
    details: List[ReceiptOrderDetailIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for d in details:
        key = f"{d.order_number}|{d.date}|{d.receipt_number}|{d.dish_id}|{d.item}|{d.depends_on}"
        try:
            await db.execute(text("""
                INSERT INTO pos_receipt_order_details (
                    order_number, date, receipt_number, dish_id, item, depends_on, company_id,
                    quantity, amount, notes, complimentary, dish_discount_pct,
                    general_discount_pct, seat_number, changes, dish_time,
                    pays_tax, tax, original_tax, pays_dish, custom_product,
                    synced, updated_at
                ) VALUES (
                    :order_number, :date, :receipt_number, :dish_id, :item, :depends_on, :company_id,
                    :quantity, :amount, :notes, :complimentary, :dish_discount_pct,
                    :general_discount_pct, :seat_number, :changes, :dish_time,
                    :pays_tax, :tax, :original_tax, :pays_dish, :custom_product,
                    1, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    quantity             = VALUES(quantity),
                    amount               = VALUES(amount),
                    notes                = VALUES(notes),
                    dish_discount_pct    = VALUES(dish_discount_pct),
                    general_discount_pct = VALUES(general_discount_pct),
                    pays_tax             = VALUES(pays_tax),
                    tax                  = VALUES(tax),
                    synced               = 1,
                    updated_at           = NOW()
            """), d.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(details), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/receipt-order-details")
async def pull_receipt_order_details(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM pos_receipt_order_details WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 1000"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "receipt_order_details": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# RECEIPT INVOICE DETAILS (recibos_detalle_factura)
# ═════════════════════════════════════════
class ReceiptInvoiceDetailIn(BaseModel):
    receipt_number: str
    order_number: str
    date: str
    dish_id: int
    item: int
    depends_on: int
    company_id: int
    quantity: Optional[float] = None
    notes: Optional[str] = None
    dish_amount: Optional[int] = 0
    complimentary: Optional[int] = 0
    discount_pct: Optional[float] = 0


@router.post("/sync/push/receipt-invoice-details")
async def push_receipt_invoice_details(
    details: List[ReceiptInvoiceDetailIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for d in details:
        key = f"{d.receipt_number}|{d.order_number}|{d.date}|{d.dish_id}|{d.item}|{d.depends_on}"
        try:
            await db.execute(text("""
                INSERT INTO pos_receipt_invoice_details (
                    receipt_number, order_number, date, dish_id, item, depends_on, company_id,
                    quantity, notes, dish_amount, complimentary, discount_pct,
                    synced, updated_at
                ) VALUES (
                    :receipt_number, :order_number, :date, :dish_id, :item, :depends_on, :company_id,
                    :quantity, :notes, :dish_amount, :complimentary, :discount_pct,
                    1, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    quantity     = VALUES(quantity),
                    notes        = VALUES(notes),
                    dish_amount  = VALUES(dish_amount),
                    discount_pct = VALUES(discount_pct),
                    synced       = 1,
                    updated_at   = NOW()
            """), d.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(details), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/receipt-invoice-details")
async def pull_receipt_invoice_details(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM pos_receipt_invoice_details WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 1000"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "receipt_invoice_details": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# RECEIPT PAYMENT METHODS (recibos_forma_pago)
# ═════════════════════════════════════════
class ReceiptPaymentIn(BaseModel):
    item: int
    payment_method_id: int
    card_id: int
    invoice_number: str
    company_id: int
    amount: Optional[float] = 0
    date: Optional[str] = None
    authorization: Optional[float] = 0
    notes: Optional[str] = None
    delivery_amount: Optional[float] = 0
    prefix: Optional[str] = None
    fac_pe: Optional[str] = None
    order_number: Optional[str] = None


@router.post("/sync/push/receipt-payments")
async def push_receipt_payments(
    payments: List[ReceiptPaymentIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for p in payments:
        key = f"{p.item}|{p.payment_method_id}|{p.card_id}|{p.invoice_number}"
        try:
            await db.execute(text("""
                INSERT INTO pos_receipt_payment_methods (
                    item, payment_method_id, card_id, invoice_number, company_id,
                    amount, date, authorization, notes, delivery_amount,
                    prefix, fac_pe, order_number, synced, updated_at
                ) VALUES (
                    :item, :payment_method_id, :card_id, :invoice_number, :company_id,
                    :amount, :date, :authorization, :notes, :delivery_amount,
                    :prefix, :fac_pe, :order_number, 1, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    amount          = VALUES(amount),
                    authorization   = VALUES(authorization),
                    notes           = VALUES(notes),
                    delivery_amount = VALUES(delivery_amount),
                    synced          = 1,
                    updated_at      = NOW()
            """), p.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(payments), "total_saved": len(saved), "total_failed": len(failed)}


# ═════════════════════════════════════════
# DELIVERY FEES — invoice_delivery_fees / receipt_delivery_fees
# ═════════════════════════════════════════

class DeliveryFeeIn(BaseModel):
    id_registro:    Optional[int]   = 0  # versiones antiguas VB6 pueden no enviarlo
    invoice_number: str
    company_id:     int
    amount:         Optional[float] = 0
    date:           Optional[str]   = None
    order_number:   Optional[str]   = ""
    employee_id:    Optional[int]   = 0
    customer_id:    Optional[int]   = 0
    synced:         Optional[int]   = 0


@router.post("/sync/push/invoice-delivery-fees")
async def push_invoice_delivery_fees(
    items: List[DeliveryFeeIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for item in items:
        key = f"{item.id_registro}|{item.company_id}"
        try:
            await db.execute(text("""
                INSERT INTO invoice_delivery_fees
                    (id_registro, invoice_number, company_id, amount, date, order_number,
                     employee_id, customer_id, synced, updated_at)
                VALUES
                    (:id_registro, :invoice_number, :company_id, :amount, :date, :order_number,
                     :employee_id, :customer_id, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    invoice_number = VALUES(invoice_number),
                    amount         = VALUES(amount),
                    date           = VALUES(date),
                    order_number   = VALUES(order_number),
                    employee_id    = VALUES(employee_id),
                    customer_id    = VALUES(customer_id),
                    synced         = 1,
                    updated_at     = NOW()
            """), item.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(items), "total_saved": len(saved), "total_failed": len(failed)}


@router.post("/sync/push/receipt-delivery-fees")
async def push_receipt_delivery_fees(
    items: List[DeliveryFeeIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for item in items:
        key = f"{item.id_registro}|{item.company_id}"
        try:
            await db.execute(text("""
                INSERT INTO receipt_delivery_fees
                    (id_registro, invoice_number, company_id, amount, date, order_number,
                     employee_id, customer_id, synced, updated_at)
                VALUES
                    (:id_registro, :invoice_number, :company_id, :amount, :date, :order_number,
                     :employee_id, :customer_id, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    invoice_number = VALUES(invoice_number),
                    amount         = VALUES(amount),
                    date           = VALUES(date),
                    order_number   = VALUES(order_number),
                    employee_id    = VALUES(employee_id),
                    customer_id    = VALUES(customer_id),
                    synced         = 1,
                    updated_at     = NOW()
            """), item.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(items), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/invoice-delivery-fees")
async def pull_invoice_delivery_fees(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM invoice_delivery_fees WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 1000"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "invoice_delivery_fees": [dict(r) for r in rows]}


@router.get("/sync/pull/receipt-delivery-fees")
async def pull_receipt_delivery_fees(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM receipt_delivery_fees WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 1000"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "receipt_delivery_fees": [dict(r) for r in rows]}


@router.get("/sync/pull/receipt-payments")
async def pull_receipt_payments(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM pos_receipt_payment_methods WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 1000"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "receipt_payments": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# CASH REGISTER CLOSINGS (cajas_cierres)
# ═════════════════════════════════════════
class CashClosingIn(BaseModel):
    id: int
    company_id: int
    register_number: Optional[int] = 0
    shift: Optional[int] = 0
    date: Optional[str] = None
    base_amount: Optional[float] = 0
    total_sales: Optional[float] = 0
    cash_sales: Optional[float] = 0
    voucher_sales: Optional[float] = 0
    tips: Optional[float] = 0
    extra_tips: Optional[float] = 0
    expenses: Optional[float] = 0
    vouchers: Optional[float] = 0
    manager_consumption: Optional[float] = 0
    final_base: Optional[float] = 0
    total_invoices: Optional[int] = 0
    voucher_invoices: Optional[int] = 0
    copy_invoices: Optional[int] = 0
    voided_invoices: Optional[int] = 0
    invoice_start: Optional[str] = "0"
    invoice_end: Optional[str] = "0"
    bills: Optional[float] = 0
    coins: Optional[float] = 0
    purchases: Optional[float] = 0
    customer_sales: Optional[float] = 0
    closed: Optional[int] = 0
    invoice_start_manual: Optional[str] = None
    invoice_end_manual: Optional[str] = None
    delivery_income: Optional[float] = 0
    delivery_expense: Optional[float] = 0
    opened_pc: Optional[str] = None
    closing_notes: Optional[str] = None
    opening_datetime: Optional[str] = None
    closing_datetime: Optional[str] = None


@router.post("/sync/push/cash-closings")
async def push_cash_closings(
    closings: List[CashClosingIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for c in closings:
        try:
            await db.execute(text("""
                INSERT INTO pos_cash_register_closings (
                    id, company_id, register_number, shift, date,
                    base_amount, total_sales, cash_sales, voucher_sales,
                    tips, extra_tips, expenses, vouchers, manager_consumption,
                    final_base, total_invoices, voucher_invoices, copy_invoices,
                    voided_invoices, invoice_start, invoice_end, bills, coins,
                    purchases, customer_sales, closed, invoice_start_manual,
                    invoice_end_manual, delivery_income, delivery_expense,
                    opened_pc, closing_notes, opening_datetime, closing_datetime,
                    synced, updated_at
                ) VALUES (
                    :id, :company_id, :register_number, :shift, :date,
                    :base_amount, :total_sales, :cash_sales, :voucher_sales,
                    :tips, :extra_tips, :expenses, :vouchers, :manager_consumption,
                    :final_base, :total_invoices, :voucher_invoices, :copy_invoices,
                    :voided_invoices, :invoice_start, :invoice_end, :bills, :coins,
                    :purchases, :customer_sales, :closed, :invoice_start_manual,
                    :invoice_end_manual, :delivery_income, :delivery_expense,
                    :opened_pc, :closing_notes, :opening_datetime, :closing_datetime,
                    1, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    total_sales     = VALUES(total_sales),
                    cash_sales      = VALUES(cash_sales),
                    total_invoices  = VALUES(total_invoices),
                    voided_invoices = VALUES(voided_invoices),
                    final_base      = VALUES(final_base),
                    closed          = VALUES(closed),
                    closing_notes   = VALUES(closing_notes),
                    closing_datetime= VALUES(closing_datetime),
                    synced          = 1,
                    updated_at      = NOW()
            """), c.dict())
            saved.append(c.id)
        except Exception as e:
            failed.append({"id": c.id, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(closings), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/cash-closings")
async def pull_cash_closings(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM pos_cash_register_closings WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 500"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "cash_closings": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# ORDER DETAIL PRODUCTS (detalle_comanda_producto)
# ═════════════════════════════════════════
class OrderDetailProductIn(BaseModel):
    order_number: str
    date: str
    invoice_number: str
    dish_id: int
    item: int
    group_id: int
    item_id: int
    quantity: Optional[float] = 0
    company_id: int


@router.post("/sync/push/order-detail-products")
async def push_order_detail_products(
    records: List[OrderDetailProductIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for r in records:
        try:
            existing = (await db.execute(text("""
                SELECT stock_deducted FROM pos_order_detail_products
                WHERE company_id=:company_id AND order_number=:order_number AND date=:date
                  AND invoice_number=:invoice_number AND dish_id=:dish_id
                  AND item=:item AND group_id=:group_id AND item_id=:item_id LIMIT 1
            """), r.dict())).mappings().first()

            await db.execute(text("""
                INSERT INTO pos_order_detail_products
                    (order_number, date, invoice_number, dish_id, item, group_id, item_id,
                     quantity, synced, stock_deducted, company_id, updated_at)
                VALUES
                    (:order_number, :date, :invoice_number, :dish_id, :item, :group_id, :item_id,
                     :quantity, 1, 0, :company_id, NOW())
                ON DUPLICATE KEY UPDATE
                    quantity   = VALUES(quantity),
                    synced     = 1,
                    updated_at = NOW()
            """), r.dict())

            if existing is None and (r.quantity or 0) > 0:
                await _stock_move(
                    db, r.company_id, r.item_id,
                    -(r.quantity), "sale",
                    "sale", None, r.date,
                    f"Venta {r.invoice_number} — plato {r.dish_id} item {r.item}",
                )
                await db.execute(text("""
                    UPDATE pos_order_detail_products SET stock_deducted=1
                    WHERE company_id=:company_id AND order_number=:order_number AND date=:date
                      AND invoice_number=:invoice_number AND dish_id=:dish_id
                      AND item=:item AND group_id=:group_id AND item_id=:item_id
                """), r.dict())

            saved.append(r.order_number)
        except Exception as e:
            failed.append({"order_number": r.order_number, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(records), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/order-detail-products")
async def pull_order_detail_products(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM pos_order_detail_products WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 1000"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "order_detail_products": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# RECEIPT ORDER DETAIL PRODUCTS (recibos_detalle_comanda_producto)
# ═════════════════════════════════════════
class ReceiptOrderDetailProductIn(BaseModel):
    order_number: str
    date: str
    invoice_number: str
    dish_id: int
    item: int
    group_id: int
    item_id: int
    quantity: Optional[float] = 0
    company_id: int


@router.post("/sync/push/receipt-order-detail-products")
async def push_receipt_order_detail_products(
    records: List[ReceiptOrderDetailProductIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for r in records:
        try:
            existing = (await db.execute(text("""
                SELECT stock_deducted FROM pos_receipt_order_detail_products
                WHERE company_id=:company_id AND order_number=:order_number AND date=:date
                  AND invoice_number=:invoice_number AND dish_id=:dish_id
                  AND item=:item AND group_id=:group_id AND item_id=:item_id LIMIT 1
            """), r.dict())).mappings().first()

            await db.execute(text("""
                INSERT INTO pos_receipt_order_detail_products
                    (order_number, date, invoice_number, dish_id, item, group_id, item_id,
                     quantity, synced, stock_deducted, company_id, updated_at)
                VALUES
                    (:order_number, :date, :invoice_number, :dish_id, :item, :group_id, :item_id,
                     :quantity, 1, 0, :company_id, NOW())
                ON DUPLICATE KEY UPDATE
                    quantity   = VALUES(quantity),
                    synced     = 1,
                    updated_at = NOW()
            """), r.dict())

            if existing is None and (r.quantity or 0) > 0:
                await _stock_move(
                    db, r.company_id, r.item_id,
                    -(r.quantity), "sale",
                    "sale", None, r.date,
                    f"Recibo {r.invoice_number} — plato {r.dish_id} item {r.item}",
                )
                await db.execute(text("""
                    UPDATE pos_receipt_order_detail_products SET stock_deducted=1
                    WHERE company_id=:company_id AND order_number=:order_number AND date=:date
                      AND invoice_number=:invoice_number AND dish_id=:dish_id
                      AND item=:item AND group_id=:group_id AND item_id=:item_id
                """), r.dict())

            saved.append(r.order_number)
        except Exception as e:
            failed.append({"order_number": r.order_number, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(records), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/receipt-order-detail-products")
async def pull_receipt_order_detail_products(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM pos_receipt_order_detail_products WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 1000"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "receipt_order_detail_products": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# DISH PRODUCTS (plato_producto)
# ═════════════════════════════════════════
class DishProductIn(BaseModel):
    dish_id: int
    measure_id: int
    supplier_id: int
    minimum_units: Optional[float] = 0
    presentation_value: Optional[float] = 0
    description: Optional[str] = None
    active: Optional[int] = 0
    company_id: int


@router.post("/sync/push/dish-products")
async def push_dish_products(
    records: List[DishProductIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for r in records:
        try:
            await db.execute(text("""
                INSERT INTO pos_dish_products
                    (dish_id, supplier_id, measure_id, minimum_units, presentation_value,
                     description, active, synced, company_id, updated_at)
                VALUES
                    (:dish_id, :supplier_id, :measure_id, :minimum_units, :presentation_value,
                     :description, :active, 1, :company_id, NOW())
                ON DUPLICATE KEY UPDATE
                    minimum_units      = VALUES(minimum_units),
                    presentation_value = VALUES(presentation_value),
                    description        = VALUES(description),
                    active             = VALUES(active),
                    synced             = 1,
                    updated_at         = NOW()
            """), r.dict())
            saved.append(r.dish_id)
        except Exception as e:
            failed.append({"dish_id": r.dish_id, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(records), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/dish-products")
async def pull_dish_products(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM pos_dish_products WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 500"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "dish_products": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# DISH PRINTERS (plato_impresoras)
# ═════════════════════════════════════════
class DishPrinterIn(BaseModel):
    item_id: int
    printer_id: int
    print_copies: Optional[int] = 1
    company_id: int


@router.post("/sync/push/dish-printers")
async def push_dish_printers(
    records: List[DishPrinterIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    # Group by (company_id, item_id) and delete+insert per dish
    processed: set = set()
    for r in records:
        key = (r.company_id, r.item_id)
        if key not in processed:
            await db.execute(text(
                "DELETE FROM pos_item_printers WHERE company_id = :cid AND item_id = :iid"
            ), {"cid": r.company_id, "iid": r.item_id})
            processed.add(key)
        try:
            await db.execute(text("""
                INSERT INTO pos_item_printers (company_id, item_id, printer_id, print_copies)
                VALUES (:company_id, :item_id, :printer_id, :print_copies)
            """), r.dict())
            saved.append(r.item_id)
        except Exception as e:
            failed.append({"item_id": r.item_id, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(records), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/dish-printers")
async def pull_dish_printers(
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    rows = (await db.execute(
        text("SELECT * FROM pos_item_printers WHERE company_id = :cid"),
        {"cid": company_id}
    )).mappings().all()
    return {"total": len(rows), "dish_printers": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# DISH ASSEMBLY (plato_armar)
# ═════════════════════════════════════════
class DishAssemblyIn(BaseModel):
    dish_id: int
    category_code: int
    max_choices: Optional[int] = 0
    is_active: Optional[int] = 0
    is_required: Optional[int] = 0
    print_on_change_only: Optional[int] = 0
    company_id: int


@router.post("/sync/push/dish-assembly")
async def push_dish_assembly(
    records: List[DishAssemblyIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for r in records:
        try:
            await db.execute(text("""
                INSERT INTO pos_dish_assembly
                    (company_id, dish_id, category_code, max_choices, is_active,
                     is_required, print_on_change_only, synced, updated_at)
                VALUES
                    (:company_id, :dish_id, :category_code, :max_choices, :is_active,
                     :is_required, :print_on_change_only, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    max_choices          = VALUES(max_choices),
                    is_active            = VALUES(is_active),
                    is_required          = VALUES(is_required),
                    print_on_change_only = VALUES(print_on_change_only),
                    synced               = 1,
                    updated_at           = NOW()
            """), r.dict())
            saved.append(r.dish_id)
        except Exception as e:
            failed.append({"dish_id": r.dish_id, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(records), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/dish-assembly")
async def pull_dish_assembly(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM pos_dish_assembly WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 500"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "dish_assembly": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# CATEGORIES (categorias)
# ═════════════════════════════════════════
class CategoryIn(BaseModel):
    id: int
    company_id: int
    name: Optional[str] = None
    description: Optional[str] = None
    photo_name: Optional[str] = None
    is_active: Optional[int] = 1
    color: Optional[str] = "#1d4ed8"


@router.post("/sync/push/categories")
async def push_categories(
    categories: List[CategoryIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for c in categories:
        try:
            await db.execute(text("""
                INSERT INTO pos_categories (id, company_id, name, description, photo_name, is_active, color, synced, updated_at)
                VALUES (:id, :company_id, :name, :description, :photo_name, :is_active, :color, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    name        = VALUES(name),
                    description = VALUES(description),
                    photo_name  = VALUES(photo_name),
                    is_active   = VALUES(is_active),
                    color       = VALUES(color),
                    synced      = 1,
                    updated_at  = NOW()
            """), c.dict())
            saved.append(c.id)
        except Exception as e:
            failed.append({"id": c.id, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(categories), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/categories")
async def pull_categories(
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    rows = (await db.execute(text(
        "SELECT * FROM pos_categories WHERE company_id = :cid ORDER BY id"
    ), {"cid": company_id})).mappings().all()
    return {"total": len(rows), "categories": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# DISH CATEGORIES (categoria_platos)
# ═════════════════════════════════════════
class DishCategoryIn(BaseModel):
    id: int
    company_id: int
    parent_category_id: Optional[int] = 0
    name: Optional[str] = None
    photo_name: Optional[str] = None
    percentage: Optional[float] = 0
    shift: Optional[int] = 0
    monday: Optional[int] = 1
    tuesday: Optional[int] = 1
    wednesday: Optional[int] = 1
    thursday: Optional[int] = 1
    friday: Optional[int] = 1
    saturday: Optional[int] = 1
    sunday: Optional[int] = 1
    is_active: Optional[int] = 1


@router.post("/sync/push/dish-categories")
async def push_dish_categories(
    categories: List[DishCategoryIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for c in categories:
        try:
            await db.execute(text("""
                INSERT INTO pos_dish_categories
                    (id, company_id, parent_category_id, name, photo_name, percentage,
                     shift, monday, tuesday, wednesday, thursday, friday, saturday, sunday,
                     is_active, synced, updated_at)
                VALUES
                    (:id, :company_id, :parent_category_id, :name, :photo_name, :percentage,
                     :shift, :monday, :tuesday, :wednesday, :thursday, :friday, :saturday, :sunday,
                     :is_active, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    parent_category_id = VALUES(parent_category_id),
                    name               = VALUES(name),
                    photo_name         = VALUES(photo_name),
                    percentage         = VALUES(percentage),
                    shift              = VALUES(shift),
                    monday             = VALUES(monday),
                    tuesday            = VALUES(tuesday),
                    wednesday          = VALUES(wednesday),
                    thursday           = VALUES(thursday),
                    friday             = VALUES(friday),
                    saturday           = VALUES(saturday),
                    sunday             = VALUES(sunday),
                    is_active          = VALUES(is_active),
                    synced             = 1,
                    updated_at         = NOW()
            """), c.dict())
            saved.append(c.id)
        except Exception as e:
            failed.append({"id": c.id, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(categories), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/dish-categories")
async def pull_dish_categories(
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    rows = (await db.execute(text(
        "SELECT * FROM pos_dish_categories WHERE company_id = :cid ORDER BY id"
    ), {"cid": company_id})).mappings().all()
    return {"total": len(rows), "dish_categories": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# PRODUCT CATEGORIES (categoria_productos)
# ═════════════════════════════════════════
class ProductCategoryIn(BaseModel):
    id: int
    company_id: int
    name: Optional[str] = None
    percentage: Optional[float] = 0
    is_active: Optional[int] = 1
    require_selection: Optional[int] = 0
    print_assembly_changes_only: Optional[int] = 0


@router.post("/sync/push/product-categories")
async def push_product_categories(
    categories: List[ProductCategoryIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for c in categories:
        try:
            await db.execute(text("""
                INSERT INTO pos_product_categories
                    (id, company_id, name, percentage, is_active,
                     require_selection, print_assembly_changes_only, synced, updated_at)
                VALUES
                    (:id, :company_id, :name, :percentage, :is_active,
                     :require_selection, :print_assembly_changes_only, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    name                        = VALUES(name),
                    percentage                  = VALUES(percentage),
                    is_active                   = VALUES(is_active),
                    require_selection           = VALUES(require_selection),
                    print_assembly_changes_only = VALUES(print_assembly_changes_only),
                    synced                      = 1,
                    updated_at                  = NOW()
            """), c.dict())
            saved.append(c.id)
        except Exception as e:
            failed.append({"id": c.id, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(categories), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/product-categories")
async def pull_product_categories(
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    rows = (await db.execute(text(
        "SELECT * FROM pos_product_categories WHERE company_id = :cid ORDER BY id"
    ), {"cid": company_id})).mappings().all()
    return {"total": len(rows), "product_categories": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# CASH REGISTERS (cajas)
# ═════════════════════════════════════════
class CashRegisterIn(BaseModel):
    id: int
    company_id: int
    name: Optional[str] = None
    initial_amount: Optional[float] = 0
    final_amount: Optional[float] = 0
    is_active: Optional[int] = 1
    is_principal: Optional[int] = 0
    is_open: Optional[int] = 0
    employee_id: Optional[int] = 0
    printer_id: Optional[int] = 0


@router.post("/sync/push/cash-registers")
async def push_cash_registers(
    registers: List[CashRegisterIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for r in registers:
        try:
            await db.execute(text("""
                INSERT INTO pos_cash_registers (
                    id, company_id, name, initial_amount, final_amount,
                    is_active, is_principal, is_open, employee_id, printer_id,
                    synced, updated_at
                ) VALUES (
                    :id, :company_id, :name, :initial_amount, :final_amount,
                    :is_active, :is_principal, :is_open, :employee_id, :printer_id,
                    1, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    name           = VALUES(name),
                    initial_amount = VALUES(initial_amount),
                    final_amount   = VALUES(final_amount),
                    is_active      = VALUES(is_active),
                    is_principal   = VALUES(is_principal),
                    is_open        = VALUES(is_open),
                    employee_id    = VALUES(employee_id),
                    printer_id     = VALUES(printer_id),
                    synced         = 1,
                    updated_at     = NOW()
            """), r.dict())
            saved.append(r.id)
        except Exception as e:
            failed.append({"id": r.id, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(registers), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/cash-registers")
async def pull_cash_registers(
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    rows = (await db.execute(text(
        "SELECT * FROM pos_cash_registers WHERE company_id = :cid AND is_active = 1 ORDER BY id"
    ), {"cid": company_id})).mappings().all()
    return {"total": len(rows), "cash_registers": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# PRINTERS (impresoras)
# ═════════════════════════════════════════
class PrinterIn(BaseModel):
    id: int
    company_id: int
    name: Optional[str] = None
    ip: Optional[str] = None
    port: Optional[int] = 9100
    is_active: Optional[int] = 1


@router.post("/sync/push/printers")
async def push_printers(
    printers: List[PrinterIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for p in printers:
        try:
            await db.execute(text("""
                INSERT INTO pos_printers (id, company_id, name, ip, port, is_active, synced, updated_at)
                VALUES (:id, :company_id, :name, :ip, :port, :is_active, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    name       = VALUES(name),
                    ip         = VALUES(ip),
                    port       = VALUES(port),
                    is_active  = VALUES(is_active),
                    synced     = 1,
                    updated_at = NOW()
            """), p.dict())
            saved.append(p.id)
        except Exception as e:
            failed.append({"id": p.id, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(printers), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/printers")
async def pull_printers(
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    rows = (await db.execute(text(
        "SELECT * FROM pos_printers WHERE company_id = :cid AND is_active = 1 ORDER BY id"
    ), {"cid": company_id})).mappings().all()
    return {"total": len(rows), "printers": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# DISH ASSEMBLY DETAIL (plato_armar_detalle)
# ═════════════════════════════════════════
class DishAssemblyDetailIn(BaseModel):
    dish_id: int
    category_code: int
    item: int
    position: int
    supply_price: Optional[float] = 0
    discount_qty: Optional[float] = 0
    is_default: Optional[int] = 0
    company_id: int


@router.post("/sync/push/dish-assembly-detail")
async def push_dish_assembly_detail(
    records: List[DishAssemblyDetailIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for r in records:
        try:
            await db.execute(text("""
                INSERT INTO pos_dish_assembly_detail
                    (company_id, dish_id, category_code, item, position,
                     supply_price, discount_qty, is_default, synced, updated_at)
                VALUES
                    (:company_id, :dish_id, :category_code, :item, :position,
                     :supply_price, :discount_qty, :is_default, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    supply_price = VALUES(supply_price),
                    discount_qty = VALUES(discount_qty),
                    is_default   = VALUES(is_default),
                    synced       = 1,
                    updated_at   = NOW()
            """), r.dict())
            saved.append(r.dish_id)
        except Exception as e:
            failed.append({"dish_id": r.dish_id, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(records), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/dish-assembly-detail")
async def pull_dish_assembly_detail(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM pos_dish_assembly_detail WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 1000"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "dish_assembly_detail": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# DAILY MENU (menu_diario)
# ═════════════════════════════════════════
class DailyMenuIn(BaseModel):
    menu_id: int
    item_id: int
    date: Optional[str] = None
    category: Optional[str] = "0"
    description: Optional[str] = "0"
    group_by: Optional[int] = 0
    selected: Optional[int] = 0
    company_id: int


@router.post("/sync/push/daily-menu")
async def push_daily_menu(
    records: List[DailyMenuIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for r in records:
        try:
            await db.execute(text("""
                INSERT INTO pos_daily_menu
                    (company_id, menu_id, item_id, date, category,
                     description, group_by, selected, synced, updated_at)
                VALUES
                    (:company_id, :menu_id, :item_id, :date, :category,
                     :description, :group_by, :selected, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    date        = VALUES(date),
                    category    = VALUES(category),
                    description = VALUES(description),
                    group_by    = VALUES(group_by),
                    selected    = VALUES(selected),
                    synced      = 1,
                    updated_at  = NOW()
            """), r.dict())
            saved.append(r.menu_id)
        except Exception as e:
            failed.append({"menu_id": r.menu_id, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(records), "total_saved": len(saved), "total_failed": len(failed)}


@router.get("/sync/pull/daily-menu")
async def pull_daily_menu(
    company_id: int = Query(...),
    since: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    sql = "SELECT * FROM pos_daily_menu WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 500"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "daily_menu": [dict(r) for r in rows]}


# ─────────────────────────────────────────────────────────────────────────────
# FIX: pos_cash_register_closings — ahora usa id_registro (multitenant safe)
# ─────────────────────────────────────────────────────────────────────────────

class CashClosingFixIn(BaseModel):
    id_registro:          int
    company_id:           int
    register_number:      Optional[int]   = 0
    shift:                Optional[int]   = 0
    date:                 Optional[str]   = None
    base_amount:          Optional[float] = 0
    total_sales:          Optional[float] = 0
    cash_sales:           Optional[float] = 0
    voucher_sales:        Optional[float] = 0
    tips:                 Optional[float] = 0
    extra_tips:           Optional[float] = 0
    expenses:             Optional[float] = 0
    vouchers:             Optional[float] = 0
    manager_consumption:  Optional[float] = 0
    final_base:           Optional[float] = 0
    total_invoices:       Optional[int]   = 0
    voucher_invoices:     Optional[int]   = 0
    copy_invoices:        Optional[int]   = 0
    voided_invoices:      Optional[int]   = 0
    invoice_start:        Optional[str]   = "0"
    invoice_end:          Optional[str]   = "0"
    bills:                Optional[float] = 0
    coins:                Optional[float] = 0
    purchases:            Optional[float] = 0
    customer_sales:       Optional[float] = 0
    closed:               Optional[int]   = 0
    invoice_start_manual: Optional[str]   = None
    invoice_end_manual:   Optional[str]   = None
    delivery_income:      Optional[float] = 0
    delivery_expense:     Optional[float] = 0
    opened_pc:            Optional[str]   = None
    closing_notes:        Optional[str]   = None
    opening_datetime:     Optional[str]   = None
    closing_datetime:     Optional[str]   = None


@router.post("/sync/push/cash-closings-v2")
async def push_cash_closings_v2(
    closings: List[CashClosingFixIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for c in closings:
        key = f"{c.id_registro}|{c.company_id}"
        try:
            await db.execute(text("""
                INSERT INTO pos_cash_register_closings (
                    id_registro, company_id, register_number, shift, date,
                    base_amount, total_sales, cash_sales, voucher_sales,
                    tips, extra_tips, expenses, vouchers, manager_consumption,
                    final_base, total_invoices, voucher_invoices, copy_invoices,
                    voided_invoices, invoice_start, invoice_end, bills, coins,
                    purchases, customer_sales, closed, invoice_start_manual,
                    invoice_end_manual, delivery_income, delivery_expense,
                    opened_pc, closing_notes, opening_datetime, closing_datetime,
                    synced, updated_at
                ) VALUES (
                    :id_registro, :company_id, :register_number, :shift, :date,
                    :base_amount, :total_sales, :cash_sales, :voucher_sales,
                    :tips, :extra_tips, :expenses, :vouchers, :manager_consumption,
                    :final_base, :total_invoices, :voucher_invoices, :copy_invoices,
                    :voided_invoices, :invoice_start, :invoice_end, :bills, :coins,
                    :purchases, :customer_sales, :closed, :invoice_start_manual,
                    :invoice_end_manual, :delivery_income, :delivery_expense,
                    :opened_pc, :closing_notes, :opening_datetime, :closing_datetime,
                    1, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    total_sales      = VALUES(total_sales),
                    cash_sales       = VALUES(cash_sales),
                    total_invoices   = VALUES(total_invoices),
                    voided_invoices  = VALUES(voided_invoices),
                    final_base       = VALUES(final_base),
                    closed           = VALUES(closed),
                    closing_notes    = VALUES(closing_notes),
                    closing_datetime = VALUES(closing_datetime),
                    synced           = 1,
                    updated_at       = NOW()
            """), c.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(closings), "total_saved": len(saved), "total_failed": len(failed)}


# ─────────────────────────────────────────────────────────────────────────────
# caja_facturas → pos_cash_register_invoices
# ─────────────────────────────────────────────────────────────────────────────

class CashRegisterInvoiceIn(BaseModel):
    register_number:    int
    closing_id:         int
    invoice_number:     str
    company_id:         int
    date:               Optional[str]   = None
    order_number:       Optional[str]   = None
    amount:             Optional[float] = 0
    base_amount:        Optional[float] = 0
    tax_vat:            Optional[float] = 0
    tax_consumption:    Optional[float] = 0
    employee_id:        Optional[int]   = 0
    shift:              Optional[int]   = 0
    source_pc:          Optional[str]   = None
    delivery_person_id: Optional[int]   = 0
    invoice_notes:      Optional[str]   = None
    prefix:             Optional[str]   = None
    fac_pe:             Optional[str]   = None


@router.post("/sync/push/cash-register-invoices")
async def push_cash_register_invoices(
    items: List[CashRegisterInvoiceIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for item in items:
        key = f"{item.invoice_number}|{item.company_id}"
        try:
            await db.execute(text("""
                INSERT INTO pos_cash_register_invoices
                    (register_number, closing_id, invoice_number, company_id, date,
                     order_number, amount, base_amount, tax_vat, tax_consumption,
                     employee_id, shift, source_pc, delivery_person_id,
                     invoice_notes, prefix, fac_pe, synced, updated_at)
                VALUES
                    (:register_number, :closing_id, :invoice_number, :company_id, :date,
                     :order_number, :amount, :base_amount, :tax_vat, :tax_consumption,
                     :employee_id, :shift, :source_pc, :delivery_person_id,
                     :invoice_notes, :prefix, :fac_pe, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    closing_id         = VALUES(closing_id),
                    amount             = VALUES(amount),
                    base_amount        = VALUES(base_amount),
                    tax_vat            = VALUES(tax_vat),
                    tax_consumption    = VALUES(tax_consumption),
                    invoice_notes      = VALUES(invoice_notes),
                    synced             = 1,
                    updated_at         = NOW()
            """), item.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(items), "total_saved": len(saved), "total_failed": len(failed)}


# ─────────────────────────────────────────────────────────────────────────────
# caja_recibos → pos_cash_register_receipts
# ─────────────────────────────────────────────────────────────────────────────

class CashRegisterReceiptIn(BaseModel):
    register_number:    int
    closing_id:         int
    receipt_number:     str
    company_id:         int
    date:               Optional[str]   = None
    order_number:       Optional[str]   = None
    amount:             Optional[float] = 0
    base_amount:        Optional[float] = 0
    tax_vat:            Optional[float] = 0
    tax_consumption:    Optional[float] = 0
    employee_id:        Optional[int]   = 0
    shift:              Optional[int]   = 0
    source_pc:          Optional[str]   = None
    delivery_person_id: Optional[int]   = 0
    notes:              Optional[str]   = None
    prefix:             Optional[str]   = None
    fac_pe:             Optional[str]   = None


@router.post("/sync/push/cash-register-receipts")
async def push_cash_register_receipts(
    items: List[CashRegisterReceiptIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for item in items:
        key = f"{item.receipt_number}|{item.company_id}"
        try:
            await db.execute(text("""
                INSERT INTO pos_cash_register_receipts
                    (register_number, closing_id, receipt_number, company_id, date,
                     order_number, amount, base_amount, tax_vat, tax_consumption,
                     employee_id, shift, source_pc, delivery_person_id,
                     notes, prefix, fac_pe, synced, updated_at)
                VALUES
                    (:register_number, :closing_id, :receipt_number, :company_id, :date,
                     :order_number, :amount, :base_amount, :tax_vat, :tax_consumption,
                     :employee_id, :shift, :source_pc, :delivery_person_id,
                     :notes, :prefix, :fac_pe, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    closing_id      = VALUES(closing_id),
                    amount          = VALUES(amount),
                    base_amount     = VALUES(base_amount),
                    tax_vat         = VALUES(tax_vat),
                    tax_consumption = VALUES(tax_consumption),
                    notes           = VALUES(notes),
                    synced          = 1,
                    updated_at      = NOW()
            """), item.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(items), "total_saved": len(saved), "total_failed": len(failed)}


# ─────────────────────────────────────────────────────────────────────────────
# gastos → pos_expenses
# ─────────────────────────────────────────────────────────────────────────────

class ExpenseIn(BaseModel):
    id_registro:    int
    company_id:     int
    register_id:    Optional[int]   = 0
    date:           Optional[str]   = None
    amount:         Optional[float] = 0
    employee_code:  Optional[str]   = None
    concept_id:     Optional[int]   = 0
    sub_concept_id: Optional[int]   = 0
    shift:          Optional[int]   = 0
    movement_number: Optional[int]  = 0
    detail:         Optional[str]   = None


@router.post("/sync/push/expenses")
async def push_expenses(
    items: List[ExpenseIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for item in items:
        key = f"{item.id_registro}|{item.company_id}"
        try:
            await db.execute(text("""
                INSERT INTO pos_expenses
                    (id_registro, company_id, register_id, date, amount,
                     employee_code, concept_id, sub_concept_id, shift,
                     movement_number, detail, synced, updated_at)
                VALUES
                    (:id_registro, :company_id, :register_id, :date, :amount,
                     :employee_code, :concept_id, :sub_concept_id, :shift,
                     :movement_number, :detail, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    amount          = VALUES(amount),
                    detail          = VALUES(detail),
                    synced          = 1,
                    updated_at      = NOW()
            """), item.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(items), "total_saved": len(saved), "total_failed": len(failed)}


# ─────────────────────────────────────────────────────────────────────────────
# compras → pos_purchases
# ─────────────────────────────────────────────────────────────────────────────

class PurchaseIn(BaseModel):
    id_registro:    int
    company_id:     int
    register_id:    Optional[int]   = 0
    date:           Optional[str]   = None
    amount:         Optional[float] = 0
    employee_code:  Optional[str]   = None
    concept_id:     Optional[int]   = 0
    sub_concept_id: Optional[int]   = 0
    shift:          Optional[int]   = 0
    movement_number: Optional[int]  = 0
    detail:         Optional[str]   = None


@router.post("/sync/push/purchases")
async def push_purchases(
    items: List[PurchaseIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for item in items:
        key = f"{item.id_registro}|{item.company_id}"
        try:
            await db.execute(text("""
                INSERT INTO pos_purchases
                    (id_registro, company_id, register_id, date, amount,
                     employee_code, concept_id, sub_concept_id, shift,
                     movement_number, detail, synced, updated_at)
                VALUES
                    (:id_registro, :company_id, :register_id, :date, :amount,
                     :employee_code, :concept_id, :sub_concept_id, :shift,
                     :movement_number, :detail, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    amount          = VALUES(amount),
                    detail          = VALUES(detail),
                    synced          = 1,
                    updated_at      = NOW()
            """), item.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(items), "total_saved": len(saved), "total_failed": len(failed)}


# ─────────────────────────────────────────────────────────────────────────────
# descuentos → pos_discounts
# ─────────────────────────────────────────────────────────────────────────────

class DiscountIn(BaseModel):
    id_registro:     int
    company_id:      int
    date:            Optional[str]   = None
    prefix:          Optional[str]   = None
    invoice_number:  Optional[str]   = None
    dish_id:         Optional[int]   = 0
    item:            Optional[int]   = 0
    typification_id: Optional[int]   = 0
    original_price:  Optional[float] = 0
    sale_price:      Optional[float] = 0
    base_value:      Optional[float] = 0
    tax_value:       Optional[float] = 0
    discount_amount: Optional[float] = 0
    percentage:      Optional[float] = 0
    reason:          Optional[str]   = None
    order_number:    Optional[str]   = None


@router.post("/sync/push/discounts")
async def push_discounts(
    items: List[DiscountIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for item in items:
        key = f"{item.id_registro}|{item.company_id}"
        try:
            await db.execute(text("""
                INSERT INTO pos_discounts
                    (id_registro, company_id, date, prefix, invoice_number,
                     dish_id, item, typification_id, original_price, sale_price,
                     base_value, tax_value, discount_amount, percentage,
                     reason, order_number, synced, updated_at)
                VALUES
                    (:id_registro, :company_id, :date, :prefix, :invoice_number,
                     :dish_id, :item, :typification_id, :original_price, :sale_price,
                     :base_value, :tax_value, :discount_amount, :percentage,
                     :reason, :order_number, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    discount_amount = VALUES(discount_amount),
                    percentage      = VALUES(percentage),
                    reason          = VALUES(reason),
                    synced          = 1,
                    updated_at      = NOW()
            """), item.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(items), "total_saved": len(saved), "total_failed": len(failed)}


# ─────────────────────────────────────────────────────────────────────────────
# recibos_descuentos → pos_receipt_discounts
# ─────────────────────────────────────────────────────────────────────────────

class ReceiptDiscountIn(BaseModel):
    id_registro:     int
    company_id:      int
    date:            Optional[str]   = None
    prefix:          Optional[str]   = None
    receipt_number:  Optional[str]   = None
    dish_id:         Optional[int]   = 0
    item:            Optional[int]   = 0
    typification_id: Optional[int]   = 0
    original_price:  Optional[float] = 0
    sale_price:      Optional[float] = 0
    base_value:      Optional[float] = 0
    tax_value:       Optional[float] = 0
    discount_amount: Optional[float] = 0
    percentage:      Optional[float] = 0
    reason:          Optional[str]   = None
    order_number:    Optional[str]   = None


@router.post("/sync/push/receipt-discounts")
async def push_receipt_discounts(
    items: List[ReceiptDiscountIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for item in items:
        key = f"{item.id_registro}|{item.company_id}"
        try:
            await db.execute(text("""
                INSERT INTO pos_receipt_discounts
                    (id_registro, company_id, date, prefix, receipt_number,
                     dish_id, item, typification_id, original_price, sale_price,
                     base_value, tax_value, discount_amount, percentage,
                     reason, order_number, synced, updated_at)
                VALUES
                    (:id_registro, :company_id, :date, :prefix, :receipt_number,
                     :dish_id, :item, :typification_id, :original_price, :sale_price,
                     :base_value, :tax_value, :discount_amount, :percentage,
                     :reason, :order_number, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    discount_amount = VALUES(discount_amount),
                    percentage      = VALUES(percentage),
                    reason          = VALUES(reason),
                    synced          = 1,
                    updated_at      = NOW()
            """), item.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(items), "total_saved": len(saved), "total_failed": len(failed)}


# ─────────────────────────────────────────────────────────────────────────────
# forma_pago → pos_payment_types  (catálogo, Variante B)
# ─────────────────────────────────────────────────────────────────────────────

class PaymentTypeIn(BaseModel):
    id:              int
    company_id:      int
    name:            str
    validate_amount: Optional[int] = 0
    is_active:       Optional[int] = 0
    select_card:     Optional[int] = 0
    value:           Optional[float] = 0
    ask_notes:       Optional[int] = 0
    ask_customer:    Optional[int] = 0
    adds_to_cash:    Optional[int] = 0
    validate_number: Optional[int] = 0
    is_default:      Optional[int] = 0


@router.post("/sync/push/payment-types")
async def push_payment_types(
    items: List[PaymentTypeIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for item in items:
        key = f"{item.id}|{item.company_id}"
        try:
            await db.execute(text("""
                INSERT INTO pos_payment_types
                    (id, company_id, name, validate_amount, is_active, select_card,
                     value, ask_notes, ask_customer, adds_to_cash, validate_number,
                     is_default, synced, updated_at)
                VALUES
                    (:id, :company_id, :name, :validate_amount, :is_active, :select_card,
                     :value, :ask_notes, :ask_customer, :adds_to_cash, :validate_number,
                     :is_default, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    name            = VALUES(name),
                    validate_amount = VALUES(validate_amount),
                    is_active       = VALUES(is_active),
                    value           = VALUES(value),
                    is_default      = VALUES(is_default),
                    synced          = 1,
                    updated_at      = NOW()
            """), item.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(items), "total_saved": len(saved), "total_failed": len(failed)}


# ─────────────────────────────────────────────────────────────────────────────
# forma_medida → pos_measure_forms  (catálogo, Variante B)
# ─────────────────────────────────────────────────────────────────────────────

class MeasureFormIn(BaseModel):
    id:        int
    company_id: int
    name:      str
    is_active: Optional[int] = 1


@router.post("/sync/push/measure-forms")
async def push_measure_forms(
    items: List[MeasureFormIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for item in items:
        key = f"{item.id}|{item.company_id}"
        try:
            await db.execute(text("""
                INSERT INTO pos_measure_forms
                    (id, company_id, name, is_active, synced, updated_at)
                VALUES
                    (:id, :company_id, :name, :is_active, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    name      = VALUES(name),
                    is_active = VALUES(is_active),
                    synced    = 1,
                    updated_at = NOW()
            """), item.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(items), "total_saved": len(saved), "total_failed": len(failed)}


# ─────────────────────────────────────────────────────────────────────────────
# lista_precios_cliente → pos_customer_price_list  (catálogo, Variante B)
# ─────────────────────────────────────────────────────────────────────────────

class CustomerPriceListIn(BaseModel):
    id_lista:        int
    id_cliente:      int
    id_producto:     int
    id_presentacion: Optional[int] = 0
    company_id:      int
    precio_producto: Optional[float] = 0
    fecha:           Optional[str]   = None
    activa:          Optional[int]   = 0


@router.post("/sync/push/customer-price-list")
async def push_customer_price_list(
    items: List[CustomerPriceListIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for item in items:
        key = f"{item.id_lista}|{item.id_cliente}|{item.id_producto}|{item.company_id}"
        try:
            await db.execute(text("""
                INSERT INTO pos_customer_price_list
                    (id_lista, id_cliente, id_producto, id_presentacion,
                     company_id, precio_producto, fecha, activa, synced, updated_at)
                VALUES
                    (:id_lista, :id_cliente, :id_producto, :id_presentacion,
                     :company_id, :precio_producto, :fecha, :activa, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    precio_producto = VALUES(precio_producto),
                    activa          = VALUES(activa),
                    synced          = 1,
                    updated_at      = NOW()
            """), item.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(items), "total_saved": len(saved), "total_failed": len(failed)}


# ─────────────────────────────────────────────────────────────────────────────
# novedades_categorias → pos_dish_note_categories  (catálogo, Variante B)
# ─────────────────────────────────────────────────────────────────────────────

class DishNoteCategoryIn(BaseModel):
    id_consecutivo: int
    cod_categoria:  int
    id_novedad:     int
    company_id:     int
    name:           Optional[str] = None


@router.post("/sync/push/dish-note-categories")
async def push_dish_note_categories(
    items: List[DishNoteCategoryIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for item in items:
        key = f"{item.id_consecutivo}|{item.cod_categoria}|{item.id_novedad}|{item.company_id}"
        try:
            await db.execute(text("""
                INSERT INTO pos_dish_note_categories
                    (id_consecutivo, cod_categoria, id_novedad, company_id, name, synced, updated_at)
                VALUES
                    (:id_consecutivo, :cod_categoria, :id_novedad, :company_id, :name, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    name       = VALUES(name),
                    synced     = 1,
                    updated_at = NOW()
            """), item.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(items), "total_saved": len(saved), "total_failed": len(failed)}


# ─────────────────────────────────────────────────────────────────────────────
# novedades_comentarios → pos_order_notes  (catálogo, Variante B)
# ─────────────────────────────────────────────────────────────────────────────

class OrderNoteIn(BaseModel):
    id:         int
    company_id: int
    name:       Optional[str] = None


@router.post("/sync/push/order-notes")
async def push_order_notes(
    items: List[OrderNoteIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for item in items:
        key = f"{item.id}|{item.company_id}"
        try:
            await db.execute(text("""
                INSERT INTO pos_order_notes (id, company_id, name, synced, updated_at)
                VALUES (:id, :company_id, :name, 1, NOW())
                ON DUPLICATE KEY UPDATE name=VALUES(name), synced=1, updated_at=NOW()
            """), item.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(items), "total_saved": len(saved), "total_failed": len(failed)}


# ─────────────────────────────────────────────────────────────────────────────
# novedades_productos → pos_product_notes  (catálogo, Variante B)
# ─────────────────────────────────────────────────────────────────────────────

class ProductNoteIn(BaseModel):
    id:         int
    company_id: int
    name:       Optional[str] = None


@router.post("/sync/push/product-notes")
async def push_product_notes(
    items: List[ProductNoteIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for item in items:
        key = f"{item.id}|{item.company_id}"
        try:
            await db.execute(text("""
                INSERT INTO pos_product_notes (id, company_id, name, synced, updated_at)
                VALUES (:id, :company_id, :name, 1, NOW())
                ON DUPLICATE KEY UPDATE name=VALUES(name), synced=1, updated_at=NOW()
            """), item.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(items), "total_saved": len(saved), "total_failed": len(failed)}


# ─────────────────────────────────────────────────────────────────────────────
# inventario_porciones → supply_items  (catálogo, Variante B)
# ─────────────────────────────────────────────────────────────────────────────

class SupplyItemSyncIn(BaseModel):
    id_grupo:           int
    id_item:            int
    company_id:         int
    id_insumo:          Optional[int]   = None
    code:               Optional[str]   = None
    description:        Optional[str]   = None
    marca_referencia:   Optional[str]   = None
    cost_price:         Optional[float] = 0
    unit_id:            Optional[int]   = None
    unit_uso_id:        Optional[int]   = None
    valor_und_compra:   Optional[float] = 0
    und_min_utilizadas: Optional[float] = 0
    stock_qty:          Optional[float] = 0
    min_stock:          Optional[float] = 0
    waste_pct:          Optional[float] = 0
    fecha_vence:        Optional[str]   = None
    posicion:           Optional[int]   = 0
    agrupar:            Optional[int]   = 0
    control_stock:      Optional[int]   = 0
    compras:            Optional[int]   = 0
    opcion_cambios:     Optional[int]   = 0
    centro_produccion:  Optional[int]   = 0
    tipo_und_minima:    Optional[int]   = 0
    cant_und_minimas:   Optional[int]   = 0
    bodega:             Optional[int]   = 0
    producto_preparado: Optional[int]   = 0
    id_preparacion:     Optional[int]   = 0
    preparado_en_sede:  Optional[int]   = 0
    descargar_en_venta: Optional[int]   = 1
    armar_plato:        Optional[int]   = 0
    cantidad_armar:     Optional[float] = 0
    insumo_cp:          Optional[int]   = 0
    is_active:          Optional[int]   = 1


@router.post("/sync/push/supply-items")
async def push_supply_items(
    items: List[SupplyItemSyncIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for item in items:
        key = f"{item.id_grupo}|{item.id_item}|{item.company_id}"
        try:
            await db.execute(text("""
                INSERT INTO supply_items
                    (company_id, id_grupo, id_item, id_insumo, code, description,
                     marca_referencia, cost_price, unit_id, unit_uso_id,
                     valor_und_compra, und_min_utilizadas, stock_qty, min_stock,
                     waste_pct, fecha_vence, posicion, agrupar, control_stock,
                     compras, opcion_cambios, centro_produccion, tipo_und_minima,
                     cant_und_minimas, bodega, producto_preparado, id_preparacion,
                     preparado_en_sede, descargar_en_venta, armar_plato, cantidad_armar,
                     insumo_cp, is_active, synced, updated_at)
                VALUES
                    (:company_id, :id_grupo, :id_item, :id_insumo, :code, :description,
                     :marca_referencia, :cost_price, :unit_id, :unit_uso_id,
                     :valor_und_compra, :und_min_utilizadas, :stock_qty, :min_stock,
                     :waste_pct, :fecha_vence, :posicion, :agrupar, :control_stock,
                     :compras, :opcion_cambios, :centro_produccion, :tipo_und_minima,
                     :cant_und_minimas, :bodega, :producto_preparado, :id_preparacion,
                     :preparado_en_sede, :descargar_en_venta, :armar_plato, :cantidad_armar,
                     :insumo_cp, :is_active, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    id_insumo          = VALUES(id_insumo),
                    code               = VALUES(code),
                    description        = VALUES(description),
                    marca_referencia   = VALUES(marca_referencia),
                    cost_price         = VALUES(cost_price),
                    unit_id            = VALUES(unit_id),
                    unit_uso_id        = VALUES(unit_uso_id),
                    valor_und_compra   = VALUES(valor_und_compra),
                    und_min_utilizadas = VALUES(und_min_utilizadas),
                    stock_qty          = VALUES(stock_qty),
                    min_stock          = VALUES(min_stock),
                    waste_pct          = VALUES(waste_pct),
                    fecha_vence        = VALUES(fecha_vence),
                    posicion           = VALUES(posicion),
                    agrupar            = VALUES(agrupar),
                    control_stock      = VALUES(control_stock),
                    compras            = VALUES(compras),
                    opcion_cambios     = VALUES(opcion_cambios),
                    centro_produccion  = VALUES(centro_produccion),
                    tipo_und_minima    = VALUES(tipo_und_minima),
                    cant_und_minimas   = VALUES(cant_und_minimas),
                    bodega             = VALUES(bodega),
                    producto_preparado = VALUES(producto_preparado),
                    id_preparacion     = VALUES(id_preparacion),
                    preparado_en_sede  = VALUES(preparado_en_sede),
                    descargar_en_venta = VALUES(descargar_en_venta),
                    armar_plato        = VALUES(armar_plato),
                    cantidad_armar     = VALUES(cantidad_armar),
                    insumo_cp          = VALUES(insumo_cp),
                    is_active          = VALUES(is_active),
                    synced             = 1,
                    updated_at         = NOW()
            """), item.dict())
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(items), "total_saved": len(saved), "total_failed": len(failed)}


# ─────────────────────────────────────────────────────────────────────────────
# PULL endpoints para todas las tablas nuevas
# ─────────────────────────────────────────────────────────────────────────────

def _pull(table: str, key: str):
    async def _handler(
        company_id: int = Query(...),
        since: Optional[str] = Query(None),
        db: AsyncSession = Depends(get_db),
        _: str = Depends(verify_api_key),
    ):
        sql = f"SELECT * FROM {table} WHERE company_id = :company_id"
        params: dict = {"company_id": company_id}
        if since:
            sql += " AND updated_at >= :since"
            params["since"] = since
        sql += " ORDER BY updated_at ASC LIMIT 1000"
        rows = (await db.execute(text(sql), params)).mappings().all()
        return {"total": len(rows), "since": since, key: [dict(r) for r in rows]}
    return _handler


router.get("/sync/pull/cash-closings-v2")(
    _pull("pos_cash_register_closings", "cash_closings"))
router.get("/sync/pull/cash-register-invoices")(
    _pull("pos_cash_register_invoices", "cash_register_invoices"))
router.get("/sync/pull/cash-register-receipts")(
    _pull("pos_cash_register_receipts", "cash_register_receipts"))
router.get("/sync/pull/expenses")(
    _pull("pos_expenses", "expenses"))
router.get("/sync/pull/purchases")(
    _pull("pos_purchases", "purchases"))
router.get("/sync/pull/discounts")(
    _pull("pos_discounts", "discounts"))
router.get("/sync/pull/receipt-discounts")(
    _pull("pos_receipt_discounts", "receipt_discounts"))
router.get("/sync/pull/payment-types")(
    _pull("pos_payment_types", "payment_types"))
router.get("/sync/pull/measure-forms")(
    _pull("pos_measure_forms", "measure_forms"))
router.get("/sync/pull/customer-price-list")(
    _pull("pos_customer_price_list", "customer_price_list"))
router.get("/sync/pull/dish-note-categories")(
    _pull("pos_dish_note_categories", "dish_note_categories"))
router.get("/sync/pull/order-notes")(
    _pull("pos_order_notes", "order_notes"))
router.get("/sync/pull/product-notes")(
    _pull("pos_product_notes", "product_notes"))
router.get("/sync/pull/supply-items")(
    _pull("supply_items", "supply_items"))
router.get("/sync/pull/inventory-physical")(
    _pull("inventory_physical", "inventory_physical"))
router.get("/sync/pull/inventory-entries")(
    _pull("inventory_entries", "inventory_entries"))
router.get("/sync/pull/inventory-exits")(
    _pull("inventory_exits", "inventory_exits"))


# ═════════════════════════════════════════
# STOCK MOVEMENT HELPER
# ═════════════════════════════════════════
async def _stock_move(
    db: AsyncSession,
    company_id: int,
    id_item: int,
    qty: float,
    mtype: str,
    ref_type: str,
    ref_id: Optional[int],
    mdate: Optional[str],
    notes: Optional[str] = None,
):
    si = (await db.execute(text("""
        SELECT id, stock_qty, control_stock
        FROM supply_items WHERE company_id = :cid AND id_item = :item LIMIT 1
    """), {"cid": company_id, "item": id_item})).mappings().first()

    if not si or not si["control_stock"]:
        return

    old_qty = float(si["stock_qty"] or 0)
    new_qty = qty if mtype == "physical" else old_qty + qty

    await db.execute(text("""
        INSERT INTO stock_movements
            (company_id, supply_item_id, movement_type, qty, qty_before, qty_after,
             reference_type, reference_id, movement_date, notes)
        VALUES
            (:cid, :sid, :mtype, :dq, :qb, :qa, :rtype, :rid, :mdate, :notes)
    """), {
        "cid": company_id, "sid": si["id"], "mtype": mtype,
        "dq": (new_qty - old_qty) if mtype == "physical" else qty,
        "qb": old_qty, "qa": new_qty,
        "rtype": ref_type, "rid": ref_id, "mdate": mdate, "notes": notes,
    })
    await db.execute(text(
        "UPDATE supply_items SET stock_qty = :q WHERE id = :id"
    ), {"q": new_qty, "id": si["id"]})


# ═════════════════════════════════════════
# INVENTORY PHYSICAL (inventarios_fisicos)
# ═════════════════════════════════════════
class InventoryPhysicalIn(BaseModel):
    id_fisico:   int
    id_item:     int
    company_id:  int
    fecha:       str
    cantidad:    Optional[float] = 0
    cod_usuario: Optional[str]  = None
    hora:        Optional[str]  = None
    observacion: Optional[str]  = None
    autorizada:  Optional[int]  = 0
    revisada:    Optional[int]  = 0
    cobrar:      Optional[int]  = 0
    agrupar:     Optional[int]  = 0


@router.post("/sync/push/inventory-physical")
async def push_inventory_physical(
    items: List[InventoryPhysicalIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for it in items:
        key = f"{it.company_id}|{it.id_fisico}"
        try:
            await db.execute(text("""
                INSERT INTO inventory_physical
                    (id_fisico, id_item, company_id, fecha, cantidad,
                     cod_usuario, hora, observacion, autorizada, revisada,
                     cobrar, agrupar, synced, updated_at)
                VALUES
                    (:id_fisico, :id_item, :company_id, :fecha, :cantidad,
                     :cod_usuario, :hora, :observacion, :autorizada, :revisada,
                     :cobrar, :agrupar, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    cantidad    = VALUES(cantidad),
                    autorizada  = VALUES(autorizada),
                    revisada    = VALUES(revisada),
                    observacion = VALUES(observacion),
                    synced      = 1,
                    updated_at  = NOW()
            """), it.dict())

            if it.autorizada:
                already = (await db.execute(text("""
                    SELECT 1 FROM stock_movements
                    WHERE company_id=:cid AND reference_type='physical' AND reference_id=:rid LIMIT 1
                """), {"cid": it.company_id, "rid": it.id_fisico})).fetchone()
                if not already:
                    await _stock_move(
                        db, it.company_id, it.id_item,
                        it.cantidad or 0, "physical",
                        "physical", it.id_fisico, it.fecha,
                        f"Inventario físico #{it.id_fisico}",
                    )

            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(items), "total_saved": len(saved), "total_failed": len(failed)}


# ═════════════════════════════════════════
# INVENTORY ENTRIES (inventarios_entradas)
# ═════════════════════════════════════════
class InventoryEntryIn(BaseModel):
    id_entrada:   int
    id_item:      int
    id_proveedor: Optional[int] = 0
    company_id:   int
    fecha:        str
    cantidad:     Optional[float] = 0
    cod_empleado: Optional[str]  = None
    observacion:  Optional[str]  = None
    autorizada:   Optional[int]  = 0
    revisada:     Optional[int]  = 0
    cobrar:       Optional[int]  = 0
    agrupar:      Optional[int]  = 0


@router.post("/sync/push/inventory-entries")
async def push_inventory_entries(
    items: List[InventoryEntryIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for it in items:
        key = f"{it.company_id}|{it.id_entrada}"
        try:
            await db.execute(text("""
                INSERT INTO inventory_entries
                    (id_entrada, id_item, id_proveedor, company_id, fecha, cantidad,
                     cod_empleado, observacion, autorizada, revisada,
                     cobrar, agrupar, synced, updated_at)
                VALUES
                    (:id_entrada, :id_item, :id_proveedor, :company_id, :fecha, :cantidad,
                     :cod_empleado, :observacion, :autorizada, :revisada,
                     :cobrar, :agrupar, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    cantidad     = VALUES(cantidad),
                    autorizada   = VALUES(autorizada),
                    observacion  = VALUES(observacion),
                    synced       = 1,
                    updated_at   = NOW()
            """), it.dict())

            already = (await db.execute(text("""
                SELECT 1 FROM stock_movements
                WHERE company_id=:cid AND reference_type='entry' AND reference_id=:rid LIMIT 1
            """), {"cid": it.company_id, "rid": it.id_entrada})).fetchone()
            if not already and (it.cantidad or 0) > 0:
                await _stock_move(
                    db, it.company_id, it.id_item,
                    it.cantidad, "entry",
                    "entry", it.id_entrada, it.fecha,
                    f"Entrada #{it.id_entrada}" + (f" — {it.observacion}" if it.observacion else ""),
                )

            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(items), "total_saved": len(saved), "total_failed": len(failed)}


# ═════════════════════════════════════════
# INVENTORY EXITS (inventarios_salidas)
# ═════════════════════════════════════════
class InventoryExitIn(BaseModel):
    id_salida:    int
    id_item:      int
    id_proveedor: Optional[int] = 0
    company_id:   int
    fecha:        str
    cantidad:     Optional[float] = 0
    cod_empleado: Optional[str]  = None
    observacion:  Optional[str]  = None
    autorizada:   Optional[int]  = 0
    revisada:     Optional[int]  = 0
    cobrar:       Optional[int]  = 0
    agrupar:      Optional[int]  = 0


@router.post("/sync/push/inventory-exits")
async def push_inventory_exits(
    items: List[InventoryExitIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for it in items:
        key = f"{it.company_id}|{it.id_salida}"
        try:
            await db.execute(text("""
                INSERT INTO inventory_exits
                    (id_salida, id_item, id_proveedor, company_id, fecha, cantidad,
                     cod_empleado, observacion, autorizada, revisada,
                     cobrar, agrupar, synced, updated_at)
                VALUES
                    (:id_salida, :id_item, :id_proveedor, :company_id, :fecha, :cantidad,
                     :cod_empleado, :observacion, :autorizada, :revisada,
                     :cobrar, :agrupar, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    cantidad     = VALUES(cantidad),
                    autorizada   = VALUES(autorizada),
                    observacion  = VALUES(observacion),
                    synced       = 1,
                    updated_at   = NOW()
            """), it.dict())

            already = (await db.execute(text("""
                SELECT 1 FROM stock_movements
                WHERE company_id=:cid AND reference_type='exit' AND reference_id=:rid LIMIT 1
            """), {"cid": it.company_id, "rid": it.id_salida})).fetchone()
            if not already and (it.cantidad or 0) > 0:
                await _stock_move(
                    db, it.company_id, it.id_item,
                    -(it.cantidad), "exit",
                    "exit", it.id_salida, it.fecha,
                    f"Salida #{it.id_salida}" + (f" — {it.observacion}" if it.observacion else ""),
                )

            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(items), "total_saved": len(saved), "total_failed": len(failed)}


# ══════════════════════════════════════════════════════════════════════════════
# SYNC BIDIRECCIONAL — Descarga web → desktop
# Todos los endpoints usan X-Api-Key igual que el resto del router.
# Solo retornan pedidos cuyo order_number empieza con 'WEB-' (origen web).
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/sync/health")
async def sync_health(x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    return {"ok": True, "ts": datetime.now().isoformat()}


@router.get("/sync/pull/web-orders")
async def pull_web_orders(
    company_id: int = Query(...),
    desde: str = Query(default="2024-01-01 00:00:00"),
    x_api_key: str = Header(...),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    verify_api_key(x_api_key)
    rows = (await db_temp.execute(text("""
        SELECT
            Nro_Pedido      AS order_number,
            Fecha           AS date,
            Nro_Factura     AS invoice_number,
            Mesa            AS table_name,
            Hora            AS time,
            Mesero          AS waiter_id,
            Cancelado       AS cancelled,
            Valor           AS amount,
            Novedad         AS notes,
            Cortesia        AS complimentary,
            Nro_Comenzales  AS guests_count,
            Domicilio       AS delivery,
            Id_Cliente      AS customer_id,
            updated_at
        FROM temp_comanda
        WHERE company_id = :cid
          AND Nro_Pedido LIKE 'WEB-%'
          AND updated_at > :desde
        ORDER BY updated_at ASC
        LIMIT 200
    """), {"cid": company_id, "desde": desde})).mappings().all()
    result = []
    for r in rows:
        row = dict(r)
        # Extraer table_id desde el order_number (formato WEB-{cid}-{tid}-{ts})
        try:
            parts = str(row["order_number"]).split("-")
            row["table_id"] = int(parts[2]) if len(parts) >= 3 else 0
        except Exception:
            row["table_id"] = 0
        result.append(row)
    return result


@router.get("/sync/pull/web-order-details")
async def pull_web_order_details(
    company_id: int = Query(...),
    desde: str = Query(default="2024-01-01 00:00:00"),
    x_api_key: str = Header(...),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    verify_api_key(x_api_key)
    rows = (await db_temp.execute(text("""
        SELECT
            Nro_pedido              AS order_number,
            Fecha                   AS date,
            Nro_Factura             AS invoice_number,
            Id_Plato                AS dish_id,
            Item                    AS item,
            Depende                 AS depends_on,
            Cantidad                AS quantity,
            Valor                   AS amount,
            Novedad                 AS notes,
            Cortesia                AS complimentary,
            Porc_Descuento_Plato    AS dish_discount_pct,
            Porc_Descuento_General  AS general_discount_pct,
            Nro_Puesto              AS seat_number,
            Paga_Impuesto           AS pays_tax,
            Impuesto                AS tax,
            Impuesto_Original       AS original_tax,
            Paga_Plato              AS pays_dish,
            Cambios                 AS changes,
            Hora_Plato              AS dish_time,
            Producto_Personalizado  AS custom_product,
            updated_at
        FROM temp_detalle_comanda_parcial
        WHERE company_id = :cid
          AND Nro_pedido LIKE 'WEB-%'
          AND Mostrar = 1
          AND updated_at > :desde
        ORDER BY updated_at ASC
        LIMIT 1000
    """), {"cid": company_id, "desde": desde})).mappings().all()
    return [dict(r) for r in rows]


@router.get("/sync/pull/web-order-assembly")
async def pull_web_order_assembly(
    company_id: int = Query(...),
    desde: str = Query(default="2024-01-01 00:00:00"),
    x_api_key: str = Header(...),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    verify_api_key(x_api_key)
    rows = (await db_temp.execute(text("""
        SELECT
            Nro_Pedido   AS order_number,
            Fecha        AS date,
            Nro_Factura  AS invoice_number,
            Id_Plato     AS dish_id,
            Item         AS item,
            Id_Grupo     AS group_id,
            Id_Item      AS item_id,
            Cantidad     AS quantity,
            updated_at
        FROM temp_plato_producto_parcial
        WHERE company_id = :cid
          AND Nro_Pedido LIKE 'WEB-%'
          AND updated_at > :desde
        ORDER BY updated_at ASC
        LIMIT 1000
    """), {"cid": company_id, "desde": desde})).mappings().all()
    return [dict(r) for r in rows]


@router.get("/sync/pull/table-status")
async def pull_table_status(
    company_id: int = Query(...),
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    verify_api_key(x_api_key)
    rows = (await db.execute(text("""
        SELECT id   AS table_id,
               name AS table_name,
               CASE WHEN status = 'free' THEN 0 ELSE 1 END AS is_open,
               updated_at
        FROM pos_tables
        WHERE company_id = :cid AND is_active = 1
        ORDER BY id
    """), {"cid": company_id})).mappings().all()
    return [dict(r) for r in rows]


class LockComandaIn(BaseModel):
    company_id: int
    nro_pedido: str
    bloqueado_por: str
    lock_token: str

@router.post("/sync/lock/comanda")
async def lock_comanda(
    data: LockComandaIn,
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    verify_api_key(x_api_key)
    TTL = 90
    existing = (await db.execute(text("""
        SELECT bloqueado_por, bloqueado_en, lock_token
        FROM pos_sync_locks
        WHERE nro_pedido = :np AND company_id = :cid LIMIT 1
    """), {"np": data.nro_pedido, "cid": data.company_id})).mappings().first()

    if existing:
        seg = (datetime.now() - existing["bloqueado_en"]).total_seconds()
        if seg < TTL and existing["bloqueado_por"] != data.bloqueado_por:
            raise HTTPException(status_code=423, detail={
                "locked_by": existing["bloqueado_por"],
                "since": str(existing["bloqueado_en"]),
                "expires_in": int(TTL - seg),
            })

    await db.execute(text("""
        INSERT INTO pos_sync_locks (nro_pedido, company_id, bloqueado_por, bloqueado_en, lock_token)
        VALUES (:np, :cid, :por, NOW(), :tok)
        ON DUPLICATE KEY UPDATE
            bloqueado_por = :por, bloqueado_en = NOW(), lock_token = :tok
    """), {"np": data.nro_pedido, "cid": data.company_id,
           "por": data.bloqueado_por, "tok": data.lock_token})
    await db.commit()
    return {"ok": True, "nro_pedido": data.nro_pedido, "ttl": TTL}


@router.delete("/sync/lock/comanda/{nro_pedido}")
async def unlock_comanda(
    nro_pedido: str,
    company_id: int = Query(...),
    lock_token: str = Query(...),
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    verify_api_key(x_api_key)
    result = await db.execute(text("""
        DELETE FROM pos_sync_locks
        WHERE nro_pedido = :np AND company_id = :cid AND lock_token = :tok
    """), {"np": nro_pedido, "cid": company_id, "tok": lock_token})
    await db.commit()
    return {"ok": True, "released": result.rowcount > 0}


# ─────────────────────────────────────────────────────────────────────────────
# PUSH — VB6 sube estado de mesas (temp_mesa_abierta → pos_tables)
# ─────────────────────────────────────────────────────────────────────────────

class TableStatusPushIn(BaseModel):
    company_id: int
    table_id:   int
    table_name: Optional[str] = ""
    is_open:    Optional[int] = 0


@router.post("/sync/push/table-status")
async def push_table_status(
    tables: List[TableStatusPushIn],
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    verify_api_key(x_api_key)
    saved, failed = 0, 0
    for t in tables:
        try:
            await db.execute(text("""
                UPDATE pos_tables
                SET is_open = :is_open, updated_at = NOW()
                WHERE company_id = :cid AND id = :tid
            """), {"is_open": t.is_open, "cid": t.company_id, "tid": t.table_id})
            saved += 1
        except Exception:
            failed += 1
    await db.commit()
    return {"total_sent": len(tables), "total_saved": saved, "total_failed": failed}


# ─────────────────────────────────────────────────────────────────────────────
# PUSH — VB6 sube novedades de platos en pedidos (temp_novedades_plato_pedido)
# Tabla destino: pos_order_dish_notes
# SQL para crear la tabla en servidor:
#   CREATE TABLE IF NOT EXISTS pos_order_dish_notes (
#     id             BIGINT AUTO_INCREMENT PRIMARY KEY,
#     company_id     INT NOT NULL,
#     order_number   VARCHAR(255) NOT NULL,
#     consecutive_id INT DEFAULT 0,
#     item           INT DEFAULT 0,
#     depends_on     INT DEFAULT 0,
#     category_id    INT DEFAULT 0,
#     note_id        INT DEFAULT 0,
#     note           TEXT,
#     synced         TINYINT DEFAULT 1,
#     updated_at     DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
#     UNIQUE KEY uq_dish_note (company_id, order_number, consecutive_id, item, depends_on, category_id, note_id)
#   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
# ─────────────────────────────────────────────────────────────────────────────

class OrderDishNoteIn(BaseModel):
    company_id:     int
    order_number:   str
    consecutive_id: Optional[int] = 0
    item:           Optional[int] = 0
    depends_on:     Optional[int] = 0
    category_id:    Optional[int] = 0
    note_id:        Optional[int] = 0
    note:           Optional[str] = ""


@router.post("/sync/push/order-dish-notes")
async def push_order_dish_notes_legacy(
    notes: List[OrderDishNoteIn],
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    verify_api_key(x_api_key)
    saved, failed = 0, 0
    for n in notes:
        try:
            await db.execute(text("""
                INSERT INTO pos_order_dish_notes
                    (company_id, order_number, consecutive_id, item,
                     depends_on, category_id, note_id, note, synced, updated_at)
                VALUES
                    (:cid, :order_number, :consecutive_id, :item,
                     :depends_on, :category_id, :note_id, :note, 1, NOW())
                ON DUPLICATE KEY UPDATE
                    note = VALUES(note), synced = 1, updated_at = NOW()
            """), {
                "cid":            n.company_id,
                "order_number":   n.order_number,
                "consecutive_id": n.consecutive_id,
                "item":           n.item,
                "depends_on":     n.depends_on,
                "category_id":    n.category_id,
                "note_id":        n.note_id,
                "note":           n.note,
            })
            saved += 1
        except Exception:
            failed += 1
    await db.commit()
    return {"total_sent": len(notes), "total_saved": saved, "total_failed": failed}


# ─────────────────────────────────────────────────────────────────────────────
# REPLACE — VB6 reemplaza ítems de comanda por pedido completo
# Estrategia: DELETE existentes + INSERT estado actual (maneja borrados parciales)
# ─────────────────────────────────────────────────────────────────────────────

class _DetailItem(BaseModel):
    dish_id:              int
    item:                 int
    depends_on:           Optional[int]   = 0
    invoice_number:       Optional[str]   = "0"
    quantity:             Optional[float] = 0
    amount:               Optional[int]   = 0
    notes:                Optional[str]   = ""
    complimentary:        Optional[int]   = 0
    dish_discount_pct:    Optional[float] = 0
    general_discount_pct: Optional[float] = 0
    seat_number:          Optional[int]   = 0
    changes:              Optional[str]   = ""
    dish_time:            Optional[str]   = ""
    pays_tax:             Optional[int]   = 0
    tax:                  Optional[int]   = 0
    original_tax:         Optional[int]   = 0
    pays_dish:            Optional[int]   = 0
    custom_product:       Optional[str]   = ""


class OrderDetailReplaceIn(BaseModel):
    company_id:   int
    order_number: str
    date:         str
    items:        List[_DetailItem]


@router.post("/sync/push/order-details-replace")
async def replace_order_details(
    orders: List[OrderDetailReplaceIn],
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    verify_api_key(x_api_key)
    saved, total_orders = 0, 0
    for order in orders:
        if order.order_number.startswith("WEB-"):
            continue
        try:
            await db.execute(text("""
                DELETE FROM pos_order_details
                WHERE company_id = :cid AND order_number = :on AND date = :d
            """), {"cid": order.company_id, "on": order.order_number, "d": order.date})
            for it in order.items:
                await db.execute(text("""
                    INSERT INTO pos_order_details
                        (company_id, order_number, date, invoice_number,
                         dish_id, item, depends_on, quantity, amount, notes,
                         complimentary, dish_discount_pct, general_discount_pct,
                         seat_number, changes, dish_time, pays_tax, tax,
                         original_tax, pays_dish, custom_product, synced, updated_at)
                    VALUES
                        (:cid, :on, :d, :inv,
                         :dish_id, :item, :dep, :qty, :amt, :notes,
                         :comp, :dsc_d, :dsc_g,
                         :seat, :changes, :dish_time, :ptax, :tax,
                         :otax, :pdish, :custom, 1, NOW())
                """), {
                    "cid": order.company_id, "on": order.order_number,
                    "d": order.date,         "inv": it.invoice_number,
                    "dish_id": it.dish_id,   "item": it.item,
                    "dep": it.depends_on,    "qty": it.quantity,
                    "amt": it.amount,        "notes": it.notes,
                    "comp": it.complimentary, "dsc_d": it.dish_discount_pct,
                    "dsc_g": it.general_discount_pct, "seat": it.seat_number,
                    "changes": it.changes,   "dish_time": it.dish_time,
                    "ptax": it.pays_tax,     "tax": it.tax,
                    "otax": it.original_tax, "pdish": it.pays_dish,
                    "custom": it.custom_product,
                })
                saved += 1
            total_orders += 1
        except Exception:
            pass
    await db.commit()
    return {"total_orders": total_orders, "total_saved": saved}


class _AssemblyItem(BaseModel):
    dish_id:        int
    item:           int
    group_id:       int
    item_id:        int
    invoice_number: Optional[str]   = "0"
    quantity:       Optional[float] = 0


class OrderAssemblyReplaceIn(BaseModel):
    company_id:   int
    order_number: str
    date:         str
    items:        List[_AssemblyItem]


@router.post("/sync/push/order-detail-products-replace")
async def replace_order_detail_products(
    orders: List[OrderAssemblyReplaceIn],
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    verify_api_key(x_api_key)
    saved, total_orders = 0, 0
    for order in orders:
        if order.order_number.startswith("WEB-"):
            continue
        try:
            await db.execute(text("""
                DELETE FROM pos_order_detail_products
                WHERE company_id = :cid AND order_number = :on
            """), {"cid": order.company_id, "on": order.order_number})
            for it in order.items:
                await db.execute(text("""
                    INSERT INTO pos_order_detail_products
                        (company_id, order_number, date, invoice_number,
                         dish_id, item, group_id, item_id, quantity, synced, updated_at)
                    VALUES
                        (:cid, :on, :d, :inv,
                         :dish_id, :item, :group_id, :item_id, :qty, 1, NOW())
                """), {
                    "cid": order.company_id, "on": order.order_number,
                    "d": order.date,         "inv": it.invoice_number,
                    "dish_id": it.dish_id,   "item": it.item,
                    "group_id": it.group_id, "item_id": it.item_id,
                    "qty": it.quantity,
                })
                saved += 1
            total_orders += 1
        except Exception:
            pass
    await db.commit()
    return {"total_orders": total_orders, "total_saved": saved}


class _DishNoteItem(BaseModel):
    consecutive_id: Optional[int] = 0
    item:           Optional[int] = 0
    depends_on:     Optional[int] = 0
    category_id:    Optional[int] = 0
    note_id:        Optional[int] = 0
    note:           Optional[str] = ""


class OrderDishNotesReplaceIn(BaseModel):
    company_id:   int
    order_number: str
    items:        List[_DishNoteItem]


@router.post("/sync/push/order-dish-notes-replace")
async def replace_order_dish_notes(
    orders: List[OrderDishNotesReplaceIn],
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    verify_api_key(x_api_key)
    saved, total_orders = 0, 0
    for order in orders:
        if order.order_number.startswith("WEB-"):
            continue
        try:
            await db.execute(text("""
                DELETE FROM pos_order_dish_notes
                WHERE company_id = :cid AND order_number = :on
            """), {"cid": order.company_id, "on": order.order_number})
            for it in order.items:
                await db.execute(text("""
                    INSERT INTO pos_order_dish_notes
                        (company_id, order_number, consecutive_id, item,
                         depends_on, category_id, note_id, note, synced, updated_at)
                    VALUES
                        (:cid, :on, :cons, :item,
                         :dep, :cat, :note_id, :note, 1, NOW())
                """), {
                    "cid": order.company_id, "on": order.order_number,
                    "cons": it.consecutive_id, "item": it.item,
                    "dep": it.depends_on,      "cat": it.category_id,
                    "note_id": it.note_id,     "note": it.note,
                })
                saved += 1
            total_orders += 1
        except Exception:
            pass
    await db.commit()
    return {"total_orders": total_orders, "total_saved": saved}
