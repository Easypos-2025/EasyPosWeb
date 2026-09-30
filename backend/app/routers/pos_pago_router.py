"""
Registro de Recibo (pantalla de pago) — con pago parcial por ítem.

  - Cada ítem del pedido es una unidad (como el escritorio); el cajero marca los que se
    pagan. Los no marcados quedan en la cuenta abierta; al pagar el último ítem la cuenta
    se cierra y la mesa se libera.
  - TODOS los valores los calcula el servidor: venta, descuento (tipificación sobre los
    ítems marcados, sin descuento sobre descuento), propina (sobre la venta del recibo),
    domicilio y total. Propina y domicilio NO suman en venta.
  - Efectivo puede superar el total: se devuelve el cambio y el recibo queda por el total.
  - Cliente = tabla `clientes` (1 = Consumidor Final).
  - Inventario: se graba pos_receipt_order_detail_products (= recibos_detalle_comanda_producto)
    con los insumos de cada ítem, y se descuenta cantidad_actual (insumo por unidad × cantidad).

Consistencia entre bases: `easyposweb` (recibo permanente) y `datatemppos` (pedido en curso)
son conexiones distintas; se confirma primero el recibo y luego se cierra lo pagado en el
pedido. Ante una falla intermedia el recibo queda registrado y los ítems siguen abiertos.
"""
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Annotated, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db, get_datatemppos_db
from app.auth.dependencies import get_current_user
from app.models.user_model import User
from app.routers.pos_shift_router import require_open_shift
from app.routers.pos_comanda_router import _recalc_total
from app.services import consecutivo_service as cs
from app.services import clientes as clientes_svc
from app.services import comanda_armado as armado_svc

router = APIRouter(prefix="/api/pos/pago", tags=["POS Pago"])

_BOG = timezone(timedelta(hours=-5))
Money = Annotated[float, Field(ge=0, le=2_000_000_000)]


async def _siguiente_id_registro(db: AsyncSession, tabla: str, cid: int) -> int:
    """Secuencia negativa propia de la web en tablas con UNIQUE (id_registro, company_id)
    heredada del escritorio (que usa positivos): nunca chocan."""
    row = (await db.execute(text(
        f"SELECT COALESCE(MIN(id_registro), 0) - 1 AS next FROM {tabla} WHERE company_id = :cid"
    ), {"cid": cid})).mappings().first()
    return int(row["next"])


async def _cargar_cuenta(db_temp: AsyncSession, cid: int, order_number: str):
    orden = (await db_temp.execute(text("""
        SELECT Nro_Pedido, Fecha, Mesa, Hora, Mesero, Valor, Nro_Comenzales, Domicilio, Id_Cliente
        FROM temp_comanda
        WHERE company_id=:cid AND Nro_Pedido=:on AND Nro_Factura='0' AND Cancelado=0
        LIMIT 1
    """), {"cid": cid, "on": order_number})).mappings().first()
    if not orden:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada o ya pagada")
    items = (await db_temp.execute(text("""
        SELECT Id_Plato, Item, Descripcion, Cantidad, Valor, Novedad, Cambios,
               Porc_Descuento_General, Id_Tipificacion, Producto_Personalizado,
               Paga_Impuesto, Impuesto
        FROM temp_detalle_comanda_parcial
        WHERE company_id=:cid AND Nro_pedido=:on AND Nro_Factura='0' AND Mostrar=1
        ORDER BY Item
    """), {"cid": cid, "on": order_number})).mappings().all()
    if not items:
        raise HTTPException(status_code=400, detail="La cuenta no tiene ítems por pagar")
    return orden, items


async def _config(db: AsyncSession, cid: int) -> dict:
    cfg = (await db.execute(text(
        "SELECT COALESCE(has_tip,0) has_tip, COALESCE(tip_percentage,0) tip_percentage, "
        "COALESCE(tip_label,'Propina') tip_label, COALESCE(has_pos_electronico,0) has_pos_electronico "
        "FROM company_configs WHERE company_id=:cid"
    ), {"cid": cid})).mappings().first()
    return {
        "has_tip": bool(cfg and cfg["has_tip"]),
        "tip_percentage": float(cfg["tip_percentage"]) if cfg else 0.0,
        "tip_label": (cfg["tip_label"] if cfg else None) or "Propina",
        "has_pos_electronico": bool(cfg and cfg["has_pos_electronico"]),
    }


# ═══════════════════════════════════════════════════════════════════════════
# GET /api/pos/pago/{order_number} — datos para la pantalla de pago
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
    ids = ",".join(str(d) for d in dish_ids)
    dishes = {int(r["id"]): r for r in (await db.execute(text(
        f"SELECT id, name, COALESCE(tax,0) AS tax FROM pos_dishes WHERE company_id=:cid AND id IN ({ids})"
    ), {"cid": cid})).mappings().all()}
    armado = await armado_svc.armado_names(db_temp, cid, [order_number])

    cfg = await _config(db, cid)
    payment_types = (await db.execute(text(
        "SELECT id, name, is_default, adds_to_cash, select_card, ask_notes, ask_customer "
        "FROM pos_payment_types WHERE company_id=:cid AND is_active=1 ORDER BY is_default DESC, id"
    ), {"cid": cid})).mappings().all()
    waiters = (await db.execute(text(
        "SELECT id, name FROM pos_waiters WHERE company_id=:cid AND status=1 ORDER BY name"
    ), {"cid": cid})).mappings().all()
    tipificaciones = (await db_temp.execute(text("""
        SELECT Id_Tipificacion, Nombre, Valor_Descuento_Porcentaje, Exigir_Info_Cliente
        FROM temp_tipificaciones_descuentos
        WHERE company_id = :cid AND Desactivada = 0 AND Id_Tipificacion <> 0
        ORDER BY Nombre
    """), {"cid": cid})).mappings().all()
    billetes = [int(r[0]) for r in (await db.execute(text(
        "SELECT value FROM pos_cash_denominations WHERE company_id=:cid ORDER BY sort_order, value DESC"
    ), {"cid": cid})).all()]

    customer = await clientes_svc.get_cliente(db, cid, int(orden["Id_Cliente"] or 0) or clientes_svc.CONSUMIDOR_FINAL_ID)
    await db.commit()   # por si se creó el Consumidor Final
    consecutivo_preview = await cs.previsualizar_consecutivo(db, company_id=cid, tipo="recibo")

    out_items = []
    for i in items:
        did, it = int(i["Id_Plato"]), int(i["Item"])
        qty = float(i["Cantidad"] or 0)
        valor = int(i["Valor"] or 0)
        cp = str(i["Producto_Personalizado"] or "")
        name = cp if cp and not cp.startswith("{") else (dishes.get(did, {}).get("name") or f"Plato {did}")
        out_items.append({
            "dish_id": did, "item": it, "name": name,
            "armado": armado.get((order_number, it), []),
            "quantity": qty, "amount": valor,
            "unit_price": round(valor / qty) if qty else valor,
            "typification_id": int(i["Id_Tipificacion"] or 0),
            "original_amount": int(i["Porc_Descuento_General"] or 0) if int(i["Id_Tipificacion"] or 0) else valor,
        })

    return {
        "order": {
            "order_number": orden["Nro_Pedido"], "date": str(orden["Fecha"]),
            "table_name": orden["Mesa"], "guests_count": int(orden["Nro_Comenzales"] or 0),
            "waiter_id": int(orden["Mesero"] or 0),
        },
        "items": out_items,
        "customer": customer,
        "tip": {"enabled": cfg["has_tip"], "percentage": cfg["tip_percentage"], "label": cfg["tip_label"]},
        "has_pos_electronico": cfg["has_pos_electronico"],
        "payment_types": [dict(p) for p in payment_types],
        "waiters": [dict(w) for w in waiters],
        "typifications": [{"id": int(t["Id_Tipificacion"]), "name": t["Nombre"],
                           "percentage": int(t["Valor_Descuento_Porcentaje"] or 0),
                           "ask_notes": bool(t["Exigir_Info_Cliente"])} for t in tipificaciones],
        "cash_denominations": billetes,
        "consecutivo_preview": consecutivo_preview,
        "turno_id": turno["id"],
    }


# ═══════════════════════════════════════════════════════════════════════════
# POST /api/pos/pago/{order_number} — registra el Recibo de los ítems marcados
# ═══════════════════════════════════════════════════════════════════════════
class DescuentoIn(BaseModel):
    typification_id: Annotated[int, Field(ge=1)]
    monto_pesos: Optional[Money] = None          # tipificación "en pesos" (sin %)
    observacion: Optional[Annotated[str, StringConstraints(max_length=250)]] = None


class PagoLinea(BaseModel):
    payment_method_id: Annotated[int, Field(ge=1)]
    amount: Money
    notes: Optional[Annotated[str, StringConstraints(max_length=250)]] = None


class PagoIn(BaseModel):
    items: Annotated[List[Annotated[int, Field(ge=1)]], Field(min_length=1, max_length=500)]
    customer_id: Optional[int] = None
    waiter_id: Optional[int] = None
    descuento: Optional[DescuentoIn] = None
    tip_mode: Literal["auto", "none", "manual"] = "auto"
    tip_amount: Optional[Money] = None
    delivery_amount: Money = 0
    delivery_customer_id: Optional[int] = None
    observacion: Optional[Annotated[str, StringConstraints(max_length=250)]] = None
    payments: Annotated[List[PagoLinea], Field(min_length=1, max_length=10)]


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

    # ── Ítems marcados (deben seguir abiertos en esta cuenta) ────────────────
    por_item = {int(i["Item"]): i for i in items}
    marcados = sorted(set(body.items))
    faltan = [n for n in marcados if n not in por_item]
    if faltan:
        raise HTTPException(status_code=409, detail="Algunos ítems ya fueron pagados o no existen. Recargue la cuenta.")
    sel = [por_item[n] for n in marcados]
    valores = {int(i["Item"]): int(i["Valor"] or 0) for i in sel}
    originales = {int(i["Item"]): (int(i["Porc_Descuento_General"] or 0) if int(i["Id_Tipificacion"] or 0) else int(i["Valor"] or 0)) for i in sel}
    tipif = {int(i["Item"]): int(i["Id_Tipificacion"] or 0) for i in sel}

    # ── Descuento (tipificación) sobre los marcados SIN descuento previo ─────
    if body.descuento:
        t = (await db_temp.execute(text("""
            SELECT Nombre, Valor_Descuento_Porcentaje, Exigir_Info_Cliente
            FROM temp_tipificaciones_descuentos
            WHERE Id_Tipificacion=:tid AND company_id=:cid AND Desactivada=0
        """), {"tid": body.descuento.typification_id, "cid": cid})).mappings().first()
        if not t:
            raise HTTPException(status_code=422, detail="Tipo de descuento no encontrado o inactivo")
        if t["Exigir_Info_Cliente"] and not (body.descuento.observacion or "").strip():
            raise HTTPException(status_code=422, detail=f'"{t["Nombre"]}" requiere una observación')
        elegibles = [n for n in marcados if not tipif[n] and valores[n] > 0]
        if not elegibles:
            raise HTTPException(status_code=422, detail="Los ítems marcados ya tienen descuento (no se permite descuento sobre descuento)")
        pct = int(t["Valor_Descuento_Porcentaje"] or 0)
        if pct > 0:
            for n in elegibles:
                valores[n] = max(0, round(originales[n] * (1 - pct / 100)))
        else:
            monto = int(body.descuento.monto_pesos or 0)
            base_eleg = sum(valores[n] for n in elegibles)
            if monto <= 0 or monto > base_eleg:
                raise HTTPException(status_code=422, detail=f'"{t["Nombre"]}": el valor a descontar debe estar entre 1 y {base_eleg}')
            restante = monto
            for k, n in enumerate(elegibles):          # reparto proporcional; el último absorbe el redondeo
                parte = restante if k == len(elegibles) - 1 else round(monto * valores[n] / base_eleg)
                parte = min(parte, valores[n], restante)
                valores[n] -= parte
                restante -= parte
        for n in elegibles:
            tipif[n] = body.descuento.typification_id

    venta = sum(valores.values())
    descuento_total = sum(originales[n] - valores[n] for n in marcados)

    # ── Propina (sobre la venta del recibo) y domicilio — no suman en venta ──
    cfg = await _config(db, cid)
    if body.tip_mode == "none" or not cfg["has_tip"]:
        tip_amount = 0
    elif body.tip_mode == "manual":
        tip_amount = int(round(body.tip_amount or 0))
    else:
        tip_amount = int(round(venta * cfg["tip_percentage"] / 100))
    delivery_amount = int(round(body.delivery_amount or 0))
    total = venta + tip_amount + delivery_amount

    # ── Formas de pago: deben cubrir el total; solo el efectivo puede exceder ─
    tipos = {int(r["id"]): r for r in (await db.execute(text(
        "SELECT id, name, adds_to_cash FROM pos_payment_types WHERE company_id=:cid AND is_active=1"
    ), {"cid": cid})).mappings().all()}
    if any(p.payment_method_id not in tipos for p in body.payments):
        raise HTTPException(status_code=422, detail="Forma de pago no válida o inactiva")
    pagos = [{"pm": p.payment_method_id, "amount": int(round(p.amount)), "notes": (p.notes or "").strip()}
             for p in body.payments if p.amount > 0]
    pagado = sum(p["amount"] for p in pagos)
    if pagado < total:
        raise HTTPException(status_code=422, detail=f"Falta por pagar ${total - pagado:,}".replace(",", "."))
    cambio = pagado - total
    if cambio:
        efectivo = sum(p["amount"] for p in pagos if tipos[p["pm"]]["adds_to_cash"])
        if cambio > efectivo:
            raise HTTPException(status_code=422, detail="Solo el efectivo puede superar el total (para dar cambio)")
        resto = cambio                                   # el recibo registra lo cobrado, no lo recibido
        for p in reversed(pagos):
            if resto and tipos[p["pm"]]["adds_to_cash"]:
                q = min(resto, p["amount"])
                p["amount"] -= q
                resto -= q
        pagos = [p for p in pagos if p["amount"] > 0]

    customer = await clientes_svc.get_cliente(db, cid, body.customer_id or int(orden["Id_Cliente"] or 0) or 1)
    delivery_customer = customer
    if delivery_amount and body.delivery_customer_id and body.delivery_customer_id != customer["id_cliente"]:
        delivery_customer = await clientes_svc.get_cliente(db, cid, body.delivery_customer_id)
    waiter_id = body.waiter_id or int(orden["Mesero"] or 0)
    if waiter_id:
        ok = (await db.execute(text("SELECT 1 FROM pos_waiters WHERE id=:w AND company_id=:cid"),
                               {"w": waiter_id, "cid": cid})).scalar()
        if not ok:
            raise HTTPException(status_code=422, detail="Vendedor no válido para esta empresa")

    # ── Consecutivo: llave única por recibo = cuenta + huella de ítems pagados ─
    #    (un segundo pago parcial de la misma cuenta es otro recibo; un doble clic
    #     sobre los mismos ítems choca con la misma llave y se rechaza)
    huella = hashlib.sha1(",".join(map(str, marcados)).encode()).hexdigest()[:10]
    receipt_number = str(await cs.generar_consecutivo(
        db, company_id=cid, nro_pedido=f"{order_number}-{huella}", fecha=orden["Fecha"], tipo="recibo",
    ))

    # ── Nro_Pedido en las tablas reales: como el escritorio, un pago parcial lleva
    #    el prefijo "P-P" (identifica el pago parcial y separa el número de cada recibo);
    #    el pedido original queda en la cuenta pendiente y el pago que la cierra lo usa.
    #    Si la cuenta ya tuvo un parcial, se agrega "-2", "-3"... para no repetir.
    pedido_real = order_number
    if len(marcados) < len(items):
        base = f"P-P{order_number}"
        usados = set((await db.execute(text("""
            SELECT order_number FROM pos_receipt_orders
            WHERE company_id=:cid AND (order_number=:b OR order_number LIKE :pref)
        """), {"cid": cid, "b": base, "pref": base + "-%"})).scalars().all())
        pedido_real, k = base, 1
        while pedido_real in usados:
            k += 1
            pedido_real = f"{base}-{k}"

    now = datetime.now(_BOG)
    fecha, hora = now.date().isoformat(), now.strftime("%H:%M:%S")
    is_delivery = 1 if delivery_amount else 0
    armado = await armado_svc.armado_names(db_temp, cid, [order_number])

    await db.execute(text("""
        INSERT INTO pos_receipts
            (receipt_number, date, company_id, cash_amount, discount, employee_id,
             tip, shift, time, time_text, amount_without_tip, customer_id,
             delivery_receipt, voided, synced)
        VALUES (:rn, :fecha, :cid, :total, :disc, :uid, :tip, 1, :hora, :hora, :venta, :cust, :isdel, 0, 0)
    """), {"rn": receipt_number, "fecha": fecha, "cid": cid, "total": total, "disc": descuento_total,
           "uid": uid, "tip": tip_amount, "hora": hora, "venta": venta, "cust": customer["id_cliente"],
           "isdel": is_delivery})

    await db.execute(text("""
        INSERT INTO pos_receipt_orders
            (order_number, date, receipt_number, table_name, time, waiter_id,
             cancelled, amount, notes, guests_count, delivery, customer_id, synced, company_id)
        VALUES (:on, :fecha, :rn, :mesa, :hora, :wid, 0, :total, :obs, :guests, :isdel, :cust, 0, :cid)
    """), {"on": pedido_real, "fecha": fecha, "rn": receipt_number, "mesa": orden["Mesa"], "hora": hora,
           "wid": waiter_id, "total": total, "obs": (body.observacion or "")[:250],
           "guests": int(orden["Nro_Comenzales"] or 0), "isdel": is_delivery,
           "cust": customer["id_cliente"], "cid": cid})

    next_disc = await _siguiente_id_registro(db, "pos_receipt_discounts", cid)
    for it in sel:
        did, n = int(it["Id_Plato"]), int(it["Item"])
        nov_armado = " - ".join(armado.get((order_number, n), []))
        await db.execute(text("""
            INSERT INTO pos_receipt_order_details
                (order_number, date, receipt_number, dish_id, item, quantity, amount, notes,
                 changes, custom_product, pays_tax, tax, original_tax, depends_on, synced, company_id)
            VALUES (:on, :fecha, :rn, :did, :item, :qty, :amount, :notes,
                    :changes, :custom, :ptax, :tax, :tax, 0, 0, :cid)
        """), {"on": pedido_real, "fecha": fecha, "rn": receipt_number, "did": did, "item": n,
               "qty": float(it["Cantidad"] or 0), "amount": valores[n],
               "notes": (nov_armado or it["Novedad"] or "")[:250], "changes": it["Cambios"],
               "custom": it["Producto_Personalizado"], "ptax": int(it["Paga_Impuesto"] or 0),
               "tax": int(it["Impuesto"] or 0), "cid": cid})
        if tipif[n]:
            await db.execute(text("""
                INSERT INTO pos_receipt_discounts
                    (id_registro, company_id, date, receipt_number, dish_id, item, typification_id,
                     original_price, sale_price, discount_amount, order_number, synced)
                VALUES (:idreg, :cid, :fecha, :rn, :did, :item, :tid, :orig, :sale, :damt, :on, 0)
            """), {"idreg": next_disc, "cid": cid, "fecha": fecha, "rn": receipt_number, "did": did,
                   "item": n, "tid": tipif[n], "orig": originales[n], "sale": valores[n],
                   "damt": max(0, originales[n] - valores[n]), "on": pedido_real})
            next_disc -= 1

    # Insumos vendidos (recibos_detalle_comanda_producto): Cantidad es por unidad del plato
    insumos = (await db_temp.execute(text(f"""
        SELECT Id_Plato, Item, Id_Grupo, Id_Item, Cantidad FROM temp_plato_producto_parcial
        WHERE company_id=:cid AND Nro_Pedido=:on AND Nro_Factura='0'
          AND Item IN ({",".join(str(n) for n in marcados)})
    """), {"cid": cid, "on": order_number})).mappings().all()
    qty_item = {int(i["Item"]): float(i["Cantidad"] or 0) for i in sel}
    for ins in insumos:
        await db.execute(text("""
            INSERT INTO pos_receipt_order_detail_products
                (order_number, date, invoice_number, dish_id, item, group_id, item_id, quantity,
                 stock_deducted, synced, company_id)
            VALUES (:on, :fecha, :rn, :did, :item, :gid, :iid, :qty, 1, 0, :cid)
        """), {"on": pedido_real, "fecha": fecha, "rn": receipt_number, "did": int(ins["Id_Plato"]),
               "item": int(ins["Item"]), "gid": int(ins["Id_Grupo"]), "iid": int(ins["Id_Item"]),
               "qty": float(ins["Cantidad"] or 0), "cid": cid})

    for idx, p in enumerate(pagos, start=1):
        await db.execute(text("""
            INSERT INTO pos_receipt_payment_methods
                (item, payment_method_id, card_id, invoice_number, amount, date, order_number, notes, synced, company_id)
            VALUES (:item, :pm, 0, :rn, :amount, :fecha, :on, :notes, 0, :cid)
        """), {"item": idx, "pm": p["pm"], "rn": receipt_number, "amount": p["amount"], "fecha": fecha,
               "on": pedido_real, "notes": p["notes"][:250], "cid": cid})

    if delivery_amount:
        await db.execute(text("""
            INSERT INTO receipt_delivery_fees
                (id_registro, invoice_number, amount, date, order_number, employee_id, customer_id, synced, company_id)
            VALUES (:idreg, :rn, :amount, :fecha, :on, :wid, :cust, 0, :cid)
        """), {"idreg": await _siguiente_id_registro(db, "receipt_delivery_fees", cid), "rn": receipt_number,
               "amount": delivery_amount, "fecha": fecha, "on": pedido_real, "wid": waiter_id or uid,
               "cust": delivery_customer["id_cliente"], "cid": cid})

    await db.execute(text("""
        INSERT INTO pos_cash_register_receipts
            (register_number, closing_id, receipt_number, date, order_number, amount, base_amount,
             employee_id, shift, company_id, synced)
        VALUES (:caja, :closing, :rn, :fecha, :on, :total, :venta, :uid, 1, :cid, 0)
    """), {"caja": int(turno.get("register_number") or 0), "closing": turno["id"], "rn": receipt_number,
           "fecha": fecha, "on": pedido_real, "total": total, "venta": venta, "uid": uid, "cid": cid})

    # ── Confirmar primero lo permanente ──────────────────────────────────────
    await db.commit()

    # ── Inventario: insumo por unidad × cantidad del ítem ────────────────────
    for ins in insumos:
        await db.execute(text("""
            UPDATE inventario_actual_porciones
            SET cantidad_actual = cantidad_actual - :qty, enviada_mysql = 0, updated_at = NOW()
            WHERE company_id = :cid AND id_item = :iid
        """), {"qty": float(ins["Cantidad"] or 0) * qty_item.get(int(ins["Item"]), 1), "cid": cid,
               "iid": int(ins["Id_Item"])})
    await db.commit()

    # ── Cerrar lo pagado en el pedido ─────────────────────────────────────────
    lista = ",".join(str(n) for n in marcados)
    for n in marcados:
        await db_temp.execute(text("""
            UPDATE temp_detalle_comanda_parcial
            SET Nro_Factura=:rn, Valor=:v, Porc_Descuento_Plato=:v,
                Porc_Descuento_General=:orig, Id_Tipificacion=:tid
            WHERE company_id=:cid AND Nro_pedido=:on AND Item=:item AND Nro_Factura='0'
        """), {"rn": receipt_number, "v": valores[n], "orig": originales[n], "tid": tipif[n],
               "cid": cid, "on": order_number, "item": n})
    await db_temp.execute(text(f"""
        UPDATE temp_plato_producto_parcial SET Nro_Factura=:rn
        WHERE company_id=:cid AND Nro_Pedido=:on AND Nro_Factura='0' AND Item IN ({lista})
    """), {"rn": receipt_number, "cid": cid, "on": order_number})

    pendientes = (await db_temp.execute(text("""
        SELECT COUNT(*) FROM temp_detalle_comanda_parcial
        WHERE company_id=:cid AND Nro_pedido=:on AND Nro_Factura='0' AND Mostrar=1
    """), {"cid": cid, "on": order_number})).scalar() or 0
    if pendientes:
        await _recalc_total(db_temp, order_number, cid)
    else:
        await db_temp.execute(text(
            "UPDATE temp_comanda SET Nro_Factura=:rn WHERE company_id=:cid AND Nro_Pedido=:on"
        ), {"rn": receipt_number, "cid": cid, "on": order_number})
        await db_temp.execute(text("""
            UPDATE temp_mesa_abierta SET Abierta=0, Abierta_Desde=NULL, updated_at=NOW()
            WHERE company_id=:cid AND Mesa=:mesa
              AND NOT EXISTS (SELECT 1 FROM temp_comanda tc WHERE tc.company_id=:cid AND tc.Mesa=:mesa
                              AND tc.Nro_Factura='0' AND tc.Cancelado=0)
        """), {"cid": cid, "mesa": orden["Mesa"]})
    await db_temp.commit()

    return {
        "ok": True, "receipt_number": receipt_number, "date": fecha, "time": hora,
        "venta": venta, "discount": descuento_total, "tip": tip_amount, "delivery": delivery_amount,
        "total": total, "change": cambio, "remaining_items": int(pendientes),
    }
