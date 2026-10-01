"""
Listas de precios (lista_precios_cliente del escritorio).

  Cabecera: pos_customer_price_list_header (id_lista, id_cliente, nombre, fecha, activa…)
  Detalle:  pos_customer_price_list (id_lista, id_cliente, id_producto, id_presentacion, precio)
            id_presentacion = 0 → el plato; > 0 → la variante (pos_dish_variants.id)

Reglas:
  - Lista DEFAULT = la lista del cliente 1 (Consumidor Final). Puede haber varias (histórico
    de precios) pero solo UNA activa. Sus precios SON los de los platos/variantes: cambiar
    uno cambia el otro.
  - Una sola lista activa por cliente.
  - Precio al tomar un pedido: lista activa del cliente si no es el 1 y la tiene; si no,
    la Default activa; si el producto no está en la lista, el precio del plato/variante.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

CLIENTE_DEFAULT = 1
_BOG = timezone(timedelta(hours=-5))


def _hoy() -> str:
    return datetime.now(_BOG).date().isoformat()


async def lista_activa(db: AsyncSession, cid: int, id_cliente: int) -> Optional[int]:
    return (await db.execute(text("""
        SELECT id_lista FROM pos_customer_price_list_header
        WHERE company_id = :cid AND id_cliente = :cli AND activa = 1
        ORDER BY id_lista DESC LIMIT 1
    """), {"cid": cid, "cli": int(id_cliente)})).scalar()


async def completar_lista(db: AsyncSession, cid: int, id_lista: int, id_cliente: int) -> None:
    """Agrega a la lista los platos activos y variantes que le falten (productos nuevos).
    Precio: el de la Default activa; para la Default misma, el del plato/variante."""
    default = await lista_activa(db, cid, CLIENTE_DEFAULT)
    fuente = default if (default and default != id_lista) else None
    f, a = _hoy(), 1
    if fuente:
        await db.execute(text("""
            INSERT IGNORE INTO pos_customer_price_list
                (id_lista, id_cliente, id_producto, id_presentacion, precio_producto, fecha, activa, company_id, synced)
            SELECT :l, :cli, d.id_producto, d.id_presentacion, d.precio_producto, :f,
                   (SELECT activa FROM pos_customer_price_list_header WHERE company_id=:cid AND id_lista=:l), :cid, 0
            FROM pos_customer_price_list d
            JOIN pos_dishes p ON p.id = d.id_producto AND p.company_id = d.company_id AND COALESCE(p.active, 0) = 0
            WHERE d.company_id = :cid AND d.id_lista = :src
        """), {"cid": cid, "l": id_lista, "cli": id_cliente, "f": f, "src": fuente})
    activa = (await db.execute(text(
        "SELECT activa FROM pos_customer_price_list_header WHERE company_id=:cid AND id_lista=:l"
    ), {"cid": cid, "l": id_lista})).scalar()
    a = 1 if activa else 0
    await db.execute(text("""
        INSERT IGNORE INTO pos_customer_price_list
            (id_lista, id_cliente, id_producto, id_presentacion, precio_producto, fecha, activa, company_id, synced)
        SELECT :l, :cli, p.id, 0, p.price, :f, :a, :cid, 0
        FROM pos_dishes p WHERE p.company_id = :cid AND COALESCE(p.active, 0) = 0
    """), {"cid": cid, "l": id_lista, "cli": id_cliente, "f": f, "a": a})
    await db.execute(text("""
        INSERT IGNORE INTO pos_customer_price_list
            (id_lista, id_cliente, id_producto, id_presentacion, precio_producto, fecha, activa, company_id, synced)
        SELECT :l, :cli, v.dish_id, v.id, v.price, :f, :a, :cid, 0
        FROM pos_dish_variants v
        JOIN pos_dishes p ON p.id = v.dish_id AND p.company_id = v.company_id AND COALESCE(p.active, 0) = 0
        WHERE v.company_id = :cid AND v.is_active = 1
    """), {"cid": cid, "l": id_lista, "cli": id_cliente, "f": f, "a": a})


async def asegurar_default(db: AsyncSession, cid: int, usuario: str = "") -> int:
    """Devuelve la lista Default activa; si la empresa no tiene, la crea con los precios de los platos."""
    actual = await lista_activa(db, cid, CLIENTE_DEFAULT)
    if actual:
        return int(actual)
    nid = int((await db.execute(text(
        "SELECT COALESCE(MAX(id_lista), 0) + 1 FROM pos_customer_price_list_header WHERE company_id = :cid"
    ), {"cid": cid})).scalar())
    await db.execute(text("""
        INSERT INTO pos_customer_price_list_header
            (company_id, id_lista, id_cliente, nombre, fecha, activa, usuario, observacion, synced)
        VALUES (:cid, :l, :cli, 'Lista Default', :f, 1, :u, 'Precios de la carta', 0)
    """), {"cid": cid, "l": nid, "cli": CLIENTE_DEFAULT, "f": _hoy(), "u": (usuario or "")[:50]})
    await completar_lista(db, cid, nid, CLIENTE_DEFAULT)
    return nid


async def precio(db: AsyncSession, cid: int, id_cliente: int, dish_id: int, id_presentacion: int,
                 respaldo: int) -> int:
    """Precio para tomar un pedido (lista del cliente → Default → precio del plato/variante)."""
    listas = []
    if id_cliente and int(id_cliente) != CLIENTE_DEFAULT:
        propia = await lista_activa(db, cid, int(id_cliente))
        if propia:
            listas.append(propia)
    default = await lista_activa(db, cid, CLIENTE_DEFAULT)
    if default:
        listas.append(default)
    for l in listas:
        p = (await db.execute(text("""
            SELECT precio_producto FROM pos_customer_price_list
            WHERE company_id = :cid AND id_lista = :l AND id_producto = :did AND id_presentacion = :pres
            LIMIT 1
        """), {"cid": cid, "l": l, "did": dish_id, "pres": int(id_presentacion or 0)})).scalar()
        if p is not None:
            return int(round(float(p)))
    return int(respaldo or 0)


async def plato_a_default(db: AsyncSession, cid: int, dish_id: int, id_presentacion: int, valor: int) -> None:
    """El precio del plato/variante cambió en su configuración → actualizar la Default activa."""
    default = await asegurar_default(db, cid)
    await db.execute(text("""
        INSERT INTO pos_customer_price_list
            (id_lista, id_cliente, id_producto, id_presentacion, precio_producto, fecha, activa, company_id, synced)
        VALUES (:l, :cli, :did, :pres, :pr, :f, 1, :cid, 0)
        ON DUPLICATE KEY UPDATE precio_producto = VALUES(precio_producto), fecha = VALUES(fecha), synced = 0
    """), {"l": default, "cli": CLIENTE_DEFAULT, "did": dish_id, "pres": int(id_presentacion or 0),
           "pr": valor, "f": _hoy(), "cid": cid})


async def default_a_platos(db: AsyncSession, cid: int, id_lista: int) -> None:
    """La Default (activa) cambió o se activó → el precio de platos y variantes = el de la lista.
    El plato y su variante por defecto quedan iguales (manda el precio de la variante)."""
    await db.execute(text("""
        UPDATE pos_dishes p
        JOIN pos_customer_price_list d
          ON d.company_id = p.company_id AND d.id_producto = p.id AND d.id_lista = :l AND d.id_presentacion = 0
        SET p.price = ROUND(d.precio_producto), p.synced = 0
        WHERE p.company_id = :cid AND p.price <> ROUND(d.precio_producto)
    """), {"cid": cid, "l": id_lista})
    await db.execute(text("""
        UPDATE pos_dish_variants v
        JOIN pos_customer_price_list d
          ON d.company_id = v.company_id AND d.id_producto = v.dish_id AND d.id_presentacion = v.id AND d.id_lista = :l
        SET v.price = ROUND(d.precio_producto)
        WHERE v.company_id = :cid AND v.price <> ROUND(d.precio_producto)
    """), {"cid": cid, "l": id_lista})
    # plato = su variante por defecto (en el plato y en la fila del plato de la lista)
    await db.execute(text("""
        UPDATE pos_dishes p
        JOIN pos_dish_variants v ON v.dish_id = p.id AND v.company_id = p.company_id AND v.is_active = 1 AND v.is_default = 1
        SET p.price = v.price, p.synced = 0
        WHERE p.company_id = :cid AND p.price <> v.price
    """), {"cid": cid})
    await db.execute(text("""
        UPDATE pos_customer_price_list d
        JOIN pos_dish_variants v ON v.dish_id = d.id_producto AND v.company_id = d.company_id AND v.is_active = 1 AND v.is_default = 1
        SET d.precio_producto = v.price
        WHERE d.company_id = :cid AND d.id_lista = :l AND d.id_presentacion = 0 AND d.precio_producto <> v.price
    """), {"cid": cid, "l": id_lista})
