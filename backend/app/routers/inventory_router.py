from datetime import date as date_type
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
    critical:    Optional[int] = Query(0),     # 1 = solo los críticos (stock ≤ min)
    category_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cid = current_user.company_id
    where_parts = ["si.company_id = :cid"]
    params: dict = {"cid": cid}

    if active == "1":
        where_parts.append("si.is_active = 1")
    elif active == "0":
        where_parts.append("si.is_active = 0")

    if critical:
        where_parts.append("si.control_stock = 1 AND si.min_stock > 0 AND si.stock_qty <= si.min_stock")

    if search and search.strip():
        where_parts.append("(si.description LIKE :search OR si.code LIKE :search)")
        params["search"] = f"%{search.strip()}%"

    if category_id:
        where_parts.append("si.agrupar = :cat_id")
        params["cat_id"] = category_id

    where_sql = " AND ".join(where_parts)

    rows = (await db.execute(text(f"""
        SELECT si.id, si.id_item, si.code, si.description,
               si.stock_qty, si.min_stock, si.control_stock,
               si.is_active, si.agrupar AS category_id,
               COALESCE(mu.name, '')   AS unit_name,
               COALESCE(cat.name, '')  AS category_name
        FROM supply_items si
        LEFT JOIN pos_measure_forms mu     ON mu.id = si.unit_id AND mu.company_id = si.company_id
        LEFT JOIN pos_product_categories cat ON cat.id = si.agrupar AND cat.company_id = si.company_id
        WHERE {where_sql}
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
        WHERE ip.company_id = :cid AND ip.autorizada = 1
        ORDER BY ip.fecha DESC, ip.created_at DESC
        LIMIT 500
    """), {"cid": current_user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.get("/physical/dates")
async def list_physical_dates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista de fechas de cortes de inventario físico (para el historial)."""
    rows = (await db.execute(text("""
        SELECT fecha, COUNT(*) AS items_contados,
               MIN(created_at) AS hora_inicio, MAX(created_at) AS hora_fin,
               MAX(cod_usuario) AS usuario
        FROM inventory_physical
        WHERE company_id = :cid AND autorizada = 1
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
            ip.id_item,
            COALESCE(si.description, CONCAT('Item #', ip.id_item)) AS item_name,
            COALESCE(si.code, '')                                   AS code,
            COALESCE(mu.name, '')                                   AS unit_name,
            ip.cantidad                                             AS contado,
            sm.qty_before                                           AS sistema,
            (ip.cantidad - sm.qty_before)                          AS diferencia
        FROM inventory_physical ip
        LEFT JOIN supply_items si  ON si.id_item = ip.id_item AND si.company_id = ip.company_id
        LEFT JOIN pos_measure_forms mu ON mu.id = si.unit_id AND mu.company_id = ip.company_id
        LEFT JOIN stock_movements sm
               ON sm.supply_item_id = si.id
              AND sm.movement_type   = 'physical'
              AND sm.movement_date   = ip.fecha
              AND sm.reference_type  = 'physical_bulk'
        WHERE ip.company_id = :cid AND ip.fecha = :fecha AND ip.autorizada = 1
        ORDER BY ABS(ip.cantidad - COALESCE(sm.qty_before, 0)) DESC
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

    res = await db.execute(text("""
        INSERT INTO inventory_physical
            (id_fisico, id_item, company_id, fecha, cantidad, cod_usuario,
             observacion, autorizada, synced, updated_at)
        VALUES
            ((SELECT COALESCE(MAX(id_fisico),0)+1 FROM inventory_physical ip2 WHERE ip2.company_id=:cid),
             :id_item, :cid, :fecha, :cantidad, :cod_usuario,
             :observacion, 1, 0, NOW())
    """), {
        "cid": current_user.company_id, "id_item": id_item,
        "fecha": fecha, "cantidad": cantidad,
        "cod_usuario": current_user.email,
        "observacion": observacion,
    })
    new_id = res.lastrowid
    await db.flush()

    await _stock_move(
        db, current_user.company_id, id_item,
        cantidad, "physical",
        "physical", new_id, fecha,
        f"Inventario físico web — {observacion or 'sin observación'}",
        current_user.id,
    )

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
               COALESCE(mu.name, '') AS unit_name
        FROM inventory_entries ie
        LEFT JOIN supply_items si ON si.id_item = ie.id_item AND si.company_id = ie.company_id
        LEFT JOIN pos_measure_forms mu ON mu.id = si.unit_id AND mu.company_id = ie.company_id
        WHERE ie.company_id = :cid
        ORDER BY ie.fecha DESC, ie.created_at DESC
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
               COALESCE(mu.name, '') AS unit_name
        FROM inventory_exits ix
        LEFT JOIN supply_items si ON si.id_item = ix.id_item AND si.company_id = ix.company_id
        LEFT JOIN pos_measure_forms mu ON mu.id = si.unit_id AND mu.company_id = ix.company_id
        WHERE ix.company_id = :cid
        ORDER BY ix.fecha DESC, ix.created_at DESC
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
