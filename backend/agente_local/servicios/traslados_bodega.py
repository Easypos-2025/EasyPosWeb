"""
Traslados de la Bodega Central en el escritorio (automático, sin cajero).

  Cada 15 s: GET /api/agente/traslados/pendientes → tareas de esta sede, se aplican en la BD del escritorio y se
  reporta el resultado (POST /api/agente/traslados/resultado).
    SALIDA   el traslado sale de esta sede: se verifica que haya la cantidad de TODOS los artículos (si falta
             alguno no se toca nada y se reporta el error) y se descuenta.
    CARGUE   el traslado llega a esta sede: el producto se busca por código (o por nombre si no tiene); si existe
             se actualizan sus valores con la regla del cero (un 0 no cambia el valor de la sede) y si no, se CREA
             igual que Crear_Plato_Nuevo (platos, plato_producto, inventario_porciones, inventario_actual_porciones,
             inventario_porciones_plato). La cantidad se SUMA.
    REVERSA  se anuló un traslado que esta sede ya había descontado: se devuelve la cantidad.
  Cada movimiento queda como entrada / salida manual con la tipificación 9 REMISIÓN MANUAL (desde la bodega) o
  7 TRASLADO ENTRE SEDES, y Cantidad_Actual se ajusta al instante (igual que el escritorio: ModRecalcularStock).

  Las tablas del escritorio son MyISAM (sin rollback): cada artículo aplicado queda en ag_bc_item (datatemppos)
  ANTES de seguir con el siguiente, así un reintento después de una caída no lo aplica dos veces.
"""
import json
import logging
from datetime import datetime

from sqlalchemy import text

from .. import nube
from ..db import SesionTemp, motor_empresa

log = logging.getLogger("agente_local")

CADA_SEG = 15
ID_PROVISIONAL = 900_000_000
USUARIO = "AGENTE BODEGA"
NOMBRES_TIPIF = {9: "REMISION MANUAL", 7: "TRASLADO PRODUCTO ENTRE SEDES"}
estado = {"ultimo_ok": None, "ultimo_error": None, "mensaje": None, "aplicados": 0}


class SinStock(Exception):
    pass


# ───────────────────────────── ayudas de escritura ─────────────────────────────

_cols_cache: dict = {}


async def _columnas(conn, tabla: str) -> dict:
    if tabla not in _cols_cache:
        filas = (await conn.execute(text("""
            SELECT column_name FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = :t
        """), {"t": tabla})).all()
        _cols_cache[tabla] = {c.lower(): c for (c,) in filas}
    return _cols_cache[tabla]


async def _insertar(conn, tabla: str, datos: dict) -> None:
    """INSERT solo con las columnas que existen en la tabla de esta sede."""
    cols = await _columnas(conn, tabla)
    d = {cols[k.lower()]: v for k, v in datos.items() if k.lower() in cols}
    if not d:
        return
    await conn.execute(text(f"INSERT INTO {tabla} ({', '.join(f'`{c}`' for c in d)}) "
                            f"VALUES ({', '.join(f':p{i}' for i in range(len(d)))})"),
                       {f"p{i}": v for i, v in enumerate(d.values())})


async def _actualizar(conn, tabla: str, datos: dict, donde: str, params: dict) -> None:
    cols = await _columnas(conn, tabla)
    d = {cols[k.lower()]: v for k, v in datos.items() if k.lower() in cols}
    if not d:
        return
    await conn.execute(text(f"UPDATE {tabla} SET {', '.join(f'`{c}` = :p{i}' for i, c in enumerate(d))} WHERE {donde}"),
                       {**{f"p{i}": v for i, v in enumerate(d.values())}, **params})


def _nombre_porcion(nombre: str) -> str:
    s = (nombre or "").replace(" ", "_")
    for ch in ("'", "@", "!", "ç", "`", "´"):
        s = s.replace(ch, "")
    return s[:250]


async def _insumo(conn, id_plato: int):
    """(Id_Grupo, Id_Item) del producto: su único insumo; si no tiene receta, el mismo Id_Plato (almacén)."""
    filas = (await conn.execute(text(
        "SELECT Id_Grupo, Id_Item FROM inventario_porciones_plato WHERE Id_Plato = :p"), {"p": id_plato})).all()
    if len(filas) == 1:
        return int(filas[0][0]), int(filas[0][1])
    if not filas and (await conn.execute(text(
            "SELECT COUNT(*) FROM inventario_actual_porciones WHERE Id_Grupo = 1 AND Id_Item = :p"), {"p": id_plato})).scalar():
        return 1, int(id_plato)
    return None


async def _stock(conn, grupo: int, item: int) -> float:
    return float((await conn.execute(text(
        "SELECT Cantidad_Actual FROM inventario_actual_porciones WHERE Id_Grupo = :g AND Id_Item = :i"),
        {"g": grupo, "i": item})).scalar() or 0)


async def _mover(conn, entrada: bool, grupo: int, item: int, producto: str, codigo: str, cantidad: float,
                 tipif: int, observacion: str, agrupar: int) -> None:
    ahora = datetime.now()
    await _insertar(conn, "inventarios_entradas_manuales" if entrada else "inventarios_salidas_manuales", {
        "Agrupar": agrupar, "Id_Novedad": tipif, "Nombre_Novedad": NOMBRES_TIPIF.get(tipif, "TRASLADO"),
        "Id_Grupo": grupo, "Id_Item": item, "Producto": producto[:250], "Fecha": ahora.date(), "Turno": 1,
        "Cantidad": cantidad, "Usuario": 0, "Nombre_Usuario": USUARIO, "Hora": ahora.strftime("%H:%M:%S"),
        "Observacion": observacion[:250], "Codigo_Motivo": tipif, "Autorizada": 1, "Revisada": 0, "Cobrar": 0,
        "Enviada_Correo": 0, "Posicion": item, "Codigo_Insumo": codigo or "", "Enviada_MySql": 0})
    await conn.execute(text(f"""
        UPDATE inventario_actual_porciones SET Cantidad_Actual = Cantidad_Actual {'+' if entrada else '-'} :q,
               Controlar = 1, Enviada_MySql = 0
        WHERE Id_Grupo = :g AND Id_Item = :i
    """), {"q": cantidad, "g": grupo, "i": item})


# ───────────────────────────── producto en el escritorio ─────────────────────────────

async def _buscar_producto(conn, codigo: str, nombre: str):
    if (codigo or "").strip():
        p = (await conn.execute(text(
            "SELECT Id_Plato FROM platos WHERE TRIM(Codigo_Producto) = :c ORDER BY Id_Plato LIMIT 1"),
            {"c": codigo.strip()})).scalar()
        if p:
            return int(p)
        return None
    p = (await conn.execute(text("SELECT Id_Plato FROM platos WHERE TRIM(Nombre) = :n ORDER BY Id_Plato LIMIT 1"),
                            {"n": (nombre or "").strip()})).scalar()
    return int(p) if p else None


async def _categoria(conn, nombre: str) -> int:
    nombre = (nombre or "GENERAL").strip()[:100] or "GENERAL"
    c = (await conn.execute(text(
        "SELECT Cod_Categoria FROM categoria_platos WHERE UPPER(TRIM(Nombre)) = :n ORDER BY Cod_Categoria LIMIT 1"),
        {"n": nombre.upper()})).scalar()
    if c:
        return int(c)
    nuevo = int((await conn.execute(text("SELECT COALESCE(MAX(Cod_Categoria), 0) + 1 FROM categoria_platos "
                                         "WHERE Cod_Categoria < :p"), {"p": ID_PROVISIONAL})).scalar())
    await _insertar(conn, "categoria_platos", {
        "Cod_Categoria": nuevo, "Categoria": nombre, "Nombre": nombre, "Porcentaje": 0, "Turno": 0, "Lunes": 1,
        "Martes": 1, "Miercoles": 1, "Jueves": 1, "Viernes": 1, "Sabado": 1, "Domingo": 1, "Activa": 1, "Enviada_MySql": 0})
    return nuevo


async def _proveedor(conn, nombre: str, nit: str) -> int:
    nit, nombre = (nit or "").strip(), (nombre or "").strip()[:100]
    if nit:
        p = (await conn.execute(text("SELECT Id_Proveedor FROM proveedores WHERE TRIM(Nit) = :n LIMIT 1"), {"n": nit})).scalar()
        if p:
            return int(p)
    if not nombre:
        nombre = "VARIOS"
    p = (await conn.execute(text("SELECT Id_Proveedor FROM proveedores WHERE UPPER(TRIM(Empresa)) = :n LIMIT 1"),
                            {"n": nombre.upper()})).scalar()
    if p:
        return int(p)
    nuevo = int((await conn.execute(text("SELECT COALESCE(MAX(Id_Proveedor), 0) + 1 FROM proveedores "
                                         "WHERE Id_Proveedor < :p"), {"p": ID_PROVISIONAL})).scalar())
    await _insertar(conn, "proveedores", {"Id_Proveedor": nuevo, "Nit": nit, "Empresa": nombre, "Activo": 1,
                                          "Enviada_MySql": 0})
    return nuevo


async def _unidad(conn) -> int:
    for desc in ("UNIDAD", "PORCION"):
        f = (await conn.execute(text("SELECT Id_Forma_Medida FROM forma_medida WHERE UPPER(TRIM(Descripcion)) = :d LIMIT 1"),
                                {"d": desc})).scalar()
        if f:
            return int(f)
    return 1


async def _crear_producto(conn, it: dict) -> int:
    """Como Crear_Plato_Nuevo del escritorio (almacén: el producto es su propio insumo, Id_Item = Id_Plato)."""
    categoria = await _categoria(conn, it["categoria"])
    proveedor = await _proveedor(conn, it["proveedor"], it["proveedor_nit"])
    unidad = await _unidad(conn)
    id_plato = int((await conn.execute(text("""
        SELECT GREATEST(COALESCE((SELECT MAX(Id_Plato) FROM platos WHERE Id_Plato < :p), 0),
                        COALESCE((SELECT MAX(Id_Item) FROM inventario_porciones WHERE Id_Grupo = 1 AND Id_Item < :p), 0)) + 1
    """), {"p": ID_PROVISIONAL})).scalar())
    nombre = (it["nombre"] or "").strip()[:250]
    if (await conn.execute(text("SELECT COUNT(*) FROM platos WHERE TRIM(Nombre) = :n"), {"n": nombre})).scalar():
        nombre = f"{nombre} {it['codigo']}".strip()[:250]
    porcion = _nombre_porcion(nombre)
    hoy = datetime.now().date()
    await _insertar(conn, "platos", {
        "Id_Plato": id_plato, "Nombre": nombre, "Codigo_Producto": it["codigo"], "Valor": int(round(it["precio"])),
        "Cod_Categoria": categoria, "Procedimiento": "", "Impresora": "Caja", "Impuesto": it["iva"],
        "Precio_x_Mayor": it["precio_minimo"], "Costo_Producto": it["costo"], "Stock_Minimo": it["stock_minimo"],
        "Pedir_Valor_Venta_Producto": 0, "Pedir_Descripcion_Producto": 1 if it["pedir_descripcion"] else 0,
        "Preparacion_Previa": 0, "Impresora_2": "", "Prioridad_Ofrecer": 0, "Tiempo": 0,
        "Impresion_Extra": "1" if it["unitario"] else "0", "Activo": 0, "Enviada_MySql": 0})
    await _insertar(conn, "plato_producto", {
        "Id_Proveedor": proveedor, "Id_Plato": id_plato, "Id_Forma_Medida": unidad, "Unidades_Minimas": 2,
        "Valor_Presentacion": int(round(it["precio"])), "Descripcion": "Unidad", "Activo": 0, "Enviada_MySql": 0})
    base = {"Id_Grupo": 1, "Id_Item": id_plato, "Descripcion": porcion, "Posicion": id_plato, "Costo": it["costo"],
            "Und_Min_Utilizadas": 1, "Agrupar": categoria, "Controlar": 1, "Und_Uso": unidad, "Bodega": 1,
            "Und_Compra": unidad, "Valor_Und_Compra": 0, "Codigo_Insumo": it["codigo"], "Fecha_Vence": hoy,
            "Stock_Minimo": it["stock_minimo"], "Enviada_MySql": 0}
    await _insertar(conn, "inventario_porciones", {**base, "Tipo_Und_Minima": unidad, "Cant_Und_Minimas": 1})
    await _insertar(conn, "inventario_actual_porciones", {**base, "Cantidad_Actual": 0})
    await _insertar(conn, "inventario_porciones_plato", {
        "Id_Plato": id_plato, "Id_Grupo": 1, "Id_Item": id_plato, "Cantidad": 1, "Unidad_Minima": 1,
        "Porciones_A_Desccontar": 1, "Posicion": id_plato, "Opcion_Cambiar": 0, "Enviada_MySql": 0})
    imp = (await conn.execute(text("SELECT Id_Impresora FROM impresoras WHERE UPPER(TRIM(Nombre)) = 'CAJA' LIMIT 1"))).scalar()
    if imp:
        await _insertar(conn, "plato_impresoras", {"Id_Plato": id_plato, "Id_Impresora": int(imp), "Enviada_MySql": 0})
    return id_plato


async def _actualizar_valores(conn, id_plato: int, it: dict) -> None:
    """Regla del cero: solo los valores distintos de 0 reemplazan los del escritorio."""
    v = {}
    if it["precio"]:
        v["Valor"] = int(round(it["precio"]))
    if it["precio_minimo"]:
        v["Precio_x_Mayor"] = it["precio_minimo"]
    if it["costo"]:
        v["Costo_Producto"] = it["costo"]
    if it["iva"]:
        v["Impuesto"] = it["iva"]
    if it["stock_minimo"]:
        v["Stock_Minimo"] = it["stock_minimo"]
    if it["unitario"]:
        v.update(Impresion_Extra="1", Activo=0)          # una unidad con IMEI que vuelve: queda vendible
    if v:
        await _actualizar(conn, "platos", {**v, "Enviada_MySql": 0}, "Id_Plato = :id", {"id": id_plato})
    if "Valor" in v:
        await _actualizar(conn, "plato_producto", {"Valor_Presentacion": v["Valor"], "Enviada_MySql": 0},
                          "Id_Plato = :id", {"id": id_plato})
    ins = await _insumo(conn, id_plato)
    if ins and ("Costo_Producto" in v or "Stock_Minimo" in v):
        cambios = {}
        if "Costo_Producto" in v:
            cambios["Costo"] = v["Costo_Producto"]
        if "Stock_Minimo" in v:
            cambios["Stock_Minimo"] = v["Stock_Minimo"]
        for tabla in ("inventario_porciones", "inventario_actual_porciones"):
            await _actualizar(conn, tabla, {**cambios, "Enviada_MySql": 0}, "Id_Grupo = :g AND Id_Item = :i",
                              {"g": ins[0], "i": ins[1]})


# ───────────────────────────── control local (sin doble aplicación) ─────────────────────────────

async def _hecho(tid: int, tarea: str, item_id: int):
    async with SesionTemp() as s:
        r = (await s.execute(text(
            "SELECT resultado FROM ag_bc_item WHERE traslado_id = :t AND tarea = :k AND item_id = :i"),
            {"t": tid, "k": tarea, "i": item_id})).scalar()
    return json.loads(r) if r else None


async def _marcar(tid: int, tarea: str, item_id: int, resultado: dict) -> None:
    async with SesionTemp() as s:
        await s.execute(text("""
            INSERT INTO ag_bc_item (traslado_id, tarea, item_id, resultado, aplicado)
            VALUES (:t, :k, :i, :r, NOW())
        """), {"t": tid, "k": tarea, "i": item_id, "r": json.dumps(resultado)})
        await s.commit()


# ───────────────────────────── aplicar una tarea ─────────────────────────────

async def aplicar(conn, t: dict) -> dict:
    tid, tarea, tipif = int(t["id"]), t["tarea"], int(t["tipificacion"])
    nota = (f"Traslado #{t['numero']} desde {t['origen']}" if tarea == "CARGUE" else
            f"Traslado #{t['numero']} a {t['destino']}" if tarea == "SALIDA" else
            f"Anulación traslado #{t['numero']}")
    items = []

    if tarea in ("SALIDA", "REVERSA"):
        # el producto es el del origen (esta sede): su número del escritorio
        pendientes = []
        for it in t["items"]:
            hecho = await _hecho(tid, tarea, it["id"])
            if hecho:
                items.append(hecho)
                continue
            id_plato = it["origen_dish_id"]
            if not (await conn.execute(text("SELECT COUNT(*) FROM platos WHERE Id_Plato = :p"), {"p": id_plato})).scalar():
                id_plato = await _buscar_producto(conn, it["codigo"], it["nombre"])
            ins = await _insumo(conn, id_plato) if id_plato else None
            if not ins:
                raise SinStock(f"«{it['nombre']}» no existe en el escritorio de esta sede")
            pendientes.append((it, id_plato, ins))
        if tarea == "SALIDA":           # todo o nada: si falta stock de alguno no se descuenta ninguno
            for it, _, ins in pendientes:
                disp = await _stock(conn, *ins)
                if disp < it["cantidad"]:
                    raise SinStock(f"«{it['nombre']}»: hay {disp:g} y el traslado pide {it['cantidad']:g}")
        for it, id_plato, ins in pendientes:
            antes = await _stock(conn, *ins)
            cat = (await conn.execute(text("SELECT Cod_Categoria FROM platos WHERE Id_Plato = :p"), {"p": id_plato})).scalar() or 0
            await _mover(conn, tarea == "REVERSA", ins[0], ins[1], it["nombre"], it["codigo"], it["cantidad"], tipif, nota, int(cat))
            await conn.commit()
            r = {"id": it["id"], "stock_antes": antes, "stock_despues": await _stock(conn, *ins)}
            await _marcar(tid, tarea, it["id"], r)
            items.append(r)
        return {"id": tid, "tarea": tarea, "ok": True, "items": items}

    # CARGUE
    for it in t["items"]:
        hecho = await _hecho(tid, tarea, it["id"])
        if hecho:
            items.append(hecho)
            continue
        id_plato = await _buscar_producto(conn, it["codigo"], it["nombre"])
        if id_plato:
            resultado = "ACTUALIZADO"
            await _actualizar_valores(conn, id_plato, it)
        else:
            resultado = "CREADO"
            id_plato = await _crear_producto(conn, it)
        await conn.commit()
        ins = await _insumo(conn, id_plato)
        if not ins:
            raise SinStock(f"«{it['nombre']}» tiene receta en el escritorio: no se puede cargar como artículo")
        antes = await _stock(conn, *ins)
        cat = (await conn.execute(text("SELECT Cod_Categoria FROM platos WHERE Id_Plato = :p"), {"p": id_plato})).scalar() or 0
        await _mover(conn, True, ins[0], ins[1], it["nombre"], it["codigo"], it["cantidad"], tipif, nota, int(cat))
        await conn.commit()
        r = {"id": it["id"], "destino_dish_id": id_plato, "resultado": resultado, "stock_antes": antes,
             "stock_despues": await _stock(conn, *ins)}
        await _marcar(tid, tarea, it["id"], r)
        items.append(r)
    return {"id": tid, "tarea": tarea, "ok": True, "items": items}


async def procesar() -> int:
    r = await nube.pedir("GET", "/api/agente/traslados/pendientes") or {}
    tareas = r.get("tareas") or []
    if not tareas:
        return 0
    resultados = []
    async with motor_empresa.connect() as conn:
        lock = (await conn.execute(text("SELECT GET_LOCK('ag_traslados', 5)"))).scalar()
        await conn.commit()
        if lock != 1:
            return 0
        try:
            for t in tareas:
                try:
                    resultados.append(await aplicar(conn, t))
                except SinStock as e:
                    resultados.append({"id": t["id"], "tarea": t["tarea"], "ok": False, "error": str(e)[:250]})
                except Exception as e:            # error de BD u otro: se reporta y se reintenta en el próximo ciclo
                    log.exception("Traslado %s", t.get("id"))
                    resultados.append({"id": t["id"], "tarea": t["tarea"], "ok": False,
                                       "error": f"Error en el escritorio: {e}"[:250]})
                    if t["tarea"] == "SALIDA":     # una salida con error técnico no se da por fallida: se reintenta
                        resultados.pop()
        finally:
            await conn.execute(text("SELECT RELEASE_LOCK('ag_traslados')"))
            await conn.commit()
    if resultados:
        await nube.pedir("POST", "/api/agente/traslados/resultado", {"resultados": resultados})
        estado["aplicados"] += sum(1 for x in resultados if x.get("ok"))
    return len(resultados)


async def ciclo() -> None:
    """Tarea de fondo: cada 15 s aplica los traslados de esta sede. Nunca se detiene."""
    import asyncio
    from .. import config
    if not config.NUBE_CLAVE:
        return
    while True:
        try:
            await procesar()
            estado.update(ultimo_ok=datetime.now(), mensaje=None)
        except nube.ErrorNube as e:
            estado.update(ultimo_error=datetime.now(), mensaje=str(e))
        except Exception as e:
            log.exception("Ciclo de traslados")
            estado.update(ultimo_error=datetime.now(), mensaje=f"Error en traslados: {e}")
        await asyncio.sleep(CADA_SEG)
