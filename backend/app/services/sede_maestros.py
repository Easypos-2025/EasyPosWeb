"""
S3 — Tablas maestras de la web hacia el escritorio (empresas con Agente Local).

NO es automático: el admin pulsa "Sincronizar con la web" en el panel del agente (o desde el
escritorio). La web manda (decisión del usuario 2026-10-10).

  Pendiente = lo que la web cambió y el escritorio aún no tiene:
    · platos (pos_dishes.synced = 0): creados, editados o desactivados (active = 1 es inactivo, VB6),
      con sus impresoras (pos_item_printers).
    · datos de la sede (configuracion_sede.synced = 0).

  Plato creado en la web en una empresa con escritorio (opción C): nace con id PROVISIONAL (desde
  ID_PROVISIONAL) e INACTIVO, para que no se venda. Al sincronizar, el agente lo crea en el escritorio
  con el siguiente Id_Plato real; la web lo renumera en sus tablas de catálogo y lo activa.

  La web solo marca synced = 1 si el registro no cambió después de que el agente lo bajó (updated_at).
"""
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

ID_PROVISIONAL = 900_000_000
MAX_PLATOS = 500

# pos_dishes → platos (escritorio)
COLUMNAS_PLATO = {
    "name": "Nombre", "product_code": "Codigo_Producto", "price": "Valor", "preparation_time": "Tiempo",
    "active": "Activo", "category_id": "Cod_Categoria", "procedure": "Procedimiento",
    "description": "Descripcion_Plato", "comment": "Comentario", "extra_print": "Impresion_Extra",
    "pre_preparation": "Preparacion_Previa", "offer": "Ofrecer", "offer_priority": "Prioridad_Ofrecer",
    "tax": "Impuesto", "wholesale_price": "Precio_x_Mayor", "product_cost": "Costo_Producto",
    "minimum_stock": "Stock_Minimo", "ask_sale_price": "Pedir_Valor_Venta_Producto",
    "ask_product_description": "Pedir_Descripcion_Producto",
}

# Tablas de catálogo de la web que guardan el id del plato (se renumeran al asignarle el Id_Plato real).
# Las de ventas no: un plato provisional está inactivo y no se puede vender.
REFERENCIAS_PLATO = (
    ("pos_customer_price_list", "id_producto"),
    ("inventario_porciones_plato", "id_plato"),
    ("pos_dish_products", "dish_id"),
    ("pos_dish_variants", "dish_id"),
    ("pos_dish_assembly", "dish_id"),
    ("pos_dish_assembly_detail", "dish_id"),
    ("pos_item_modifiers", "item_id"),
    ("pos_item_printers", "item_id"),
)

CAMPOS_SEDE = ("Nombre_Almacen", "Nombre_Autorizado", "Nit_Autorizado", "Razon_Social", "Direccion_Sede",
               "Mail_Uno", "Mail_Dos", "Nombre_Logo_Empresa")


async def siguiente_id_plato(db: AsyncSession, cid: int, con_sede: bool) -> int:
    """Id para un plato nuevo de la web. Con escritorio: provisional (lo reemplaza el Id_Plato real)."""
    if con_sede:
        maximo = (await db.execute(text(
            "SELECT COALESCE(MAX(id), 0) FROM pos_dishes WHERE company_id = :c AND id >= :p FOR UPDATE"
        ), {"c": cid, "p": ID_PROVISIONAL})).scalar() or 0
        return max(int(maximo) + 1, ID_PROVISIONAL)
    maximo = (await db.execute(text(
        "SELECT COALESCE(MAX(id), 0) FROM pos_dishes WHERE company_id = :c AND id < :p FOR UPDATE"
    ), {"c": cid, "p": ID_PROVISIONAL})).scalar() or 0
    return int(maximo) + 1


def es_provisional(id_plato: int) -> bool:
    return int(id_plato) >= ID_PROVISIONAL


def _iso(v) -> Optional[str]:
    return v.isoformat(sep=" ", timespec="seconds") if v else None


async def pendientes(db: AsyncSession, cid: int) -> dict:
    cols = ", ".join(f"`{c}`" for c in COLUMNAS_PLATO)
    platos = (await db.execute(text(f"""
        SELECT id, {cols}, updated_at FROM pos_dishes
        WHERE company_id = :c AND synced = 0 ORDER BY id LIMIT :n
    """), {"c": cid, "n": MAX_PLATOS})).mappings().all()
    impresoras: dict = {}
    if platos:
        ids = [int(p["id"]) for p in platos]
        ph = ", ".join(f":i{n}" for n in range(len(ids)))
        for r in (await db.execute(text(f"""
            SELECT item_id, printer_id, COALESCE(print_copies, 1) AS copias FROM pos_item_printers
            WHERE company_id = :c AND item_id IN ({ph})
        """), {"c": cid, **{f"i{n}": v for n, v in enumerate(ids)}})).mappings().all():
            impresoras.setdefault(int(r["item_id"]), []).append({"id": int(r["printer_id"]), "copias": int(r["copias"] or 1)})
    max_web = (await db.execute(text(
        "SELECT COALESCE(MAX(id), 0) FROM pos_dishes WHERE company_id = :c AND id < :p"
    ), {"c": cid, "p": ID_PROVISIONAL})).scalar() or 0
    sede = (await db.execute(text(f"""
        SELECT {', '.join(CAMPOS_SEDE)}, updated_at FROM configuracion_sede WHERE company_id = :c AND synced = 0
    """), {"c": cid})).mappings().first()
    return {
        "max_id_web": int(max_web),
        "platos": [{
            "id": int(p["id"]), "provisional": es_provisional(p["id"]), "actualizado": _iso(p["updated_at"]),
            "datos": {COLUMNAS_PLATO[k]: (float(p[k]) if k in ("tax", "wholesale_price", "product_cost", "minimum_stock")
                                          and p[k] is not None else p[k]) for k in COLUMNAS_PLATO},
            "impresoras": impresoras.get(int(p["id"]), [])} for p in platos],
        "sede": ({**{k: sede[k] for k in CAMPOS_SEDE}, "actualizado": _iso(sede["updated_at"])} if sede else None),
    }


async def confirmar(db: AsyncSession, cid: int, platos: list, sede_actualizado: Optional[str]) -> dict:
    """El agente aplicó los cambios en el escritorio. Renumera los provisionales con su Id_Plato real
    (y los activa) y marca synced = 1 lo que no cambió desde que se bajó. No hace commit."""
    renumerados, confirmados, errores = [], [], []
    for p in platos:
        id_web, id_real = int(p["id_web"]), int(p["id_real"])
        visto = p.get("actualizado")
        actual = id_web
        if id_web != id_real:
            if not es_provisional(id_web) or es_provisional(id_real) or id_real <= 0:
                errores.append({"id_web": id_web, "error": "Renumeración no válida"})
                continue
            existe = (await db.execute(text("SELECT 1 FROM pos_dishes WHERE company_id = :c AND id = :i"),
                                       {"c": cid, "i": id_real})).scalar()
            if existe:
                errores.append({"id_web": id_web, "error": f"El Id_Plato {id_real} ya existe en la web"})
                continue
            if not (await db.execute(text("SELECT 1 FROM pos_dishes WHERE company_id = :c AND id = :i"),
                                     {"c": cid, "i": id_web})).scalar():
                continue
            # Se activa (ya existe en el escritorio). synced se evalúa con el updated_at anterior (la columna
            # se actualiza sola al final de la sentencia).
            await db.execute(text("""
                UPDATE pos_dishes SET id = :r, active = 0,
                       synced = IF(:v IS NULL OR updated_at <= :v, 1, 0)
                WHERE company_id = :c AND id = :w
            """), {"r": id_real, "c": cid, "w": id_web, "v": visto})
            for tabla, col in REFERENCIAS_PLATO:
                await db.execute(text(f"UPDATE {tabla} SET {col} = :r WHERE company_id = :c AND {col} = :w"),
                                 {"r": id_real, "c": cid, "w": id_web})
            renumerados.append({"id_web": id_web, "id_real": id_real})
            confirmados.append(id_real)
            continue
        n = (await db.execute(text("""
            UPDATE pos_dishes SET synced = 1
            WHERE company_id = :c AND id = :i AND (:v IS NULL OR updated_at <= :v)
        """), {"c": cid, "i": actual, "v": visto})).rowcount
        if n:
            confirmados.append(actual)
    sede_ok = False
    if sede_actualizado is not None:
        sede_ok = bool((await db.execute(text("""
            UPDATE configuracion_sede SET synced = 1 WHERE company_id = :c AND updated_at <= :v
        """), {"c": cid, "v": sede_actualizado})).rowcount)
    return {"renumerados": renumerados, "confirmados": confirmados, "errores": errores, "sede": sede_ok}
