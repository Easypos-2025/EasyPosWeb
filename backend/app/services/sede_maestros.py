"""
S3 — Tablas maestras de la web hacia el escritorio (empresas con Agente Local).

NO es automático: el admin pulsa "Sincronizar con la web" en el panel del agente (o desde el
escritorio). La web manda (decisión del usuario 2026-10-10).

  Pendiente = lo que la web cambió y el escritorio aún no tiene (synced = 0, o enviada_mysql = 0 en clientes).

  Catálogos con número propio (ENTIDADES): formas de medida, categorías de productos y de platos,
  proveedores, insumos (con sus formas de medida y proveedores) y clientes. Más los platos (con
  impresoras, receta, armado y presentaciones, que viajan con el plato), las listas de precios y los
  datos de la sede.

  Opción C (id provisional): lo que la web crea en una empresa con escritorio nace con número
  PROVISIONAL (desde ID_PROVISIONAL); el plato, además, inactivo. Al sincronizar, el agente lo crea en
  el escritorio con el siguiente número real y la web lo renumera en todas sus tablas (REFERENCIAS).

  La web solo marca "al día" lo que no cambió después de que el agente lo bajó (updated_at).
  Variantes (tamaños): no existen en el escritorio; el pedido baja ya resuelto (plato, armado, insumos).
"""
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

ID_PROVISIONAL = 900_000_000
MAX_FILAS = 500

# ───────────────────────────── catálogos con número propio ─────────────────────────────
# columnas: web → escritorio. refs: columna del escritorio → entidad a la que apunta (el agente
# traduce los provisionales). referencias: (tabla web, columna) a renumerar cuando el escritorio
# asigna el número real.
ENTIDADES = {
    "forma_medida": {
        "tabla": "pos_measure_forms", "llave": "id", "pendiente": "synced = 0", "al_dia": "synced = 1",
        "escritorio": "forma_medida", "llave_escritorio": "Id_Forma_Medida",
        "columnas": {"name": "Descripcion", "is_active": "Activa"},
        "referencias": [("supply_items", "unit_id"), ("supply_items", "unit_uso_id"), ("pos_dish_products", "measure_id"),
                        ("insumos_forma_medida", "id_forma_medida"), ("insumos_proveedor", "id_forma_medida"),
                        ("pos_customer_price_list", "id_presentacion")],
    },
    "categoria_productos": {
        "tabla": "pos_product_categories", "llave": "id", "pendiente": "synced = 0", "al_dia": "synced = 1",
        "escritorio": "categoria_productos", "llave_escritorio": "Cod_Categoria",
        "columnas": {"name": "Nombre", "percentage": "Porcentaje", "is_active": "Activa",
                     "require_selection": "Exgir_Seleccion", "print_assembly_changes_only": "Imprimir_Armar_Solo_Cambio"},
        "referencias": [("pos_dish_assembly", "category_code"), ("pos_dish_assembly_detail", "category_code"),
                        ("supply_items", "agrupar")],
    },
    "categoria_platos": {
        "tabla": "pos_dish_categories", "llave": "id", "pendiente": "synced = 0", "al_dia": "synced = 1",
        "escritorio": "categoria_platos", "llave_escritorio": "Cod_Categoria",
        "columnas": {"parent_category_id": "Categoria", "name": "Nombre", "photo_name": "Nombre_foto",
                     "percentage": "Porcentaje", "shift": "Turno", "monday": "Lunes", "tuesday": "Martes",
                     "wednesday": "Miercoles", "thursday": "Jueves", "friday": "Viernes", "saturday": "Sabado",
                     "sunday": "Domingo", "is_active": "Activa"},
        "referencias": [("pos_dishes", "category_id")],
    },
    "proveedor": {
        "tabla": "suppliers", "llave": "id_proveedor", "pendiente": "synced = 0", "al_dia": "synced = 1",
        "escritorio": "proveedores", "llave_escritorio": "Id_Proveedor",
        "columnas": {"nit": "Nit", "name": "Empresa", "email": "Mail_Empresa", "address": "Direccion",
                     "phone": "Telefono_Fijo", "telefono_celular": "Telefono_Celular", "notes": "Observaciones",
                     "is_active": "Activo"},
        "referencias": [("insumos_proveedor", "id_proveedor"), ("pos_dish_products", "supplier_id")],
    },
    "insumo": {
        "tabla": "supply_items", "llave": "id_item", "pendiente": "synced = 0", "al_dia": "synced = 1",
        "escritorio": "inventario_porciones", "llave_escritorio": "Id_Item",
        "columnas": {"code": "Codigo_Insumo", "id_grupo": "Id_Grupo", "description": "Descripcion", "cost_price": "Costo",
                     "unit_id": "Und_Compra", "valor_und_compra": "Valor_Und_Compra",
                     "und_min_utilizadas": "Und_Min_Utilizadas", "posicion": "Posicion", "agrupar": "Agrupar",
                     "compras": "Compras", "control_stock": "Controlar", "opcion_cambios": "Opcion_Cambios",
                     "unit_uso_id": "Und_Uso", "centro_produccion": "Centro_Produccion",
                     "tipo_und_minima": "Tipo_Und_Minima", "cant_und_minimas": "Cant_Und_Minimas", "bodega": "Bodega",
                     "producto_preparado": "Producto_Preparado", "id_preparacion": "Id_preparacion",
                     "preparado_en_sede": "Preparado_En_Sede", "descargar_en_venta": "Descargar_En_Venta",
                     "armar_plato": "Armar_Plato", "cantidad_armar": "Cantidad_Armar", "id_insumo": "Id_Insumo",
                     "insumo_cp": "Insumo_Cp", "waste_pct": "Porcentaje_Merma", "marca_referencia": "Marca_Referencia",
                     "fecha_vence": "Fecha_Vence", "min_stock": "Stock_MInimo"},
        "refs": {"Und_Compra": "forma_medida", "Und_Uso": "forma_medida", "Agrupar": "categoria_productos"},
        "referencias": [("inventario_porciones_plato", "id_item"), ("pos_dish_assembly_detail", "item"),
                        ("insumos_forma_medida", "id_insumo"), ("insumos_proveedor", "id_insumo"),
                        ("inventario_actual_porciones", "id_item"), ("supply_items", "posicion"),
                        ("supply_items", "id_insumo"),
                        # Posicion del insumo (en uno nuevo es el mismo número): armado y receta la usan
                        ("pos_dish_assembly_detail", "position"), ("inventario_porciones_plato", "posicion")],
        "hijos": {
            "insumos_forma_medida": {"tabla": "insumos_forma_medida", "por": "id_insumo", "escritorio": "insumos_forma_medida",
                                     "llave_hijo": "Id_Insumo",
                                     "columnas": {"id_insumo": "Id_Insumo", "id_forma_medida": "Id_Forma_Medida",
                                                  "cant_unidades_minimas": "Cant_Unidades_Minimas"},
                                     "refs": {"Id_Insumo": "insumo", "Id_Forma_Medida": "forma_medida"}},
            "insumos_proveedor": {"tabla": "insumos_proveedor", "por": "id_insumo", "escritorio": "insumos_proveedor",
                                  "llave_hijo": "Id_Insumo",
                                  "columnas": {"id_proveedor": "Id_Proveedor", "id_insumo": "Id_Insumo",
                                               "fecha_inicial_negociacion": "Fecha_Inicial_Negociacion",
                                               "fecha_final_negociacion": "Fecha_Final_Negociacion",
                                               "precio_pactado": "Precio_Pactado", "id_forma_medida": "Id_Forma_Medida",
                                               "nombre_forma_medida": "Nombre_Forma_Medida", "observacion": "Observacion"},
                                  "refs": {"Id_Insumo": "insumo", "Id_Proveedor": "proveedor", "Id_Forma_Medida": "forma_medida"}},
        },
    },
    "cliente": {
        "tabla": "clientes", "llave": "id_cliente", "pendiente": "enviada_mysql = 0", "al_dia": "enviada_mysql = 1",
        "escritorio": "clientes", "llave_escritorio": "Id_Cliente",
        "columnas": {"cedula": "cedula", "nombres": "nombres", "apellidos": "Apellidos", "direccion": "direccion",
                     "telefono": "telefono", "barrio": "Barrio", "mail": "Mail", "dia_cumple": "Dia_Cumple",
                     "mes_cumple": "Mes_Cumple", "edad": "Edad", "ocupacion": "Ocupacion", "porc_descuento": "Porc_Descuento",
                     "observaciones": "Observaciones", "fecha_aniversario": "Fecha_Aniversario", "fecha_grado": "Fecha_Grado",
                     "empresa": "Empresa", "id_klob": "Id_Klob", "tarjeta_fiel": "Tarjeta_Fiel", "cod_barrio": "Cod_Barrio",
                     "id_sede": "Id_Sede", "referencia": "Referencia"},
        "referencias": [("pos_customer_price_list", "id_cliente"), ("pos_customer_price_list_header", "id_cliente"),
                        ("pos_sede_lotes", "id_cliente")],
        "referencias_temp": [("temp_comanda", "Id_Cliente")],      # datatemppos de la web (pedidos abiertos)
    },
}
ORDEN = ("forma_medida", "categoria_productos", "categoria_platos", "proveedor", "insumo", "cliente")

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
REFS_PLATO = {"Cod_Categoria": "categoria_platos"}

# Lo que viaja con el plato (se reemplaza en el escritorio cuando la web tiene al menos una fila)
HIJOS_PLATO = {
    "receta": {"tabla": "inventario_porciones_plato", "por": "id_plato", "escritorio": "inventario_porciones_plato",
               "llave_hijo": "Id_Plato",
               "columnas": {"id_grupo": "Id_Grupo", "id_item": "Id_Item", "cantidad": "Cantidad", "unidad_minima": "Unidad_Minima",
                            "porciones_a_desccontar": "Porciones_A_Desccontar", "posicion": "Posicion",
                            "opcion_cambiar": "Opcion_Cambiar"},
               "refs": {"Id_Item": "insumo", "Id_Grupo": "categoria_productos", "Posicion": "insumo"}},
    "armado": {"tabla": "pos_dish_assembly", "por": "dish_id", "escritorio": "plato_armar", "llave_hijo": "Id_Plato",
               "columnas": {"category_code": "Cod_Categoria", "max_choices": "Cantidad_Elegir", "is_active": "Activa",
                            "is_required": "Exgir_Seleccion", "print_on_change_only": "Imprimir_Armar_Solo_Cambio"},
               "refs": {"Cod_Categoria": "categoria_productos"}},
    "armado_detalle": {"tabla": "pos_dish_assembly_detail", "por": "dish_id", "escritorio": "plato_armar_detalle",
                       "llave_hijo": "Id_Plato",
                       "columnas": {"category_code": "Cod_Categoria", "item": "Item", "position": "Posicion",
                                    "supply_price": "Precio_Insumo", "discount_qty": "Cantidad_Descontar",
                                    "is_default": "Por_Default"},
                       "refs": {"Cod_Categoria": "categoria_productos", "Item": "insumo", "Posicion": "insumo"}},
    "presentaciones": {"tabla": "pos_dish_products", "por": "dish_id", "escritorio": "plato_producto", "llave_hijo": "Id_Plato",
                       "columnas": {"measure_id": "Id_Forma_Medida", "minimum_units": "Unidades_Minimas",
                                    "presentation_value": "Valor_Presentacion", "description": "Descripcion",
                                    "active": "Activo", "supplier_id": "id_proveedor"},
                       "refs": {"Id_Forma_Medida": "forma_medida", "id_proveedor": "proveedor"}},
}

# Tablas de catálogo de la web que guardan el id del plato (se renumeran al asignarle el Id_Plato real).
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

COLUMNAS_LISTA = {"id_lista": "id_lista", "id_cliente": "Id_Cliente", "id_producto": "Id_Producto",
                  "id_presentacion": "Id_Presentacion", "precio_producto": "Precio_Producto", "fecha": "Fecha",
                  "activa": "Activa"}
REFS_LISTA = {"Id_Cliente": "cliente", "Id_Producto": "plato", "Id_Presentacion": "forma_medida"}
COLUMNAS_LISTA_CAB = {"id_lista": "id_lista", "id_cliente": "Id_Cliente", "nombre": "Nombre", "fecha": "Fecha",
                      "activa": "Activa", "usuario": "Usuario", "observacion": "Observacion"}

CAMPOS_SEDE = ("Nombre_Almacen", "Nombre_Autorizado", "Nit_Autorizado", "Razon_Social", "Direccion_Sede",
               "Mail_Uno", "Mail_Dos", "Nombre_Logo_Empresa")


# ───────────────────────────── numeración en la web ─────────────────────────────

async def siguiente_id(db: AsyncSession, tabla: str, columna: str, cid: int, con_sede: bool) -> int:
    """Número para un registro nuevo de la web. Con escritorio: provisional (lo reemplaza el real)."""
    if con_sede:
        maximo = (await db.execute(text(
            f"SELECT COALESCE(MAX({columna}), 0) FROM {tabla} WHERE company_id = :c AND {columna} >= :p FOR UPDATE"
        ), {"c": cid, "p": ID_PROVISIONAL})).scalar() or 0
        return max(int(maximo) + 1, ID_PROVISIONAL)
    maximo = (await db.execute(text(
        f"SELECT COALESCE(MAX({columna}), 0) FROM {tabla} WHERE company_id = :c AND {columna} < :p FOR UPDATE"
    ), {"c": cid, "p": ID_PROVISIONAL})).scalar() or 0
    return int(maximo) + 1


async def siguiente_id_plato(db: AsyncSession, cid: int, con_sede: bool) -> int:
    return await siguiente_id(db, "pos_dishes", "id", cid, con_sede)


def es_provisional(valor) -> bool:
    try:
        return int(valor) >= ID_PROVISIONAL
    except (TypeError, ValueError):
        return False


def _iso(v) -> Optional[str]:
    return v.isoformat(sep=" ", timespec="seconds") if v else None


def _valor(v):
    if hasattr(v, "isoformat"):
        return v.isoformat()
    if v is not None and type(v).__name__ == "Decimal":
        return float(v)
    return v


def _datos(fila, columnas: dict) -> dict:
    return {des: _valor(fila[web]) for web, des in columnas.items()}


async def _hijos(db: AsyncSession, cid: int, spec: dict, ids: list) -> dict:
    if not ids:
        return {}
    ph = ", ".join(f":i{n}" for n in range(len(ids)))
    cols = ", ".join([spec["por"]] + [c for c in spec["columnas"] if c != spec["por"]])
    out: dict = {}
    for r in (await db.execute(text(
        f"SELECT {cols} FROM {spec['tabla']} WHERE company_id = :c AND {spec['por']} IN ({ph})"
    ), {"c": cid, **{f"i{n}": v for n, v in enumerate(ids)}})).mappings().all():
        out.setdefault(int(r[spec["por"]]), []).append(_datos(r, spec["columnas"]))
    return out


# ───────────────────────────── lo que baja ─────────────────────────────

async def pendientes(db: AsyncSession, cid: int) -> dict:
    entidades, max_ids = {}, {}
    for nombre in ORDEN:
        e = ENTIDADES[nombre]
        cols = ", ".join(f"`{c}`" for c in e["columnas"] if c != e["llave"])
        filas = (await db.execute(text(f"""
            SELECT {e['llave']} AS llave, {cols}, updated_at FROM {e['tabla']}
            WHERE company_id = :c AND {e['pendiente']} AND {e['llave']} IS NOT NULL AND {e['llave']} > 0
            ORDER BY {e['llave']} LIMIT :n
        """), {"c": cid, "n": MAX_FILAS})).mappings().all()
        hijos = {h: await _hijos(db, cid, s, [int(f["llave"]) for f in filas]) for h, s in e.get("hijos", {}).items()}
        entidades[nombre] = [{
            "id": int(f["llave"]), "provisional": es_provisional(f["llave"]), "actualizado": _iso(f["updated_at"]),
            "datos": {des: _valor(f[web]) for web, des in e["columnas"].items() if web != e["llave"]},
            "hijos": {h: hijos[h].get(int(f["llave"]), []) for h in hijos}} for f in filas]
        max_ids[nombre] = int((await db.execute(text(
            f"SELECT COALESCE(MAX({e['llave']}), 0) FROM {e['tabla']} WHERE company_id = :c AND {e['llave']} < :p"
        ), {"c": cid, "p": ID_PROVISIONAL})).scalar() or 0)

    cols = ", ".join(f"`{c}`" for c in COLUMNAS_PLATO)
    platos = (await db.execute(text(f"""
        SELECT id, {cols}, updated_at FROM pos_dishes
        WHERE company_id = :c AND synced = 0 ORDER BY id LIMIT :n
    """), {"c": cid, "n": MAX_FILAS})).mappings().all()
    ids = [int(p["id"]) for p in platos]
    impresoras: dict = {}
    if ids:
        ph = ", ".join(f":i{n}" for n in range(len(ids)))
        for r in (await db.execute(text(f"""
            SELECT item_id, printer_id, COALESCE(print_copies, 1) AS copias FROM pos_item_printers
            WHERE company_id = :c AND item_id IN ({ph})
        """), {"c": cid, **{f"i{n}": v for n, v in enumerate(ids)}})).mappings().all():
            impresoras.setdefault(int(r["item_id"]), []).append({"id": int(r["printer_id"]), "copias": int(r["copias"] or 1)})
    hijos_plato = {h: await _hijos(db, cid, s, ids) for h, s in HIJOS_PLATO.items()}
    max_ids["plato"] = int((await db.execute(text(
        "SELECT COALESCE(MAX(id), 0) FROM pos_dishes WHERE company_id = :c AND id < :p"
    ), {"c": cid, "p": ID_PROVISIONAL})).scalar() or 0)

    listas = (await db.execute(text(f"""
        SELECT id, {', '.join(COLUMNAS_LISTA)}, updated_at FROM pos_customer_price_list
        WHERE company_id = :c AND synced = 0 ORDER BY id LIMIT 2000
    """), {"c": cid})).mappings().all()
    cabeceras = (await db.execute(text(f"""
        SELECT id, {', '.join(COLUMNAS_LISTA_CAB)}, updated_at FROM pos_customer_price_list_header
        WHERE company_id = :c AND synced = 0 ORDER BY id LIMIT 200
    """), {"c": cid})).mappings().all()

    sede = (await db.execute(text(f"""
        SELECT {', '.join(CAMPOS_SEDE)}, updated_at FROM configuracion_sede WHERE company_id = :c AND synced = 0
    """), {"c": cid})).mappings().first()
    return {
        "max_id_web": max_ids["plato"],              # compatibilidad con agentes anteriores
        "max_ids": max_ids,
        "entidades": entidades,
        "platos": [{
            "id": int(p["id"]), "provisional": es_provisional(p["id"]), "actualizado": _iso(p["updated_at"]),
            "datos": {COLUMNAS_PLATO[k]: _valor(p[k]) for k in COLUMNAS_PLATO},
            "impresoras": impresoras.get(int(p["id"]), []),
            "hijos": {h: hijos_plato[h].get(int(p["id"]), []) for h in HIJOS_PLATO}} for p in platos],
        "listas": [{"id": int(r["id"]), "actualizado": _iso(r["updated_at"]), "datos": _datos(r, COLUMNAS_LISTA)} for r in listas],
        "listas_cabecera": [{"id": int(r["id"]), "actualizado": _iso(r["updated_at"]), "datos": _datos(r, COLUMNAS_LISTA_CAB)}
                            for r in cabeceras],
        "sede": ({**{k: sede[k] for k in CAMPOS_SEDE}, "actualizado": _iso(sede["updated_at"])} if sede else None),
    }


# ───────────────────────────── confirmación del agente ─────────────────────────────

async def _renumerar(db: AsyncSession, cid: int, tabla: str, llave: str, referencias, id_web: int, id_real: int,
                     extra_set: str = "", db_temp: Optional[AsyncSession] = None, referencias_temp=()) -> Optional[str]:
    if not es_provisional(id_web) or es_provisional(id_real) or id_real <= 0:
        return "Renumeración no válida"
    if (await db.execute(text(f"SELECT 1 FROM {tabla} WHERE company_id = :c AND {llave} = :i"), {"c": cid, "i": id_real})).scalar():
        return f"El número {id_real} ya existe en la web"
    if not (await db.execute(text(f"SELECT 1 FROM {tabla} WHERE company_id = :c AND {llave} = :w"), {"c": cid, "w": id_web})).scalar():
        return None
    await db.execute(text(f"UPDATE {tabla} SET {llave} = :r{extra_set} WHERE company_id = :c AND {llave} = :w"),
                     {"r": id_real, "c": cid, "w": id_web})
    for t, col in referencias:
        if t == tabla and col == llave:
            continue
        await db.execute(text(f"UPDATE {t} SET {col} = :r WHERE company_id = :c AND {col} = :w"),
                         {"r": id_real, "c": cid, "w": id_web})
    if db_temp is not None:
        for t, col in referencias_temp:
            await db_temp.execute(text(f"UPDATE {t} SET {col} = :r WHERE company_id = :c AND {col} = :w"),
                                  {"r": id_real, "c": cid, "w": id_web})
    return None


async def _al_dia(db: AsyncSession, cid: int, tabla: str, llave: str, al_dia: str, valor, visto: Optional[str]) -> int:
    """Marca al día lo aplicado si no cambió desde que el agente lo bajó (antes de renumerar: renumerar
    actualiza updated_at)."""
    return (await db.execute(text(f"""
        UPDATE {tabla} SET {al_dia} WHERE company_id = :c AND {llave} = :i AND (:v IS NULL OR updated_at <= :v)
    """), {"c": cid, "i": valor, "v": visto})).rowcount


async def confirmar(db: AsyncSession, cid: int, platos: list, sede_actualizado: Optional[str],
                    entidades: Optional[dict] = None, listas: Optional[list] = None,
                    listas_cabecera: Optional[list] = None, db_temp: Optional[AsyncSession] = None) -> dict:
    """El agente aplicó los cambios en el escritorio: marca al día lo que no cambió desde que se bajó y
    renumera los provisionales con su número real (y activa los platos). No hace commit."""
    renumerados, confirmados, errores = [], [], []
    entidades = entidades or {}
    # 1. al día (todo con su número de la web, aún provisional)
    for nombre in ORDEN:
        e = ENTIDADES[nombre]
        for x in entidades.get(nombre, []):
            await _al_dia(db, cid, e["tabla"], e["llave"], e["al_dia"], int(x["id_web"]), x.get("actualizado"))
    for p in platos:
        if await _al_dia(db, cid, "pos_dishes", "id", "synced = 1", int(p["id_web"]), p.get("actualizado")):
            confirmados.append(int(p["id_real"]))
    for tabla, filas in (("pos_customer_price_list", listas or []), ("pos_customer_price_list_header", listas_cabecera or [])):
        for x in filas:
            await _al_dia(db, cid, tabla, "id", "synced = 1", int(x["id"]), x.get("actualizado"))
    sede_ok = False
    if sede_actualizado is not None:
        sede_ok = bool((await db.execute(text("""
            UPDATE configuracion_sede SET synced = 1 WHERE company_id = :c AND updated_at <= :v
        """), {"c": cid, "v": sede_actualizado})).rowcount)

    # 2. renumerar provisionales
    for nombre in ORDEN:
        e = ENTIDADES[nombre]
        for x in entidades.get(nombre, []):
            id_web, id_real = int(x["id_web"]), int(x["id_real"])
            if id_web == id_real:
                continue
            err = await _renumerar(db, cid, e["tabla"], e["llave"], e["referencias"], id_web, id_real,
                                   db_temp=db_temp, referencias_temp=e.get("referencias_temp", ()))
            if err:
                errores.append({"entidad": nombre, "id_web": id_web, "error": err})
            else:
                renumerados.append({"entidad": nombre, "id_web": id_web, "id_real": id_real})
    for p in platos:
        id_web, id_real = int(p["id_web"]), int(p["id_real"])
        if id_web == id_real:
            continue
        err = await _renumerar(db, cid, "pos_dishes", "id", REFERENCIAS_PLATO, id_web, id_real, extra_set=", active = 0")
        if err:
            errores.append({"entidad": "plato", "id_web": id_web, "error": err})
        else:
            renumerados.append({"entidad": "plato", "id_web": id_web, "id_real": id_real})
    return {"renumerados": renumerados, "confirmados": confirmados, "errores": errores, "sede": sede_ok}
