import os
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db

router = APIRouter(prefix="/api/pos", tags=["POS Sync"])

POS_API_KEY = os.getenv("POS_API_KEY", "easypos-sync-key-2024")


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != POS_API_KEY:
        raise HTTPException(status_code=401, detail="API Key inválida")


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

    for inv in invoices:
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
    receipt_number: str
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
    delivery_receipt: Optional[int] = 0


@router.post("/sync/push/receipts")
async def push_receipts(
    receipts: List[ReceiptIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for r in receipts:
        try:
            await db.execute(text("""
                INSERT INTO pos_receipts (
                    receipt_number, company_id, date, cash_amount, discount,
                    customer_id, employee_id, voided, paid_vat, adjustment,
                    credit_card_amount, debit_card_amount, tip, shift,
                    time, time_text, extra_tip, amount_without_tip, analyzed,
                    currency_type_id, foreign_amount, manual_receipt, resolution_id,
                    reservation_receipt, delivery_receipt, synced, updated_at
                ) VALUES (
                    :receipt_number, :company_id, :date, :cash_amount, :discount,
                    :customer_id, :employee_id, :voided, :paid_vat, :adjustment,
                    :credit_card_amount, :debit_card_amount, :tip, :shift,
                    :time, :time_text, :extra_tip, :amount_without_tip, :analyzed,
                    :currency_type_id, :foreign_amount, :manual_receipt, :resolution_id,
                    :reservation_receipt, :delivery_receipt, 1, NOW()
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
                    delivery_receipt   = VALUES(delivery_receipt),
                    synced             = 1,
                    updated_at         = NOW()
            """), r.dict())
            saved.append(r.receipt_number)
        except Exception as e:
            failed.append({"receipt_number": r.receipt_number, "error": str(e)})
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
                    active, category_id, photo_path, description, printer, comment,
                    extra_print, printer_2, pre_preparation, offer, offer_priority,
                    tax, wholesale_price, product_cost, minimum_stock,
                    ask_sale_price, ask_product_description, synced, updated_at
                ) VALUES (
                    :id, :company_id, :name, :product_code, :price, :preparation_time,
                    :active, :category_id, :photo_path, :description, :printer, :comment,
                    :extra_print, :printer_2, :pre_preparation, :offer, :offer_priority,
                    :tax, :wholesale_price, :product_cost, :minimum_stock,
                    :ask_sale_price, :ask_product_description, 1, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    name                   = VALUES(name),
                    product_code           = VALUES(product_code),
                    price                  = VALUES(price),
                    active                 = VALUES(active),
                    category_id            = VALUES(category_id),
                    description            = VALUES(description),
                    tax                    = VALUES(tax),
                    wholesale_price        = VALUES(wholesale_price),
                    product_cost           = VALUES(product_cost),
                    minimum_stock          = VALUES(minimum_stock),
                    synced                 = 1,
                    updated_at             = NOW()
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
    for w in waiters:
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
    sql = "SELECT * FROM pos_waiters WHERE company_id = :company_id"
    params = {"company_id": company_id}
    if since:
        sql += " AND updated_at >= :since"
        params["since"] = since
    sql += " ORDER BY updated_at ASC LIMIT 500"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "since": since, "waiters": [dict(r) for r in rows]}


# ═════════════════════════════════════════
# TABLES LAYOUT (mesas)
# ═════════════════════════════════════════
class TableLayoutIn(BaseModel):
    id: int
    company_id: int
    branch_id: Optional[int] = 0
    name: str
    location: Optional[str] = ""
    seats: Optional[int] = 0
    customer_id: Optional[int] = 0
    dynamic_zone: Optional[int] = 0
    active: Optional[int] = 0
    zone_id: Optional[int] = 0


@router.post("/sync/push/tables")
async def push_tables(
    tables: List[TableLayoutIn],
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    saved, failed = [], []
    for t in tables:
        try:
            await db.execute(text("""
                INSERT INTO pos_tables_layout (
                    id, company_id, branch_id, name, location, seats,
                    customer_id, dynamic_zone, active, zone_id, synced, updated_at
                ) VALUES (
                    :id, :company_id, :branch_id, :name, :location, :seats,
                    :customer_id, :dynamic_zone, :active, :zone_id, 1, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    name         = VALUES(name),
                    location     = VALUES(location),
                    seats        = VALUES(seats),
                    active       = VALUES(active),
                    zone_id      = VALUES(zone_id),
                    synced       = 1,
                    updated_at   = NOW()
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
