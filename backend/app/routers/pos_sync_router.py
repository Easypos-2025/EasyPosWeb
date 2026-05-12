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
    id_number: Optional[str] = "1"
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
    currency_type: Optional[int] = 0
    foreign_amount: Optional[float] = 0
    manual_invoice: Optional[int] = 0
    resolution_id: Optional[int] = 0
    customer_id: Optional[int] = 0
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
                    id_number, employee_id, voided, paid_vat, adjustment,
                    credit_card_amount, debit_card_amount, tip, shift,
                    time, time_text, extra_tip, amount_without_tip, analyzed,
                    currency_type, foreign_amount, manual_invoice, resolution_id,
                    customer_id, reservation_invoice, delivery_invoice,
                    synced, updated_at
                ) VALUES (
                    :invoice_number, :company_id, :date, :cash_amount, :discount,
                    :id_number, :employee_id, :voided, :paid_vat, :adjustment,
                    :credit_card_amount, :debit_card_amount, :tip, :shift,
                    :time, :time_text, :extra_tip, :amount_without_tip, :analyzed,
                    :currency_type, :foreign_amount, :manual_invoice, :resolution_id,
                    :customer_id, :reservation_invoice, :delivery_invoice,
                    1, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    cash_amount         = VALUES(cash_amount),
                    discount            = VALUES(discount),
                    id_number           = VALUES(id_number),
                    employee_id         = VALUES(employee_id),
                    voided              = VALUES(voided),
                    credit_card_amount  = VALUES(credit_card_amount),
                    debit_card_amount   = VALUES(debit_card_amount),
                    tip                 = VALUES(tip),
                    extra_tip           = VALUES(extra_tip),
                    amount_without_tip  = VALUES(amount_without_tip),
                    delivery_invoice    = VALUES(delivery_invoice),
                    synced              = 1,
                    updated_at          = NOW()
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
    company_id: int = Query(..., description="ID de la empresa"),
    since: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD HH:MM:SS)"),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    if since:
        result = await db.execute(text("""
            SELECT * FROM pos_invoices
            WHERE company_id = :company_id
              AND updated_at >= :since
            ORDER BY updated_at ASC
        """), {"company_id": company_id, "since": since})
    else:
        result = await db.execute(text("""
            SELECT * FROM pos_invoices
            WHERE company_id = :company_id
            ORDER BY updated_at ASC
            LIMIT 500
        """), {"company_id": company_id})

    rows = result.mappings().all()
    return {
        "total": len(rows),
        "since": since,
        "invoices": [dict(r) for r in rows],
    }
