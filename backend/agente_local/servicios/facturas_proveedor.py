"""
Factura de Proveedor registrada en la web → escritorio (automático, sin cajero).

  Cada 15 s: GET /api/agente/facturas-proveedor/pendientes → facturas de esta sede, se aplican en la BD del
  escritorio y se reporta el resultado (POST /api/agente/facturas-proveedor/resultado). La web solo entrega una
  factura cuando todos sus productos y el proveedor ya tienen número real (bajaron con el catálogo).
    APLICAR  igual que el formulario de registro de precios del escritorio, por cada línea:
             inventario_porciones_precios (Id_Registro nuevo, costo anterior y nuevo), entrada manual con la
             tipificación 7 "REGISTRO PRECIOS" (Autorizada = Id_Registro; Enviada_MySql = 1 porque la web ya la
             tiene), la cantidad se suma a Cantidad_Actual y el costo nuevo queda en inventario_porciones
             (Costo y Valor_Und_Compra) y en platos.Costo_Producto.
    REVERSA  la factura se anuló en la web: como "eliminar" del formulario del escritorio, borra el registro de
             precios y la entrada manual, resta la cantidad y devuelve el costo anterior — solo de las líneas que
             este agente alcanzó a aplicar.

  Tablas MyISAM (sin rollback): cada línea aplicada queda en ag_fp_item (datatemppos) antes de seguir con la
  siguiente; un reintento después de una caída no la aplica dos veces.
"""
import json
import logging
from datetime import datetime

from sqlalchemy import text

from .. import nube
from ..db import SesionTemp, motor_empresa
from .traslados_bodega import _actualizar, _insertar, _insumo, _stock, _unidad

log = logging.getLogger("agente_local")

CADA_SEG = 15
TIPIFICACION = 7
NOMBRE_TIPIF = "REGISTRO PRECIOS"
estado = {"ultimo_ok": None, "ultimo_error": None, "mensaje": None, "aplicadas": 0}


async def _hecho(fid: int, item: int):
    async with SesionTemp() as s:
        r = (await s.execute(text("SELECT resultado FROM ag_fp_item WHERE factura_id = :f AND item = :i"),
                             {"f": fid, "i": item})).scalar()
    return json.loads(r) if r else None


async def _marcar(fid: int, item: int, resultado: dict) -> None:
    async with SesionTemp() as s:
        await s.execute(text("""
            INSERT INTO ag_fp_item (factura_id, item, resultado, aplicado) VALUES (:f, :i, :r, NOW())
            ON DUPLICATE KEY UPDATE resultado = :r, aplicado = NOW()
        """), {"f": fid, "i": item, "r": json.dumps(resultado)})
        await s.commit()


async def _aplicadas(fid: int) -> list[tuple[int, dict]]:
    async with SesionTemp() as s:
        filas = (await s.execute(text(
            "SELECT item, resultado FROM ag_fp_item WHERE factura_id = :f AND resultado NOT LIKE '%\"revertida\": true%'"),
            {"f": fid})).all()
    return [(int(i), json.loads(r)) for i, r in filas]


async def _registro(fid: int):
    async with SesionTemp() as s:
        return (await s.execute(text("SELECT registro FROM ag_fp_registro WHERE factura_id = :f"), {"f": fid})).scalar()


async def _nuevo_registro(conn, fid: int) -> int:
    """Id_Registro del escritorio para esta factura (uno por factura, como "nueva entrada" del formulario)."""
    ya = await _registro(fid)
    if ya:
        return int(ya)
    reg = int((await conn.execute(text("SELECT COALESCE(MAX(Id_Registro), 0) + 1 FROM inventario_porciones_precios"))).scalar())
    async with SesionTemp() as s:
        await s.execute(text("INSERT INTO ag_fp_registro (factura_id, registro, creado) VALUES (:f, :r, NOW())"),
                        {"f": fid, "r": reg})
        await s.commit()
    return reg


async def aplicar(conn, t: dict) -> dict:
    fid = int(t["id"])
    reg = await _nuevo_registro(conn, fid)
    unidad = await _unidad(conn)
    ahora = datetime.now()
    for ln in t["lineas"]:
        if await _hecho(fid, ln["item"]):
            continue
        id_plato = int(ln["id_plato"])
        ins = await _insumo(conn, id_plato)
        if not ins:
            raise RuntimeError(f"«{ln['nombre']}» no existe en el escritorio o lleva receta")
        grupo, item = ins
        posicion = int((await conn.execute(text(
            "SELECT Posicion FROM inventario_porciones WHERE Id_Grupo = :g AND Id_Item = :i LIMIT 1"),
            {"g": grupo, "i": item})).scalar() or item)
        fila = (await conn.execute(text(
            "SELECT Costo, Codigo_Insumo, Agrupar FROM inventario_porciones WHERE Id_Grupo = :g AND Id_Item = :i LIMIT 1"),
            {"g": grupo, "i": item})).first()
        costo_anterior = float(fila[0] or 0) if fila else float(ln["precio_anterior"] or 0)
        await _insertar(conn, "inventario_porciones_precios", {
            "Id_Registro": reg, "Item": int(ln["item"]), "Id_Proveedor": int(t["id_proveedor"]), "Posicion": posicion,
            "Fecha_Registro": t["fecha"], "Precio_Anterior": int(round(costo_anterior)),
            "Precio_Actual": int(round(ln["precio"])), "Cantidad": ln["cantidad"], "Total_Articulo": ln["total"],
            "Id_Presentacion": unidad, "Descripcion": ln["nombre"][:255], "Nro_Factura": t["nro_factura"]})
        await _insertar(conn, "inventarios_entradas_manuales", {
            "id_proveedor": int(t["id_proveedor"]), "Agrupar": int((fila[2] if fila else 0) or 0),
            "Id_Novedad": TIPIFICACION, "Nombre_Novedad": NOMBRE_TIPIF, "Id_Grupo": grupo, "Id_Item": item,
            "Producto": ln["nombre"][:250], "Fecha": t["fecha"], "Turno": 1, "Cantidad": ln["cantidad"], "Usuario": 0,
            "Nombre_Usuario": t["nro_factura"][:100], "Hora": ahora.strftime("%H:%M:%S"),
            "Observacion": f"{(t.get('observacion') or '').strip()} {NOMBRE_TIPIF} (web)".strip()[:250],
            "Codigo_Motivo": TIPIFICACION, "Enviada_Correo": 0, "Posicion": posicion,
            "Codigo_Insumo": (fila[1] if fila else ln["codigo"]) or "", "Autorizada": reg,
            "Enviada_MySql": 1})                         # la web ya tiene esta entrada: no se vuelve a subir
        await conn.execute(text("""
            UPDATE inventario_actual_porciones SET Cantidad_Actual = Cantidad_Actual + :q, Costo = :c, Enviada_MySql = 0
            WHERE Id_Grupo = :g AND Id_Item = :i
        """), {"q": ln["cantidad"], "c": ln["precio"], "g": grupo, "i": item})
        await _actualizar(conn, "inventario_porciones", {"Costo": ln["precio"], "Und_Compra": unidad,
                                                         "Valor_Und_Compra": ln["precio"], "Enviada_MySql": 0},
                          "Id_Grupo = :g AND Id_Item = :i", {"g": grupo, "i": item})
        await _actualizar(conn, "platos", {"Costo_Producto": ln["precio"], "Enviada_MySql": 0},
                          "Id_Plato = :p", {"p": id_plato})
        await conn.commit()
        await _marcar(fid, ln["item"], {"grupo": grupo, "item": item, "posicion": posicion, "id_plato": id_plato,
                                        "cantidad": ln["cantidad"], "costo_anterior": costo_anterior,
                                        "stock": await _stock(conn, grupo, item)})
    return {"id": fid, "tarea": "APLICAR", "ok": True, "registro": reg}


async def reversar(conn, t: dict) -> dict:
    fid = int(t["id"])
    reg = await _registro(fid)
    for n, r in await _aplicadas(fid):
        if reg:
            await conn.execute(text("DELETE FROM inventario_porciones_precios WHERE Id_Registro = :r AND Item = :n"),
                               {"r": reg, "n": n})
            await conn.execute(text("""
                DELETE FROM inventarios_entradas_manuales
                WHERE Id_Novedad = :t AND Codigo_Motivo = :t AND Autorizada = :r AND Id_Grupo = :g AND Id_Item = :i
                LIMIT 1
            """), {"t": TIPIFICACION, "r": reg, "g": r["grupo"], "i": r["item"]})
        await conn.execute(text("""
            UPDATE inventario_actual_porciones SET Cantidad_Actual = Cantidad_Actual - :q, Costo = :c, Enviada_MySql = 0
            WHERE Id_Grupo = :g AND Id_Item = :i
        """), {"q": r["cantidad"], "c": r["costo_anterior"], "g": r["grupo"], "i": r["item"]})
        await _actualizar(conn, "inventario_porciones", {"Costo": r["costo_anterior"], "Valor_Und_Compra": r["costo_anterior"],
                                                         "Enviada_MySql": 0},
                          "Id_Grupo = :g AND Id_Item = :i", {"g": r["grupo"], "i": r["item"]})
        await _actualizar(conn, "platos", {"Costo_Producto": r["costo_anterior"], "Enviada_MySql": 0},
                          "Id_Plato = :p", {"p": r["id_plato"]})
        await conn.commit()
        await _marcar(fid, n, {**r, "revertida": True})
    return {"id": fid, "tarea": "REVERSA", "ok": True, "registro": reg}


async def procesar() -> int:
    r = await nube.pedir("GET", "/api/agente/facturas-proveedor/pendientes") or {}
    tareas = r.get("tareas") or []
    if not tareas:
        return 0
    resultados = []
    async with motor_empresa.connect() as conn:
        lock = (await conn.execute(text("SELECT GET_LOCK('ag_facturas_proveedor', 5)"))).scalar()
        await conn.commit()
        if lock != 1:
            return 0
        try:
            for t in tareas:
                try:
                    resultados.append(await (aplicar(conn, t) if t["tarea"] == "APLICAR" else reversar(conn, t)))
                except Exception as e:            # queda pendiente con el error a la vista y se reintenta
                    log.exception("Factura de proveedor %s", t.get("id"))
                    resultados.append({"id": t["id"], "tarea": t["tarea"], "ok": False,
                                       "error": f"Error en el escritorio: {e}"[:250]})
        finally:
            await conn.execute(text("SELECT RELEASE_LOCK('ag_facturas_proveedor')"))
            await conn.commit()
    if resultados:
        await nube.pedir("POST", "/api/agente/facturas-proveedor/resultado", {"resultados": resultados})
        estado["aplicadas"] += sum(1 for x in resultados if x.get("ok"))
    return len(resultados)


async def ciclo() -> None:
    """Tarea de fondo: cada 15 s baja las facturas de proveedor de la web. Nunca se detiene."""
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
            log.exception("Ciclo de facturas de proveedor")
            estado.update(ultimo_error=datetime.now(), mensaje=f"Error en facturas de proveedor: {e}")
        await asyncio.sleep(CADA_SEG)
