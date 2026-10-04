"""
Registro de auditoría (ag_auditoria) y conteo de intentos para el límite anti-abuso.
La auditoría usa su propia sesión: queda guardada aunque la operación falle.
"""
from datetime import datetime, timedelta

from sqlalchemy import text

from .db import SesionTemp


async def registrar(evento: str, resultado: str, ip: str = "", usuario: str | None = None,
                    cod_empleado: int | None = None, id_dispositivo: int | None = None,
                    detalle: str | None = None) -> None:
    async with SesionTemp() as s:
        await s.execute(text("""
            INSERT INTO ag_auditoria (fecha, evento, resultado, usuario, cod_empleado, id_dispositivo, ip, detalle)
            VALUES (:f, :e, :r, :u, :c, :d, :ip, :det)
        """), {"f": datetime.now(), "e": evento, "r": resultado, "u": (usuario or None) and usuario[:25],
               "c": cod_empleado, "d": id_dispositivo, "ip": ip[:45], "det": (detalle or None) and detalle[:255]})
        await s.commit()


async def contar(evento: str, resultado: str, minutos: int, ip: str | None = None,
                 usuario: str | None = None) -> int:
    """Eventos recientes de la IP o del usuario (el mayor de los dos)."""
    desde = datetime.now() - timedelta(minutes=minutos)
    maximo = 0
    async with SesionTemp() as s:
        for campo, valor in (("ip", ip), ("usuario", usuario)):
            if not valor:
                continue
            n = (await s.execute(text(f"""
                SELECT COUNT(*) FROM ag_auditoria
                WHERE evento = :e AND resultado = :r AND fecha >= :desde AND {campo} = :v
            """), {"e": evento, "r": resultado, "desde": desde, "v": valor})).scalar() or 0
            maximo = max(maximo, int(n))
    return maximo
