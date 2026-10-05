"""
Comunicación del agente con la nube (EasyPosWeb), con la clave propia de la empresa
(AG_NUBE_CLAVE, la asigna SYSADMIN en "Agentes Locales"):

  · latido cada minuto: URL/IP local y versión (la nube sabe dónde está el agente)
  · errores pendientes de ag_errores → Monitor de Errores de la nube (tipo AGENTE_LOCAL)
  · fotos de los platos subidas en la web → carpeta de fotos del escritorio (una vez al día)
  · versión vigente del agente → descarga y, al abrir turno, actualización (actualizador.py)

Todo es de salida (el PC de caja no abre puertos a internet). Sin internet el agente sigue
funcionando en la red local y reintenta en el siguiente ciclo.
"""
import asyncio
import json
import logging
import socket
import urllib.error
import urllib.request
from datetime import datetime, timedelta

from sqlalchemy import text

from . import VERSION, config
from .db import SesionTemp

log = logging.getLogger("agente_local")

# Estado visible en el panel de administración
estado = {"configurada": bool(config.NUBE_CLAVE), "ultimo_ok": None, "ultimo_error": None,
          "mensaje": None, "empresa": None, "fotos": None}


class ErrorNube(Exception):
    pass


def ip_local() -> str:
    """IP de este PC en la red local (sin enviar nada: el socket UDP solo elige la interfaz)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def _pedir(metodo: str, ruta: str, cuerpo=None, timeout: int = 15):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(config.NUBE_URL + ruta, data=datos, method=metodo, headers={
        "X-Agente-Clave": config.NUBE_CLAVE, "Content-Type": "application/json",
        "User-Agent": f"EasyPosAgenteLocal/{VERSION}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        try:
            detalle = json.loads(e.read()).get("detail")
        except Exception:
            detalle = None
        raise ErrorNube(f"La nube respondió {e.code}: {detalle or e.reason}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise ErrorNube(f"Sin conexión con la nube ({getattr(e, 'reason', e)})")


async def pedir(metodo: str, ruta: str, cuerpo=None, timeout: int = 15):
    return await asyncio.to_thread(_pedir, metodo, ruta, cuerpo, timeout)


async def latido() -> None:
    from . import actualizador
    reporte = actualizador.estado["reportar"]
    r = await pedir("POST", "/api/agente/latido", {
        "url_local": f"http://{ip_local()}:{config.PUERTO}", "ip_local": ip_local(), "version": VERSION,
        "actualizacion": reporte})
    if reporte:
        actualizador.estado["reportar"] = None
    estado["empresa"] = (r or {}).get("empresa")
    actualizador.estado["vigente"] = (r or {}).get("version_vigente")


async def turno_y_pedidos() -> tuple[str, int]:
    """Fecha de negocio (cambia al abrir turno en el escritorio) y pedidos abiertos de los dispositivos."""
    from .servicios.negocio import fecha_negocio
    async with SesionTemp() as s:
        fecha = await fecha_negocio(s)
        abiertos = (await s.execute(text("SELECT COUNT(*) FROM temp_comanda WHERE Movil = 1 AND Salio = 0"))).scalar() or 0
    return fecha.isoformat(), int(abiertos)


async def enviar_errores() -> int:
    async with SesionTemp() as s:
        filas = (await s.execute(text("""
            SELECT id, origen, tipo, nivel, titulo, mensaje, detalle, vista, dispositivo, pendiente_nube
            FROM ag_errores WHERE pendiente_nube > 0 ORDER BY ultima LIMIT 50
        """))).mappings().all()
        if not filas:
            return 0
        await pedir("POST", "/api/agente/errores", {"eventos": [{
            "origen": f["origen"] if f["origen"] in ("agente", "dispositivo") else "agente",
            "tipo": f["tipo"], "nivel": f["nivel"], "titulo": f["titulo"][:255],
            "mensaje": (f["mensaje"] or "")[:4000] or None, "detalle": (f["detalle"] or "")[:8000] or None,
            "vista": f["vista"], "dispositivo": f["dispositivo"], "ocurrencias": max(1, int(f["pendiente_nube"])),
            "version": VERSION} for f in filas]})
        # Solo se descuenta lo enviado (pudieron llegar más ocurrencias mientras tanto)
        for f in filas:
            await s.execute(text("UPDATE ag_errores SET pendiente_nube = GREATEST(pendiente_nube - :n, 0) WHERE id = :id"),
                            {"n": int(f["pendiente_nube"]), "id": f["id"]})
        await s.commit()
        return len(filas)


async def ciclo() -> None:
    """Tarea de fondo del agente (arranca con la aplicación)."""
    if not config.NUBE_CLAVE:
        estado["mensaje"] = "Sin clave de la nube (AG_NUBE_CLAVE): el agente no reporta a la nube."
        return
    from . import actualizador
    from .servicios import fotos_web           # evita importación circular al arrancar
    proximas_fotos = datetime.now() + timedelta(minutes=2)
    fecha_turno = None
    while True:
        try:
            await actualizador.revisar_resultado()       # resultado de una actualización recién aplicada
            await latido()
            await enviar_errores()
            await actualizador.descargar_si_hace_falta()
            await actualizador.publicar_aviso()          # para el dashboard del escritorio (ag_config)
            # Opción B: al abrir turno (cambia la fecha de negocio) y sin pedidos abiertos de dispositivos
            fecha, abiertos = await turno_y_pedidos()
            if fecha_turno and fecha != fecha_turno:
                actualizador.al_abrir_turno(abiertos)
            fecha_turno = fecha
            if datetime.now() >= proximas_fotos:
                estado["fotos"] = await fotos_web.sincronizar()
                proximas_fotos = datetime.now() + timedelta(hours=24)
            estado.update(ultimo_ok=datetime.now(), mensaje="Conectado con la nube.")
        except ErrorNube as e:
            estado.update(ultimo_error=datetime.now(), mensaje=str(e))
        except Exception as e:                  # nunca detiene el ciclo
            log.exception("Ciclo de la nube")
            estado.update(ultimo_error=datetime.now(), mensaje=f"Error en el ciclo de la nube: {e}")
        await asyncio.sleep(config.NUBE_CADA_SEG)
