"""
Errores del agente y de sus dispositivos (tabla ag_errores), con el mismo criterio del Monitor de
Errores de la nube: un registro por error distinto (huella) con contador; si un error resuelto
vuelve a ocurrir se reabre como regresión. Cuando hay internet se envían a la nube (nube.py).
La escritura usa su propia sesión y nunca lanza: registrar un error no puede romper nada.
"""
import hashlib
import logging
import re
from datetime import datetime

from sqlalchemy import text

from .db import SesionTemp

log = logging.getLogger("agente_local")

TIPOS = ("SERVIDOR", "BASE_DATOS", "RED", "VISTA", "IMPRESION", "INTEGRACION")
NIVELES = ("CRITICO", "ERROR", "ADVERTENCIA")


def _normalizar(texto: str) -> str:
    """Quita números y comillas variables para que el mismo error tenga la misma huella."""
    texto = re.sub(r"'[^']*'", "'…'", texto or "")
    return re.sub(r"\d+", "#", texto)[:300]


def huella(origen: str, tipo: str, titulo: str, vista: str | None) -> str:
    base = "|".join([origen, tipo, _normalizar(titulo), vista or ""])
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


async def registrar(*, origen: str = "agente", tipo: str = "SERVIDOR", nivel: str = "ERROR", titulo: str,
                    mensaje: str | None = None, detalle: str | None = None, vista: str | None = None,
                    dispositivo: str | None = None, ip: str | None = None) -> None:
    tipo = tipo if tipo in TIPOS else "SERVIDOR"
    nivel = nivel if nivel in NIVELES else "ERROR"
    ahora = datetime.now()
    try:
        async with SesionTemp() as s:
            await s.execute(text("""
                INSERT INTO ag_errores
                    (huella, origen, tipo, nivel, titulo, mensaje, detalle, vista, dispositivo, ip,
                     ocurrencias, primera, ultima, estado, pendiente_nube)
                VALUES (:h, :o, :t, :n, :ti, :m, :d, :v, :disp, :ip, 1, :a, :a, 'NUEVO', 1)
                ON DUPLICATE KEY UPDATE
                    ocurrencias = ocurrencias + 1, ultima = :a, mensaje = :m, detalle = COALESCE(:d, detalle),
                    dispositivo = COALESCE(:disp, dispositivo), ip = COALESCE(:ip, ip),
                    pendiente_nube = pendiente_nube + 1,
                    regresiones = regresiones + IF(estado = 'RESUELTO', 1, 0),
                    estado = IF(estado = 'RESUELTO', 'NUEVO', estado)
            """), {"h": huella(origen, tipo, titulo, vista), "o": origen, "t": tipo, "n": nivel,
                   "ti": titulo[:255], "m": (mensaje or "")[:4000] or None, "d": (detalle or "")[:60000] or None,
                   "v": (vista or "")[:255] or None, "disp": (dispositivo or "")[:150] or None,
                   "ip": (ip or "")[:45] or None, "a": ahora})
            await s.commit()
    except Exception:
        log.exception("No fue posible registrar el error: %s", titulo)


def tipo_de_excepcion(exc: BaseException) -> str:
    nombre = type(exc).__module__ + "." + type(exc).__name__
    if any(x in nombre.lower() for x in ("sqlalchemy", "pymysql", "aiomysql", "operationalerror")):
        return "BASE_DATOS"
    return "SERVIDOR"
