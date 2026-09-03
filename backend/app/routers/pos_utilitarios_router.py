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
    SELECT CONVERT(Nro_Pedido  USING utf8mb4) COLLATE utf8mb4_general_ci FROM temp_comanda
     WHERE company_id = :cid AND Cancelado = 1
    UNION
    SELECT CONVERT(Nro_Pedido  USING utf8mb4) COLLATE utf8mb4_general_ci FROM easyposweb.historico_comandas_eliminadas
     WHERE company_id = :cid
    UNION
    SELECT CONVERT(order_number USING utf8mb4) COLLATE utf8mb4_general_ci FROM easyposweb.pos_orders
     WHERE company_id = :cid
    UNION
    SELECT CONVERT(order_number USING utf8mb4) COLLATE utf8mb4_general_ci FROM easyposweb.pos_receipt_orders
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
#
# Dos pasadas de limpieza, ambas acotadas a company_id:
#   1) Pedidos "ya resueltos" en el mundo facturado (Cancelado=1,
#      archivado, ya facturado en pos_orders/pos_receipt_orders).
#      El set de huérfanos se calcula UNA sola vez y se reutiliza
#      para archivar + los 4 DELETE (antes se recalculaba 5 veces).
#   2) Huérfanos por integridad referencial dentro de datatemppos
#      (tablas chicas, sin tocar pos_orders/pos_receipt_orders):
#        - hijo sin padre → se borra siempre, sin importar antigüedad
#        - temp_comanda sin ítems → solo si Salio=1 (ya se confirmó
#          y envió a cocina; Salio=0 = mesa recién abierta, no tocar)
# ═══════════════════════════════════════════════════════════════
@router.post("/cleanup-temp")
async def cleanup_temp(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    user = await _get_admin_user(authorization, db)
    cid = user.company_id

    result_tables = {t["name"]: 0 for t in TEMP_TABLES}

    # ── Pasada 1: pedidos ya resueltos (facturados/cancelados/archivados) ──
    try:
        orphan_rows = (await db_temp.execute(text(f"""
            SELECT DISTINCT Nro_Pedido FROM temp_comanda
            WHERE company_id = :cid
              AND Nro_Pedido IN ({ORPHAN_SUBQUERY})
        """), {"cid": cid})).fetchall()
        orphan_ids = [r[0] for r in orphan_rows]
    except Exception:
        orphan_ids = []

    if orphan_ids:
        try:
            await archive_commands_to_history(db_temp, db, cid, orphan_ids, "manual_cleanup")
        except Exception:
            pass  # Archivado best-effort; la limpieza continúa igual

        ph = ",".join(f":oid_{i}" for i in range(len(orphan_ids)))
        params: dict = {"cid": cid}
        params.update({f"oid_{i}": v for i, v in enumerate(orphan_ids)})
        for t in TEMP_TABLES:
            r = await db_temp.execute(text(f"""
                DELETE FROM {t['name']}
                WHERE company_id = :cid AND {t['col']} IN ({ph})
            """), params)
            result_tables[t["name"]] += r.rowcount

    # ── Pasada 2: huérfanos por integridad referencial (dentro de datatemppos) ──

    # 2a. Detalle sin cabecera padre en temp_comanda
    r = await db_temp.execute(text("""
        DELETE d FROM temp_detalle_comanda_parcial d
        LEFT JOIN temp_comanda tc
               ON tc.company_id = d.company_id
              AND tc.Nro_Pedido = d.Nro_pedido
              AND tc.Fecha      = d.Fecha
        WHERE d.company_id = :cid AND tc.company_id IS NULL
    """), {"cid": cid})
    result_tables["temp_detalle_comanda_parcial"] += r.rowcount

    # 2b. Novedades sin cabecera padre en temp_comanda
    r = await db_temp.execute(text("""
        DELETE n FROM temp_novedades_plato_pedido n
        LEFT JOIN temp_comanda tc
               ON tc.company_id = n.company_id
              AND tc.Nro_Pedido = n.Nro_Pedido
        WHERE n.company_id = :cid AND tc.company_id IS NULL
    """), {"cid": cid})
    result_tables["temp_novedades_plato_pedido"] += r.rowcount

    # 2c. Armado/modificadores sin ítem padre en temp_detalle_comanda_parcial
    #     (se ejecuta después de 2a para atrapar también los que quedaron
    #      huérfanos por la limpieza de detalle sin cabecera).
    r = await db_temp.execute(text("""
        DELETE p FROM temp_plato_producto_parcial p
        LEFT JOIN temp_detalle_comanda_parcial d
               ON d.company_id = p.company_id
              AND d.Nro_pedido = p.Nro_Pedido
              AND d.Fecha      = p.Fecha
              AND d.Id_Plato   = p.Id_Plato
              AND d.Item       = p.Item
        WHERE p.company_id = :cid AND d.company_id IS NULL
    """), {"cid": cid})
    result_tables["temp_plato_producto_parcial"] += r.rowcount

    # 2d. Cabeceras confirmadas (Salio=1) que se quedaron sin ítems
    empty_rows = (await db_temp.execute(text("""
        SELECT tc.Nro_Pedido FROM temp_comanda tc
        LEFT JOIN temp_detalle_comanda_parcial d
               ON d.company_id = tc.company_id
              AND d.Nro_pedido = tc.Nro_Pedido
              AND d.Fecha      = tc.Fecha
        WHERE tc.company_id = :cid AND tc.Salio = 1 AND d.company_id IS NULL
    """), {"cid": cid})).fetchall()
    empty_ids = [r[0] for r in empty_rows]
    if empty_ids:
        try:
            await archive_commands_to_history(db_temp, db, cid, empty_ids, "manual_cleanup_empty")
        except Exception:
            pass
        ph2 = ",".join(f":eid_{i}" for i in range(len(empty_ids)))
        params2: dict = {"cid": cid}
        params2.update({f"eid_{i}": v for i, v in enumerate(empty_ids)})
        r = await db_temp.execute(text(f"""
            DELETE FROM temp_comanda
            WHERE company_id = :cid AND Nro_Pedido IN ({ph2})
        """), params2)
        result_tables["temp_comanda"] += r.rowcount

    await db_temp.commit()

    result_list = [
        {"name": t["name"], "label": t["label"], "deleted": result_tables[t["name"]]}
        for t in TEMP_TABLES
    ]
    total_headers = result_tables["temp_comanda"]
    total_details = sum(v for k, v in result_tables.items() if k != "temp_comanda")

    return {
        "deleted_headers": total_headers,
        "deleted_details": total_details,
        "tables": result_list,
    }


# ═══════════════════════════════════════════════════════════════
# GET /api/pos/utilitarios/command-history
# Facturas/Recibos del período con sus ítems COMANDADOS archivados.
# Patrón idéntico a pos_consultas_router:
#   Facturas : pos_invoices JOIN pos_orders  → order_number, mesa, mesero
#   Recibos  : pos_receipts JOIN pos_receipt_orders → order_number, mesa, mesero
#   Detalle  : order_command_history_items WHERE Nro_Pedido = order_number
# ═══════════════════════════════════════════════════════════════
@router.get("/command-history")
async def command_history(
    desde: str = Query(..., description="YYYY-MM-DD"),
    hasta: str = Query(..., description="YYYY-MM-DD"),
    tipo:  str = Query("ambos", description="ambos|factura|recibo"),
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_admin_user(authorization, db)
    cid = user.company_id

    rows: list = []

    if tipo in ("factura", "ambos"):
        fact_rows = (await db.execute(text("""
            SELECT
                i.invoice_number                                    AS numero,
                i.date,
                i.time                                              AS hora,
                COALESCE(o.table_name, '')                          AS mesa,
                COALESCE(w.name, '')                                AS mesero,
                COALESCE(o.order_number, '')                        AS order_number,
                COALESCE(i.cash_amount,0)+COALESCE(i.credit_card_amount,0)
                  +COALESCE(i.debit_card_amount,0)+COALESCE(i.adjustment,0)
                  -COALESCE(i.discount,0)                          AS valor,
                'factura'                                           AS tipo
            FROM pos_invoices i
            LEFT JOIN pos_orders o
                   ON o.invoice_number = i.invoice_number
                  AND o.company_id     = i.company_id
                  AND o.date           = i.date
                  AND o.delivery       = 0
            LEFT JOIN pos_waiters w
                   ON w.id = o.waiter_id AND w.company_id = i.company_id
            WHERE i.company_id = :cid
              AND i.date BETWEEN :desde AND :hasta
              AND i.voided = 0
            ORDER BY i.invoice_number DESC
            LIMIT 500
        """), {"cid": cid, "desde": desde, "hasta": hasta})).mappings().all()
        rows.extend([dict(r) for r in fact_rows])

    if tipo in ("recibo", "ambos"):
        rec_rows = (await db.execute(text("""
            SELECT
                rc.receipt_number                                   AS numero,
                rc.date,
                rc.time                                             AS hora,
                COALESCE(ro.table_name, '')                         AS mesa,
                COALESCE(w.name, '')                                AS mesero,
                COALESCE(ro.order_number, '')                       AS order_number,
                COALESCE(rc.cash_amount,0)+COALESCE(rc.credit_card_amount,0)
                  +COALESCE(rc.debit_card_amount,0)+COALESCE(rc.adjustment,0)
                  -COALESCE(rc.discount,0)                         AS valor,
                'recibo'                                            AS tipo
            FROM pos_receipts rc
            LEFT JOIN pos_receipt_orders ro
                   ON ro.receipt_number = rc.receipt_number
                  AND ro.company_id     = rc.company_id
                  AND ro.date           = rc.date
            LEFT JOIN pos_waiters w
                   ON w.id = ro.waiter_id AND w.company_id = rc.company_id
            WHERE rc.company_id = :cid
              AND rc.date BETWEEN :desde AND :hasta
              AND rc.voided = 0
            ORDER BY rc.receipt_number DESC
            LIMIT 500
        """), {"cid": cid, "desde": desde, "hasta": hasta})).mappings().all()
        rows.extend([dict(r) for r in rec_rows])

    if not rows:
        return {"ventas": []}

    rows.sort(key=lambda x: (str(x["date"]), str(x["hora"])), reverse=True)
    rows = rows[:500]

    # Separar números por tipo para las consultas de ítems
    fact_nums   = [r["numero"]       for r in rows if r["tipo"] == "factura"]
    rec_nums    = [r["numero"]       for r in rows if r["tipo"] == "recibo"]
    order_nums  = [r["order_number"] for r in rows if r.get("order_number")]

    inv_items_by_num:  dict = {}
    rec_items_by_num:  dict = {}
    cmd_by_order:      dict = {}

    # Ítems facturados (pos_order_details por invoice_number)
    if fact_nums:
        phf = ",".join(f":fn_{i}" for i in range(len(fact_nums)))
        pf: dict = {"cid": cid}
        pf.update({f"fn_{i}": v for i, v in enumerate(fact_nums)})
        inv_rows = (await db.execute(text(f"""
            SELECT od.invoice_number AS numero,
                   COALESCE(d.name, od.dish_id) AS dish_name,
                   od.dish_id, od.item, od.quantity,
                   COALESCE(od.amount, 0) AS valor, od.notes
            FROM pos_order_details od
            LEFT JOIN pos_dishes d ON d.id = od.dish_id AND d.company_id = :cid
            WHERE od.company_id = :cid AND od.invoice_number IN ({phf})
            ORDER BY od.invoice_number, od.item
        """), pf)).mappings().all()
        for it in inv_rows:
            inv_items_by_num.setdefault(it["numero"], []).append(dict(it))

    # Ítems facturados (pos_receipt_order_details por receipt_number)
    if rec_nums:
        phr = ",".join(f":rn_{i}" for i in range(len(rec_nums)))
        pr: dict = {"cid": cid}
        pr.update({f"rn_{i}": v for i, v in enumerate(rec_nums)})
        rec_det_rows = (await db.execute(text(f"""
            SELECT rod.receipt_number AS numero,
                   COALESCE(d.name, rod.dish_id) AS dish_name,
                   rod.dish_id, rod.item, rod.quantity,
                   COALESCE(rod.amount, 0) AS valor, rod.notes
            FROM pos_receipt_order_details rod
            LEFT JOIN pos_dishes d ON d.id = rod.dish_id AND d.company_id = :cid
            WHERE rod.company_id = :cid AND rod.receipt_number IN ({phr})
            ORDER BY rod.receipt_number, rod.item
        """), pr)).mappings().all()
        for it in rec_det_rows:
            rec_items_by_num.setdefault(it["numero"], []).append(dict(it))

    # Ítems comandados archivados (order_command_history_items por order_number)
    if order_nums:
        pho = ",".join(f":np_{i}" for i in range(len(order_nums)))
        po: dict = {"cid": cid}
        po.update({f"np_{i}": v for i, v in enumerate(order_nums)})
        cmd_rows = (await db.execute(text(f"""
            SELECT chi.Nro_Pedido,
                   COALESCE(d.name, chi.Id_Plato) AS dish_name,
                   chi.Id_Plato, chi.Item, chi.Cantidad, chi.Valor,
                   chi.Novedad, chi.Cambios, chi.Hora_Plato
            FROM order_command_history_items chi
            LEFT JOIN pos_dishes d ON d.id = chi.Id_Plato AND d.company_id = :cid
            WHERE chi.company_id = :cid
              AND chi.Nro_Pedido IN ({pho})
              AND chi.Mostrar = 1
            ORDER BY chi.Nro_Pedido, chi.Item
        """), po)).mappings().all()
        for it in cmd_rows:
            cmd_by_order.setdefault(it["Nro_Pedido"], []).append(dict(it))

    ventas = []
    for r in rows:
        np  = r.get("order_number", "")
        num = r["numero"]
        inv_items = inv_items_by_num.get(num, []) if r["tipo"] == "factura" else rec_items_by_num.get(num, [])
        ventas.append({
            "numero":          num,
            "date":            str(r["date"]),
            "hora":            str(r["hora"]),
            "mesa":            r["mesa"],
            "mesero":          r["mesero"],
            "order_number":    np,
            "valor":           float(r["valor"] or 0),
            "tipo":            r["tipo"],
            "invoiced_items":  inv_items,
            "commanded_items": cmd_by_order.get(np, []),
        })

    return {"ventas": ventas}
