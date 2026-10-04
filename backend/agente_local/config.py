"""
Configuración del Agente Local.

Se lee de `agente_local/.env` (uno por PC del negocio; ver `.env.ejemplo`).
  AG_DB_EMPRESA_URL  BD real de la empresa (ej. maduritos): catálogo, precios, clientes,
                     mesas, meseros y registro_dispositivos.
  AG_DB_TEMP_URL     datatemppos: pedidos (temp_comanda…), menú del día, armado y
                     las tablas propias del agente (ag_*).
  AG_SECRETO         firma de los tokens (≥ 32 caracteres). Si falta se genera una vez
                     y se guarda en `secreto.key` junto a este archivo.
"""
import os
import secrets
import sys
from pathlib import Path

from dotenv import load_dotenv

# Carpeta de trabajo del agente (.env, secreto.key, logs, caché de fotos).
# Instalado (ejecutable): la carpeta del .exe. En desarrollo: la carpeta de este paquete.
EMPAQUETADO = getattr(sys, "frozen", False)
BASE = Path(sys.executable).resolve().parent if EMPAQUETADO else Path(__file__).resolve().parent
load_dotenv(BASE / ".env")


def _requerida(nombre: str) -> str:
    valor = os.getenv(nombre, "").strip()
    if not valor:
        raise RuntimeError(f"Falta la variable {nombre} en el archivo .env del agente ({BASE})")
    return valor


def _secreto() -> str:
    valor = os.getenv("AG_SECRETO", "").strip()
    if len(valor) >= 32:
        return valor
    archivo = BASE / "secreto.key"
    if archivo.exists():
        valor = archivo.read_text(encoding="utf-8").strip()
        if len(valor) >= 32:
            return valor
    valor = secrets.token_urlsafe(48)
    archivo.write_text(valor, encoding="utf-8")
    return valor


DB_EMPRESA_URL = _requerida("AG_DB_EMPRESA_URL")
DB_TEMP_URL    = _requerida("AG_DB_TEMP_URL")
SECRETO        = _secreto()

HOST   = os.getenv("AG_HOST", "0.0.0.0")

# Carpeta de la mini-app compilada (por defecto la del repositorio)
DIR_APP = Path(os.getenv("AG_DIR_APP") or (BASE / "app" if EMPAQUETADO else BASE.parent.parent / "frontend" / "dist_tomapedido"))
PUERTO = int(os.getenv("AG_PUERTO", "8090"))

# Sesión del mesero: dura un turno largo; un nuevo ingreso invalida la anterior
TOKEN_HORAS = int(os.getenv("AG_TOKEN_HORAS", "14"))

# Anti-abuso
LOGIN_MAX_FALLOS        = 5     # fallos permitidos por usuario o por IP…
LOGIN_VENTANA_MIN       = 10    # …en esta ventana de minutos
REGISTRO_MAX_POR_IP     = 5     # registros de dispositivo por IP por hora
REGISTRO_MAX_PENDIENTES = 20    # dispositivos esperando activación en el escritorio
MAX_CUERPO_BYTES        = 64 * 1024

# Nube (EasyPosWeb): latido, envío de errores al Monitor y fotos de la web.
# La clave la asigna SYSADMIN en "Agentes Locales" (una por empresa). Sin clave el agente
# funciona igual en la red local, solo que no reporta a la nube.
NUBE_URL   = os.getenv("AG_NUBE_URL", "https://easyposweb.com").rstrip("/")
NUBE_CLAVE = os.getenv("AG_NUBE_CLAVE", "").strip()
NUBE_CADA_SEG = int(os.getenv("AG_NUBE_CADA_SEG", "60"))
