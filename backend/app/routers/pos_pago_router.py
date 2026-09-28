"""
Fase 2 — Registro de Recibo (pantalla de pago, botón "PAGAR").

A diferencia de la toma de pedido (kiosco de mesero, `pos_comanda_router`),
el registro de un recibo es una operación de dinero: exige sesión de panel
completo (`get_current_user`, tabla `users`) y turno de caja abierto
(`require_open_shift`) — el `id_caja` que se anexa a `pos_cash_register_receipts`
es el de quien está confirmando el pago en este momento, sin importar quién
montó el pedido.

Nota de consistencia entre bases de datos: `easyposweb` (recibo permanente)
y `datatemppos` (pedido en curso) son motores/conexiones distintos, no hay
transacción atómica real entre ambos. Por eso se confirma primero el recibo
en `easyposweb` (el registro permanente y lo que de verdad importa contable/
fiscalmente) y solo si eso tiene éxito se cierra el pedido en `datatemppos`
— así, ante una falla a mitad de camino, en el peor caso el recibo ya quedó
registrado y el pedido sigue abierto (recuperable a mano) en vez de perderse.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db, get_datatemppos_db
from app.auth.dependencies import get_current_user
from app.models.user_model import User
from app.routers.pos_shift_router import require_open_shift
from app.services import consecutivo_service as cs

router = APIRouter(prefix="/api/pos/pago", tags=["POS Pago"])

_BOG = timezone(timedelta(hours=-5))


async def _siguiente_id_registro(db: AsyncSession, tabla: str, cid: int) -> int:
    """
    Varias tablas de recibo (pos_receipt_discounts, receipt_delivery_fees,
    pos_cash_register_closings...) traen una UNIQUE KEY (id_registro, company_id)
    heredada de la sincronización con escritorio (id_registro = su propio
    autoincremental, siempre positivo). Las filas nativas de la web usan una
    secuencia negativa propia para no repetir nunca ni chocar con el escritorio.
    """
    row = (await db.execute(text(
        f"SELECT COALESCE(MIN(id_registro), 0) - 1 AS next FROM {tabla} WHERE company_id = :cid"
    ), {"cid": cid})).mappings().first()
    return int(row["next"])


async def _cliente_consumidor_final(db: AsyncSession, cid: int) -> int:
    row = (await db.execute(text(
        "SELECT id FROM clients WHERE company_id=:cid AND document_number='222222222222' LIMIT 1"
    ), {"cid": cid})).mappings().first()
    if row:
        return int(row["id"])
    await db.execute(text("""
        INSERT INTO clients (company_id, name, document_type, document_number, is_active, created_at)
        VALUES (:cid, 'Consumidor Final', 'CC', '222222222222', 1, NOW())
    """), {"cid": cid})
    await db.commit()
    new_row = (await db.execute(text(
        "SELECT id FROM clients WHERE company_id=:cid AND document_number='222222222222' LIMIT 1"
    ), {"cid": cid})).mappings().first()
    return int(new_row["id"])


async def _cargar_cuenta(db_temp: AsyncSession, cid: int, order_number: str):
    orden = (await db_temp.execute(text("""
        SELECT Nro_Pedido, Fecha, Mesa, Hora, Mesero, Valor, Nro_Comenzales, Domicilio, Id_Cliente
        FROM temp_comanda
        WHERE company_id=:cid AND Nro_Pedido=:on AND Nro_Factura='0' AND Cancelado=0
        LIMIT 1
    """), {"cid": cid, "on": order_number})).mappings().first()
    if not orden:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada o ya facturada")

    items = (await db_temp.execute(text("""
        SELECT Id_Plato, Item, Descripcion, Cantidad, Valor, Porc_Descuento_General, Id_Tipificacion
        FROM temp_detalle_comanda_parcial
        WHERE company_id=:cid AND Nro_pedido=:on AND Nro_Factura='0' AND Mostrar=1
        ORDER BY Item
    """), {"cid": cid, "on": order_number})).mappings().all()
    if not items:
        raise HTTPException(status_code=400, detail="La cuenta no tiene ítems")

    return orden, items


# ═══════════════════════════════════════════════════════════════════════════
# GET /api/pos/pago/{order_number} — datos para armar la pantalla de pago
# ═══════════════════════════════════════════════════════════════════════════
@router.get("/{order_number}")
async def datos_pago(
    order_number: str,
    db: AsyncSession = Depends(get_db),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
    current_user: User = Depends(get_current_user),
    turno: dict = Depends(require_open_shift),
):
    cid = current_user.company_id
    orden, items = await _cargar_cuenta(db_temp, cid, order_number)

    dish_ids = list({int(i["Id_Plato"]) for i in items})
    dish_names = {}
    if dish_ids:
        ids = ",".join(str(d) for d in dish_ids)
        drows = (await db.execute(text(
            f"SELECT id, name FROM pos_dishes WHERE company_id=:cid AND id IN ({ids})"
        ), {"cid": cid})).mappings().all()
        dish_names = {int(r["id"]): r["name"] for r in drows}

    subtotal = int(orden["Valor"] or 0)
    tiene_descuento_item = any(int(i["Id_Tipificacion"] or 0) != 0 for i in items)

    cfg = (await db.execute(text(
        "SELECT COALESCE(has_tip,0) has_tip, COALESCE(tip_percentage,0) tip_percentage, "
        "COALESCE(tip_label,'Propina') tip_label, COALESCE(has_pos_electronico,0) has_pos_electronico "
        "FROM company_configs WHERE company_id=:cid"
    ), {"cid": cid})).mappings().first()
    has_tip = bool(cfg and cfg["has_tip"])
    tip_suggested = round(subtotal * float(cfg["tip_percentage"]) / 100) if has_tip else 0

    payment_types = (await db.execute(text(
        "SELECT id, name, is_default, select_card, ask_notes, ask_customer "
        "FROM pos_payment_types WHERE company_id=:cid AND is_active=1 ORDER BY is_default DESC, id"
    ), {"cid": cid})).mappings().all()

    waiters = (await db.execute(text(
        "SELECT id, name FROM pos_waiters WHERE company_id=:cid AND status=1 ORDER BY name"
    ), {"cid": cid})).mappings().all()

    cliente_default = int(orden["Id_Cliente"] or 0) or await _cliente_consumidor_final(db, cid)
    consecutivo_preview = await cs.previsualizar_consecutivo(db, company_id=cid, tipo="recibo")

    return {
        "order": {
            "order_number": orden["Nro_Pedido"], "date": str(orden["Fecha"]),
            "table_name": orden["Mesa"], "guests_count": int(orden["Nro_Comenzales"] or 0),
            "is_delivery": bool(orden["Domicilio"]), "waiter_id": int(orden["Mesero"] or 0),
        },
        "items": [{
            "dish_id": int(i["Id_Plato"]), "item": int(i["Item"]),
            "name": dish_names.get(int(i["Id_Plato"]), f"Plato {i['Id_Plato']}"),
            "quantity": float(i["Cantidad"] or 0), "amount": int(i["Valor"] or 0),
            "typification_id": int(i["Id_Tipificacion"] or 0),
        } for i in items],
        "subtotal": subtotal,
        "has_item_discount": tiene_descuento_item,
        "tip": {"enabled": has_tip, "suggested": tip_suggested, "label": cfg["tip_label"] if cfg else "Propina"},
        "has_pos_electronico": bool(cfg and cfg["has_pos_electronico"]),
        "payment_types": [dict(p) for p in payment_types],
        "waiters": [dict(w) for w in waiters],
        "default_customer_id": cliente_default,
        "consecutivo_preview": consecutivo_preview,
        "turno_id": turno["id"],
    }


class PagoIn(BaseModel):
    customer_id: Optional[int] = None
    waiter_id: Optional[int] = None
    discount_percentage: float = 0
    tip_amount: Optional[int] = None
    delivery_amount: int = 0
    observacion: Optional[str] = None
    payments: List[dict] = []  # [{payment_method_id, amount, notes?}]


# ═══════════════════════════════════════════════════════════════════════════
# POST /api/pos/pago/{order_number} — registra el Recibo
# ═══════════════════════════════════════════════════════════════════════════
@router.post("/{order_number}")
async def registrar_recibo(
    order_number: str,
    body: PagoIn,
    db: AsyncSession = Depends(get_db),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
    current_user: User = Depends(get_current_user),
    turno: dict = Depends(require_open_shift),
):
    cid, uid = current_user.company_id, current_user.id
    orden, items = await _cargar_cuenta(db_temp, cid, order_number)

    subtotal = sum(int(i["Valor"] or 0) for i in items)
    tiene_descuento_item = any(int(i["Id_Tipificacion"] or 0) != 0 for i in items)

    discount_amount = 0
    if body.discount_percentage:
        if tiene_descuento_item:
            raise HTTPException(
                status_code=422,
                detail="No se puede aplicar descuento general: ya hay ítems con descuento individual aplicado",
            )
        if not (0 < body.discount_percentage <= 100):
            raise HTTPException(status_code=422, detail="Porcentaje de descuento inválido")
        discount_amount = round(subtotal * body.discount_percentage / 100)

    base = subtotal - discount_amount

    cfg = (await db.execute(text(
        "SELECT COALESCE(has_tip,0) has_tip, COALESCE(tip_percentage,0) tip_percentage "
        "FROM company_configs WHERE company_id=:cid"
    ), {"cid": cid})).mappings().first()
    if body.tip_amount is not None:
        tip_amount = max(0, int(body.tip_amount))
    elif cfg and cfg["has_tip"]:
        tip_amount = round(base * float(cfg["tip_percentage"]) / 100)
    else:
        tip_amount = 0

    delivery_amount = max(0, int(body.delivery_amount or 0))
    grand_total = base + tip_amount + delivery_amount

    if not body.payments:
        raise HTTPException(status_code=422, detail="Debe seleccionar al menos una forma de pago")
    total_pagado = sum(float(p.get("amount", 0)) for p in body.payments)
    if abs(total_pagado - grand_total) > 1:
        raise HTTPException(
            status_code=422,
            detail=f"La suma de pagos ({total_pagado:.0f}) no coincide con el total a pagar ({grand_total})",
        )

    customer_id = body.customer_id or int(orden["Id_Cliente"] or 0) or await _cliente_consumidor_final(db, cid)
    waiter_id = body.waiter_id or int(orden["Mesero"] or 0)

    # ── Consecutivo definitivo (reserva independiente, ver consecutivo_service) ─
    receipt_number = str(await cs.generar_consecutivo(
        db, company_id=cid, nro_pedido=order_number, fecha=orden["Fecha"], tipo="recibo",
    ))

    now = datetime.now(_BOG)
    fecha, hora = now.date().isoformat(), now.strftime("%H:%M:%S")
    is_delivery = 1 if delivery_amount else 0

    # ── pos_receipts (encabezado permanente) ────────────────────────────────
    await db.execute(text("""
        INSERT INTO pos_receipts
            (receipt_number, date, company_id, cash_amount, discount, employee_id,
             tip, shift, time, time_text, amount_without_tip, customer_id,
             delivery_receipt, voided, synced)
        VALUES
            (:rn, :fecha, :cid, :total, :disc, :uid,
             :tip, 1, :hora, :hora, :base, :cust,
             :is_delivery, 0, 0)
    """), {
        "rn": receipt_number, "fecha": fecha, "cid": cid, "total": grand_total, "disc": discount_amount,
        "uid": uid, "tip": tip_amount, "hora": hora, "base": base, "cust": customer_id,
        "is_delivery": is_delivery,
    })

    # ── pos_receipt_orders (cabecera de comanda) ────────────────────────────
    await db.execute(text("""
        INSERT INTO pos_receipt_orders
            (order_number, date, receipt_number, table_name, time, waiter_id,
             cancelled, amount, notes, guests_count, delivery, customer_id, synced, company_id)
        VALUES
            (:on, :fecha, :rn, :mesa, :hora, :wid,
             0, :total, :obs, :guests, :is_delivery, :cust, 0, :cid)
    """), {
        "on": order_number, "fecha": fecha, "rn": receipt_number, "mesa": orden["Mesa"], "hora": hora,
        "wid": waiter_id, "total": grand_total, "obs": (body.observacion or "")[:250],
        "guests": int(orden["Nro_Comenzales"] or 0), "is_delivery": is_delivery, "cust": customer_id, "cid": cid,
    })

    # ── pos_receipt_order_details + pos_receipt_discounts ───────────────────
    next_id_registro_disc = await _siguiente_id_registro(db, "pos_receipt_discounts", cid)
    for it in items:
        dish_id, item_no = int(it["Id_Plato"]), int(it["Item"])
        await db.execute(text("""
            INSERT INTO pos_receipt_order_details
                (order_number, date, receipt_number, dish_id, item, quantity,
                 amount, notes, depends_on, synced, company_id)
            VALUES
                (:on, :fecha, :rn, :did, :item, :qty,
                 :amount, :notes, 0, 0, :cid)
        """), {
            "on": order_number, "fecha": fecha, "rn": receipt_number, "did": dish_id, "item": item_no,
            "qty": float(it["Cantidad"] or 0), "amount": int(it["Valor"] or 0),
            "notes": it["Descripcion"], "cid": cid,
        })

        tip_id = int(it["Id_Tipificacion"] or 0)
        if tip_id:
            original = int(it["Porc_Descuento_General"] or 0)
            sale = int(it["Valor"] or 0)
            await db.execute(text("""
                INSERT INTO pos_receipt_discounts
                    (id_registro, company_id, date, receipt_number, dish_id, item,
                     typification_id, original_price, sale_price, discount_amount,
                     order_number, synced)
                VALUES
                    (:idreg, :cid, :fecha, :rn, :did, :item,
                     :tid, :orig, :sale, :desc_amt,
                     :on, 0)
            """), {
                "idreg": next_id_registro_disc, "cid": cid, "fecha": fecha, "rn": receipt_number,
                "did": dish_id, "item": item_no,
                "tid": tip_id, "orig": original, "sale": sale, "desc_amt": max(0, original - sale),
                "on": order_number,
            })
            next_id_registro_disc -= 1

    # ── pos_receipt_payment_methods ──────────────────────────────────────────
    for idx, pago in enumerate(body.payments, start=1):
        await db.execute(text("""
            INSERT INTO pos_receipt_payment_methods
                (item, payment_method_id, card_id, invoice_number, amount, date,
                 order_number, notes, synced, company_id)
            VALUES
                (:item, :pm_id, 0, :rn, :amount, :fecha,
                 :on, :notes, 0, :cid)
        """), {
            "item": idx, "pm_id": int(pago["payment_method_id"]), "rn": receipt_number, "amount": float(pago.get("amount", 0)),
            "fecha": fecha, "on": order_number, "notes": (pago.get("notes") or "")[:250], "cid": cid,
        })

    # ── receipt_delivery_fees (si aplica) ────────────────────────────────────
    if delivery_amount:
        next_id_registro_dom = await _siguiente_id_registro(db, "receipt_delivery_fees", cid)
        await db.execute(text("""
            INSERT INTO receipt_delivery_fees
                (id_registro, invoice_number, amount, date, order_number, employee_id, customer_id, synced, company_id)
            VALUES
                (:idreg, :rn, :amount, :fecha, :on, :wid, :cust, 0, :cid)
        """), {
            "idreg": next_id_registro_dom,
            "rn": receipt_number, "amount": delivery_amount, "fecha": fecha, "on": order_number,
            "wid": waiter_id, "cust": customer_id, "cid": cid,
        })

    # ── pos_cash_register_receipts (relaciona el recibo con el turno/caja) ──
    await db.execute(text("""
        INSERT INTO pos_cash_register_receipts
            (register_number, closing_id, receipt_number, date, order_number,
             amount, base_amount, employee_id, shift, company_id, synced)
        VALUES
            (:rn_caja, :closing_id, :rn, :fecha, :on,
             :total, :base, :uid, 1, :cid, 0)
    """), {
        "rn_caja": int(turno.get("register_number") or 0), "closing_id": turno["id"], "rn": receipt_number,
        "fecha": fecha, "on": order_number, "total": grand_total, "base": base, "uid": uid, "cid": cid,
    })

    # ── Confirmar primero lo permanente (easyposweb) ─────────────────────────
    await db.commit()

    # ── Descontar inventario y cerrar el pedido en datatemppos ───────────────
    for it in items:
        dish_id, item_no = int(it["Id_Plato"]), int(it["Item"])
        insumos = (await db_temp.execute(text("""
            SELECT Id_Item, Cantidad FROM temp_plato_producto_parcial
            WHERE company_id=:cid AND Nro_Pedido=:on AND Nro_Factura='0'
              AND Id_Plato=:did AND Item=:item
        """), {"cid": cid, "on": order_number, "did": dish_id, "item": item_no})).mappings().all()
        for ins in insumos:
            await db_temp.execute(text("""
                UPDATE easyposweb.inventario_actual_porciones
                SET cantidad_actual = cantidad_actual - :qty, enviada_mysql = 0, updated_at = NOW()
                WHERE company_id = :cid AND id_item = :iid
            """), {"qty": float(ins["Cantidad"] or 0), "cid": cid, "iid": int(ins["Id_Item"])})

    await db_temp.execute(text("""
        UPDATE temp_comanda SET Nro_Factura = :rn WHERE company_id=:cid AND Nro_Pedido=:on
    """), {"rn": receipt_number, "cid": cid, "on": order_number})
    await db_temp.execute(text("""
        UPDATE temp_detalle_comanda_parcial SET Nro_Factura = :rn WHERE company_id=:cid AND Nro_pedido=:on AND Nro_Factura='0'
    """), {"rn": receipt_number, "cid": cid, "on": order_number})
    await db_temp.commit()

    return {
        "ok": True, "receipt_number": receipt_number, "date": fecha, "time": hora,
        "subtotal": subtotal, "discount": discount_amount, "tip": tip_amount,
        "delivery": delivery_amount, "total": grand_total,
    }
