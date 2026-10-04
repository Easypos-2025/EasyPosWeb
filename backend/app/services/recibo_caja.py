"""
Cobros que generan recibo fuera del flujo de Restaurante (Servi-Cars: Órdenes de Servicio y Parking),
con las mismas reglas de caja que Restaurante:

  · Exigen Id_Caja abierto (require_open_shift); el recibo lleva la fecha de apertura del Id_Caja.
  · Número = consecutivo de recibos (consecutivo_service), el mismo de Restaurante.
  · Formas de pago de la empresa y activas; sin formas → EFECTIVO. Deben sumar el total (el total
    lo calcula el servidor).
  · caja_recibos (pos_cash_register_receipts) amarra el recibo al Id_Caja → sale en el Cuadre de Caja.
"""
from datetime import date

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import consecutivo_service as cs
from app.services.formas_pago import es_efectivo_sql


async def preparar_pagos(db: AsyncSession, cid: int, total: int, pagos: list) -> list[dict]:
    """[{payment_method_id, amount, notes}] validados contra la empresa; sin pagos → EFECTIVO por el total."""
    tipos = {int(r["id"]): r for r in (await db.execute(text(
        f"SELECT id, name, is_default, ask_notes, {es_efectivo_sql('pos_payment_types')} AS es_efectivo "
        "FROM pos_payment_types WHERE company_id = :cid AND is_active = 1"
    ), {"cid": cid})).mappings().all()}
    out = []
    for p in pagos or []:
        try:
            pm, amt = int(p.get("payment_method_id")), float(p.get("amount") or 0)
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="Forma de pago no válida")
        if amt < 0 or amt > 2_000_000_000:
            raise HTTPException(status_code=422, detail="Valor de pago no válido")
        if pm not in tipos:
            raise HTTPException(status_code=422, detail="Forma de pago no válida o inactiva")
        notes = str(p.get("notes") or "").strip()[:255]
        if tipos[pm]["ask_notes"] and not notes:
            raise HTTPException(status_code=422, detail=f"La forma de pago {tipos[pm]['name']} exige una observación")
        if amt > 0:
            out.append({"payment_method_id": pm, "amount": int(round(amt)), "notes": notes})
    if not out:
        ef = next((t for t in tipos.values() if t["es_efectivo"]), None) or next((t for t in tipos.values() if t["is_default"]), None)
        if not ef:
            raise HTTPException(status_code=422, detail="La empresa no tiene la forma de pago EFECTIVO activa")
        out = [{"payment_method_id": int(ef["id"]), "amount": int(total), "notes": ""}]
    pagado = sum(p["amount"] for p in out)
    if abs(pagado - int(total)) > 1:      # tolerancia $1 por redondeo
        raise HTTPException(status_code=422, detail=f"La suma de pagos (${pagado:,}) no coincide con el total (${int(total):,})".replace(",", "."))
    return out


async def consecutivo_recibo(db: AsyncSession, cid: int, clave: str, fecha: str) -> str:
    """Número de recibo del consecutivo (una clave repetida = doble cobro → 409).
    Si la empresa ya tiene recibos numerados por fuera del consecutivo (antes se usaba MAX + 1),
    el consecutivo arranca después del mayor: se deja una sola fila de ajuste con ese número."""
    mayor = int((await db.execute(text(
        "SELECT COALESCE(MAX(CAST(receipt_number AS UNSIGNED)), 0) FROM pos_receipts WHERE company_id = :cid"
    ), {"cid": cid})).scalar() or 0)
    if mayor >= await cs.previsualizar_consecutivo(db, cid, "recibo"):
        await db.execute(text("""
            INSERT IGNORE INTO consecutivo_factura_manual (company_id, Id_Consecutivo, Nro_Pedido, Fecha, Enviada_MySql, updated_at)
            VALUES (:cid, :n, :np, :f, 1, NOW())
        """), {"cid": cid, "n": mayor, "np": f"AJUSTE-RECIBOS-{mayor}", "f": fecha})
        await db.commit()
    return str(await cs.generar_consecutivo(db, company_id=cid, nro_pedido=clave[:50],
                                            fecha=date.fromisoformat(fecha), tipo="recibo"))


async def amarrar_a_caja(db: AsyncSession, cid: int, turno: dict, receipt_number: str, fecha: str,
                         order_number: str, total: int, base: int, uid: int) -> None:
    """caja_recibos: el recibo queda en el Id_Caja (y su caja)."""
    await db.execute(text("""
        INSERT INTO pos_cash_register_receipts
            (register_number, closing_id, receipt_number, date, order_number, amount, base_amount,
             employee_id, shift, company_id, synced)
        VALUES (:caja, :closing, :rn, :fecha, :on, :total, :base, :uid, 1, :cid, 0)
    """), {"caja": int(turno.get("register_number") or 0), "closing": turno["id"], "rn": receipt_number,
           "fecha": fecha, "on": order_number, "total": int(total), "base": int(base), "uid": uid, "cid": cid})


async def guardar_pagos_recibo(db: AsyncSession, cid: int, receipt_number: str, fecha: str,
                               order_number: str, pagos: list[dict]) -> None:
    for idx, p in enumerate(pagos, start=1):
        await db.execute(text("""
            INSERT INTO pos_receipt_payment_methods
                (item, payment_method_id, card_id, invoice_number, amount, date, order_number, notes, synced, company_id)
            VALUES (:item, :pm, 0, :rn, :amount, :fecha, :orden, :notes, 0, :cid)
        """), {"item": idx, "pm": p["payment_method_id"], "rn": receipt_number, "amount": p["amount"],
               "fecha": fecha, "orden": order_number, "notes": p["notes"], "cid": cid})


async def exigir_reimpresion(db: AsyncSession, user, cid: int, receipt_number: str) -> bool:
    """Control de Acceso "Reimprimir Facturas" (sin límite de tiempo): la primera impresión de un
    recibo es libre; si ya se imprimió (contador web o recibo subido del escritorio, que lo imprimió
    allá) exige el permiso. Devuelve True si el recibo existe (para contar la impresión)."""
    from app.services import permisos
    r = (await db.execute(text(
        "SELECT COALESCE(print_count, 0) n, COALESCE(synced, 0) s FROM pos_receipts "
        "WHERE company_id = :cid AND receipt_number = :rn LIMIT 1"
    ), {"cid": cid, "rn": str(receipt_number)})).mappings().first()
    if not r:
        return False
    if int(r["n"]) >= 1 or int(r["s"]) == 1:
        permisos.exigir(await permisos.permisos_usuario(db, user), "reimprimir_facturas",
                        "Este recibo ya se imprimió: su rol no tiene permiso para reimprimir")
    return True


async def contar_impresion(db: AsyncSession, cid: int, receipt_number: str) -> None:
    await db.execute(text(
        "UPDATE pos_receipts SET print_count = COALESCE(print_count, 0) + 1 WHERE company_id = :cid AND receipt_number = :rn"
    ), {"cid": cid, "rn": str(receipt_number)})
    await db.commit()
