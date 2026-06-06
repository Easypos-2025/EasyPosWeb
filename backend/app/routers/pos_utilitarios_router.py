from fastapi import APIRouter, Header, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from typing import Optional

from app.database import get_db, get_datatemppos_db
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.user_model import User
from app.utils.pos_archive import archive_commands_to_history

router = APIRouter(prefix="/api/pos/utilitarios", tags=["POS Utilitarios"])

# Tablas temp_ involucradas en la limpieza (orden: detalles primero, cabecera al final)
TEMP_TABLES = [
    {"name": "temp_detalle_comanda_parcial", "col": "Nro_pedido",  "label": "Detalle ítems"},
    {"name": "temp_plato_producto_parcial",  "col": "Nro_Pedido",  "label": "Platos / Productos"},
    {"name": "temp_novedades_plato_pedido",  "col": "Nro_Pedido",  "label": "Novedades de plato"},
    {"name": "temp_comanda",                 "col": "Nro_Pedido",  "label": "Cabeceras de pedido"},
]

ORPHAN_SUBQUERY = """
    SELECT Nro_Pedido FROM temp_comanda
     WHERE company_id = :cid AND Cancelado = 1
    UNION
    SELECT Nro_Pedido FROM easyposweb.historico_comandas_eliminadas
     WHERE company_id = :cid
    UNION
    SELECT order_number FROM easyposweb.pos_orders
     WHERE company_id = :cid
    UNION
    SELECT order_number FROM easyposweb.pos_receipt_orders
     WHERE company_id = :cid
"""


async def _get_admin_user(authorization: str, db: AsyncSession) -> User:
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
    if user.role and not user.role.is_system:
        if "ADMIN" not in (user.role.name or "").upper():
            raise HTTPException(status_code=403, detail="Requiere rol ADMIN")
    return user


# ═══════════════════════════════════════════════════════════════
# GET /api/pos/utilitarios/temp-status
# ═══════════════════════════════════════════════════════════════
@router.get("/temp-status")
async def temp_status(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    user = await _get_admin_user(authorization, db)
    cid = user.company_id

    tables = []
    for t in TEMP_TABLES:
        row = (await db_temp.execute(
            text(f"SELECT COUNT(*) AS cnt FROM {t['name']} WHERE company_id = :cid"),
            {"cid": cid}
        )).mappings().first()
        tables.append({
            "name":    t["name"],
            "label":   t["label"],
            "records": int(row["cnt"] or 0),
        })
    return {"tables": tables}


# ═══════════════════════════════════════════════════════════════
# POST /api/pos/utilitarios/cleanup-temp
# ═══════════════════════════════════════════════════════════════
@router.post("/cleanup-temp")
async def cleanup_temp(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    user = await _get_admin_user(authorization, db)
    cid = user.company_id

    # Identificar huérfanos antes de borrar para archivar
    try:
        orphan_rows = (await db_temp.execute(text(f"""
            SELECT DISTINCT Nro_Pedido FROM temp_comanda
            WHERE company_id = :cid
              AND Nro_Pedido IN ({ORPHAN_SUBQUERY})
        """), {"cid": cid})).fetchall()
        orphan_ids = [r[0] for r in orphan_rows]
        if orphan_ids:
            await archive_commands_to_history(db_temp, db, cid, orphan_ids, "manual_cleanup")
    except Exception:
        pass  # Archivado best-effort; la limpieza continúa igual

    result_tables = []
    for t in TEMP_TABLES:
        if t["name"] == "temp_comanda":
            r = await db_temp.execute(text(f"""
                DELETE FROM temp_comanda
                WHERE company_id = :cid
                  AND Nro_Pedido IN ({ORPHAN_SUBQUERY})
            """), {"cid": cid})
        else:
            r = await db_temp.execute(text(f"""
                DELETE FROM {t['name']}
                WHERE company_id = :cid
                  AND {t['col']} IN ({ORPHAN_SUBQUERY})
            """), {"cid": cid})
        result_tables.append({
            "name":    t["name"],
            "label":   t["label"],
            "deleted": r.rowcount,
        })

    await db_temp.commit()

    total_headers = next((x["deleted"] for x in result_tables if x["name"] == "temp_comanda"), 0)
    total_details = sum(x["deleted"] for x in result_tables if x["name"] != "temp_comanda")

    return {
        "deleted_headers": total_headers,
        "deleted_details": total_details,
        "tables": result_tables,
    }


# ═══════════════════════════════════════════════════════════════
# GET /api/pos/utilitarios/command-history
# Retorna historial de comandas archivadas para una fecha,
# con comparación contra factura/recibo correspondiente.
# ═══════════════════════════════════════════════════════════════
@router.get("/command-history")
async def command_history(
    fecha: str = Query(..., description="YYYY-MM-DD"),
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_admin_user(authorization, db)
    cid = user.company_id

    # 1. Cabeceras archivadas del día
    headers = (await db.execute(text("""
        SELECT Nro_Pedido, Mesa, Hora, Mesero, Valor, Cancelado,
               Movil, archive_reason, archived_at
        FROM order_command_history
        WHERE company_id = :cid AND Fecha = :fecha
        ORDER BY archived_at DESC
    """), {"cid": cid, "fecha": fecha})).mappings().all()

    if not headers:
        return {"orders": []}

    nro_pedidos = [h["Nro_Pedido"] for h in headers]
    ph = ",".join(f":np_{i}" for i in range(len(nro_pedidos)))
    id_params = {"cid": cid}
    id_params.update({f"np_{i}": v for i, v in enumerate(nro_pedidos)})

    # 2. Ítems archivados
    items_rows = (await db.execute(text(f"""
        SELECT Nro_Pedido, Id_Plato, Item, Cantidad, Valor, Novedad, Cambios, Hora_Plato, Mostrar
        FROM order_command_history_items
        WHERE company_id = :cid AND Nro_Pedido IN ({ph})
        ORDER BY Nro_Pedido, Item
    """), id_params)).mappings().all()

    items_by_order: dict = {}
    for it in items_rows:
        items_by_order.setdefault(it["Nro_Pedido"], []).append(dict(it))

    # 3. Facturas DIAN (pos_orders + pos_invoice_details)
    invoice_rows = (await db.execute(text(f"""
        SELECT order_number, invoice_number, amount, time
        FROM pos_orders
        WHERE company_id = :cid AND order_number IN ({ph})
    """), id_params)).mappings().all()
    invoices_by_order = {r["order_number"]: dict(r) for r in invoice_rows}

    inv_detail_rows = (await db.execute(text(f"""
        SELECT order_number, dish_id, item, quantity, dish_amount AS amount, notes, complimentary
        FROM pos_invoice_details
        WHERE company_id = :cid AND order_number IN ({ph})
        ORDER BY order_number, item
    """), id_params)).mappings().all()
    inv_details_by_order: dict = {}
    for d in inv_detail_rows:
        inv_details_by_order.setdefault(d["order_number"], []).append(dict(d))

    # 4. Recibos (pos_receipt_orders + pos_order_details)
    receipt_rows = (await db.execute(text(f"""
        SELECT order_number, receipt_number, amount, time
        FROM pos_receipt_orders
        WHERE company_id = :cid AND order_number IN ({ph})
    """), id_params)).mappings().all()
    receipts_by_order = {r["order_number"]: dict(r) for r in receipt_rows}

    rec_detail_rows = (await db.execute(text(f"""
        SELECT order_number, dish_id, item, quantity, amount, notes, complimentary
        FROM pos_order_details
        WHERE company_id = :cid AND order_number IN ({ph})
        ORDER BY order_number, item
    """), id_params)).mappings().all()
    rec_details_by_order: dict = {}
    for d in rec_detail_rows:
        rec_details_by_order.setdefault(d["order_number"], []).append(dict(d))

    # 5. Info de eliminación
    del_rows = (await db.execute(text(f"""
        SELECT Nro_Pedido, Quien_Elimino, Motivo_Eliminacion, Fecha
        FROM historico_comandas_eliminadas
        WHERE company_id = :cid AND Nro_Pedido IN ({ph})
    """), id_params)).mappings().all()
    deletions_by_order = {r["Nro_Pedido"]: dict(r) for r in del_rows}

    # 6. Nombres de meseros
    waiter_rows = (await db.execute(text(
        "SELECT id, full_name FROM pos_users WHERE company_id = :cid"
    ), {"cid": cid})).mappings().all()
    waiter_names = {str(r["id"]): r["full_name"] for r in waiter_rows}

    # 7. Ensamblar respuesta
    orders = []
    for h in headers:
        np = h["Nro_Pedido"]
        invoice = invoices_by_order.get(np)
        receipt = receipts_by_order.get(np)

        if invoice:
            invoice_info = {
                "type":           "dian",
                "number":         invoice["invoice_number"],
                "amount":         float(invoice["amount"] or 0),
                "time":           str(invoice["time"] or ""),
                "items":          inv_details_by_order.get(np, []),
            }
        elif receipt:
            invoice_info = {
                "type":           "receipt",
                "number":         receipt["receipt_number"],
                "amount":         float(receipt["amount"] or 0),
                "time":           str(receipt["time"] or ""),
                "items":          rec_details_by_order.get(np, []),
            }
        else:
            invoice_info = None

        deletion = deletions_by_order.get(np)
        mesero_id = str(h["Mesero"] or "")

        orders.append({
            "order_number":   np,
            "Mesa":           str(h["Mesa"]   or ""),
            "Hora":           str(h["Hora"]   or ""),
            "Mesero":         waiter_names.get(mesero_id, mesero_id),
            "Valor":          float(h["Valor"] or 0),
            "Cancelado":      int(h["Cancelado"] or 0),
            "Movil":          int(h["Movil"]    or 0),
            "archive_reason": h["archive_reason"],
            "archived_at":    str(h["archived_at"] or ""),
            "commanded_items": items_by_order.get(np, []),
            "invoice":         invoice_info,
            "deletion":        {
                "quien":  deletion["Quien_Elimino"]       if deletion else None,
                "motivo": deletion["Motivo_Eliminacion"]  if deletion else None,
            } if deletion else None,
        })

    return {"orders": orders}
