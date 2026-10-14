"""
Traslados de inventario de la Bodega Central (migración 047). Todo queda en la nube (bc_traslados /
bc_traslado_items) y nunca se borra.

  Origen y destino: la bodega o cualquier sede de su mismo NIT (bodega → sede, sede → sede, sede → bodega).
  Un traslado = un origen → un destino; desde la pantalla se arma una grilla productos × destinos y se crea un
  traslado por destino.

  Todo es AUTOMÁTICO (sin cajero). Según dónde está el inventario:
    · Empresa solo web (y la bodega): se descuenta / se carga al instante en la web (kardex inventory_exits /
      inventory_entries, igual que las pantallas de inventario).
    · Empresa con escritorio (Agente Local activo): su agente aplica la salida (verificando que tenga el stock)
      o el cargue en el escritorio y lo reporta → PENDIENTE_SALIDA / PENDIENTE_CARGUE hasta entonces.
      (El escritorio sube luego su stock a la web con la sincronización normal.)

  Cargue en destino: el producto se reconoce por su vínculo con la bodega o por código; si existe se actualizan
  sus valores (regla del cero: un 0 no cambia el valor de la sede) y si no, se CREA con la foto que viaja en el
  traslado (categoría y proveedor se crean en la empresa si faltan). La cantidad se SUMA a la existente.

  Anular: solo lo que aún no se ha cargado; queda el motivo, la fecha y quién. Si el origen ya descontó en la web
  se le devuelve al instante; si descontó su agente, queda reversa_pendiente para que el agente lo devuelva.
  Lo ya cargado no se anula: se hace un traslado de vuelta.
"""
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.bodega_guard import Bodega
from app.services import bodega_central as bc
from app.services import sede_maestros, sede_pedidos
from app.services.stock import apply_stock_move

MAX_LINEAS = 300
ABIERTOS = ("PENDIENTE_SALIDA", "PENDIENTE_CARGUE")
CARGADOR_WEB = "Sistema web (automático)"


# ─── Inventario de una empresa ───────────────────────────────────────────────

async def _insumo(db: AsyncSession, cid: int, dish_id: int) -> Optional[int]:
    """Id_Item del inventario del producto: su único insumo (almacén: Id_Item = Id_Plato). None si tiene receta."""
    items = (await db.execute(text(
        "SELECT id_item FROM inventario_porciones_plato WHERE company_id = :c AND id_plato = :d"),
        {"c": cid, "d": dish_id})).scalars().all()
    if len(items) == 1:
        return int(items[0])
    if not items and (await db.execute(text(
            "SELECT 1 FROM supply_items WHERE company_id = :c AND id_item = :d"), {"c": cid, "d": dish_id})).scalar():
        return int(dish_id)
    return None


async def _stock(db: AsyncSession, cid: int, id_item: int, bloquear: bool = False) -> float:
    q = "SELECT cantidad_actual FROM inventario_actual_porciones WHERE company_id = :c AND id_item = :i"
    return float((await db.execute(text(q + (" FOR UPDATE" if bloquear else "")),
                                   {"c": cid, "i": id_item})).scalar() or 0)


async def _mover(db: AsyncSession, cid: int, id_item: int, cantidad: float, observacion: str, user) -> None:
    """Entrada (cantidad > 0) o salida (< 0) en el kardex web de la empresa, como las pantallas de inventario."""
    from datetime import date
    hoy = date.today().isoformat()
    await db.execute(text(
        "UPDATE supply_items SET control_stock = 1 WHERE company_id = :c AND id_item = :i AND COALESCE(control_stock, 0) = 0"),
        {"c": cid, "i": id_item})
    tabla, col = ("inventory_entries", "id_entrada") if cantidad > 0 else ("inventory_exits", "id_salida")
    res = await db.execute(text(f"""
        INSERT INTO {tabla} ({col}, id_item, id_proveedor, company_id, fecha, cantidad, cod_empleado, observacion,
                             autorizada, synced, updated_at)
        VALUES ((SELECT COALESCE(MAX({col}), 0) + 1 FROM {tabla} t2 WHERE t2.company_id = :c),
                :i, 0, :c, :f, :q, :emp, :obs, 1, 0, NOW())
    """), {"c": cid, "i": id_item, "f": hoy, "q": abs(cantidad), "emp": (getattr(user, "email", "") or "")[:50],
           "obs": observacion[:255]})
    await db.flush()
    await apply_stock_move(db, cid, id_item, cantidad, "entry" if cantidad > 0 else "exit", "traslado_bodega",
                           res.lastrowid, hoy, observacion, getattr(user, "id", None))


async def es_escritorio(db: AsyncSession, cid: int) -> bool:
    return await sede_pedidos.tiene_sede(db, cid)


# ─── Productos del origen ────────────────────────────────────────────────────

async def productos_origen(db: AsyncSession, cid: int) -> list[dict]:
    """Productos visibles del origen con su stock (solo los que tienen un único insumo: se pueden trasladar)."""
    filas = (await db.execute(text("""
        SELECT d.id, d.name, d.product_code, d.price, c.name AS categoria,
               IF(COALESCE(d.extra_print, '0') = '1', 1, 0) AS unitario,
               (SELECT COUNT(*) FROM inventario_porciones_plato ip WHERE ip.company_id = d.company_id AND ip.id_plato = d.id) AS insumos,
               (SELECT ip.id_item FROM inventario_porciones_plato ip WHERE ip.company_id = d.company_id AND ip.id_plato = d.id LIMIT 1) AS id_item
        FROM pos_dishes d
        LEFT JOIN pos_dish_categories c ON c.company_id = d.company_id AND c.id = d.category_id
        WHERE d.company_id = :c AND COALESCE(d.active, 0) = 0 AND d.id < :prov
        ORDER BY d.name
    """), {"c": cid, "prov": sede_maestros.ID_PROVISIONAL})).mappings().all()
    stocks = {int(f[0]): float(f[1] or 0) for f in (await db.execute(text(
        "SELECT id_item, cantidad_actual FROM inventario_actual_porciones WHERE company_id = :c"), {"c": cid})).all()}
    out = []
    for f in filas:
        if int(f["insumos"] or 0) > 1:
            continue                                  # con receta: no es un artículo trasladable
        item = int(f["id_item"]) if f["id_item"] else int(f["id"])
        out.append({"id": f["id"], "name": f["name"], "product_code": f["product_code"], "price": int(f["price"] or 0),
                    "categoria": f["categoria"], "unitario": bool(f["unitario"]), "stock": stocks.get(item, 0.0)})
    return out


async def _foto_producto(db: AsyncSession, cid: int, dish_id: int) -> dict:
    f = (await db.execute(text("""
        SELECT d.id, d.name, d.product_code, d.price, d.wholesale_price, d.product_cost, d.tax, d.minimum_stock,
               IF(COALESCE(d.extra_print, '0') = '1', 1, 0) AS unitario, COALESCE(d.ask_product_description, 0) AS pedir,
               c.name AS categoria, s.name AS proveedor, s.nit AS proveedor_nit
        FROM pos_dishes d
        LEFT JOIN pos_dish_categories c ON c.company_id = d.company_id AND c.id = d.category_id
        LEFT JOIN pos_dish_products dp ON dp.company_id = d.company_id AND dp.dish_id = d.id
        LEFT JOIN suppliers s ON s.company_id = d.company_id AND s.id_proveedor = dp.supplier_id
        WHERE d.company_id = :c AND d.id = :d
        ORDER BY dp.supplier_id DESC LIMIT 1
    """), {"c": cid, "d": dish_id})).mappings().first()
    if not f:
        raise HTTPException(status_code=404, detail="Producto no encontrado en el origen")
    return dict(f)


# ─── Crear traslados ─────────────────────────────────────────────────────────

async def crear_traslados(db: AsyncSession, bodega: Bodega, origen_id: int, lineas: list[dict],
                          observacion: str, clave: Optional[str]) -> dict:
    """lineas: [{dish_id (del origen), destinos: [{empresa_id, cantidad}]}]. Un traslado por destino."""
    grupo = await bc.empresas_grupo(db, bodega)
    if origen_id not in grupo:
        raise HTTPException(status_code=403, detail="El origen no pertenece a la bodega central")
    if clave and (await db.execute(text(
            "SELECT 1 FROM bc_traslados WHERE bodega_id = :b AND clave = :k LIMIT 1"), {"b": bodega.id, "k": clave})).scalar():
        return {"ok": True, "repetida": True, "traslados": []}
    if not lineas or len(lineas) > MAX_LINEAS:
        raise HTTPException(status_code=422, detail=f"Escoja entre 1 y {MAX_LINEAS} productos")

    por_destino: dict = {}
    totales: dict = {}
    fotos: dict = {}
    for ln in lineas:
        dish = int(ln["dish_id"])
        if dish in fotos:
            raise HTTPException(status_code=422, detail="Hay productos repetidos")
        foto = await _foto_producto(db, origen_id, dish)
        item = await _insumo(db, origen_id, dish)
        if item is None:
            raise HTTPException(status_code=422, detail=f"«{foto['name']}» tiene receta: no se puede trasladar")
        foto["id_item"] = item
        fotos[dish] = foto
        destinos = [d for d in ln["destinos"] if float(d["cantidad"] or 0) > 0]
        for d in destinos:
            dest = int(d["empresa_id"])
            cant = float(d["cantidad"])
            if dest not in grupo or dest == origen_id:
                raise HTTPException(status_code=422, detail="Destino no válido")
            if cant != int(cant):
                raise HTTPException(status_code=422, detail="Las cantidades deben ser enteras")
            por_destino.setdefault(dest, []).append((dish, cant))
            totales[dish] = totales.get(dish, 0) + cant
        if foto["unitario"] and (totales.get(dish, 0) != 1 or len(destinos) != 1):
            raise HTTPException(status_code=422, detail=f"«{foto['name']}» es de cargue unitario (IMEI): cantidad 1 a un solo destino")
    if not por_destino:
        raise HTTPException(status_code=422, detail="Escriba al menos una cantidad")

    origen_web = not await es_escritorio(db, origen_id)
    if origen_web:     # el origen debe tener el stock (bloqueando, para que dos envíos no lo dejen en negativo)
        for dish, total in totales.items():
            disp = await _stock(db, origen_id, fotos[dish]["id_item"], bloquear=True)
            if disp < total:
                raise HTTPException(status_code=409, detail=f"«{fotos[dish]['name']}»: hay {disp:g} en {grupo[origen_id]} y se piden {total:g}")

    ahora = datetime.now()
    numero = int((await db.execute(text(
        "SELECT COALESCE(MAX(numero), 0) FROM bc_traslados WHERE bodega_id = :b FOR UPDATE"), {"b": bodega.id})).scalar() or 0)
    creados = []
    for dest, items in por_destino.items():
        numero += 1
        res = await db.execute(text("""
            INSERT INTO bc_traslados (bodega_id, numero, origen_id, destino_id, estado, observacion, enviado_en,
                                      enviado_por, enviado_por_id, ip, clave)
            VALUES (:b, :n, :o, :d, :e, :obs, :ahora, :por, :uid, :ip, :k)
        """), {"b": bodega.id, "n": numero, "o": origen_id, "d": dest,
               "e": "PENDIENTE_CARGUE" if origen_web else "PENDIENTE_SALIDA", "obs": (observacion or "")[:255],
               "ahora": ahora, "por": bodega.usuario, "uid": bodega.user.id, "ip": bodega.ip, "k": clave})
        tid = res.lastrowid
        for n, (dish, cant) in enumerate(items, start=1):
            f = fotos[dish]
            await db.execute(text("""
                INSERT INTO bc_traslado_items (traslado_id, item, origen_dish_id, codigo, nombre, categoria, proveedor,
                    proveedor_nit, precio, precio_minimo, costo, iva, stock_minimo, desactivar_al_vender,
                    pedir_descripcion, cantidad)
                VALUES (:t, :n, :d, :cod, :nom, :cat, :prov, :nit, :p, :pm, :co, :iva, :sm, :u, :pd, :q)
            """), {"t": tid, "n": n, "d": dish, "cod": f["product_code"], "nom": f["name"], "cat": f["categoria"],
                   "prov": f["proveedor"], "nit": f["proveedor_nit"], "p": f["price"] or 0, "pm": f["wholesale_price"] or 0,
                   "co": f["product_cost"] or 0, "iva": f["tax"] or 0, "sm": f["minimum_stock"] or 0,
                   "u": int(f["unitario"]), "pd": int(f["pedir"] or 0), "q": cant})
        if origen_web:
            await _salida_web(db, bodega.user, tid, origen_id, f"Traslado #{numero} a {grupo[dest]}")
            if not await es_escritorio(db, dest):
                await cargar_en_web(db, bodega, tid)
        creados.append({"id": tid, "numero": numero, "destino": grupo[dest]})
        await bc.movimiento(db, bodega, "TRASLADO", None, sum(c for _, c in items),
                            f"Traslado #{numero}: {grupo[origen_id]} → {grupo[dest]} ({len(items)} productos)",
                            sede_id=dest if dest != bodega.id else origen_id)
    estados = {t["id"]: (await db.execute(text("SELECT estado FROM bc_traslados WHERE id = :t"), {"t": t["id"]})).scalar()
               for t in creados}
    for t in creados:
        t["estado"] = estados[t["id"]]
    return {"ok": True, "repetida": False, "traslados": creados}


async def _salida_web(db: AsyncSession, user, tid: int, origen_id: int, observacion: str) -> None:
    items = (await db.execute(text(
        "SELECT id, origen_dish_id, cantidad FROM bc_traslado_items WHERE traslado_id = :t ORDER BY item"),
        {"t": tid})).mappings().all()
    for it in items:
        id_item = await _insumo(db, origen_id, int(it["origen_dish_id"]))
        antes = await _stock(db, origen_id, id_item, bloquear=True)
        await _mover(db, origen_id, id_item, -float(it["cantidad"]), observacion, user)
        await db.execute(text(
            "UPDATE bc_traslado_items SET stock_origen_antes = :a, stock_origen_despues = :d WHERE id = :id"),
            {"a": antes, "d": await _stock(db, origen_id, id_item), "id": it["id"]})
    await db.execute(text(
        "UPDATE bc_traslados SET salida_en = NOW(), salida_por = :p, estado = 'PENDIENTE_CARGUE' WHERE id = :t"),
        {"p": CARGADOR_WEB, "t": tid})


# ─── Cargue en un destino web ────────────────────────────────────────────────

async def _id_catalogo(db: AsyncSession, cid: int, tabla: str, nombre: Optional[str]) -> Optional[int]:
    nombre = (nombre or "").strip()[:100]
    if not nombre:
        return None
    existe = (await db.execute(text(
        f"SELECT id FROM {tabla} WHERE company_id = :c AND UPPER(TRIM(name)) = :n ORDER BY id LIMIT 1"),
        {"c": cid, "n": nombre.upper()})).scalar()
    if existe:
        return int(existe)
    nuevo = await sede_maestros.siguiente_id(db, tabla, "id", cid, await es_escritorio(db, cid))
    await db.execute(text(f"INSERT INTO {tabla} (id, company_id, name, is_active, synced) VALUES (:id, :c, :n, 1, 0)"),
                     {"id": nuevo, "c": cid, "n": nombre})
    return nuevo


async def _proveedor(db: AsyncSession, cid: int, nombre: Optional[str], nit: Optional[str]) -> int:
    nit, nombre = (nit or "").strip(), (nombre or "").strip()[:150]
    if nit:
        p = (await db.execute(text(
            "SELECT id_proveedor FROM suppliers WHERE company_id = :c AND TRIM(nit) = :n AND id_proveedor IS NOT NULL LIMIT 1"),
            {"c": cid, "n": nit})).scalar()
        if p is not None:
            return int(p)
    if nombre:
        p = (await db.execute(text(
            "SELECT id_proveedor FROM suppliers WHERE company_id = :c AND UPPER(TRIM(name)) = :n AND id_proveedor IS NOT NULL LIMIT 1"),
            {"c": cid, "n": nombre.upper()})).scalar()
        if p is not None:
            return int(p)
        nuevo = await sede_maestros.siguiente_id(db, "suppliers", "id_proveedor", cid, await es_escritorio(db, cid))
        await db.execute(text("""
            INSERT INTO suppliers (company_id, id_proveedor, name, nit, is_active, synced, created_at)
            VALUES (:c, :p, :n, :nit, 1, 0, NOW())
        """), {"c": cid, "p": nuevo, "n": nombre, "nit": nit or None})
        return nuevo
    return await bc.asegurar_varios(db, cid)


async def _producto_destino(db: AsyncSession, bodega: Bodega, tras: dict, it: dict) -> Optional[int]:
    """Producto del destino: vínculo con la bodega o mismo código."""
    origen, destino = int(tras["origen_id"]), int(tras["destino_id"])
    if origen == bodega.id:          # bodega → sede: vínculo del producto de la bodega con esa sede
        sd = (await db.execute(text(
            "SELECT sede_dish_id FROM bc_producto_sede WHERE bodega_id = :b AND dish_id = :d AND sede_id = :s "
            "AND estado = 'VINCULADO'"), {"b": bodega.id, "d": it["origen_dish_id"], "s": destino})).scalar()
        if sd and (await db.execute(text("SELECT 1 FROM pos_dishes WHERE company_id = :s AND id = :d"),
                                    {"s": destino, "d": sd})).scalar():
            return int(sd)
    elif destino == bodega.id:       # sede → bodega: el producto de la bodega vinculado a esa sede
        bd = (await db.execute(text(
            "SELECT dish_id FROM bc_producto_sede WHERE bodega_id = :b AND sede_id = :s AND sede_dish_id = :d "
            "AND estado = 'VINCULADO'"), {"b": bodega.id, "s": origen, "d": it["origen_dish_id"]})).scalar()
        if bd and (await db.execute(text("SELECT 1 FROM pos_dishes WHERE company_id = :b AND id = :d"),
                                    {"b": bodega.id, "d": bd})).scalar():
            return int(bd)
    codigo = (it["codigo"] or "").strip()
    if codigo:
        sd = (await db.execute(text(
            "SELECT MIN(id) FROM pos_dishes WHERE company_id = :c AND TRIM(product_code) = :k"),
            {"c": destino, "k": codigo})).scalar()
        if sd:
            return int(sd)
    return None


async def _vincular(db: AsyncSession, bodega: Bodega, tras: dict, origen_dish: int, destino_dish: int) -> None:
    origen, destino = int(tras["origen_id"]), int(tras["destino_id"])
    if origen == bodega.id:
        par = (origen_dish, destino, destino_dish)
    elif destino == bodega.id:
        par = (destino_dish, origen, origen_dish)
    else:
        return
    await db.execute(text("""
        INSERT INTO bc_producto_sede (bodega_id, dish_id, sede_id, sede_dish_id, estado)
        VALUES (:b, :d, :s, :sd, 'VINCULADO')
        ON DUPLICATE KEY UPDATE sede_dish_id = VALUES(sede_dish_id), estado = 'VINCULADO', error = NULL
    """), {"b": bodega.id, "d": par[0], "s": par[1], "sd": par[2]})


async def cargar_en_web(db: AsyncSession, bodega: Bodega, tid: int) -> None:
    """Carga un traslado en un destino web: crea o actualiza cada producto y SUMA la cantidad."""
    tras = dict((await db.execute(text("SELECT * FROM bc_traslados WHERE id = :t FOR UPDATE"), {"t": tid})).mappings().first())
    if tras["estado"] != "PENDIENTE_CARGUE":
        return
    destino = int(tras["destino_id"])
    grupo = await bc.empresas_grupo(db, bodega)
    unidad = await bc.asegurar_unidad(db, destino)
    items = (await db.execute(text("SELECT * FROM bc_traslado_items WHERE traslado_id = :t ORDER BY item"),
                              {"t": tid})).mappings().all()
    for it in items:
        it = dict(it)
        dd = await _producto_destino(db, bodega, tras, it)
        if dd:
            resultado = "ACTUALIZADO"
            actual = (await db.execute(text(
                f"SELECT {', '.join(bc.CAMPOS_VALORES)} FROM pos_dishes WHERE company_id = :c AND id = :d"),
                {"c": destino, "d": dd})).mappings().first()
            nuevos = {"price": it["precio"], "wholesale_price": it["precio_minimo"], "product_cost": it["costo"],
                      "tax": it["iva"], "minimum_stock": it["stock_minimo"]}
            cambios = [{"campo": k, "nuevo": float(v)} for k, v in nuevos.items()
                       if float(v or 0) != 0 and round(float(v), 2) != round(float(actual[k] or 0), 2)]   # regla del cero
            if cambios:
                await bc._aplicar_valores(db, destino, dd, cambios)
        else:
            resultado = "CREADO"
            categoria = await _id_catalogo(db, destino, "pos_dish_categories", it["categoria"]) or await bc._categoria_general(db, destino)
            proveedor = await _proveedor(db, destino, it["proveedor"], it["proveedor_nit"])
            nombre = it["nombre"]
            if (await db.execute(text("SELECT 1 FROM pos_dishes WHERE company_id = :c AND name = :n"),
                                 {"c": destino, "n": nombre})).scalar():
                nombre = f"{nombre} {it['codigo'] or ''}".strip()[:250]
            nuevo_id = await (sede_maestros.siguiente_id_plato(db, destino, True) if await es_escritorio(db, destino)
                              else bc._nuevo_id(db, destino))
            dd = await bc.crear_producto(db, destino, {
                "name": nombre, "product_code": it["codigo"], "price": it["precio"], "wholesale_price": it["precio_minimo"],
                "product_cost": it["costo"], "tax": it["iva"], "minimum_stock": it["stock_minimo"],
                "extra_print": bool(it["desactivar_al_vender"]), "ask_product_description": bool(it["pedir_descripcion"]),
                "category_id": categoria, "id_proveedor": proveedor,
            }, nuevo_id=nuevo_id, unidad=unidad, validado=True)
        id_item = await _insumo(db, destino, dd) or dd
        antes = await _stock(db, destino, id_item, bloquear=True)
        await _mover(db, destino, id_item, float(it["cantidad"]),
                     f"Traslado #{tras['numero']} desde {grupo.get(int(tras['origen_id']), 'origen')}", bodega.user)
        await db.execute(text("""
            UPDATE bc_traslado_items SET destino_dish_id = :dd, resultado = :r, estado = 'CARGADO',
                   stock_destino_antes = :a, stock_destino_despues = :d WHERE id = :id
        """), {"dd": dd, "r": resultado, "a": antes, "d": await _stock(db, destino, id_item), "id": it["id"]})
        await _vincular(db, bodega, tras, int(it["origen_dish_id"]), dd)
    await db.execute(text(
        "UPDATE bc_traslados SET estado = 'CARGADO', cargado_en = NOW(), cargado_por = :p WHERE id = :t"),
        {"p": CARGADOR_WEB, "t": tid})


# ─── Anular ──────────────────────────────────────────────────────────────────

async def anular(db: AsyncSession, bodega: Bodega, tid: int, motivo: str) -> dict:
    tras = (await db.execute(text(
        "SELECT * FROM bc_traslados WHERE id = :t AND bodega_id = :b FOR UPDATE"), {"t": tid, "b": bodega.id})).mappings().first()
    if not tras:
        raise HTTPException(status_code=404, detail="Traslado no encontrado")
    if tras["estado"] not in ABIERTOS:
        raise HTTPException(status_code=409, detail="Solo se anula un traslado que aún no se ha cargado. "
                                                    "Para devolver lo cargado haga un traslado de vuelta.")
    motivo = (motivo or "").strip()
    if len(motivo) < 5:
        raise HTTPException(status_code=422, detail="Escriba el motivo de la anulación")
    grupo = await bc.empresas_grupo(db, bodega)
    origen = int(tras["origen_id"])
    reversa = 0
    if tras["salida_en"]:
        if await es_escritorio(db, origen) and tras["salida_por"] != CARGADOR_WEB:
            reversa = 1                 # descontó el agente del escritorio: él debe devolverlo
        else:
            items = (await db.execute(text(
                "SELECT origen_dish_id, cantidad FROM bc_traslado_items WHERE traslado_id = :t"), {"t": tid})).mappings().all()
            for it in items:
                id_item = await _insumo(db, origen, int(it["origen_dish_id"]))
                if id_item:
                    await _mover(db, origen, id_item, float(it["cantidad"]),
                                 f"Anulación traslado #{tras['numero']}", bodega.user)
    await db.execute(text("""
        UPDATE bc_traslados SET estado = 'ANULADO', anulado_en = NOW(), anulado_por = :p, anulado_motivo = :m,
               reversa_pendiente = :r WHERE id = :t
    """), {"p": bodega.usuario, "m": motivo[:255], "r": reversa, "t": tid})
    await db.execute(text("UPDATE bc_traslado_items SET estado = 'ANULADO' WHERE traslado_id = :t"), {"t": tid})
    await bc.movimiento(db, bodega, "TRASLADO", None, 0,
                        f"Traslado #{tras['numero']} ANULADO ({grupo.get(origen)} → {grupo.get(int(tras['destino_id']))}): {motivo}"[:255],
                        sede_id=int(tras["destino_id"]) if int(tras["destino_id"]) != bodega.id else origen)
    return {"ok": True, "reversa_pendiente": bool(reversa)}


# ─── Consultas ───────────────────────────────────────────────────────────────

def _iso(v):
    return v.isoformat(timespec="minutes") if v else None


async def listar(db: AsyncSession, bodega: Bodega, estado: Optional[str], empresa: Optional[int],
                 desde: Optional[str], hasta: Optional[str]) -> list[dict]:
    conds, p = ["t.bodega_id = :b"], {"b": bodega.id}
    if estado:
        conds.append("t.estado = :e"); p["e"] = estado
    if empresa:
        conds.append("(t.origen_id = :emp OR t.destino_id = :emp)"); p["emp"] = empresa
    if desde:
        conds.append("t.enviado_en >= :d"); p["d"] = f"{desde} 00:00:00"
    if hasta:
        conds.append("t.enviado_en <= :h"); p["h"] = f"{hasta} 23:59:59"
    grupo = await bc.empresas_grupo(db, bodega)
    filas = (await db.execute(text(f"""
        SELECT t.id, t.numero, t.origen_id, t.destino_id, t.estado, t.enviado_en, t.enviado_por, t.cargado_en,
               t.cargado_por, t.anulado_en, t.anulado_motivo, t.reversa_pendiente, t.error, t.observacion,
               (SELECT COUNT(*) FROM bc_traslado_items i WHERE i.traslado_id = t.id) AS productos,
               (SELECT COALESCE(SUM(i.cantidad), 0) FROM bc_traslado_items i WHERE i.traslado_id = t.id) AS unidades
        FROM bc_traslados t WHERE {' AND '.join(conds)}
        ORDER BY t.numero DESC LIMIT 300
    """), p)).mappings().all()
    return [{**dict(f), "origen": grupo.get(f["origen_id"], f"Empresa {f['origen_id']}"),
             "destino": grupo.get(f["destino_id"], f"Empresa {f['destino_id']}"), "unidades": float(f["unidades"] or 0),
             "enviado_en": _iso(f["enviado_en"]), "cargado_en": _iso(f["cargado_en"]), "anulado_en": _iso(f["anulado_en"])}
            for f in filas]


async def detalle(db: AsyncSession, bodega: Bodega, tid: int) -> dict:
    t = (await db.execute(text("SELECT * FROM bc_traslados WHERE id = :t AND bodega_id = :b"),
                          {"t": tid, "b": bodega.id})).mappings().first()
    if not t:
        raise HTTPException(status_code=404, detail="Traslado no encontrado")
    grupo = await bc.empresas_grupo(db, bodega)
    items = (await db.execute(text("SELECT * FROM bc_traslado_items WHERE traslado_id = :t ORDER BY item"),
                              {"t": tid})).mappings().all()
    num = ("precio", "precio_minimo", "costo", "iva", "stock_minimo", "cantidad", "stock_origen_antes",
           "stock_origen_despues", "stock_destino_antes", "stock_destino_despues")
    cab = {k: v for k, v in dict(t).items() if k not in ("clave", "ip", "enviado_por_id")}
    for k in ("enviado_en", "salida_en", "cargado_en", "anulado_en", "created_at", "updated_at"):
        cab[k] = _iso(cab.get(k))
    cab["origen"] = grupo.get(t["origen_id"], f"Empresa {t['origen_id']}")
    cab["destino"] = grupo.get(t["destino_id"], f"Empresa {t['destino_id']}")
    return {"traslado": cab,
            "items": [{**dict(i), **{k: (float(i[k]) if i[k] is not None else None) for k in num}} for i in items]}


# ─── Agente Local (empresas con escritorio) ──────────────────────────────────
# El agente de cada sede con escritorio consulta sus tareas y reporta el resultado:
#   SALIDA  traslado con origen en su sede, PENDIENTE_SALIDA: descontar (verificando que tenga el stock).
#   CARGUE  traslado con destino en su sede, PENDIENTE_CARGUE: crear o actualizar el producto y sumar.
#   REVERSA traslado ANULADO con reversa_pendiente: devolver lo que su agente ya había descontado.
# El escritorio usa la tipificación 9 REMISIÓN MANUAL (desde la bodega) o 7 TRASLADO ENTRE SEDES.
TIPIF_REMISION, TIPIF_ENTRE_SEDES = 9, 7
MAX_TAREAS = 20


def _agente_como_bodega(bodega_id: int, nit: str, agente: dict) -> Bodega:
    from types import SimpleNamespace
    quien = f"Agente {agente.get('codigo') or ''} ({agente.get('empresa') or ''})".strip()[:150]
    return Bodega(id=bodega_id, nit=nit, user=SimpleNamespace(id=None, email=f"agente:{agente.get('codigo')}",
                                                              nombre=quien), ip="")


async def tareas_agente(db: AsyncSession, cid: int) -> list[dict]:
    filas = (await db.execute(text("""
        SELECT t.*, ob.name AS origen_nombre, de.name AS destino_nombre,
               CASE WHEN t.estado = 'PENDIENTE_SALIDA' AND t.origen_id = :c THEN 'SALIDA'
                    WHEN t.estado = 'PENDIENTE_CARGUE' AND t.destino_id = :c THEN 'CARGUE'
                    WHEN t.estado = 'ANULADO' AND t.reversa_pendiente = 1 AND t.origen_id = :c THEN 'REVERSA' END AS tarea
        FROM bc_traslados t
        JOIN companies ob ON ob.id_company = t.origen_id
        JOIN companies de ON de.id_company = t.destino_id
        WHERE (t.estado = 'PENDIENTE_SALIDA' AND t.origen_id = :c)
           OR (t.estado = 'PENDIENTE_CARGUE' AND t.destino_id = :c)
           OR (t.estado = 'ANULADO' AND t.reversa_pendiente = 1 AND t.origen_id = :c)
        ORDER BY t.id LIMIT :n
    """), {"c": cid, "n": MAX_TAREAS})).mappings().all()
    out = []
    for t in filas:
        items = (await db.execute(text("SELECT * FROM bc_traslado_items WHERE traslado_id = :t ORDER BY item"),
                                  {"t": t["id"]})).mappings().all()
        desde_bodega = int(t["origen_id"]) == int(t["bodega_id"])
        out.append({
            "id": int(t["id"]), "numero": int(t["numero"]), "tarea": t["tarea"],
            "tipificacion": TIPIF_REMISION if desde_bodega else TIPIF_ENTRE_SEDES,
            "origen": t["origen_nombre"], "destino": t["destino_nombre"], "observacion": t["observacion"] or "",
            "items": [{
                "id": int(i["id"]), "item": int(i["item"]), "origen_dish_id": int(i["origen_dish_id"]),
                "codigo": i["codigo"] or "", "nombre": i["nombre"], "categoria": i["categoria"] or "",
                "proveedor": i["proveedor"] or "", "proveedor_nit": i["proveedor_nit"] or "",
                "precio": float(i["precio"] or 0), "precio_minimo": float(i["precio_minimo"] or 0),
                "costo": float(i["costo"] or 0), "iva": float(i["iva"] or 0), "stock_minimo": float(i["stock_minimo"] or 0),
                "unitario": bool(i["desactivar_al_vender"]), "pedir_descripcion": bool(i["pedir_descripcion"]),
                "cantidad": float(i["cantidad"])} for i in items]})
    return out


async def resultado_agente(db: AsyncSession, agente: dict, r: dict) -> dict:
    """r: {id, tarea, ok, error, items: [{id, destino_dish_id, resultado, stock_antes, stock_despues}]}"""
    cid = int(agente["company_id"])
    t = (await db.execute(text("SELECT * FROM bc_traslados WHERE id = :t FOR UPDATE"), {"t": int(r["id"])})).mappings().first()
    if not t:
        return {"id": r["id"], "ok": False, "motivo": "no existe"}
    tarea = r["tarea"]
    esperado = {"SALIDA": (t["estado"] == "PENDIENTE_SALIDA" and int(t["origen_id"]) == cid),
                "CARGUE": (t["estado"] == "PENDIENTE_CARGUE" and int(t["destino_id"]) == cid),
                "REVERSA": (t["estado"] == "ANULADO" and int(t["reversa_pendiente"]) == 1 and int(t["origen_id"]) == cid)}
    if not esperado.get(tarea):
        return {"id": r["id"], "ok": True, "ignorado": True}        # repetido o ya no aplica: sin daño
    quien = f"Agente {agente.get('codigo')}"
    items = {int(i["id"]): i for i in r.get("items") or []}
    if tarea == "REVERSA":
        if r.get("ok"):
            await db.execute(text("UPDATE bc_traslados SET reversa_pendiente = 0, error = NULL WHERE id = :t"), {"t": t["id"]})
        else:                          # sigue pendiente: el agente reintenta
            await db.execute(text("UPDATE bc_traslados SET error = :e WHERE id = :t"),
                             {"e": (r.get("error") or "No se pudo devolver en el origen")[:255], "t": t["id"]})
        return {"id": r["id"], "ok": True}
    if not r.get("ok"):
        if tarea == "SALIDA":         # el origen no pudo descontar (ej. ya vendió): el traslado no sigue
            await db.execute(text("UPDATE bc_traslados SET estado = 'ERROR', error = :e WHERE id = :t"),
                             {"e": (r.get("error") or "No se pudo descontar en el origen")[:255], "t": t["id"]})
            await db.execute(text("UPDATE bc_traslado_items SET estado = 'ERROR' WHERE traslado_id = :t"), {"t": t["id"]})
        else:                          # cargue: queda pendiente con el mensaje (el agente reintenta)
            await db.execute(text("UPDATE bc_traslados SET error = :e WHERE id = :t"),
                             {"e": (r.get("error") or "No se pudo cargar en el destino")[:255], "t": t["id"]})
        return {"id": r["id"], "ok": True}
    nit = (await db.execute(text("SELECT identification_number FROM companies WHERE id_company = :b"),
                            {"b": t["bodega_id"]})).scalar() or ""
    bod = _agente_como_bodega(int(t["bodega_id"]), str(nit), agente)
    if tarea == "SALIDA":
        for iid, it in items.items():
            await db.execute(text("""
                UPDATE bc_traslado_items SET stock_origen_antes = :a, stock_origen_despues = :d
                WHERE id = :id AND traslado_id = :t
            """), {"a": it.get("stock_antes"), "d": it.get("stock_despues"), "id": iid, "t": t["id"]})
        await db.execute(text("""
            UPDATE bc_traslados SET estado = 'PENDIENTE_CARGUE', salida_en = NOW(), salida_por = :p, error = NULL
            WHERE id = :t
        """), {"p": quien, "t": t["id"]})
        if not await es_escritorio(db, int(t["destino_id"])):       # destino web: se carga ya
            await cargar_en_web(db, bod, int(t["id"]))
        return {"id": r["id"], "ok": True}
    # CARGUE
    for iid, it in items.items():
        dd = int(it.get("destino_dish_id") or 0)
        await db.execute(text("""
            UPDATE bc_traslado_items SET destino_dish_id = :dd, resultado = :r, estado = 'CARGADO',
                   stock_destino_antes = :a, stock_destino_despues = :d WHERE id = :id AND traslado_id = :t
        """), {"dd": dd or None, "r": it.get("resultado") if it.get("resultado") in ("CREADO", "ACTUALIZADO") else None,
               "a": it.get("stock_antes"), "d": it.get("stock_despues"), "id": iid, "t": t["id"]})
        orig = (await db.execute(text("SELECT origen_dish_id FROM bc_traslado_items WHERE id = :id"), {"id": iid})).scalar()
        if dd and orig:
            await _vincular(db, bod, dict(t), int(orig), dd)
    await db.execute(text("""
        UPDATE bc_traslados SET estado = 'CARGADO', cargado_en = NOW(), cargado_por = :p, error = NULL WHERE id = :t
    """), {"p": quien, "t": t["id"]})
    return {"id": r["id"], "ok": True}
