"""
Bloqueo de mesas.

temp_mesa_abierta es la tabla que respeta el escritorio (y la app anterior): una fila con
Abierta = 1 marca la mesa como abierta en algún equipo. No tiene hora, así que si una app se
cierra sin liberar, la mesa queda bloqueada para siempre.

El agente agrega ag_bloqueo_mesa con vencimiento: un bloqueo creado por el agente que venció
se limpia solo. Los bloqueos del escritorio (sin fila en ag_bloqueo_mesa) nunca se tocan.
"""
import os
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..sesion import Mesero

MINUTOS_BLOQUEO = int(os.getenv("AG_BLOQUEO_MIN", "10"))


async def _limpiar_vencidos(tmp: AsyncSession) -> None:
    vencidos = (await tmp.execute(text(
        "SELECT id_mesa, mesa FROM ag_bloqueo_mesa WHERE vence < :ahora"), {"ahora": datetime.now()})).all()
    for id_mesa, mesa in vencidos:
        await tmp.execute(text("DELETE FROM temp_mesa_abierta WHERE Id_Mesa = :i AND Mesa = :m"),
                          {"i": id_mesa, "m": mesa})
        await tmp.execute(text("DELETE FROM ag_bloqueo_mesa WHERE id_mesa = :i AND mesa = :m"),
                          {"i": id_mesa, "m": mesa})


async def quien_bloquea(tmp: AsyncSession, id_mesa: int, mesa: str, mesero: Mesero) -> str | None:
    """None si la mesa está libre o la bloquea este mismo dispositivo; si no, quién la tiene."""
    await _limpiar_vencidos(tmp)
    propio = (await tmp.execute(text("""
        SELECT id_dispositivo FROM ag_bloqueo_mesa WHERE id_mesa = :i AND mesa = :m
    """), {"i": id_mesa, "m": mesa})).scalar()
    if propio is not None:
        return None if propio == mesero.id_dispositivo else "otro dispositivo"
    desde = (await tmp.execute(text("""
        SELECT Abierta_Desde FROM temp_mesa_abierta WHERE Id_Mesa = :i AND Abierta = 1 LIMIT 1
    """), {"i": id_mesa})).scalar()
    if desde is None:
        return None
    return (desde or "otro equipo").strip() or "otro equipo"


async def bloquear(tmp: AsyncSession, id_mesa: int, mesa: str, mesero: Mesero) -> None:
    """Bloquea (o renueva el bloqueo de) la mesa para este dispositivo. 409 si la tiene otro."""
    otro = await quien_bloquea(tmp, id_mesa, mesa, mesero)
    if otro:
        raise HTTPException(status_code=409, detail=f"La mesa '{mesa.strip()}' ya se encuentra abierta en {otro}.")
    ahora = datetime.now()
    vence = ahora + timedelta(minutes=MINUTOS_BLOQUEO)
    renovado = (await tmp.execute(text("""
        UPDATE ag_bloqueo_mesa SET vence = :v WHERE id_mesa = :i AND mesa = :m AND id_dispositivo = :d
    """), {"v": vence, "i": id_mesa, "m": mesa, "d": mesero.id_dispositivo})).rowcount
    if renovado:
        return
    try:
        # La llave primaria de ag_bloqueo_mesa evita que dos dispositivos la tomen a la vez
        await tmp.execute(text("""
            INSERT INTO ag_bloqueo_mesa (id_mesa, mesa, cod_empleado, id_dispositivo, desde, vence)
            VALUES (:i, :m, :c, :d, :a, :v)
        """), {"i": id_mesa, "m": mesa, "c": mesero.cod_empleado, "d": mesero.id_dispositivo,
               "a": ahora, "v": vence})
    except IntegrityError:
        await tmp.rollback()
        raise HTTPException(status_code=409, detail=f"La mesa '{mesa.strip()}' ya se encuentra abierta en otro dispositivo.")
    await tmp.execute(text("""
        INSERT INTO temp_mesa_abierta (Id_Mesa, Mesa, Abierta, Abierta_Desde) VALUES (:i, :m, 1, :desde)
    """), {"i": id_mesa, "m": mesa, "desde": mesero.nombre_dispositivo[:100]})


async def liberar(tmp: AsyncSession, id_mesa: int, mesa: str, mesero: Mesero) -> None:
    """Libera solo un bloqueo de este dispositivo."""
    borrados = (await tmp.execute(text("""
        DELETE FROM ag_bloqueo_mesa WHERE id_mesa = :i AND mesa = :m AND id_dispositivo = :d
    """), {"i": id_mesa, "m": mesa, "d": mesero.id_dispositivo})).rowcount
    if borrados:
        await tmp.execute(text("DELETE FROM temp_mesa_abierta WHERE Id_Mesa = :i AND Mesa = :m"),
                          {"i": id_mesa, "m": mesa})
