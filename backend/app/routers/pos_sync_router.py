import os
from typing import List, Optional
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
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
                    branch_id, customer_id, dynamic_zone, synced, updated_at
                ) VALUES (
                    :id, :company_id, :zone_id, :name, :capacity, :is_active,
                    0, 0, 0, 1, NOW()
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
    id_registro:    int
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
            await db.execute(text("""
                INSERT INTO pos_order_detail_products
                    (order_number, date, invoice_number, dish_id, item, group_id, item_id,
                     quantity, synced, company_id, updated_at)
                VALUES
                    (:order_number, :date, :invoice_number, :dish_id, :item, :group_id, :item_id,
                     :quantity, 1, :company_id, NOW())
                ON DUPLICATE KEY UPDATE
                    quantity   = VALUES(quantity),
                    synced     = 1,
                    updated_at = NOW()
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
            await db.execute(text("""
                INSERT INTO pos_receipt_order_detail_products
                    (order_number, date, invoice_number, dish_id, item, group_id, item_id,
                     quantity, synced, company_id, updated_at)
                VALUES
                    (:order_number, :date, :invoice_number, :dish_id, :item, :group_id, :item_id,
                     :quantity, 1, :company_id, NOW())
                ON DUPLICATE KEY UPDATE
                    quantity   = VALUES(quantity),
                    synced     = 1,
                    updated_at = NOW()
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
