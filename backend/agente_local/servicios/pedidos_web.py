"""
Pedidos web → escritorio (sala de espera con aceptación en caja).

  1. descargar()  cada 10 s: lotes pendientes de la nube → ag_pw_lote / ag_pw_item, y confirma que llegaron.
  2. El cajero acepta o rechaza (con motivo): form VB6 (frmPedidosWeb) o panel de la mini-app.
     Solo cambian ag_pw_lote.estado PENDIENTE → ACEPTADO / RECHAZADO (con quién, desde dónde y cuándo).
  3. aplicar_aceptados()  cada 2 s: pasa los ACEPTADOS a los temporales del escritorio, igual que
     "Enviar pedido" de la toma de pedidos (tablas gemelas, cola de impresión, Enviada_MySql de último).
       · Precio: el de la nube (decisión del usuario 2026-10-10).
       · Orden por pedido: un lote espera a que se aplique el anterior del mismo pedido.
       · Si no se puede (caja cerrada, mesa ocupada, pedido ya cerrado, producto inexistente) queda
         en ERROR con el mensaje: se puede volver a aceptar o rechazar.
  4. reportar()  cada ciclo: lo que cambió de estado (nube_estado <> estado) se reporta a la nube.

Nada se borra de ag_pw_*: es el histórico (también queda en la nube) para reclamos.
Las tablas del escritorio son MyISAM (sin rollback): se escribe en el mismo orden que el VB6 y el
mapa ítem web → Depende evita aplicar dos veces un lote si el agente se cae a mitad de camino.
"""
import json
import logging
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .. import nube
from ..db import SesionEmpresa, SesionTemp
from . import catalogo, impresion
from .negocio import exigir_caja_abierta, facturacion
from .pedidos import hora_corta, limpiar_texto, partes_cantidad, siguiente_item

log = logging.getLogger("agente_local")

ENVIADO_DESDE = "WEB"
MAX_TEXTO = 250
ESTADOS_PROCESADOS = ("APLICADO", "RECHAZADO")
estado = {"ultimo_ok": None, "ultimo_error": None, "mensaje": None}


class NoAplicable(Exception):
    """El lote no se puede pasar al escritorio ahora: queda en ERROR con este mensaje."""


def _entero(v, defecto: int = 0, minimo: int = 0, maximo: int = 2_000_000_000) -> int:
    try:
        n = int(v)
    except (TypeError, ValueError):
        return defecto
    return n if minimo <= n <= maximo else defecto


def _decimal(v, maximo: float = 10_000) -> float:
    try:
        n = round(float(v), 4)
    except (TypeError, ValueError):
        return 0.0
    return n if 0 <= n <= maximo else 0.0


def _fecha(v):
    try:
        return datetime.fromisoformat(str(v)) if v else None
    except ValueError:
        return None


# ───────────────────────────── 1. descargar ─────────────────────────────

async def descargar() -> int:
    r = await nube.pedir("GET", "/api/agente/pedidos/pendientes") or {}
    lotes = r.get("lotes") or []
    if not lotes:
        return 0
    recibidos = []
    async with SesionTemp() as s:
        for L in lotes[:50]:
            lote_id = _entero(L.get("id"), 0, 1)
            nro = limpiar_texto(L.get("nro_pedido"), 255)
            tipo = L.get("tipo") if L.get("tipo") in ("NUEVO", "AGREGAR") else None
            items = L.get("items") or []
            if not lote_id or not nro or not tipo or not items or len(items) > 200:
                continue
            await s.execute(text("""
                INSERT IGNORE INTO ag_pw_lote
                    (id, nro_pedido, tipo, canal, id_mesa, mesa, mesero, mesero_nombre, id_cliente, comensales,
                     total, items, enviado_por, creado_en, recibido_en, estado)
                VALUES (:id, :nro, :tipo, :canal, :idm, :mesa, :mes, :mesn, :cli, :com, :tot, :n, :por, :creado, NOW(), 'PENDIENTE')
            """), {"id": lote_id, "nro": nro, "tipo": tipo, "canal": limpiar_texto(L.get("canal"), 20) or "MESA",
                   "idm": _entero(L.get("id_mesa")), "mesa": limpiar_texto(L.get("mesa"), 200),
                   "mes": _entero(L.get("mesero")), "mesn": limpiar_texto(L.get("mesero_nombre"), 150) or None,
                   "cli": _entero(L.get("id_cliente"), 1, 1), "com": _entero(L.get("comensales"), 1, 1, 999),
                   "tot": _entero(L.get("total")), "n": len(items),
                   "por": limpiar_texto(L.get("enviado_por"), 150) or None, "creado": _fecha(L.get("creado_en"))})
            for it in items:
                await s.execute(text("""
                    INSERT IGNORE INTO ag_pw_item
                        (lote_id, item, id_plato, descripcion, cantidad, valor, novedad, cambios,
                         producto_personalizado, insumos, novedades)
                    VALUES (:l, :it, :p, :d, :q, :v, :nov, :cam, :pp, :ins, :novs)
                """), {"l": lote_id, "it": _entero(it.get("item"), 0, 1), "p": _entero(it.get("id_plato"), 0, 1),
                       "d": limpiar_texto(it.get("descripcion"), 255) or None,
                       "q": _decimal(it.get("cantidad"), 1000) or 1, "v": _entero(it.get("valor")),
                       "nov": limpiar_texto(it.get("novedad"), MAX_TEXTO) or None,
                       "cam": limpiar_texto(it.get("cambios"), MAX_TEXTO) or None,
                       "pp": limpiar_texto(it.get("producto_personalizado"), 1000) or None,
                       "ins": json.dumps(it.get("insumos") or [])[:60000],
                       "novs": json.dumps(it.get("novedades") or [])[:60000]})
            recibidos.append(lote_id)
        await s.commit()
    if recibidos:
        await nube.pedir("POST", "/api/agente/pedidos/recibidos", {"ids": recibidos})
    return len(recibidos)


# ───────────────────────────── 2. aceptar / rechazar (panel de la mini-app) ─────────────────────────────

async def marcar(ids: list[int], accion: str, por: str, desde: str, pc: str, motivo: str | None = None) -> int:
    """PENDIENTE (o ERROR) → ACEPTADO / RECHAZADO. Lo mismo que hace el form VB6 con un UPDATE.
    Solo cambia si sigue pendiente: si se procesa a la vez en dos sitios, cuenta el primero."""
    if accion not in ("ACEPTADO", "RECHAZADO") or not ids:
        return 0
    n = 0
    async with SesionTemp() as s:
        for i in ids:
            n += (await s.execute(text("""
                UPDATE ag_pw_lote SET estado = :e, procesado_por = :por, procesado_desde = :desde, pc = :pc,
                       procesado_en = NOW(), motivo = :motivo, mensaje = NULL
                WHERE id = :id AND estado IN ('PENDIENTE', 'ERROR')
            """), {"e": accion, "por": por[:150], "desde": desde, "pc": pc[:100],
                   "motivo": (motivo or None) and motivo[:255], "id": i})).rowcount
        await s.commit()
    return n


# ───────────────────────────── 3. aplicar en el escritorio ─────────────────────────────

async def _plato(emp: AsyncSession, id_plato: int) -> dict:
    fila = (await emp.execute(text("""
        SELECT Id_Plato, Nombre, Cod_Categoria, Impuesto, Impresora FROM platos WHERE Id_Plato = :i
    """), {"i": id_plato})).mappings().first()
    if not fila:
        raise NoAplicable(f"El producto {id_plato} no existe en el escritorio.")
    return dict(fila)


async def _insertar_items(conn, emp: AsyncSession, lote: dict, items: list[dict], fecha, ahora: datetime,
                          item: int, nuevo: bool) -> None:
    """Cada ítem de la web (una unidad, o una cantidad decimal) → filas del escritorio:
    una por unidad y por impresora del plato (Mostrar = 1 en la primera), con el precio de la nube."""
    from .pedidos import _COLS_DETALLE
    nro = lote["nro_pedido"]
    hora = hora_corta(ahora)
    paga = (await facturacion(emp))["paga_impuesto"]
    for it in items:
        plato = await _plato(emp, int(it["id_plato"]))
        impresoras = await catalogo.impresoras_plato(emp, plato)
        cantidad = float(it["cantidad"] or 1)
        nombre = (plato["Nombre"] or "").strip()
        personalizado = (it["producto_personalizado"] or nombre)[:1000]
        novedad = (it["novedad"] or "")[:MAX_TEXTO]
        insumos = json.loads(it["insumos"] or "[]")
        inicial = item
        for parte in partes_cantidad(cantidad):
            maestro = item
            valor = int(round(int(it["valor"] or 0) * parte / cantidad)) if cantidad else 0
            for idx, impresora in enumerate(impresoras):
                p = {"nro": nro, "fecha": fecha, "plato": plato["Id_Plato"], "item": item, "desc": nombre[:255],
                     "cant": parte, "valor": valor, "hora": hora, "nov": novedad, "mostrar": 1 if idx == 0 else 0,
                     "impresora": impresora[:255], "depende": str(inicial), "cat": plato["Cod_Categoria"],
                     "paga": paga, "imp": plato["Impuesto"] or 0, "pers": personalizado, "cortesia": 1 if nuevo else 0}
                await conn.execute(text("INSERT INTO temp_detalle_comanda " + _COLS_DETALLE), p)
                await conn.execute(text("INSERT INTO temp_detalle_comanda_parcial " + _COLS_DETALLE), p)
                item += 1
            # Inventario por unidad: lo que la web ya calculó (receta fija + opciones), proporcional a la fila
            for ins in insumos[:100]:
                q = {"nro": nro, "fecha": fecha.strftime("%Y/%m/%d"), "plato": plato["Id_Plato"], "item": maestro,
                     "g": _entero(ins.get("g")), "i": _entero(ins.get("i")),
                     "c": round(_decimal(ins.get("c")) * parte / cantidad, 4) if cantidad else 0,
                     "pos": _entero(ins.get("p")), "adic": round(_decimal(ins.get("v"), 100_000_000) * parte / cantidad, 2)}
                for tabla in ("temp_plato_producto", "temp_plato_producto_parcial"):
                    await conn.execute(text(f"""
                        INSERT INTO {tabla}
                            (Nro_Pedido, Fecha, Nro_Factura, Id_Plato, Item, Id_Grupo, Id_Item, Cantidad,
                             Enviada_MySql, Item_Original, Posicion, Opcion_Cambiar, Valor_Adicional_Armar)
                        VALUES (:nro, :fecha, '0', :plato, :item, :g, :i, :c, 0, :item, :pos, 0, :adic)
                    """), q)
        for consecutivo, nov in enumerate(json.loads(it["novedades"] or "[]")[:30], start=1):
            await conn.execute(text("""
                INSERT INTO temp_novedades_plato_pedido
                    (Id_Consecutivo, Nro_Pedido, Item, Depende, Cod_Categoria, Id_Novedad, Novedad)
                VALUES (:c, :nro, :item, :item, :cat, :idn, :nov)
            """), {"c": consecutivo, "nro": nro, "item": inicial, "cat": _entero(nov.get("cat")),
                   "idn": _entero(nov.get("id")), "nov": limpiar_texto(nov.get("txt"), MAX_TEXTO)})
        await conn.execute(text("""
            INSERT INTO ag_pw_mapa (nro_pedido, item_web, depende, lote_id) VALUES (:n, :w, :d, :l)
        """), {"n": nro, "w": int(it["item"]), "d": inicial, "l": lote["id"]})
        await conn.commit()          # el mapa (InnoDB) queda a la par de lo escrito en MyISAM


async def _aplicar(conn, emp: AsyncSession, lote: dict) -> None:
    from ..routers.mesas import mesa_existe
    from ..routers.pedidos import VISIBLE
    nro = lote["nro_pedido"]
    items = [dict(r) for r in (await conn.execute(text(
        "SELECT * FROM ag_pw_item WHERE lote_id = :l ORDER BY item"), {"l": lote["id"]})).mappings().all()]
    if not items:
        raise NoAplicable("El lote no tiene productos.")
    try:
        fecha = await exigir_caja_abierta(emp)
    except HTTPException as e:
        raise NoAplicable(str(e.detail))
    # Ya aplicado antes (el agente se cayó antes de marcarlo): no se repite; solo se completa el envío
    hechos = (await conn.execute(text("SELECT COUNT(*) FROM ag_pw_mapa WHERE lote_id = :l"), {"l": lote["id"]})).scalar()
    if hechos:
        if hechos < len(items):
            raise NoAplicable("El lote quedó aplicado a medias en el escritorio. Revise el pedido en caja.")
        pedido = (await conn.execute(text("SELECT Mesa, Imprimio_Precuenta FROM temp_comanda WHERE Nro_Pedido = :n"),
                                     {"n": nro})).mappings().first()
        if pedido:
            await impresion.enviar_pedido(conn, emp, nro, lote["tipo"] == "NUEVO", fecha, datetime.now(), ENVIADO_DESDE,
                                          int(pedido["Imprimio_Precuenta"] or 0), pedido["Mesa"])
        return
    for it in items:
        await _plato(emp, int(it["id_plato"]))         # todos deben existir antes de escribir nada
    ahora = datetime.now()

    if lote["tipo"] == "NUEVO":
        mesa = (lote["mesa"] or "").strip()
        if not mesa or not await mesa_existe(emp, int(lote["id_mesa"]), lote["mesa"]):
            raise NoAplicable(f"La mesa '{mesa}' no existe en el escritorio.")
        if (await conn.execute(text("SELECT COUNT(*) FROM temp_comanda WHERE Nro_Pedido = :n"), {"n": nro})).scalar():
            raise NoAplicable("El pedido ya existe en el escritorio.")
        if (await conn.execute(text("SELECT COUNT(*) FROM temp_comanda WHERE Mesa = :m"), {"m": lote["mesa"]})).scalar():
            raise NoAplicable(f"'{mesa}' ya tiene un pedido abierto o en uso en caja.")
        id_cliente = int(lote["id_cliente"] or 1)
        if not (await emp.execute(text("SELECT COUNT(*) FROM clientes WHERE Id_Cliente = :c"), {"c": id_cliente})).scalar():
            id_cliente = 1
        await conn.execute(text("""
            INSERT INTO temp_comanda
                (Nro_Pedido, Fecha, Nro_Factura, Mesa, Hora, Mesero, Cancelado, Valor, Salio, Cortesia,
                 Imprimio_Precuenta, Nro_Comenzales, Nro_Puestos, Domicilio, Id_Cliente, Movil)
            VALUES (:n, :f, '0', :mesa, :hora, :mesero, 0, 0, 0, 0, :id_mesa, :comensales, 1, 0, :cli, 1)
        """), {"n": nro, "f": fecha.strftime("%Y/%m/%d"), "mesa": lote["mesa"], "hora": ahora.strftime("%I:%M:%S %p"),
               "mesero": int(lote["mesero"] or 0), "id_mesa": int(lote["id_mesa"]),
               "comensales": max(1, int(lote["comensales"] or 1)), "cli": id_cliente})
        await _insertar_items(conn, emp, lote, items, fecha, ahora, 1, nuevo=True)
        await impresion.enviar_pedido(conn, emp, nro, True, fecha, ahora, ENVIADO_DESDE, int(lote["id_mesa"]), lote["mesa"])
    else:
        pedido = (await conn.execute(text(f"""
            SELECT Mesa, Imprimio_Precuenta, Salio FROM temp_comanda WHERE Nro_Pedido = :n AND {VISIBLE}
        """), {"n": nro})).mappings().first()
        if not pedido:
            raise NoAplicable("El pedido ya no está abierto en caja (facturado, eliminado o en edición).")
        item = await siguiente_item(conn, nro)
        await _insertar_items(conn, emp, lote, items, fecha, ahora, item, nuevo=False)
        await impresion.enviar_pedido(conn, emp, nro, False, fecha, ahora, ENVIADO_DESDE,
                                      int(pedido["Imprimio_Precuenta"] or 0), pedido["Mesa"])


async def aplicar_aceptados() -> int:
    from ..routers.pedidos import _escritura
    async with SesionTemp() as s:
        lotes = [dict(r) for r in (await s.execute(text(
            "SELECT * FROM ag_pw_lote WHERE estado = 'ACEPTADO' ORDER BY id LIMIT 20"))).mappings().all()]
    hechos = 0
    for lote in lotes:
        async with SesionTemp() as s:
            previos = {r[0] for r in (await s.execute(text("""
                SELECT CONCAT(tipo, ':', estado) FROM ag_pw_lote
                WHERE nro_pedido = :n AND id < :id AND estado <> 'APLICADO'
            """), {"n": lote["nro_pedido"], "id": lote["id"]})).all()}
        mensaje = None
        if "NUEVO:RECHAZADO" in previos:
            mensaje = "El pedido nuevo de esta cuenta fue rechazado: rechace también estos productos."
        elif any(not p.endswith(":RECHAZADO") for p in previos):
            continue                                  # espera a que se procese el anterior del mismo pedido
        if not mensaje:
            try:
                async with SesionEmpresa() as emp, _escritura() as conn:
                    await _aplicar(conn, emp, lote)
                    await conn.execute(text("""
                        UPDATE ag_pw_lote SET estado = 'APLICADO', aplicado_en = NOW(), mensaje = NULL
                        WHERE id = :id AND estado = 'ACEPTADO'
                    """), {"id": lote["id"]})
                    await conn.commit()
                hechos += 1
                continue
            except NoAplicable as e:
                mensaje = str(e)
            except HTTPException as e:
                mensaje = str(e.detail)
            except Exception as e:                        # se registra y el lote queda para reintentar
                log.exception("Aplicar pedido web %s", lote["id"])
                mensaje = f"Error al pasar el pedido al escritorio: {e}"[:500]
        async with SesionTemp() as s:
            await s.execute(text("UPDATE ag_pw_lote SET estado = 'ERROR', mensaje = :m WHERE id = :id AND estado = 'ACEPTADO'"),
                            {"m": mensaje[:500], "id": lote["id"]})
            await s.commit()
    return hechos


# ───────────────────────────── 4. reportar a la nube ─────────────────────────────

async def reportar() -> int:
    async with SesionTemp() as s:
        filas = (await s.execute(text("""
            SELECT id, estado, procesado_por, procesado_desde, pc, motivo, mensaje FROM ag_pw_lote
            WHERE estado <> 'PENDIENTE' AND estado <> COALESCE(nube_estado, '') ORDER BY id LIMIT 50
        """))).mappings().all()
    if not filas:
        return 0
    r = await nube.pedir("POST", "/api/agente/pedidos/resultado", {"resultados": [{
        "id": int(f["id"]), "estado": f["estado"], "por": f["procesado_por"],
        "desde": f["procesado_desde"] if f["procesado_desde"] in ("VB", "MINIAPP") else None,
        "pc": f["pc"], "motivo": f["motivo"], "mensaje": f["mensaje"]} for f in filas]}) or {}
    confirmados = {int(i) for i in r.get("confirmados") or []}
    async with SesionTemp() as s:
        for f in filas:
            if int(f["id"]) in confirmados:
                await s.execute(text("UPDATE ag_pw_lote SET nube_estado = :e WHERE id = :id AND estado = :e"),
                                {"e": f["estado"], "id": f["id"]})
        await s.commit()
    return len(confirmados)


async def pendientes() -> int:
    async with SesionTemp() as s:
        return int((await s.execute(text("SELECT COUNT(*) FROM ag_pw_lote WHERE estado = 'PENDIENTE'"))).scalar() or 0)


# ───────────────────────────── ciclo ─────────────────────────────

CADA_DESCARGA_SEG = 10
CADA_APLICAR_SEG = 2


async def ciclo() -> None:
    """Tarea de fondo: baja los lotes cada 10 s y pasa al escritorio lo aceptado cada 2 s.
    Sin internet sigue aplicando lo ya aceptado; el reporte a la nube se reintenta solo."""
    import asyncio
    from .. import config
    if not config.NUBE_CLAVE:
        return
    vueltas = 0
    while True:
        try:
            aplicados = await aplicar_aceptados()
            if vueltas % (CADA_DESCARGA_SEG // CADA_APLICAR_SEG) == 0:
                await descargar()
                await reportar()
            elif aplicados:
                await reportar()
            estado.update(ultimo_ok=datetime.now(), mensaje=None)
        except nube.ErrorNube as e:
            estado.update(ultimo_error=datetime.now(), mensaje=str(e))
        except Exception as e:                  # nunca detiene el ciclo
            log.exception("Ciclo de pedidos web")
            estado.update(ultimo_error=datetime.now(), mensaje=f"Error en pedidos web: {e}")
        vueltas += 1
        await asyncio.sleep(CADA_APLICAR_SEG)
