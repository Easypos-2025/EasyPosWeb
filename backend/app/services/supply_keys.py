"""
Llaves de insumo (supply_items = inventario_porciones del escritorio).

Todo insumo necesita id_grupo / id_item / posicion: con ellos se relaciona con
inventario_actual_porciones, armado (plato_armar_detalle.Posicion), insumos fijos
(inventario_porciones_plato) y el descuento de inventario. Los insumos creados en
la web no los tenían; aquí se asignan.

id_item es consecutivo por empresa y se toma por encima del máximo de supply_items
e inventario_actual_porciones para no chocar con registros existentes.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

DEFAULT_ID_GRUPO = 1


async def next_id_item(db: AsyncSession, cid: int) -> int:
    # FOR UPDATE bloquea el rango de la empresa hasta el commit → evita ids repetidos en concurrencia
    max_si = (await db.execute(text(
        "SELECT COALESCE(MAX(id_item), 0) FROM supply_items WHERE company_id = :cid FOR UPDATE"
    ), {"cid": cid})).scalar() or 0
    # También por encima de los id_item con historial (ventas, físicos, entradas, salidas):
    # si un insumo nuevo reutilizara un id viejo, el recálculo le sumaría movimientos ajenos.
    maximos = [int(max_si)]
    for tabla, col in (
        ("inventario_actual_porciones",       "id_item"),
        ("inventory_physical",                "id_item"),
        ("inventory_entries",                 "id_item"),
        ("inventory_exits",                   "id_item"),
        ("pos_receipt_order_detail_products", "item_id"),
        ("pos_order_detail_products",         "item_id"),
    ):
        try:
            v = (await db.execute(text(
                f"SELECT COALESCE(MAX({col}), 0) FROM {tabla} WHERE company_id = :cid"
            ), {"cid": cid})).scalar() or 0
            maximos.append(int(v))
        except Exception:
            # tabla inexistente en algún entorno: no bloquea la asignación
            pass
    return max(maximos) + 1


async def assign_missing_keys(db: AsyncSession, cid: int) -> int:
    """Asigna id_grupo/id_item/posicion a los insumos de la empresa que no los tengan."""
    rows = (await db.execute(text(
        "SELECT id, id_grupo, id_item FROM supply_items "
        "WHERE company_id = :cid AND (COALESCE(id_item, 0) = 0 OR COALESCE(id_grupo, 0) = 0) ORDER BY id"
    ), {"cid": cid})).mappings().all()
    if not rows:
        return 0
    nxt = await next_id_item(db, cid)
    for r in rows:
        id_item = r["id_item"]
        if not id_item:
            id_item, nxt = nxt, nxt + 1
        await db.execute(text("""
            UPDATE supply_items
            SET id_grupo = IF(COALESCE(id_grupo, 0) = 0, :g, id_grupo), id_item = :iid,
                posicion = IF(COALESCE(posicion, 0) = 0, :iid, posicion)
            WHERE id = :id AND company_id = :cid
        """), {"g": DEFAULT_ID_GRUPO, "iid": id_item, "id": r["id"], "cid": cid})
    return len(rows)


# Campos de catálogo que se copian de supply_items a inventario_actual_porciones.
# cantidad_actual NO se toca: es el campo propio del stock (lo calcula el recálculo).
CATALOG_SELECT = """
    si.company_id, si.id_grupo, si.id_item, si.code, si.description, COALESCE(si.cost_price, 0),
    COALESCE(si.unit_id, 0), COALESCE(si.valor_und_compra, 0), COALESCE(si.und_min_utilizadas, 0),
    COALESCE(si.agrupar, 0), COALESCE(si.compras, 0), COALESCE(si.control_stock, 0),
    COALESCE(si.opcion_cambios, 0), COALESCE(si.unit_uso_id, 0), COALESCE(si.centro_produccion, 0),
    COALESCE(si.bodega, 0), COALESCE(si.insumo_cp, 0), si.fecha_vence, COALESCE(si.min_stock, 0)
"""

CATALOG_UPDATE = """
    iap.id_grupo           = si.id_grupo,
    iap.codigo_insumo      = si.code,
    iap.descripcion        = si.description,
    iap.costo              = COALESCE(si.cost_price, 0),
    iap.und_compra         = COALESCE(si.unit_id, 0),
    iap.valor_und_compra   = COALESCE(si.valor_und_compra, 0),
    iap.und_min_utilizadas = COALESCE(si.und_min_utilizadas, 0),
    iap.agrupar            = COALESCE(si.agrupar, 0),
    iap.compras            = COALESCE(si.compras, 0),
    iap.controlar          = COALESCE(si.control_stock, 0),
    iap.opcion_cambios     = COALESCE(si.opcion_cambios, 0),
    iap.und_uso            = COALESCE(si.unit_uso_id, 0),
    iap.centro_produccion  = COALESCE(si.centro_produccion, 0),
    iap.bodega             = COALESCE(si.bodega, 0),
    iap.insumo_cp          = COALESCE(si.insumo_cp, 0),
    iap.fecha_vence        = si.fecha_vence,
    iap.stock_minimo       = COALESCE(si.min_stock, 0)
"""

# Un insumo por id_item (si hubiera duplicados en el catálogo se toma el de menor id)
CATALOG_SOURCE = """
    (SELECT s.* FROM supply_items s
     JOIN (SELECT MIN(id) AS id FROM supply_items
           WHERE company_id = :cid AND id_item > 0 AND id_grupo > 0
           GROUP BY id_item) u ON u.id = s.id)
"""


async def upsert_stock_row(db: AsyncSession, cid: int, supply_id: int) -> None:
    """Refleja un insumo del catálogo en inventario_actual_porciones (alta/edición desde la web)."""
    await db.execute(text(f"""
        INSERT INTO inventario_actual_porciones
            (company_id, id_grupo, id_item, codigo_insumo, descripcion, costo,
             und_compra, valor_und_compra, und_min_utilizadas, agrupar,
             compras, controlar, opcion_cambios, und_uso, centro_produccion,
             bodega, insumo_cp, fecha_vence, stock_minimo, cantidad_actual, enviada_mysql)
        SELECT {CATALOG_SELECT}, 0, 0
        FROM supply_items si
        WHERE si.id = :sid AND si.company_id = :cid AND si.id_item > 0 AND si.id_grupo > 0
        ON DUPLICATE KEY UPDATE
            id_grupo=VALUES(id_grupo), codigo_insumo=VALUES(codigo_insumo),
            descripcion=VALUES(descripcion), costo=VALUES(costo), und_compra=VALUES(und_compra),
            valor_und_compra=VALUES(valor_und_compra), und_min_utilizadas=VALUES(und_min_utilizadas),
            agrupar=VALUES(agrupar), compras=VALUES(compras), controlar=VALUES(controlar),
            opcion_cambios=VALUES(opcion_cambios), und_uso=VALUES(und_uso),
            centro_produccion=VALUES(centro_produccion), bodega=VALUES(bodega),
            insumo_cp=VALUES(insumo_cp), fecha_vence=VALUES(fecha_vence),
            stock_minimo=VALUES(stock_minimo), enviada_mysql=0
    """), {"cid": cid, "sid": supply_id})
