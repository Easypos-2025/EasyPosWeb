from datetime import date as date_type, datetime, timedelta
from collections import defaultdict
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


# ── helpers ────────────────────────────────────────────────────────────────────

async def _stock_move(
    db: AsyncSession, company_id: int, id_item: int,
    qty: float, mtype: str, ref_type: str, ref_id: Optional[int],
    mdate: Optional[str], notes: Optional[str] = None, user_id: int = None,
):
    si = (await db.execute(text("""
        SELECT id, stock_qty, control_stock
        FROM supply_items WHERE company_id=:cid AND id_item=:item LIMIT 1
    """), {"cid": company_id, "item": id_item})).mappings().first()

    if not si or not si["control_stock"]:
        return

    old_qty = float(si["stock_qty"] or 0)
    new_qty = qty if mtype in ("physical", "physical_snapshot") else old_qty + qty

    await db.execute(text("""
        INSERT INTO stock_movements
            (company_id, supply_item_id, movement_type, qty, qty_before, qty_after,
             reference_type, reference_id, movement_date, notes, created_by)
        VALUES
            (:cid, :sid, :mtype, :dq, :qb, :qa, :rtype, :rid, :mdate, :notes, :uid)
    """), {
        "cid": company_id, "sid": si["id"], "mtype": mtype,
        "dq": (new_qty - old_qty) if mtype in ("physical", "physical_snapshot") else qty,
        "qb": old_qty, "qa": new_qty,
        "rtype": ref_type, "rid": ref_id, "mdate": mdate,
        "notes": notes, "uid": user_id,
    })

    if mtype != "physical_snapshot":
        await db.execute(text(
            "UPDATE supply_items SET stock_qty=:q WHERE id=:id"
        ), {"q": new_qty, "id": si["id"]})


# ═══════════════════════════════════════════════════════════════════════════════
# STOCK — vista general de insumos con stock actual
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/categories")
async def list_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Categorías de insumos — provienen de pos_product_categories (sincronizadas desde VB6
    via SincronizarCategoriaProductos → /sync/push/product-categories).
    supply_items.agrupar = pos_product_categories.id
    """
    rows = (await db.execute(text("""
        SELECT id, name, is_active
        FROM pos_product_categories
        WHERE company_id = :cid AND is_active = 1
        ORDER BY name
    """), {"cid": current_user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.get("/stock")
async def get_stock(
    search:      Optional[str] = Query(None),
    active:      Optional[str] = Query("1"),   # "1"=activos "0"=inactivos "all"=todos
    critical:    Optional[int] = Query(0),     # 1 = solo los críticos (stock calculado ≤ min)
    category_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stock calculado dinámicamente:
      stock = último inventario físico (inventory_physical)
            + entradas desde esa fecha (inventory_entries)
            − salidas desde esa fecha (inventory_exits)
    Funciona con datos sincronizados desde VB6 (no depende de supply_items.stock_qty).
    """
    cid = current_user.company_id
    where_parts = ["si.company_id = :cid"]
    params: dict = {"cid": cid}

    if active == "1":
        where_parts.append("si.is_active = 1")
    elif active == "0":
        where_parts.append("si.is_active = 0")

    if search and search.strip():
        where_parts.append("(si.description LIKE :search OR si.code LIKE :search)")
        params["search"] = f"%{search.strip()}%"

    if category_id:
        where_parts.append("si.agrupar = :cat_id")
        params["cat_id"] = category_id

    where_sql = " AND ".join(where_parts)

    # ── fórmula completa: físico + entradas - salidas - ventas_VB6 ──────────────
    STOCK_EXPR = (
        "COALESCE(lp.cantidad,0) + COALESCE(ea.total,0) - COALESCE(xa.total,0)"
        " - COALESCE(rs.total,0) - COALESCE(inv.total,0)"
    )

    critical_clause = ""
    if critical:
        critical_clause = f"""
            AND si.control_stock = 1 AND si.min_stock > 0
            AND ({STOCK_EXPR}) <= si.min_stock
        """

    rows = (await db.execute(text(f"""
        WITH ranked_phys AS (
            SELECT id_item, cantidad, fecha,
                   ROW_NUMBER() OVER (PARTITION BY id_item ORDER BY fecha DESC, created_at DESC) AS rn
            FROM inventory_physical WHERE company_id = :cid
        ),
        last_phys AS (
            SELECT id_item, cantidad, fecha FROM ranked_phys WHERE rn = 1
        ),
        entries_adj AS (
            SELECT ie.id_item, SUM(ie.cantidad) AS total
            FROM inventory_entries ie
            LEFT JOIN last_phys lp ON lp.id_item = ie.id_item
            WHERE ie.company_id = :cid
              AND (lp.fecha IS NULL OR ie.fecha >= lp.fecha)
            GROUP BY ie.id_item
        ),
        exits_adj AS (
            SELECT ix.id_item, SUM(ix.cantidad) AS total
            FROM inventory_exits ix
            LEFT JOIN last_phys lp ON lp.id_item = ix.id_item
            WHERE ix.company_id = :cid
              AND (lp.fecha IS NULL OR ix.fecha >= lp.fecha)
            GROUP BY ix.id_item
        ),
        receipt_sales AS (
            SELECT prd.item_id, SUM(prd.quantity) AS total
            FROM pos_receipt_order_detail_products prd
            LEFT JOIN last_phys lp ON lp.id_item = prd.item_id
            LEFT JOIN pos_receipts pr
                   ON pr.receipt_number = prd.invoice_number AND pr.company_id = prd.company_id
            WHERE prd.company_id = :cid
              AND (lp.fecha IS NULL OR prd.date >= lp.fecha)
              AND (pr.voided IS NULL OR pr.voided = 0)
            GROUP BY prd.item_id
        ),
        invoice_sales AS (
            SELECT pod.item_id, SUM(pod.quantity) AS total
            FROM pos_order_detail_products pod
            LEFT JOIN last_phys lp ON lp.id_item = pod.item_id
            LEFT JOIN pos_invoices pi
                   ON pi.invoice_number = pod.invoice_number AND pi.company_id = pod.company_id
            WHERE pod.company_id = :cid
              AND (lp.fecha IS NULL OR pod.date >= lp.fecha)
              AND (pi.voided IS NULL OR pi.voided = 0)
            GROUP BY pod.item_id
        )
        SELECT si.id, si.id_item, si.code, si.description,
               {STOCK_EXPR} AS stock_qty,
               si.min_stock, si.control_stock, si.is_active, si.agrupar AS category_id,
               COALESCE(mu.name,  '') AS unit_name,
               COALESCE(cat.name, '') AS category_name,
               lp.fecha               AS last_inventory_date
        FROM supply_items si
        LEFT JOIN pos_measure_forms mu
               ON mu.id = si.unit_id AND mu.company_id = si.company_id
        LEFT JOIN pos_product_categories cat
               ON cat.id = si.agrupar AND cat.company_id = si.company_id
        LEFT JOIN last_phys lp      ON lp.id_item  = si.id_item
        LEFT JOIN entries_adj ea    ON ea.id_item   = si.id_item
        LEFT JOIN exits_adj xa      ON xa.id_item   = si.id_item
        LEFT JOIN receipt_sales rs  ON rs.item_id   = si.id_item
        LEFT JOIN invoice_sales inv ON inv.item_id  = si.id_item
        WHERE {where_sql}
        {critical_clause}
        ORDER BY si.description
    """), params)).mappings().all()
    return [dict(r) for r in rows]


@router.patch("/stock/{id_item}/min-stock")
async def update_min_stock(
    id_item: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    min_stock = float(data.get("min_stock", 0))
    if min_stock < 0:
        raise HTTPException(400, "min_stock no puede ser negativo")

    res = await db.execute(text("""
        UPDATE supply_items SET min_stock = :ms, updated_at = NOW()
        WHERE id_item = :item AND company_id = :cid
    """), {"ms": min_stock, "item": id_item, "cid": current_user.company_id})
    await db.commit()

    if res.rowcount == 0:
        raise HTTPException(404, "Insumo no encontrado")
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════════
# RECALCULAR STOCK — sincroniza supply_items.stock_qty con la fórmula real
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/stock/recalculate")
async def recalculate_stock(
    data: dict = Body(default={}),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Recalcula supply_items.stock_qty usando la fórmula completa:
      físico + entradas - salidas - ventas_recibos_VB6 - ventas_facturas_VB6
    scope: "all" | "category" | "item"
    """
    scope       = data.get("scope", "all")
    category_id = data.get("category_id")
    id_item     = data.get("id_item")
    cid         = current_user.company_id

    where_parts = ["si.company_id = :cid"]
    params: dict = {"cid": cid}
    if scope == "category" and category_id:
        where_parts.append("si.agrupar = :cat_id")
        params["cat_id"] = int(category_id)
    elif scope == "item" and id_item:
        where_parts.append("si.id_item = :item")
        params["item"] = int(id_item)
    where_sql = " AND ".join(where_parts)

    # 1. Calcular el stock real para cada ítem del scope
    calc_rows = (await db.execute(text(f"""
        WITH ranked_phys AS (
            SELECT id_item, cantidad, fecha,
                   ROW_NUMBER() OVER (PARTITION BY id_item ORDER BY fecha DESC, created_at DESC) AS rn
            FROM inventory_physical WHERE company_id = :cid
        ),
        last_phys AS (SELECT id_item, cantidad, fecha FROM ranked_phys WHERE rn = 1),
        entries_adj AS (
            SELECT ie.id_item, SUM(ie.cantidad) AS total
            FROM inventory_entries ie
            LEFT JOIN last_phys lp ON lp.id_item = ie.id_item
            WHERE ie.company_id = :cid AND (lp.fecha IS NULL OR ie.fecha >= lp.fecha)
            GROUP BY ie.id_item
        ),
        exits_adj AS (
            SELECT ix.id_item, SUM(ix.cantidad) AS total
            FROM inventory_exits ix
            LEFT JOIN last_phys lp ON lp.id_item = ix.id_item
            WHERE ix.company_id = :cid AND (lp.fecha IS NULL OR ix.fecha >= lp.fecha)
            GROUP BY ix.id_item
        ),
        receipt_sales AS (
            SELECT prd.item_id, SUM(prd.quantity) AS total
            FROM pos_receipt_order_detail_products prd
            LEFT JOIN last_phys lp ON lp.id_item = prd.item_id
            LEFT JOIN pos_receipts pr
                   ON pr.receipt_number = prd.invoice_number AND pr.company_id = prd.company_id
            WHERE prd.company_id = :cid
              AND (lp.fecha IS NULL OR prd.date >= lp.fecha)
              AND (pr.voided IS NULL OR pr.voided = 0)
            GROUP BY prd.item_id
        ),
        invoice_sales AS (
            SELECT pod.item_id, SUM(pod.quantity) AS total
            FROM pos_order_detail_products pod
            LEFT JOIN last_phys lp ON lp.id_item = pod.item_id
            LEFT JOIN pos_invoices pi
                   ON pi.invoice_number = pod.invoice_number AND pi.company_id = pod.company_id
            WHERE pod.company_id = :cid
              AND (lp.fecha IS NULL OR pod.date >= lp.fecha)
              AND (pi.voided IS NULL OR pi.voided = 0)
            GROUP BY pod.item_id
        )
        SELECT si.id,
               COALESCE(lp.cantidad,0) + COALESCE(ea.total,0) - COALESCE(xa.total,0)
               - COALESCE(rs.total,0) - COALESCE(inv.total,0) AS new_stock
        FROM supply_items si
        LEFT JOIN last_phys lp      ON lp.id_item  = si.id_item
        LEFT JOIN entries_adj ea    ON ea.id_item   = si.id_item
        LEFT JOIN exits_adj xa      ON xa.id_item   = si.id_item
        LEFT JOIN receipt_sales rs  ON rs.item_id   = si.id_item
        LEFT JOIN invoice_sales inv ON inv.item_id  = si.id_item
        WHERE {where_sql}
    """), params)).mappings().all()

    # 2. Bulk UPDATE
    for row in calc_rows:
        await db.execute(text("""
            UPDATE supply_items SET stock_qty = :q, updated_at = NOW() WHERE id = :id
        """), {"q": float(row["new_stock"]), "id": row["id"]})

    await db.commit()
    return {"ok": True, "updated": len(calc_rows)}


# ═══════════════════════════════════════════════════════════════════════════════
# MOVIMIENTOS — historial de un insumo o de todos
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/movements")
async def get_movements_all(
    id_item:  Optional[int] = Query(None),
    mtype:    Optional[str] = Query(None),   # movement_type filter
    desde:    Optional[str] = Query(None),
    hasta:    Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cid = current_user.company_id
    where_parts = ["sm.company_id = :cid", "sm.movement_type != 'physical_snapshot'"]
    params: dict = {"cid": cid}

    if id_item:
        si = (await db.execute(text(
            "SELECT id FROM supply_items WHERE company_id=:cid AND id_item=:item LIMIT 1"
        ), {"cid": cid, "item": id_item})).mappings().first()
        if si:
            where_parts.append("sm.supply_item_id = :sid")
            params["sid"] = si["id"]

    if mtype:
        if mtype == 'sale':
            where_parts.append("sm.movement_type IN ('sale_vb6','sale_web','sale_online')")
        else:
            where_parts.append("sm.movement_type = :mtype")
            params["mtype"] = mtype

    if desde:
        where_parts.append("sm.movement_date >= :desde")
        params["desde"] = desde
    if hasta:
        where_parts.append("sm.movement_date <= :hasta")
        params["hasta"] = hasta

    where_sql = " AND ".join(where_parts)

    rows = (await db.execute(text(f"""
        SELECT sm.id, sm.movement_type, sm.qty, sm.qty_before, sm.qty_after,
               sm.reference_type, sm.reference_id, sm.movement_date, sm.notes,
               sm.created_at,
               COALESCE(si.description, '') AS item_name,
               si.id_item,
               COALESCE(mu.name, '') AS unit_name,
               COALESCE(u.nombre, u.email, '') AS usuario
        FROM stock_movements sm
        LEFT JOIN supply_items si ON si.id = sm.supply_item_id
        LEFT JOIN pos_measure_forms mu ON mu.id = si.unit_id AND mu.company_id = sm.company_id
        LEFT JOIN users u ON u.id = sm.created_by
        WHERE {where_sql}
        ORDER BY sm.created_at DESC
        LIMIT 500
    """), params)).mappings().all()
    return [dict(r) for r in rows]


@router.get("/movements/{id_item}")
async def get_movements(
    id_item: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    si = (await db.execute(text(
        "SELECT id FROM supply_items WHERE company_id=:cid AND id_item=:item LIMIT 1"
    ), {"cid": current_user.company_id, "item": id_item})).mappings().first()
    if not si:
        raise HTTPException(404, "Insumo no encontrado")

    rows = (await db.execute(text("""
        SELECT sm.id, sm.movement_type, sm.qty, sm.qty_before, sm.qty_after,
               sm.reference_type, sm.reference_id, sm.movement_date, sm.notes, sm.created_at,
               COALESCE(u.nombre, u.email, '') AS usuario
        FROM stock_movements sm
        LEFT JOIN users u ON u.id = sm.created_by
        WHERE sm.supply_item_id = :sid AND sm.movement_type != 'physical_snapshot'
        ORDER BY sm.created_at DESC LIMIT 200
    """), {"sid": si["id"]})).mappings().all()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# INVENTARIOS FÍSICOS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/physical")
async def list_physical(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(text("""
        SELECT ip.id, ip.id_fisico, ip.id_item, ip.fecha, ip.cantidad,
               ip.observacion, ip.autorizada, ip.cod_usuario, ip.created_at,
               COALESCE(si.description, CONCAT('Item #', ip.id_item)) AS item_name,
               COALESCE(mu.name, '') AS unit_name
        FROM inventory_physical ip
        LEFT JOIN supply_items si ON si.id_item = ip.id_item AND si.company_id = ip.company_id
        LEFT JOIN pos_measure_forms mu ON mu.id = si.unit_id AND mu.company_id = ip.company_id
        WHERE ip.company_id = :cid
        ORDER BY ip.fecha DESC, ip.created_at DESC
        LIMIT 500
    """), {"cid": current_user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.get("/physical/dates")
async def list_physical_dates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista de fechas de cortes de inventario físico (para el historial).
    No filtra por autorizada porque VB6 sincroniza con autorizada=0."""
    rows = (await db.execute(text("""
        SELECT fecha, COUNT(*) AS items_contados,
               MIN(created_at) AS hora_inicio, MAX(created_at) AS hora_fin,
               MAX(cod_usuario) AS usuario
        FROM inventory_physical
        WHERE company_id = :cid
        GROUP BY fecha
        ORDER BY fecha DESC
        LIMIT 100
    """), {"cid": current_user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.get("/physical/report/{fecha}")
async def physical_report(
    fecha: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reporte de diferencias para un corte de inventario físico."""
    cid = current_user.company_id
    rows = (await db.execute(text("""
        SELECT
            ip.id,
            ip.id_item,
            COALESCE(si.description, CONCAT('Item #', ip.id_item)) AS item_name,
            COALESCE(si.code, '')                                   AS code,
            COALESCE(mu.name, '')                                   AS unit_name,
            COALESCE(cat.name, '')                                  AS category_name,
            ip.observacion,
            ip.cantidad                                             AS contado,
            COALESCE(sm.qty_before,
                (SELECT prev.cantidad
                 FROM inventory_physical prev
                 WHERE prev.id_item = ip.id_item AND prev.company_id = ip.company_id
                   AND prev.fecha < ip.fecha
                 ORDER BY prev.fecha DESC LIMIT 1),
                0)                                                  AS sistema,
            ip.cantidad - COALESCE(sm.qty_before,
                (SELECT prev.cantidad
                 FROM inventory_physical prev
                 WHERE prev.id_item = ip.id_item AND prev.company_id = ip.company_id
                   AND prev.fecha < ip.fecha
                 ORDER BY prev.fecha DESC LIMIT 1),
                0)                                                  AS diferencia
        FROM inventory_physical ip
        LEFT JOIN supply_items si  ON si.id_item = ip.id_item AND si.company_id = ip.company_id
        LEFT JOIN pos_measure_forms mu ON mu.id = si.unit_id AND mu.company_id = ip.company_id
        LEFT JOIN pos_product_categories cat ON cat.id = si.agrupar AND cat.company_id = ip.company_id
        LEFT JOIN stock_movements sm
               ON sm.supply_item_id = si.id
              AND sm.movement_type   = 'physical'
              AND sm.movement_date   = ip.fecha
              AND sm.reference_type  = 'physical_bulk'
        WHERE ip.company_id = :cid AND ip.fecha = :fecha
        ORDER BY COALESCE(cat.name, 'zzz'), si.description
    """), {"cid": cid, "fecha": fecha})).mappings().all()
    return [dict(r) for r in rows]


@router.post("/physical")
async def create_physical(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    id_item = data.get("id_item")
    cantidad = float(data.get("cantidad") or 0)
    fecha = data.get("fecha") or date_type.today().isoformat()
    observacion = (data.get("observacion") or "").strip()

    if not id_item:
        raise HTTPException(400, "id_item es requerido")

    # Reusar el id_fisico existente para esa fecha, o crear uno nuevo
    existing = (await db.execute(text("""
        SELECT id_fisico FROM inventory_physical
        WHERE company_id=:cid AND fecha=:fecha LIMIT 1
    """), {"cid": current_user.company_id, "fecha": fecha})).mappings().first()
    id_fisico = existing["id_fisico"] if existing else (
        (await db.execute(text(
            "SELECT COALESCE(MAX(id_fisico),0)+1 FROM inventory_physical WHERE company_id=:cid"
        ), {"cid": current_user.company_id})).scalar() or 1
    )

    res = await db.execute(text("""
        INSERT INTO inventory_physical
            (id_fisico, id_item, company_id, fecha, cantidad, cod_usuario,
             observacion, autorizada, synced, updated_at)
        VALUES
            (:id_fisico, :id_item, :cid, :fecha, :cantidad, :cod_usuario,
             :observacion, 0, 0, NOW())
        ON DUPLICATE KEY UPDATE
            cantidad    = VALUES(cantidad),
            observacion = VALUES(observacion),
            updated_at  = NOW()
    """), {
        "cid": current_user.company_id, "id_fisico": id_fisico,
        "id_item": id_item, "fecha": fecha, "cantidad": cantidad,
        "cod_usuario": current_user.email,
        "observacion": observacion,
    })
    new_id = res.lastrowid
    await db.commit()
    return {"ok": True, "id": new_id}


@router.post("/physical/bulk")
async def create_physical_bulk(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Toma de inventario físico completa (bulk).
    - Paso 1: snapshot del stock actual de todos los ítems (movement_type='physical_snapshot')
    - Paso 2: aplica los valores contados a stock_qty
    - Paso 3: registra en inventory_physical
    Ítems no incluidos en items[] también se actualizan a 0 si se indica reset_all=true.
    """
    cid = current_user.company_id
    fecha = data.get("fecha") or date_type.today().isoformat()
    observacion = (data.get("observacion") or "").strip()
    items: list = data.get("items", [])   # [{id_item, cantidad}]

    if not items:
        raise HTTPException(400, "Se requiere al menos un ítem")

    # Construir mapa de conteos
    conteo = {int(it["id_item"]): float(it.get("cantidad") or 0) for it in items}

    # Paso 1: Snapshot del stock actual de todos los ítems del conteo
    for id_item, cantidad in conteo.items():
        si = (await db.execute(text("""
            SELECT id, stock_qty, control_stock
            FROM supply_items WHERE company_id=:cid AND id_item=:item LIMIT 1
        """), {"cid": cid, "item": id_item})).mappings().first()

        if not si or not si["control_stock"]:
            continue

        old_qty = float(si["stock_qty"] or 0)

        # Snapshot: solo registra en stock_movements, no toca stock_qty
        await db.execute(text("""
            INSERT INTO stock_movements
                (company_id, supply_item_id, movement_type, qty, qty_before, qty_after,
                 reference_type, reference_id, movement_date, notes, created_by)
            VALUES
                (:cid, :sid, 'physical_snapshot', :dq, :qb, :qa,
                 'physical_bulk', NULL, :mdate, :notes, :uid)
        """), {
            "cid": cid, "sid": si["id"],
            "dq": cantidad - old_qty,
            "qb": old_qty, "qa": cantidad,
            "mdate": fecha,
            "notes": f"Snapshot pre-corte inv. físico — {observacion or 'sin observación'}",
            "uid": current_user.id,
        })

    await db.flush()

    # Paso 2 + 3: Aplicar conteos y registrar en inventory_physical
    next_id_fisico = (await db.execute(text(
        "SELECT COALESCE(MAX(id_fisico),0)+1 FROM inventory_physical WHERE company_id=:cid"
    ), {"cid": cid})).scalar() or 1

    saved = 0
    for id_item, cantidad in conteo.items():
        si = (await db.execute(text("""
            SELECT id, stock_qty, control_stock
            FROM supply_items WHERE company_id=:cid AND id_item=:item LIMIT 1
        """), {"cid": cid, "item": id_item})).mappings().first()

        if not si:
            continue

        # Insertar en inventory_physical
        res = await db.execute(text("""
            INSERT INTO inventory_physical
                (id_fisico, id_item, company_id, fecha, cantidad, cod_usuario,
                 observacion, autorizada, synced, updated_at)
            VALUES (:idf, :id_item, :cid, :fecha, :cantidad, :cod_usuario,
                    :observacion, 1, 0, NOW())
        """), {
            "idf": next_id_fisico, "id_item": id_item, "cid": cid,
            "fecha": fecha, "cantidad": cantidad,
            "cod_usuario": current_user.email,
            "observacion": observacion,
        })
        new_id = res.lastrowid
        await db.flush()

        # Aplicar stock (movement physical)
        if si["control_stock"]:
            old_qty = float(si["stock_qty"] or 0)
            await db.execute(text("""
                INSERT INTO stock_movements
                    (company_id, supply_item_id, movement_type, qty, qty_before, qty_after,
                     reference_type, reference_id, movement_date, notes, created_by)
                VALUES
                    (:cid, :sid, 'physical', :dq, :qb, :qa,
                     'physical_bulk', :rid, :mdate, :notes, :uid)
            """), {
                "cid": cid, "sid": si["id"],
                "dq": cantidad - old_qty,
                "qb": old_qty, "qa": cantidad,
                "rid": new_id, "mdate": fecha,
                "notes": f"Inventario físico web — {observacion or 'sin observación'}",
                "uid": current_user.id,
            })
            await db.execute(text(
                "UPDATE supply_items SET stock_qty=:q, updated_at=NOW() WHERE id=:id"
            ), {"q": cantidad, "id": si["id"]})

        next_id_fisico += 1
        saved += 1

    await db.commit()
    return {"ok": True, "saved": saved, "fecha": fecha}


@router.patch("/physical/{pid}")
async def update_physical(
    pid: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Editar cantidad y/u observación de un registro de inventario físico."""
    row = (await db.execute(text(
        "SELECT id FROM inventory_physical WHERE id=:pid AND company_id=:cid LIMIT 1"
    ), {"pid": pid, "cid": current_user.company_id})).mappings().first()
    if not row:
        raise HTTPException(404, "Registro no encontrado")

    cantidad    = data.get("cantidad")
    observacion = data.get("observacion")
    sets = []
    params: dict = {"pid": pid}
    if cantidad is not None:
        sets.append("cantidad = :cantidad")
        params["cantidad"] = float(cantidad)
    if observacion is not None:
        sets.append("observacion = :observacion")
        params["observacion"] = str(observacion)
    if not sets:
        raise HTTPException(400, "Nada que actualizar")

    sets.append("updated_at = NOW()")
    await db.execute(text(
        f"UPDATE inventory_physical SET {', '.join(sets)} WHERE id=:pid"
    ), params)
    await db.commit()
    return {"ok": True}


@router.delete("/physical/date/{fecha}")
async def delete_physical_by_date(
    fecha: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Eliminar todos los registros de un corte de inventario por fecha."""
    res = await db.execute(text(
        "DELETE FROM inventory_physical WHERE company_id=:cid AND fecha=:fecha"
    ), {"cid": current_user.company_id, "fecha": fecha})
    await db.commit()
    return {"ok": True, "deleted": res.rowcount}


@router.delete("/physical/{pid}")
async def delete_physical(
    pid: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Eliminar un registro individual de inventario físico."""
    res = await db.execute(text(
        "DELETE FROM inventory_physical WHERE id=:pid AND company_id=:cid"
    ), {"pid": pid, "cid": current_user.company_id})
    await db.commit()
    if res.rowcount == 0:
        raise HTTPException(404, "Registro no encontrado")
    return {"ok": True}


@router.patch("/physical/{pid}/authorize")
async def authorize_physical(
    pid: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = (await db.execute(text("""
        SELECT id_fisico, id_item, cantidad, fecha, autorizada
        FROM inventory_physical WHERE id=:pid AND company_id=:cid LIMIT 1
    """), {"pid": pid, "cid": current_user.company_id})).mappings().first()
    if not row:
        raise HTTPException(404, "Registro no encontrado")
    if row["autorizada"]:
        raise HTTPException(400, "Ya está autorizado")

    await db.execute(text(
        "UPDATE inventory_physical SET autorizada=1, updated_at=NOW() WHERE id=:pid"
    ), {"pid": pid})

    already = (await db.execute(text("""
        SELECT 1 FROM stock_movements
        WHERE company_id=:cid AND reference_type='physical' AND reference_id=:rid LIMIT 1
    """), {"cid": current_user.company_id, "rid": row["id_fisico"]})).fetchone()
    if not already:
        await _stock_move(
            db, current_user.company_id, row["id_item"],
            float(row["cantidad"]), "physical",
            "physical", row["id_fisico"], str(row["fecha"]),
            "Inventario físico autorizado",
            current_user.id,
        )

    await db.commit()
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════════
# KARDEX — trazabilidad completa de un insumo desde el último inventario físico
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/kardex/last-date")
async def kardex_last_date(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fecha del último inventario físico registrado (global, aplica a todos los insumos)."""
    row = (await db.execute(text("""
        SELECT MAX(fecha) AS fecha FROM inventory_physical WHERE company_id = :cid
    """), {"cid": current_user.company_id})).mappings().first()
    fecha = str(row["fecha"]).split(" ")[0] if row and row["fecha"] else None
    return {"fecha": fecha}


@router.get("/kardex/items")
async def kardex_items(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista de insumos disponibles para el Kardex (solo los que tienen movimientos)."""
    rows = (await db.execute(text("""
        SELECT si.id_item, si.description, si.code,
               COALESCE(mu.name,  '') AS unit_name,
               COALESCE(cat.name, '') AS category_name,
               si.agrupar AS category_id
        FROM supply_items si
        LEFT JOIN pos_measure_forms mu  ON mu.id  = si.unit_id AND mu.company_id  = si.company_id
        LEFT JOIN pos_product_categories cat ON cat.id = si.agrupar AND cat.company_id = si.company_id
        WHERE si.company_id = :cid AND si.is_active = 1
        ORDER BY cat.name, si.description
    """), {"cid": current_user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.get("/kardex/{id_item}")
async def get_kardex(
    id_item: int,
    desde: Optional[str] = Query(None),
    hasta:  Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Kardex de un insumo: balance diario desde el último inventario físico.
    - desde: si no se pasa, usa la fecha del último inventario físico del ítem.
    - hasta: si no se pasa, usa hoy.
    Columnas diarias: fecha | ini | entradas | salidas | total
    Detalle:          fecha | concepto | numero | cantidad | obs
    """
    cid = current_user.company_id
    today = date_type.today().isoformat()
    hasta_d = hasta or today

    # ── Info del insumo ────────────────────────────────────────────────────────
    item_row = (await db.execute(text("""
        SELECT si.id, si.id_item, si.description, si.code,
               COALESCE(mu.name,  '') AS unit_name,
               COALESCE(cat.name, '') AS category_name
        FROM supply_items si
        LEFT JOIN pos_measure_forms mu  ON mu.id  = si.unit_id AND mu.company_id  = si.company_id
        LEFT JOIN pos_product_categories cat ON cat.id = si.agrupar AND cat.company_id = si.company_id
        WHERE si.company_id = :cid AND si.id_item = :item LIMIT 1
    """), {"cid": cid, "item": id_item})).mappings().first()

    if not item_row:
        raise HTTPException(404, "Insumo no encontrado")

    si_id = item_row["id"]

    # ── Fecha de inicio: fecha global del último inventario físico ────────────
    # Si se pasa 'desde' (= fecha global del último inv.), buscar el item en ESA fecha exacta.
    # Si no existe en esa fecha → inv. inicial = 0 (no se busca en fechas anteriores).
    # Si no se pasa 'desde', calcular la fecha global máxima.
    if desde:
        start_fecha = desde
        phys_exact = (await db.execute(text("""
            SELECT SUM(cantidad) AS cantidad
            FROM inventory_physical
            WHERE company_id = :cid AND id_item = :item AND fecha = :fecha
        """), {"cid": cid, "item": id_item, "fecha": desde})).mappings().first()
        start_qty = float(phys_exact["cantidad"]) if phys_exact and phys_exact["cantidad"] else 0.0
    else:
        # Fecha global máxima del inventario físico de la empresa
        global_date = (await db.execute(text("""
            SELECT MAX(fecha) AS fecha FROM inventory_physical WHERE company_id = :cid
        """), {"cid": cid})).mappings().first()
        start_fecha = str(global_date["fecha"]).split(" ")[0] if global_date and global_date["fecha"] else today
        phys_exact = (await db.execute(text("""
            SELECT SUM(cantidad) AS cantidad
            FROM inventory_physical
            WHERE company_id = :cid AND id_item = :item AND fecha = :fecha
        """), {"cid": cid, "item": id_item, "fecha": start_fecha})).mappings().first()
        start_qty = float(phys_exact["cantidad"]) if phys_exact and phys_exact["cantidad"] else 0.0

    desde_d = start_fecha

    base_p = {"cid": cid, "item": id_item, "desde": desde_d, "hasta": hasta_d}

    # ── Entradas ───────────────────────────────────────────────────────────────
    entries = (await db.execute(text("""
        SELECT ie.fecha, ie.id_entrada AS numero, ie.cantidad,
               COALESCE(ie.observacion, '') AS obs,
               COALESCE(ie.cod_empleado, '') AS usuario
        FROM inventory_entries ie
        WHERE ie.company_id = :cid AND ie.id_item = :item
          AND ie.fecha BETWEEN :desde AND :hasta
        ORDER BY ie.fecha, ie.id
    """), base_p)).mappings().all()

    # ── Salidas ────────────────────────────────────────────────────────────────
    exits = (await db.execute(text("""
        SELECT ix.fecha, ix.id_salida AS numero, ix.cantidad,
               COALESCE(ix.observacion, '') AS obs,
               COALESCE(ix.cod_empleado, '') AS usuario
        FROM inventory_exits ix
        WHERE ix.company_id = :cid AND ix.id_item = :item
          AND ix.fecha BETWEEN :desde AND :hasta
        ORDER BY ix.fecha, ix.id
    """), base_p)).mappings().all()

    # ── Ventas VB6 — Recibos (pos_receipt_order_detail_products) ─────────────
    rec_sales = (await db.execute(text("""
        SELECT prd.date AS fecha,
               prd.invoice_number AS numero,
               COALESCE(d.name, CONCAT('Plato #', prd.dish_id)) AS dish_name,
               SUM(prd.quantity) AS cantidad
        FROM pos_receipt_order_detail_products prd
        LEFT JOIN pos_receipts pr ON pr.receipt_number = prd.invoice_number
                                  AND pr.company_id    = prd.company_id
        LEFT JOIN pos_dishes d   ON d.id = prd.dish_id AND d.company_id = prd.company_id
        WHERE prd.company_id = :cid
          AND prd.item_id = :item
          AND prd.date BETWEEN :desde AND :hasta
          AND (pr.voided IS NULL OR pr.voided = 0)
        GROUP BY prd.date, prd.invoice_number, prd.dish_id
        ORDER BY prd.date, prd.invoice_number
    """), base_p)).mappings().all()

    # ── Ventas VB6 — Facturas (pos_order_detail_products) ────────────────────
    inv_sales = (await db.execute(text("""
        SELECT pod.date AS fecha,
               pod.invoice_number AS numero,
               COALESCE(d.name, CONCAT('Plato #', pod.dish_id)) AS dish_name,
               SUM(pod.quantity) AS cantidad
        FROM pos_order_detail_products pod
        LEFT JOIN pos_invoices pi ON pi.invoice_number = pod.invoice_number
                                  AND pi.company_id    = pod.company_id
        LEFT JOIN pos_dishes d   ON d.id = pod.dish_id AND d.company_id = pod.company_id
        WHERE pod.company_id = :cid
          AND pod.item_id = :item
          AND pod.date BETWEEN :desde AND :hasta
          AND (pi.voided IS NULL OR pi.voided = 0)
        GROUP BY pod.date, pod.invoice_number, pod.dish_id
        ORDER BY pod.date, pod.invoice_number
    """), base_p)).mappings().all()

    # ── Ventas web (stock_movements — canal web/online) ────────────────────────
    web_sales = (await db.execute(text("""
        SELECT DATE(sm.movement_date) AS fecha,
               CASE sm.movement_type
                 WHEN 'sale_vb6'    THEN 'VENTA'
                 WHEN 'sale_web'    THEN 'VENTA WEB'
                 WHEN 'sale_online' THEN 'VENTA ONLINE'
                 ELSE 'VENTA' END AS concepto,
               sm.reference_id AS numero,
               ABS(sm.qty)     AS cantidad,
               COALESCE(sm.notes, '') AS obs,
               COALESCE(u.nombre, u.email, '') AS usuario
        FROM stock_movements sm
        LEFT JOIN users u ON u.id = sm.created_by
        WHERE sm.supply_item_id = :sid
          AND sm.movement_type IN ('sale_vb6','sale_web','sale_online')
          AND sm.movement_date BETWEEN :desde AND :hasta
        ORDER BY sm.movement_date, sm.id
    """), {"sid": si_id, "desde": desde_d, "hasta": hasta_d})).mappings().all()

    # ── Construir lista de movimientos ─────────────────────────────────────────
    movements = []
    for r in entries:
        movements.append({
            "fecha":    str(r["fecha"]).split(" ")[0],
            "concepto": "ENTRADA",
            "numero":   r["numero"],
            "cantidad": float(r["cantidad"]),
            "obs":      r["obs"],
            "usuario":  r["usuario"],
            "tipo":     "entrada",
        })
    for r in exits:
        movements.append({
            "fecha":    str(r["fecha"]).split(" ")[0],
            "concepto": "SALIDA",
            "numero":   r["numero"],
            "cantidad": float(r["cantidad"]),
            "obs":      r["obs"],
            "usuario":  r["usuario"],
            "tipo":     "salida",
        })
    for r in rec_sales:
        qty = float(r["cantidad"] or 0)
        if qty > 0:
            movements.append({
                "fecha":    str(r["fecha"]).split(" ")[0],
                "concepto": r["dish_name"],
                "numero":   r["numero"],
                "cantidad": qty,
                "obs":      "Recibo",
                "usuario":  "",
                "tipo":     "venta",
            })
    for r in inv_sales:
        qty = float(r["cantidad"] or 0)
        if qty > 0:
            movements.append({
                "fecha":    str(r["fecha"]).split(" ")[0],
                "concepto": r["dish_name"],
                "numero":   r["numero"],
                "cantidad": qty,
                "obs":      "Factura",
                "usuario":  "",
                "tipo":     "venta",
            })
    for r in web_sales:
        movements.append({
            "fecha":    str(r["fecha"]).split(" ")[0],
            "concepto": r["concepto"],
            "numero":   r["numero"],
            "cantidad": float(r["cantidad"]),
            "obs":      r["obs"],
            "usuario":  r["usuario"],
            "tipo":     "venta",
        })
    movements.sort(key=lambda x: (x["fecha"], x["concepto"], x["numero"] or 0))

    # ── Totales por día ────────────────────────────────────────────────────────
    d_ent = defaultdict(float)
    d_sal = defaultdict(float)
    d_ven = defaultdict(float)
    for m in movements:
        if   m["tipo"] == "entrada": d_ent[m["fecha"]] += m["cantidad"]
        elif m["tipo"] == "salida":  d_sal[m["fecha"]] += m["cantidad"]
        elif m["tipo"] == "venta":   d_ven[m["fecha"]] += m["cantidad"]

    # ── Serie diaria (solo días con movimiento + día inicial) ──────────────────
    d1 = datetime.strptime(desde_d, "%Y-%m-%d").date()
    d2 = datetime.strptime(hasta_d, "%Y-%m-%d").date()
    daily   = []
    balance = start_qty
    cur     = d1
    while cur <= d2:
        ds  = cur.isoformat()
        ini = balance
        ent = d_ent.get(ds, 0.0)
        sal = d_sal.get(ds, 0.0)
        ven = d_ven.get(ds, 0.0)
        balance = ini + ent - sal - ven
        if ds == start_fecha or ent or sal or ven:
            daily.append({
                "fecha":    ds,
                "ini":      ini,
                "entradas": ent,
                "salidas":  sal,
                "ventas":   ven,
                "total":    balance,
                "is_start": ds == start_fecha,
            })
        cur += timedelta(days=1)

    has_ventas = any(d["ventas"] for d in daily)

    return {
        "item": dict(item_row),
        "start":    {"fecha": start_fecha, "cantidad": start_qty},
        "desde":    desde_d,
        "hasta":    hasta_d,
        "has_ventas": has_ventas,
        "movements": movements,
        "daily":     daily,
        "totals": {
            "entradas":        sum(d_ent.values()),
            "salidas":         sum(d_sal.values()),
            "ventas":          sum(d_ven.values()),
            "stock_calculado": balance,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRADAS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/entries")
async def list_entries(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(text("""
        SELECT ie.id, ie.id_entrada, ie.id_item, ie.id_proveedor,
               ie.fecha, ie.cantidad, ie.observacion, ie.cod_empleado,
               ie.autorizada, ie.created_at,
               COALESCE(si.description, CONCAT('Item #', ie.id_item)) AS item_name,
               COALESCE(si.code, '') AS code,
               COALESCE(mu.name, '') AS unit_name,
               COALESCE(cat.name, '') AS category_name
        FROM inventory_entries ie
        LEFT JOIN supply_items si ON si.id_item = ie.id_item AND si.company_id = ie.company_id
        LEFT JOIN pos_measure_forms mu ON mu.id = si.unit_id AND mu.company_id = ie.company_id
        LEFT JOIN pos_product_categories cat ON cat.id = si.agrupar AND cat.company_id = ie.company_id
        WHERE ie.company_id = :cid
        ORDER BY COALESCE(cat.name, 'zzz'), si.description, ie.fecha DESC
        LIMIT 500
    """), {"cid": current_user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.post("/entries")
async def create_entry(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    id_item = data.get("id_item")
    cantidad = float(data.get("cantidad") or 0)
    if not id_item or cantidad <= 0:
        raise HTTPException(400, "id_item y cantidad > 0 son requeridos")

    fecha = data.get("fecha") or date_type.today().isoformat()
    observacion = (data.get("observacion") or "").strip()

    res = await db.execute(text("""
        INSERT INTO inventory_entries
            (id_entrada, id_item, id_proveedor, company_id, fecha, cantidad,
             cod_empleado, observacion, autorizada, synced, updated_at)
        VALUES
            ((SELECT COALESCE(MAX(id_entrada),0)+1 FROM inventory_entries ie2 WHERE ie2.company_id=:cid),
             :id_item, :id_proveedor, :cid, :fecha, :cantidad,
             :cod_empleado, :observacion, 1, 0, NOW())
    """), {
        "cid": current_user.company_id, "id_item": id_item,
        "id_proveedor": int(data.get("id_proveedor") or 0),
        "fecha": fecha, "cantidad": cantidad,
        "cod_empleado": current_user.email,
        "observacion": observacion,
    })
    new_id = res.lastrowid
    await db.flush()

    await _stock_move(
        db, current_user.company_id, id_item,
        cantidad, "entry",
        "entry_web", new_id, fecha,
        f"Entrada web — {observacion or 'sin observación'}",
        current_user.id,
    )

    await db.commit()
    return {"ok": True, "id": new_id}


@router.delete("/entries/{eid}")
async def delete_entry(
    eid: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = (await db.execute(text("""
        SELECT id_item, cantidad, fecha FROM inventory_entries
        WHERE id=:eid AND company_id=:cid LIMIT 1
    """), {"eid": eid, "cid": current_user.company_id})).mappings().first()
    if not row:
        raise HTTPException(404, "Registro no encontrado")

    await db.execute(text("DELETE FROM inventory_entries WHERE id=:eid"), {"eid": eid})
    await _stock_move(
        db, current_user.company_id, row["id_item"],
        -(float(row["cantidad"])), "entry",
        "entry_web_del", eid, str(row["fecha"]),
        "Anulación entrada web",
        current_user.id,
    )
    await db.commit()
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════════
# SALIDAS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/exits")
async def list_exits(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(text("""
        SELECT ix.id, ix.id_salida, ix.id_item, ix.id_proveedor,
               ix.fecha, ix.cantidad, ix.observacion, ix.cod_empleado,
               ix.autorizada, ix.created_at,
               COALESCE(si.description, CONCAT('Item #', ix.id_item)) AS item_name,
               COALESCE(si.code, '') AS code,
               COALESCE(mu.name, '') AS unit_name,
               COALESCE(cat.name, '') AS category_name
        FROM inventory_exits ix
        LEFT JOIN supply_items si ON si.id_item = ix.id_item AND si.company_id = ix.company_id
        LEFT JOIN pos_measure_forms mu ON mu.id = si.unit_id AND mu.company_id = ix.company_id
        LEFT JOIN pos_product_categories cat ON cat.id = si.agrupar AND cat.company_id = ix.company_id
        WHERE ix.company_id = :cid
        ORDER BY COALESCE(cat.name, 'zzz'), si.description, ix.fecha DESC
        LIMIT 500
    """), {"cid": current_user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.post("/exits")
async def create_exit(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    id_item = data.get("id_item")
    cantidad = float(data.get("cantidad") or 0)
    if not id_item or cantidad <= 0:
        raise HTTPException(400, "id_item y cantidad > 0 son requeridos")

    fecha = data.get("fecha") or date_type.today().isoformat()
    observacion = (data.get("observacion") or "").strip()

    res = await db.execute(text("""
        INSERT INTO inventory_exits
            (id_salida, id_item, id_proveedor, company_id, fecha, cantidad,
             cod_empleado, observacion, autorizada, synced, updated_at)
        VALUES
            ((SELECT COALESCE(MAX(id_salida),0)+1 FROM inventory_exits ix2 WHERE ix2.company_id=:cid),
             :id_item, :id_proveedor, :cid, :fecha, :cantidad,
             :cod_empleado, :observacion, 1, 0, NOW())
    """), {
        "cid": current_user.company_id, "id_item": id_item,
        "id_proveedor": int(data.get("id_proveedor") or 0),
        "fecha": fecha, "cantidad": cantidad,
        "cod_empleado": current_user.email,
        "observacion": observacion,
    })
    new_id = res.lastrowid
    await db.flush()

    await _stock_move(
        db, current_user.company_id, id_item,
        -(cantidad), "exit",
        "exit_web", new_id, fecha,
        f"Salida web — {observacion or 'sin observación'}",
        current_user.id,
    )

    await db.commit()
    return {"ok": True, "id": new_id}


@router.delete("/exits/{xid}")
async def delete_exit(
    xid: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = (await db.execute(text("""
        SELECT id_item, cantidad, fecha FROM inventory_exits
        WHERE id=:xid AND company_id=:cid LIMIT 1
    """), {"xid": xid, "cid": current_user.company_id})).mappings().first()
    if not row:
        raise HTTPException(404, "Registro no encontrado")

    await db.execute(text("DELETE FROM inventory_exits WHERE id=:xid"), {"xid": xid})
    await _stock_move(
        db, current_user.company_id, row["id_item"],
        float(row["cantidad"]), "exit",
        "exit_web_del", xid, str(row["fecha"]),
        "Anulación salida web",
        current_user.id,
    )
    await db.commit()
    return {"ok": True}
