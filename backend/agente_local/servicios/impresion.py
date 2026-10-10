"""
Cola de impresión de comandas: Enviar_Pedido_Impresion del escritorio (VB6).

Al pulsar "Enviar pedido" (pedido nuevo o productos agregados) el agente pasa las filas del pedido
que aún no se han impreso (temp_detalle_comanda.Impreso = 0 y Min = 0) a
datatemppos.temp_impresion_tirilla_comanda; un temporizador del escritorio revisa esa tabla y
envía cada fila a su impresora.

Banderas (variables_del_sistema de la BD de la empresa):
  · Imprimir_Tirilla_Comanda o Imprimir_Comanda_Plazoleta → se encola.

Después, "Enviar pedido" (enviar_pedido) hace lo mismo que el escritorio, en este orden y siempre:
  1. Impreso = 1 en temp_detalle_comanda y temp_detalle_comanda_parcial (gemelas) del pedido.
  2. Libera la mesa: temp_mesa_abierta por Id_Mesa y por Mesa (y el bloqueo propio del agente).
  3. Borra temp_plato_armar / temp_plato_armar_detalle del pedido.
  4. Enviada_MySql = 1 en la cola del pedido. Se inserta con 0 para que el escritorio no imprima un
     pedido a medias; las tablas son MyISAM (cada sentencia se ve al terminar), así que este UPDATE
     debe ir de último. Cada sentencia se espera (await) antes de la siguiente, como en el VB6.

Diferencias con el VB6 (decididas con el usuario, 2026-10-07):
  · Nombre del mesero: temp_meseros → temp_meseros_dia → meseros. El VB6 hace INNER JOIN con
    temp_meseros y, si el mesero no está allí, el pedido no se imprime y no avisa.
  · No se vuelve a encolar un ítem del pedido que ya está en la cola (si se agrega antes de que el
    temporizador imprima lo anterior, el VB6 lo imprimiría dos veces).
  · NORMA: la comanda va en ítem descendente (último en ingresar, primero en la tirilla): se encola
    en ese orden.
  · Enviar_Pedido_domicilio_caja (impresión directa de domicilios) queda pendiente: la toma de
    pedidos no crea domicilios.
"""
from datetime import date, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from . import meseros


async def banderas(emp: AsyncSession) -> dict:
    fila = (await emp.execute(text("""
        SELECT Imprimir_Tirilla_Comanda, Imprimir_Comanda_Plazoleta, Actualizar_Tablas_Manualmente
        FROM variables_del_sistema LIMIT 1
    """))).mappings().first() or {}
    return {"tirilla": bool(fila.get("Imprimir_Tirilla_Comanda")),
            "plazoleta": bool(fila.get("Imprimir_Comanda_Plazoleta")),
            "manual": bool(fila.get("Actualizar_Tablas_Manualmente"))}


async def _nombre_mesero(tmp, emp: AsyncSession, cod: int) -> str:
    nombre = (await tmp.execute(text("SELECT nombres FROM temp_meseros WHERE cod_empleado = :c"), {"c": cod})).scalar()
    if (nombre or "").strip():
        return nombre.strip()
    return (await meseros.nombres(emp, tmp, {cod})).get(cod) or ""


async def enviar_pedido_impresion(tmp, emp: AsyncSession, nro: str, nuevo: bool, fecha: date,
                                  ahora: datetime, enviado_desde: str) -> int:
    """Encola lo pendiente de imprimir del pedido. Devuelve cuántas filas se encolaron.
    tmp: la conexión de escritura (con el candado de pedidos) de datatemppos."""
    b = await banderas(emp)
    if not (b["tirilla"] or b["plazoleta"]):
        return 0
    # Productos agregados: solo si hay algo visible sin imprimir (como el VB6)
    if not nuevo and not (await tmp.execute(text("""
            SELECT COUNT(*) FROM temp_detalle_comanda WHERE Nro_pedido = :n AND Mostrar = 1 AND Impreso = 0
        """), {"n": nro})).scalar():
        return 0

    filas = (await tmp.execute(text("""
        SELECT d.Nro_pedido, d.Id_Plato, d.Item, d.Depende, d.Descripcion, d.Cantidad, d.Novedad, d.Cambios,
               d.Mostrar, d.Impresora, c.Mesa, c.Mesero, c.Domicilio
        FROM temp_detalle_comanda d
        JOIN temp_comanda c ON c.Nro_Pedido = d.Nro_pedido
        WHERE d.Nro_pedido = :n AND d.Impreso = 0 AND d.Min = 0
          AND NOT EXISTS (SELECT 1 FROM temp_impresion_tirilla_comanda t
                          WHERE t.Nro_pedido = d.Nro_pedido AND t.Item = d.Item)
        ORDER BY d.Item DESC
    """), {"n": nro})).mappings().all()
    if filas:
        mesero = await _nombre_mesero(tmp, emp, int(filas[0]["Mesero"] or 0))
        hora = ahora.strftime("%I:%M:%S %p")
        for f in filas:
            dep = str(f["Depende"] or "").strip()
            await tmp.execute(text("""
                INSERT INTO temp_impresion_tirilla_comanda
                    (Nro_pedido, Mesero, Fecha, Nro_Mesa, Id_Plato, Item, Depende, Descripcion, Cantidad, Hora,
                     Novedad, Impreso, Cambios, Mostrar, Impresora, Enviada_MySql, Nro_Puesto, Nuevo, Cancelado,
                     Enviado_Desde, Hora_Plato, Domicilio)
                VALUES (:nro, :mesero, :fecha, :mesa, :plato, :item, :dep, :desc, :cant, :hora,
                        :nov, 0, :camb, :mostrar, :imp, 0, 0, :nuevo, 0,
                        :desde, :hora, :domi)
            """), {"nro": nro, "mesero": mesero[:255], "fecha": fecha, "mesa": f["Mesa"], "plato": f["Id_Plato"],
                   "item": f["Item"], "dep": int(dep) if dep.isdigit() else 0, "desc": f["Descripcion"],
                   "cant": f["Cantidad"], "hora": hora, "nov": (f["Novedad"] or "")[:255],
                   "camb": (f["Cambios"] or "")[:255], "mostrar": 1 if f["Mostrar"] else 0, "imp": f["Impresora"],
                   "nuevo": 1 if nuevo else 0, "desde": (enviado_desde or "")[:255],
                   "domi": 1 if f["Domicilio"] else 0})
    return len(filas)


async def enviar_pedido(tmp, emp: AsyncSession, nro: str, nuevo: bool, fecha: date, ahora: datetime,
                        enviado_desde: str, id_mesa: int, mesa: str) -> int:
    """"Enviar pedido" completo (pedido nuevo o productos agregados). Devuelve las filas encoladas."""
    encoladas = await enviar_pedido_impresion(tmp, emp, nro, nuevo, fecha, ahora, enviado_desde)
    for tabla in ("temp_detalle_comanda", "temp_detalle_comanda_parcial"):
        await tmp.execute(text(f"UPDATE {tabla} SET Impreso = 1 WHERE Nro_pedido = :n"), {"n": nro})
    await tmp.execute(text("DELETE FROM temp_mesa_abierta WHERE Id_Mesa = :i"), {"i": id_mesa})
    await tmp.execute(text("DELETE FROM temp_mesa_abierta WHERE Mesa = :m"), {"m": mesa})
    await tmp.execute(text("DELETE FROM ag_bloqueo_mesa WHERE id_mesa = :i OR mesa = :m"), {"i": id_mesa, "m": mesa})
    for tabla in ("temp_plato_armar", "temp_plato_armar_detalle"):
        await tmp.execute(text(f"DELETE FROM {tabla} WHERE Nro_Pedido = :n"), {"n": nro})
    await tmp.execute(text("UPDATE temp_impresion_tirilla_comanda SET Enviada_MySql = 1 WHERE Nro_pedido = :n"),
                      {"n": nro})
    return encoladas
