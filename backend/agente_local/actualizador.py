"""
Actualización del agente instalado (solo el ejecutable; en desarrollo la versión es "dev").

  1. En cada latido la nube informa la versión vigente (versión, SHA-256, tamaño, notas).
  2. Si es distinta a la instalada, se descarga en segundo plano a actualizaciones/ y se
     verifica la huella SHA-256 (si no coincide, se descarta).
  3. Se aplica:
       A. con el botón "Actualizar ahora" del panel del administrador, o
       B. sola al ABRIR TURNO (cambia la fecha de negocio en datatemppos) si no hay pedidos
          abiertos de los dispositivos.
  4. Para reemplazarse a sí mismo registra una tarea de Windows de un solo uso (cuenta SYSTEM)
     que: detiene el agente, guarda el programa actual en actualizaciones/respaldo, descomprime
     el nuevo, lo arranca y espera que responda con la versión nueva. Si no responde en ~1 minuto
     vuelve al programa anterior. El resultado queda en actualizaciones/resultado.json; el agente
     lo reporta a la nube y al panel al arrancar.
"""
import asyncio
import hashlib
import json
import logging
import subprocess
import urllib.request

from . import VERSION, config

log = logging.getLogger("agente_local")

DIR = config.BASE / "actualizaciones"
TAREA_PRINCIPAL = "EasyPos Agente Local"
TAREA_ACTUALIZAR = "EasyPos Agente Actualizar"
ARCHIVOS = ("_internal", "app", "EasyPosAgente.exe", "easypos.ico")
SIN_VENTANA = 0x08000000

estado = {
    "vigente": None,        # {version, sha256, tamano, notas} informada por la nube
    "descargada": None,     # versión descargada y verificada, lista para aplicar
    "descargando": False,
    "aplicando": False,
    "ultimo": None,         # resultado de la última actualización (resultado.json)
    "reportar": None,       # texto pendiente de enviar a la nube en el próximo latido
    "error": None,
}


def disponible() -> bool:
    """Hay una versión vigente distinta a la instalada (y el agente está instalado, no en desarrollo)."""
    v = estado["vigente"]
    return bool(config.EMPAQUETADO and v and v.get("version") and v["version"] != VERSION)


def _zip(version: str):
    return DIR / f"agente-{version}.zip"


def _sha256(ruta) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def _descargar(v: dict) -> None:
    DIR.mkdir(exist_ok=True)
    destino, temporal = _zip(v["version"]), DIR / "descarga.tmp"
    if destino.exists() and _sha256(destino) == v["sha256"]:
        return
    req = urllib.request.Request(f"{config.NUBE_URL}/api/agente/descarga/{v['version']}",
                                 headers={"X-Agente-Clave": config.NUBE_CLAVE, "User-Agent": f"EasyPosAgenteLocal/{VERSION}"})
    limite = int(v.get("tamano") or 0) + 1024 * 1024
    with urllib.request.urlopen(req, timeout=60) as r, open(temporal, "wb") as f:
        leidos = 0
        while bloque := r.read(1024 * 1024):
            leidos += len(bloque)
            if leidos > limite:
                raise ValueError("El paquete es más grande de lo informado")
            f.write(bloque)
    if _sha256(temporal) != v["sha256"]:
        temporal.unlink(missing_ok=True)
        raise ValueError("La huella SHA-256 del paquete no coincide: se descartó")
    temporal.replace(destino)
    for viejo in DIR.glob("agente-*.zip"):           # solo se conserva el paquete vigente
        if viejo != destino:
            viejo.unlink(missing_ok=True)


async def descargar_si_hace_falta() -> None:
    v = estado["vigente"]
    if not disponible() or estado["descargando"] or estado["descargada"] == v["version"]:
        return
    estado["descargando"] = True
    try:
        await asyncio.to_thread(_descargar, v)
        estado["descargada"], estado["error"] = v["version"], None
        log.info("Actualización %s descargada y verificada", v["version"])
    except Exception as e:
        estado["error"] = f"No se pudo descargar la versión {v['version']}: {e}"
        log.warning(estado["error"])
    finally:
        estado["descargando"] = False


def _script(nueva: str) -> str:
    """PowerShell que reemplaza el programa (corre aparte, como SYSTEM, mientras el agente se detiene)."""
    lista = ",".join(f"'{a}'" for a in ARCHIVOS)
    return f"""$ErrorActionPreference = 'Continue'
$dest = '{config.BASE}'
$zip = '{_zip(nueva)}'
$res = '{DIR / 'resultado.json'}'
$respaldo = '{DIR / 'respaldo'}'
$archivos = @({lista})
$anterior = '{VERSION}'; $nueva = '{nueva}'; $puerto = {config.PUERTO}
function Escribir($estado, $mensaje) {{
  @{{ estado = $estado; desde = $anterior; hacia = $nueva; mensaje = $mensaje; fecha = (Get-Date -Format s) }} |
    ConvertTo-Json | Set-Content -Encoding UTF8 $res
}}
function Detener {{
  schtasks /End /TN '{TAREA_PRINCIPAL}' | Out-Null
  Start-Sleep -Seconds 2
  taskkill /F /IM EasyPosAgente.exe 2>$null | Out-Null
  Start-Sleep -Seconds 2
}}
function Responde {{
  for ($i = 0; $i -lt 30; $i++) {{
    try {{ $r = Invoke-RestMethod "http://127.0.0.1:$puerto/api/ag/salud" -TimeoutSec 3; if ($r.version -eq $nueva) {{ return $true }} }} catch {{}}
    Start-Sleep -Seconds 2
  }}
  return $false
}}
Detener
Remove-Item -Recurse -Force $respaldo -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $respaldo | Out-Null
foreach ($n in $archivos) {{ if (Test-Path "$dest\\$n") {{ Move-Item "$dest\\$n" "$respaldo\\$n" -Force }} }}
$err = ''
try {{ Expand-Archive -Path $zip -DestinationPath $dest -Force -ErrorAction Stop; $ok = $true }} catch {{ $ok = $false; $err = $_.Exception.Message }}
if ($ok) {{
  schtasks /Run /TN '{TAREA_PRINCIPAL}' | Out-Null
  if (Responde) {{ Escribir 'OK' 'Actualizado'; schtasks /Delete /TN '{TAREA_ACTUALIZAR}' /F | Out-Null; exit 0 }}
  $err = 'La versión nueva no respondió'
}}
Detener
foreach ($n in $archivos) {{
  Remove-Item -Recurse -Force "$dest\\$n" -ErrorAction SilentlyContinue
  if (Test-Path "$respaldo\\$n") {{ Move-Item "$respaldo\\$n" "$dest\\$n" -Force }}
}}
Escribir 'REVERTIDO' $err
schtasks /Run /TN '{TAREA_PRINCIPAL}' | Out-Null
schtasks /Delete /TN '{TAREA_ACTUALIZAR}' /F | Out-Null
"""


def _tarea_xml(script) -> str:
    return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>Actualización del EasyPos Agente Local (se borra sola)</Description></RegistrationInfo>
  <Principals><Principal id="Author"><UserId>S-1-5-18</UserId><RunLevel>HighestAvailable</RunLevel></Principal></Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT30M</ExecutionTimeLimit>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
  </Settings>
  <Actions Context="Author">
    <Exec><Command>powershell.exe</Command><Arguments>-NoProfile -ExecutionPolicy Bypass -File "{script}"</Arguments></Exec>
  </Actions>
</Task>"""


def aplicar(motivo: str) -> None:
    """Lanza la tarea que reemplaza el programa. El agente se detiene en pocos segundos."""
    nueva = estado["descargada"]
    if not disponible() or not nueva or nueva != estado["vigente"]["version"] or estado["aplicando"]:
        raise RuntimeError("No hay una actualización descargada y verificada para aplicar.")
    estado["aplicando"] = True
    script, xml = DIR / "actualizar.ps1", DIR / "actualizar.xml"
    script.write_text(_script(nueva), encoding="utf-8-sig")
    xml.write_text(_tarea_xml(script), encoding="utf-16")
    (DIR / "resultado.json").unlink(missing_ok=True)
    for args in (["schtasks", "/Create", "/TN", TAREA_ACTUALIZAR, "/XML", str(xml), "/F"],
                 ["schtasks", "/Run", "/TN", TAREA_ACTUALIZAR]):
        r = subprocess.run(args, capture_output=True, text=True, creationflags=SIN_VENTANA)
        if r.returncode != 0:
            estado["aplicando"] = False
            raise RuntimeError(f"No se pudo iniciar la actualización: {(r.stderr or r.stdout).strip()}")
    log.info("Actualización %s → %s iniciada (%s)", VERSION, nueva, motivo)


async def aplicar_ahora(motivo: str) -> str:
    """Opción A (panel del agente o pantalla de los meseros): descarga si falta y aplica.
    Solo instala la versión vigente publicada, verificada por su huella. Lanza RuntimeError."""
    if not disponible():
        raise RuntimeError("El agente ya tiene la versión vigente.")
    if not estado["descargada"]:
        await descargar_si_hace_falta()
    aplicar(motivo)
    await publicar_aviso()
    return estado["descargada"]


def para_dispositivos() -> dict:
    """Lo que ve la mini-app: solo si hay una versión nueva lista para instalar."""
    v = estado["vigente"] or {}
    lista = bool(disponible() and estado["descargada"] and estado["descargada"] == v.get("version"))
    return {"lista": lista, "aplicando": bool(estado["aplicando"]),
            "nueva": v.get("version") if lista else None, "notas": v.get("notas") if lista else None}


def texto_aviso() -> str:
    """Aviso para mostrar en el escritorio (vacío si no hay nada que avisar)."""
    v = estado["vigente"] or {}
    if estado["aplicando"]:
        return f"Actualizando el EasyPos Agente Local a la versión {v.get('version')}…"
    if disponible():
        if estado["descargada"]:
            return (f"Hay una actualización del EasyPos Agente Local (versión {v.get('version')}). "
                    "Se instala sola al abrir turno, o ahora desde el Panel del Agente.")
        return f"Descargando una actualización del EasyPos Agente Local (versión {v.get('version')})…"
    return ""


async def publicar_aviso() -> None:
    """Deja el aviso en datatemppos.ag_config para que el programa de escritorio lo muestre:
         SELECT valor FROM ag_config WHERE clave = 'aviso_escritorio'
    Nunca lanza."""
    from sqlalchemy import text

    from .db import SesionTemp
    v = estado["vigente"] or {}
    valores = {"aviso_escritorio": texto_aviso(), "version_instalada": VERSION,
               "version_disponible": v.get("version") if disponible() else ""}
    try:
        async with SesionTemp() as s:
            for clave, valor in valores.items():
                await s.execute(text("""
                    INSERT INTO ag_config (clave, valor) VALUES (:c, :v) ON DUPLICATE KEY UPDATE valor = :v
                """), {"c": clave, "v": (valor or "")[:255]})
            await s.commit()
    except Exception:
        log.exception("No se pudo publicar el aviso para el escritorio")


def al_abrir_turno(pedidos_abiertos: int) -> bool:
    """Opción B: se abrió turno en el escritorio. Se actualiza si hay versión lista y ningún
    pedido de los dispositivos está abierto (si los hay, espera al próximo turno)."""
    if not (estado["descargada"] and disponible()) or estado["aplicando"]:
        return False
    if pedidos_abiertos:
        log.info("Turno abierto con %s pedidos de dispositivos: la actualización espera", pedidos_abiertos)
        return False
    aplicar("apertura de turno")
    return True


async def revisar_resultado() -> None:
    """Se llama al arrancar y en cada ciclo: el script escribe resultado.json cuando el agente nuevo
    ya está corriendo (o tras volver al anterior), así que no basta con leerlo al arrancar."""
    if not (DIR / "resultado.json").exists():
        return
    leer_resultado()
    ultimo = estado["ultimo"] or {}
    if ultimo.get("estado") != "OK":
        from . import errores
        await errores.registrar(origen="agente", tipo="SERVIDOR", nivel="CRITICO",
                                titulo=f"La actualización a {ultimo.get('hacia')} falló y se volvió a la versión anterior",
                                mensaje=ultimo.get("mensaje"))


def leer_resultado() -> None:
    """Al arrancar: resultado de la última actualización (para el panel y la nube)."""
    archivo, reportado = DIR / "resultado.json", DIR / "resultado_reportado.json"
    try:
        if archivo.exists():
            r = json.loads(archivo.read_text(encoding="utf-8-sig"))
            estado["reportar"] = f"{r.get('estado')} {r.get('desde')} → {r.get('hacia')} {r.get('fecha', '')}: {r.get('mensaje', '')}"[:255]
            archivo.replace(reportado)
        elif reportado.exists():
            r = json.loads(reportado.read_text(encoding="utf-8-sig"))
        else:
            return
        estado["ultimo"] = r
    except Exception:
        log.exception("No se pudo leer el resultado de la actualización")
