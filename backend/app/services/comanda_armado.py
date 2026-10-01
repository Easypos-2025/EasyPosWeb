"""
Armado de platos en la comanda web — misma lógica y tablas del escritorio.

Al comandar un ítem:
  temp_plato_producto_parcial   → insumos a descontar = FIJOS (inventario_porciones_plato)
                                  + SELECCIONADOS (plato_armar_detalle o menú del día),
                                  con Id_Grupo/Id_Item reales del insumo, Posicion y
                                  Valor_Adicional_Armar. Cantidad es POR UNIDAD del plato.
  temp_novedades_plato_pedido   → registro de armado (Cod_Categoria=1, Id_Novedad=1,
                                  Novedad=' - OPCION - OPCION ') + novedades del catálogo
                                  (Cod_Categoria = categoría del plato) + novedad libre
                                  (Id_Novedad = 0).
  temp_detalle_comanda_parcial.Producto_Personalizado → SIEMPRE el nombre de lo que se vende.

Reglas del escritorio:
  - Plato de armado  = platos.Prioridad_Ofrecer = 1 (pos_dishes.offer_priority).
  - Categoría armado = plato_armar (pos_dish_assembly) cuya categoria_productos tenga
                       Porcentaje = 1 y Activa = 1 (pos_product_categories.percentage / is_active).
  - Insumos posibles = inventario_porciones.Armar_Plato = 1 y Agrupar = Cod_Categoria
                       (supply_items.armar_plato / agrupar) — se usan al configurar el plato y el menú.
Opciones de una categoría de armado:
  - Si el administrador armó el menú del día → menu_diario del día con Agrupar = categoría
    (pos_daily_menu.group_by; menu_id = Id_Menu, consecutivo del menú del día).
  - Si no → las configuradas en el plato (plato_armar_detalle / pos_dish_assembly_detail).
"""
import re
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

ARMADO_COD_CATEGORIA = 1
ARMADO_ID_NOVEDAD = 1
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_text(value: Optional[str], max_len: int) -> str:
    """Quita caracteres de control y recorta a la longitud de la columna."""
    return _CTRL.sub("", (value or "")).strip()[:max_len]


def armado_text(names: list) -> str:
    """Formato del escritorio: ' - DESMECHADA - POLLO DESMECHADO ' ('' → ' ')."""
    return "".join(f" - {n}" for n in names) + " "


def parse_armado_text(novedad: Optional[str]) -> list:
    return [p.strip() for p in (novedad or "").split(" - ") if p.strip()]


async def build_assembly(db: AsyncSession, cid: int, dish_id: int, today: str) -> list:
    """Categorías de armado del plato con sus opciones disponibles hoy. Solo si el plato es de
    armado (Prioridad_Ofrecer = 1) y solo categorías de armado activas (Porcentaje = 1, Activa = 1)."""
    es_armado = (await db.execute(text(
        "SELECT COALESCE(offer_priority, 0) FROM pos_dishes WHERE id = :did AND company_id = :cid"
    ), {"did": dish_id, "cid": cid})).scalar()
    if int(es_armado or 0) != 1:
        return []
    cats = (await db.execute(text("""
        SELECT da.category_code, da.max_choices, da.is_required, da.print_on_change_only,
               pc.name AS category_name
        FROM pos_dish_assembly da
        INNER JOIN pos_product_categories pc
                ON pc.id = da.category_code AND pc.company_id = da.company_id
               AND pc.percentage = 1 AND pc.is_active = 1
        WHERE da.dish_id = :did AND da.company_id = :cid AND da.is_active = 1
        ORDER BY da.category_code
    """), {"did": dish_id, "cid": cid})).mappings().all()
    if not cats:
        return []

    detail = (await db.execute(text("""
        SELECT dad.category_code, dad.position, dad.discount_qty, dad.supply_price, dad.is_default,
               si.id_grupo, si.posicion, si.description
        FROM pos_dish_assembly_detail dad
        LEFT JOIN supply_items si ON si.company_id = dad.company_id AND si.id_item = dad.position
        WHERE dad.dish_id = :did AND dad.company_id = :cid
        ORDER BY si.description
    """), {"did": dish_id, "cid": cid})).mappings().all()
    by_cat: dict = {}
    for d in detail:
        by_cat.setdefault(int(d["category_code"]), {})[int(d["position"])] = d

    codes = [int(c["category_code"]) for c in cats]
    ph = ", ".join(f":c{i}" for i in range(len(codes)))
    params = {"cid": cid, "today": today, **{f"c{i}": c for i, c in enumerate(codes)}}
    daily = (await db.execute(text(f"""
        SELECT dm.group_by, dm.item_id, dm.description, si.id_grupo, si.posicion
        FROM pos_daily_menu dm
        LEFT JOIN supply_items si ON si.company_id = dm.company_id AND si.id_item = dm.item_id
        WHERE dm.company_id = :cid AND dm.date = :today AND dm.group_by IN ({ph})
          AND COALESCE(dm.selected, 1) = 1
        ORDER BY dm.description
    """), params)).mappings().all()
    daily_by_cat: dict = {}
    for d in daily:
        daily_by_cat.setdefault(int(d["group_by"]), []).append(d)

    result = []
    for c in cats:
        cc = int(c["category_code"])
        conf = by_cat.get(cc, {})
        options = []
        if daily_by_cat.get(cc):
            for d in daily_by_cat[cc]:
                iid = int(d["item_id"])
                det = conf.get(iid)
                options.append({
                    "item_id":      iid,
                    "item_name":    d["description"] or (det["description"] if det else f"Insumo {iid}"),
                    "discount_qty": float(det["discount_qty"]) if det and det["discount_qty"] else 1.0,
                    "supply_price": float(det["supply_price"] or 0) if det else 0.0,
                    "is_default":   bool(det["is_default"]) if det else False,
                    "id_grupo":     int(d["id_grupo"] or 1),
                    "posicion":     int(d["posicion"] or iid),
                })
        else:
            for iid, det in conf.items():
                options.append({
                    "item_id":      iid,
                    "item_name":    det["description"] or f"Insumo {iid}",
                    "discount_qty": float(det["discount_qty"] or 1),
                    "supply_price": float(det["supply_price"] or 0),
                    "is_default":   bool(det["is_default"]),
                    "id_grupo":     int(det["id_grupo"] or 1),
                    "posicion":     int(det["posicion"] or iid),
                })
        result.append({
            "category_code":        cc,
            "category_name":        c["category_name"] or f"Categoría {cc}",
            "max_choices":          max(int(c["max_choices"] or 1), 1),
            "is_required":          bool(c["is_required"]),
            "print_on_change_only": bool(c["print_on_change_only"]),
            "daily_menu":           bool(daily_by_cat.get(cc)),
            "options":              options,
        })
    return result


async def fixed_products(db: AsyncSession, cid: int, dish_id: int) -> list:
    rows = (await db.execute(text("""
        SELECT ipp.id_grupo, ipp.id_item, ipp.porciones_a_desccontar, ipp.posicion, si.description
        FROM inventario_porciones_plato ipp
        LEFT JOIN supply_items si ON si.company_id = ipp.company_id AND si.id_item = ipp.id_item
        WHERE ipp.company_id = :cid AND ipp.id_plato = :did
    """), {"cid": cid, "did": dish_id})).mappings().all()
    return [{
        "id_grupo": int(r["id_grupo"]), "item_id": int(r["id_item"]),
        "quantity": float(r["porciones_a_desccontar"] or 0), "posicion": int(r["posicion"] or r["id_item"]),
        "description": r["description"],
    } for r in rows]


# ── Variantes (solo web): Personal / Dúo / Familiar… ─────────────────────────
# Toda opción de venta de un plato con variantes es una variante (precio propio). La receta
# de la variante solo ajusta la cantidad de los insumos fijos del plato y cada categoría de
# armado puede pedir una cantidad distinta de sabores según la variante.

async def dish_variants(db: AsyncSession, cid: int, dish_id: int) -> list:
    rows = (await db.execute(text("""
        SELECT id, name, price, COALESCE(is_default, 0) AS is_default
        FROM pos_dish_variants
        WHERE company_id = :cid AND dish_id = :did AND is_active = 1
        ORDER BY order_index, id
    """), {"cid": cid, "did": dish_id})).mappings().all()
    return [{"id": int(r["id"]), "name": r["name"], "price": int(r["price"] or 0),
             "is_default": bool(r["is_default"])} for r in rows]


async def variant_assembly(db: AsyncSession, cid: int, variant_id: int) -> dict:
    """{category_code: max_choices} de la variante (sobrescribe plato_armar.Cantidad_Elegir)."""
    rows = (await db.execute(text(
        "SELECT category_code, max_choices FROM pos_dish_variant_assembly WHERE company_id=:cid AND variant_id=:vid"
    ), {"cid": cid, "vid": variant_id})).all()
    return {int(r[0]): max(int(r[1] or 1), 1) for r in rows}


async def variant_fixed_products(db: AsyncSession, cid: int, dish_id: int, variant_id: int) -> list:
    """Insumos fijos del plato con las cantidades de la receta de la variante."""
    fixed = await fixed_products(db, cid, dish_id)
    over = {int(r[0]): float(r[1]) for r in (await db.execute(text(
        "SELECT id_item, porciones FROM pos_dish_variant_products WHERE company_id=:cid AND variant_id=:vid"
    ), {"cid": cid, "vid": variant_id})).all()}
    for f in fixed:
        if f["item_id"] in over:
            f["quantity"] = over[f["item_id"]]
    return fixed


async def variant_price(db: AsyncSession, cid: int, customer_id: int, variant: dict, dish_id: int) -> int:
    """Precio de la variante según las listas (cliente → Default → precio de la variante)."""
    from app.services import listas_precios
    return await listas_precios.precio(db, cid, int(customer_id or 0), dish_id, int(variant["id"]), int(variant["price"]))


async def client_price(db: AsyncSession, cid: int, customer_id: int, dish_id: int, default_price: int) -> int:
    """Precio del plato según las listas (cliente → Default → platos.Valor)."""
    from app.services import listas_precios
    return await listas_precios.precio(db, cid, int(customer_id or 0), dish_id, 0, int(default_price or 0))


async def write_item_products(db_temp: AsyncSession, cid: int, order_number: str, fecha, dish_id: int,
                              item: int, fixed: list, selected: list) -> None:
    """temp_plato_producto_parcial: fijos + seleccionados (se suman si el insumo coincide)."""
    rows: dict = {}
    for f in fixed:
        k = (f["id_grupo"], f["item_id"])
        rows[k] = {"qty": f["quantity"], "pos": f["posicion"], "valor": 0.0}
    for s in selected:
        k = (s["id_grupo"], s["item_id"])
        if k in rows:
            rows[k]["qty"] += s["discount_qty"]
            rows[k]["valor"] += s["supply_price"]
        else:
            rows[k] = {"qty": s["discount_qty"], "pos": s["posicion"], "valor": s["supply_price"]}
    for (gid, iid), r in rows.items():
        await db_temp.execute(text("""
            INSERT INTO temp_plato_producto_parcial
                (company_id, Nro_Pedido, Fecha, Nro_Factura, Id_Plato, Item, Id_Grupo, Id_Item,
                 Cantidad, Posicion, Valor_Adicional_Armar, updated_at)
            VALUES (:cid, :on, :fecha, '0', :did, :item, :gid, :iid, :qty, :pos, :valor, NOW())
            ON DUPLICATE KEY UPDATE Cantidad = VALUES(Cantidad), Posicion = VALUES(Posicion),
                                    Valor_Adicional_Armar = VALUES(Valor_Adicional_Armar)
        """), {"cid": cid, "on": order_number, "fecha": fecha, "did": dish_id, "item": item,
               "gid": gid, "iid": iid, "qty": r["qty"], "pos": r["pos"], "valor": r["valor"]})


async def _insert_novedad(db_temp: AsyncSession, cid: int, order_number: str, item: int,
                          cod: int, id_nov: int, texto: str) -> None:
    # La llave incluye (Cod_Categoria, Id_Novedad): si coincide, se concatena en vez de perderse
    await db_temp.execute(text("""
        INSERT INTO temp_novedades_plato_pedido
            (company_id, Id_Consecutivo, Nro_Pedido, Item, Depende, Cod_Categoria, Id_Novedad, Novedad, updated_at)
        VALUES (:cid, 0, :on, :item, :item, :cod, :idn, :txt, NOW())
        ON DUPLICATE KEY UPDATE Novedad = CONCAT(Novedad, ' | ', VALUES(Novedad))
    """), {"cid": cid, "on": order_number, "item": item, "cod": cod, "idn": id_nov, "txt": texto})


async def write_item_armado(db_temp: AsyncSession, cid: int, order_number: str, item: int,
                            has_assembly: bool, selected: list) -> None:
    if has_assembly:
        await _insert_novedad(db_temp, cid, order_number, item, ARMADO_COD_CATEGORIA, ARMADO_ID_NOVEDAD,
                              armado_text([s["item_name"] for s in selected]))


async def write_item_notes(db: AsyncSession, db_temp: AsyncSession, cid: int, order_number: str,
                           item: int, dish_category: int, notes: Optional[str]) -> None:
    """Novedades del catálogo (por nombre dentro de la categoría del plato) + libres (Id_Novedad=0)."""
    await db_temp.execute(text("""
        DELETE FROM temp_novedades_plato_pedido
        WHERE company_id = :cid AND Nro_Pedido = :on AND Item = :item
          AND NOT (Cod_Categoria = :ac AND Id_Novedad = :an)
    """), {"cid": cid, "on": order_number, "item": item, "ac": ARMADO_COD_CATEGORIA, "an": ARMADO_ID_NOVEDAD})
    parts = [clean_text(p, 250) for p in (notes or "").split("|")]
    parts = [p for p in parts if p]
    if not parts:
        return
    catalog = {r["name"].strip().upper(): int(r["id_novedad"]) for r in (await db.execute(text(
        "SELECT name, id_novedad FROM pos_dish_note_categories WHERE company_id = :cid AND cod_categoria = :cc"
    ), {"cid": cid, "cc": dish_category or 0})).mappings().all() if r["name"]}
    libres = []
    for p in parts:
        idn = catalog.get(p.upper())
        if idn:
            await _insert_novedad(db_temp, cid, order_number, item, dish_category or 0, idn, p + " ")
        else:
            libres.append(p)
    if libres:
        await _insert_novedad(db_temp, cid, order_number, item, dish_category or 0, 0, " | ".join(libres) + " ")


async def delete_item_temp(db_temp: AsyncSession, cid: int, order_number: str, dish_id: int, item: int) -> None:
    await db_temp.execute(text("""
        DELETE FROM temp_plato_producto_parcial
        WHERE Nro_Pedido = :on AND Id_Plato = :did AND Item = :item AND company_id = :cid
    """), {"on": order_number, "did": dish_id, "item": item, "cid": cid})
    await db_temp.execute(text("""
        DELETE FROM temp_novedades_plato_pedido
        WHERE Nro_Pedido = :on AND Item = :item AND company_id = :cid
    """), {"on": order_number, "item": item, "cid": cid})


async def armado_names(db_temp: AsyncSession, cid: int, order_numbers: list) -> dict:
    """{(Nro_Pedido, Item): [nombres elegidos]} desde el registro de armado (1/1)."""
    if not order_numbers:
        return {}
    ph = ", ".join(f":o{i}" for i in range(len(order_numbers)))
    rows = (await db_temp.execute(text(f"""
        SELECT Nro_Pedido, Item, Novedad FROM temp_novedades_plato_pedido
        WHERE company_id = :cid AND Nro_Pedido IN ({ph})
          AND Cod_Categoria = :ac AND Id_Novedad = :an
    """), {"cid": cid, "ac": ARMADO_COD_CATEGORIA, "an": ARMADO_ID_NOVEDAD,
           **{f"o{i}": o for i, o in enumerate(order_numbers)}})).mappings().all()
    return {(r["Nro_Pedido"], int(r["Item"])): parse_armado_text(r["Novedad"]) for r in rows}


async def assembly_structured(db: AsyncSession, db_temp: AsyncSession, cid: int, order_number: str,
                              dish_ids: list) -> dict:
    """{item: [{category_code, item_id, item_name}]} — selecciones de armado de un pedido
    (excluye insumos fijos) para mostrar y agrupar en la comanda."""
    if not dish_ids:
        return {}
    rows = (await db_temp.execute(text("""
        SELECT Id_Plato, Item, Id_Item FROM temp_plato_producto_parcial
        WHERE company_id = :cid AND Nro_Pedido = :on
    """), {"cid": cid, "on": order_number})).mappings().all()
    if not rows:
        return {}
    ids = ",".join(str(int(d)) for d in dish_ids)
    conf = (await db.execute(text(f"""
        SELECT dad.dish_id, dad.position, dad.category_code, si.description
        FROM pos_dish_assembly_detail dad
        LEFT JOIN supply_items si ON si.company_id = dad.company_id AND si.id_item = dad.position
        WHERE dad.company_id = :cid AND dad.dish_id IN ({ids})
    """), {"cid": cid})).mappings().all()
    cmap = {(int(r["dish_id"]), int(r["position"])): (int(r["category_code"]), r["description"]) for r in conf}
    daily = (await db.execute(text(f"""
        SELECT da.dish_id, dm.item_id, dm.group_by, dm.description
        FROM pos_dish_assembly da
        JOIN pos_daily_menu dm ON dm.company_id = da.company_id AND dm.group_by = da.category_code
        WHERE da.company_id = :cid AND da.dish_id IN ({ids})
    """), {"cid": cid})).mappings().all()
    for r in daily:
        cmap.setdefault((int(r["dish_id"]), int(r["item_id"])), (int(r["group_by"]), r["description"]))
    out: dict = {}
    for r in rows:
        hit = cmap.get((int(r["Id_Plato"]), int(r["Id_Item"])))
        if hit:
            out.setdefault(int(r["Item"]), []).append(
                {"category_code": hit[0], "item_id": int(r["Id_Item"]), "item_name": hit[1] or f"Insumo {r['Id_Item']}"})
    for v in out.values():
        v.sort(key=lambda x: (x["category_code"], x["item_id"]))
    return out
