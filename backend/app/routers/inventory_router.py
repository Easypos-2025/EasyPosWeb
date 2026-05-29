from datetime import date as date_type
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Body
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
    new_qty = qty if mtype == "physical" else old_qty + qty

    await db.execute(text("""
        INSERT INTO stock_movements
            (company_id, supply_item_id, movement_type, qty, qty_before, qty_after,
             reference_type, reference_id, movement_date, notes, created_by)
        VALUES
            (:cid, :sid, :mtype, :dq, :qb, :qa, :rtype, :rid, :mdate, :notes, :uid)
    """), {
        "cid": company_id, "sid": si["id"], "mtype": mtype,
        "dq": (new_qty - old_qty) if mtype == "physical" else qty,
        "qb": old_qty, "qa": new_qty,
        "rtype": ref_type, "rid": ref_id, "mdate": mdate,
        "notes": notes, "uid": user_id,
    })
    await db.execute(text(
        "UPDATE supply_items SET stock_qty=:q WHERE id=:id"
    ), {"q": new_qty, "id": si["id"]})


def _items_base_query(company_id: int):
    return """
        SELECT si.id_item, si.description, si.code, si.stock_qty, si.min_stock,
               si.control_stock, si.unit_id,
               COALESCE(mu.name, '') AS unit_name
        FROM supply_items si
        LEFT JOIN pos_measure_forms mu ON mu.id = si.unit_id AND mu.company_id = si.company_id
        WHERE si.company_id = :cid AND si.is_active = 1
        ORDER BY si.description
    """


# ═══════════════════════════════════════════════════════════════════════════════
# STOCK — vista general de insumos con stock actual
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/stock")
async def get_stock(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        text(_items_base_query(current_user.company_id)),
        {"cid": current_user.company_id}
    )).mappings().all()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# MOVIMIENTOS — historial de un insumo
# ═══════════════════════════════════════════════════════════════════════════════

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
        SELECT id, movement_type, qty, qty_before, qty_after,
               reference_type, reference_id, movement_date, notes, created_at
        FROM stock_movements
        WHERE supply_item_id=:sid
        ORDER BY created_at DESC LIMIT 200
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
    autorizada = int(data.get("autorizada", 1))

    if not id_item:
        raise HTTPException(400, "id_item es requerido")

    res = await db.execute(text("""
        INSERT INTO inventory_physical
            (id_fisico, id_item, company_id, fecha, cantidad, cod_usuario,
             observacion, autorizada, synced, updated_at)
        VALUES
            ((SELECT COALESCE(MAX(id_fisico),0)+1 FROM inventory_physical ip2 WHERE ip2.company_id=:cid),
             :id_item, :cid, :fecha, :cantidad, :cod_usuario,
             :observacion, :autorizada, 0, NOW())
    """), {
        "cid": current_user.company_id, "id_item": id_item,
        "fecha": fecha, "cantidad": cantidad,
        "cod_usuario": current_user.email,
        "observacion": observacion, "autorizada": autorizada,
    })
    new_id = res.lastrowid
    await db.flush()

    if autorizada:
        await _stock_move(
            db, current_user.company_id, id_item,
            cantidad, "physical",
            "physical", new_id, fecha,
            f"Inventario físico web — {observacion or 'sin observación'}",
            current_user.id,
        )

    await db.commit()
    return {"ok": True, "id": new_id}


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
