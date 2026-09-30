from fastapi import Depends
from app.auth.tenant import tenant_guard
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.auth.dependencies import get_current_user

# Aislamiento multi-tenant: valida todo company_id que envíe el navegador (CLAUDE.md §6)
router = APIRouter(prefix="/api/payment-types", tags=["Payment Types"], dependencies=[Depends(tenant_guard)])


# ─── Billetes rápidos (pago en efectivo) — máx. 6 por empresa ─────────────────
# Declarados antes de /{payment_id} para que esa ruta no los capture.
_MAX_BILLETES = 6


@router.get("/billetes")
async def list_billetes(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rows = (await db.execute(text(
        "SELECT value FROM pos_cash_denominations WHERE company_id = :cid ORDER BY sort_order, value DESC"
    ), {"cid": current_user.company_id})).all()
    return [int(r[0]) for r in rows]


@router.put("/billetes")
async def set_billetes(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Reemplaza la lista de billetes de la empresa (valores enteros > 0, sin repetir)."""
    raw = body.get("values") or []
    if not isinstance(raw, list):
        raise HTTPException(status_code=422, detail="values debe ser una lista")
    try:
        values = [int(v) for v in raw]
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Los valores deben ser números enteros")
    values = list(dict.fromkeys(v for v in values if 0 < v <= 100_000_000))
    if len(values) > _MAX_BILLETES:
        raise HTTPException(status_code=422, detail=f"Máximo {_MAX_BILLETES} billetes")
    cid = current_user.company_id
    await db.execute(text("DELETE FROM pos_cash_denominations WHERE company_id = :cid"), {"cid": cid})
    for i, v in enumerate(values):
        await db.execute(text(
            "INSERT INTO pos_cash_denominations (company_id, value, sort_order) VALUES (:cid, :v, :o)"
        ), {"cid": cid, "v": v, "o": i})
    await db.commit()
    return {"ok": True, "values": values}

# ─── Listar ────────────────────────────────────────────────────────────────────
@router.get("")
async def list_payment_types(
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rows = (await db.execute(text("""
        SELECT id, company_id, name, is_active, is_default,
               adds_to_cash, select_card, ask_notes,
               validate_amount, validate_number, ask_customer
        FROM pos_payment_types
        WHERE company_id = :cid
        ORDER BY is_default DESC, id ASC
    """), {"cid": company_id})).mappings().all()
    return [dict(r) for r in rows]


# ─── Crear ─────────────────────────────────────────────────────────────────────
@router.post("")
async def create_payment_type(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = body.get("company_id")
    name       = (body.get("name") or "").strip()
    if not company_id or not name:
        raise HTTPException(status_code=422, detail="company_id y name son requeridos")

    # Siguiente id para esta empresa
    row = (await db.execute(text(
        "SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM pos_payment_types WHERE company_id = :cid"
    ), {"cid": company_id})).mappings().first()
    next_id = int(row["next_id"])

    is_default = int(bool(body.get("is_default", 0)))

    # Si es default, quitar default al resto
    if is_default:
        await db.execute(text(
            "UPDATE pos_payment_types SET is_default = 0 WHERE company_id = :cid"
        ), {"cid": company_id})

    await db.execute(text("""
        INSERT INTO pos_payment_types
            (id, company_id, name, is_active, is_default,
             adds_to_cash, select_card, ask_notes,
             validate_amount, validate_number, ask_customer, synced)
        VALUES
            (:id, :cid, :name, :active, :def,
             :cash, :card, :notes, :val_amt, :val_num, :ask_cust, 0)
    """), {
        "id":       next_id,
        "cid":      company_id,
        "name":     name,
        "active":   int(bool(body.get("is_active", 1))),
        "def":      is_default,
        "cash":     int(bool(body.get("adds_to_cash", 0))),
        "card":     int(bool(body.get("select_card", 0))),
        "notes":    int(bool(body.get("ask_notes", 0))),
        "val_amt":  int(bool(body.get("validate_amount", 0))),
        "val_num":  int(bool(body.get("validate_number", 0))),
        "ask_cust": int(bool(body.get("ask_customer", 0))),
    })
    await db.commit()

    return {"id": next_id, "company_id": company_id, "name": name}


# ─── Actualizar ────────────────────────────────────────────────────────────────
@router.put("/{payment_id}")
async def update_payment_type(
    payment_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = body.get("company_id")
    name       = (body.get("name") or "").strip()
    if not company_id or not name:
        raise HTTPException(status_code=422, detail="company_id y name son requeridos")

    exists = (await db.execute(text(
        "SELECT id FROM pos_payment_types WHERE id = :pid AND company_id = :cid"
    ), {"pid": payment_id, "cid": company_id})).mappings().first()
    if not exists:
        raise HTTPException(status_code=404, detail="Forma de pago no encontrada")

    is_default = int(bool(body.get("is_default", 0)))
    if is_default:
        await db.execute(text(
            "UPDATE pos_payment_types SET is_default = 0 WHERE company_id = :cid AND id != :pid"
        ), {"cid": company_id, "pid": payment_id})

    await db.execute(text("""
        UPDATE pos_payment_types SET
            name             = :name,
            is_active        = :active,
            is_default       = :def,
            adds_to_cash     = :cash,
            select_card      = :card,
            ask_notes        = :notes,
            validate_amount  = :val_amt,
            validate_number  = :val_num,
            ask_customer     = :ask_cust
        WHERE id = :pid AND company_id = :cid
    """), {
        "name":     name,
        "active":   int(bool(body.get("is_active", 1))),
        "def":      is_default,
        "cash":     int(bool(body.get("adds_to_cash", 0))),
        "card":     int(bool(body.get("select_card", 0))),
        "notes":    int(bool(body.get("ask_notes", 0))),
        "val_amt":  int(bool(body.get("validate_amount", 0))),
        "val_num":  int(bool(body.get("validate_number", 0))),
        "ask_cust": int(bool(body.get("ask_customer", 0))),
        "pid":      payment_id,
        "cid":      company_id,
    })
    await db.commit()
    return {"ok": True}


# ─── Eliminar ──────────────────────────────────────────────────────────────────
@router.delete("/{payment_id}")
async def delete_payment_type(
    payment_id: int,
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Verificar que no tenga pagos registrados
    used = (await db.execute(text("""
        SELECT COUNT(*) AS cnt FROM pos_receipt_payment_methods
        WHERE payment_method_id = :pid AND company_id = :cid
    """), {"pid": payment_id, "cid": company_id})).mappings().first()

    if used and int(used["cnt"]) > 0:
        raise HTTPException(
            status_code=409,
            detail=f"No se puede eliminar: esta forma de pago tiene {used['cnt']} pago(s) registrado(s)"
        )

    await db.execute(text(
        "DELETE FROM pos_payment_types WHERE id = :pid AND company_id = :cid"
    ), {"pid": payment_id, "cid": company_id})
    await db.commit()
    return {"ok": True}


# ─── Toggle activo ─────────────────────────────────────────────────────────────
@router.patch("/{payment_id}/toggle-active")
async def toggle_active(
    payment_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = body.get("company_id")
    if not company_id:
        raise HTTPException(status_code=422, detail="company_id requerido")

    row = (await db.execute(text(
        "SELECT is_active FROM pos_payment_types WHERE id = :pid AND company_id = :cid"
    ), {"pid": payment_id, "cid": company_id})).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Forma de pago no encontrada")

    new_val = 0 if row["is_active"] else 1
    await db.execute(text(
        "UPDATE pos_payment_types SET is_active = :v WHERE id = :pid AND company_id = :cid"
    ), {"v": new_val, "pid": payment_id, "cid": company_id})
    await db.commit()
    return {"is_active": new_val}
