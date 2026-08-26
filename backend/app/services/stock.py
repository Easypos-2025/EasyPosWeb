from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

"""
Único punto de escritura de stock de insumos.
Fuente de verdad: inventario_actual_porciones (cantidad_actual, stock_minimo).
supply_items.stock_qty / min_stock quedan como copia de catálogo (VB6 la
resincroniza periódicamente vía /sync/push/supply-items) y NO deben usarse
para decidir nada — solo inventario_actual_porciones se actualiza aquí.
"""


async def apply_stock_move(
    db: AsyncSession,
    company_id: int,
    id_item: int,
    qty: float,
    mtype: str,
    ref_type: str,
    ref_id: Optional[int],
    mdate: Optional[str],
    notes: Optional[str] = None,
    user_id: Optional[int] = None,
) -> None:
    row = (await db.execute(text("""
        SELECT si.id AS supply_item_id, si.control_stock,
               COALESCE(iap.cantidad_actual, 0) AS cantidad_actual
        FROM supply_items si
        LEFT JOIN inventario_actual_porciones iap
               ON iap.company_id = si.company_id AND iap.id_item = si.id_item
        WHERE si.company_id = :cid AND si.id_item = :item
        LIMIT 1
    """), {"cid": company_id, "item": id_item})).mappings().first()

    if not row or not row["control_stock"]:
        return

    old_qty = float(row["cantidad_actual"] or 0)
    new_qty = qty if mtype in ("physical", "physical_snapshot") else old_qty + qty

    await db.execute(text("""
        INSERT INTO stock_movements
            (company_id, supply_item_id, movement_type, qty, qty_before, qty_after,
             reference_type, reference_id, movement_date, notes, created_by)
        VALUES
            (:cid, :sid, :mtype, :dq, :qb, :qa, :rtype, :rid, :mdate, :notes, :uid)
    """), {
        "cid": company_id, "sid": row["supply_item_id"], "mtype": mtype,
        "dq": (new_qty - old_qty) if mtype in ("physical", "physical_snapshot") else qty,
        "qb": old_qty, "qa": new_qty,
        "rtype": ref_type, "rid": ref_id, "mdate": mdate,
        "notes": notes, "uid": user_id,
    })

    if mtype == "physical":
        await db.execute(text("""
            UPDATE inventario_actual_porciones
            SET cantidad_actual = :q, enviada_mysql = 0, updated_at = NOW()
            WHERE company_id = :cid AND id_item = :item
        """), {"q": new_qty, "cid": company_id, "item": id_item})
    elif mtype != "physical_snapshot":
        await db.execute(text("""
            UPDATE inventario_actual_porciones
            SET cantidad_actual = cantidad_actual + :q, enviada_mysql = 0, updated_at = NOW()
            WHERE company_id = :cid AND id_item = :item
        """), {"q": qty, "cid": company_id, "item": id_item})


async def set_min_stock(db: AsyncSession, company_id: int, id_item: int, min_stock: float) -> bool:
    """Actualiza el mínimo en la fuente de verdad. Devuelve False si el insumo no existe."""
    res = await db.execute(text("""
        UPDATE inventario_actual_porciones
        SET stock_minimo = :ms, enviada_mysql = 0, updated_at = NOW()
        WHERE company_id = :cid AND id_item = :item
    """), {"ms": min_stock, "cid": company_id, "item": id_item})
    return res.rowcount > 0


async def nudge_iap_quantity(db: AsyncSession, company_id: int, id_item: Optional[int], delta_qty: float) -> None:
    """
    Aplica un delta a inventario_actual_porciones para flujos que ya registraron su
    propio movimiento/auditoría por otra vía (ej. recepción de mercancía) y solo
    necesitan reflejar el cambio en la fuente de verdad. No-op si el insumo no
    tiene id_item vinculado (creado manualmente en la web, sin origen VB6).
    """
    if id_item is None:
        return
    await db.execute(text("""
        UPDATE inventario_actual_porciones
        SET cantidad_actual = cantidad_actual + :q, enviada_mysql = 0, updated_at = NOW()
        WHERE company_id = :cid AND id_item = :item
    """), {"q": delta_qty, "cid": company_id, "item": id_item})
