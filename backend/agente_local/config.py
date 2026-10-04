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
from pathlib import Path

from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / ".env")


def _requerida(nombre: str) -> str:
    valor = os.getenv(nombre, "").strip()
    if not valor:
        raise RuntimeError(f"Falta la variable {nombre} en agente_local/.env")
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
DIR_APP = Path(os.getenv("AG_DIR_APP") or BASE.parent.parent / "frontend" / "dist_tomapedido")
PUERTO = int(os.getenv("AG_PUERTO", "8090"))

# Sesión del mesero: dura un turno largo; un nuevo ingreso invalida la anterior
TOKEN_HORAS = int(os.getenv("AG_TOKEN_HORAS", "14"))

# Anti-abuso
LOGIN_MAX_FALLOS        = 5     # fallos permitidos por usuario o por IP…
LOGIN_VENTANA_MIN       = 10    # …en esta ventana de minutos
REGISTRO_MAX_POR_IP     = 5     # registros de dispositivo por IP por hora
REGISTRO_MAX_PENDIENTES = 20    # dispositivos esperando activación en el escritorio
MAX_CUERPO_BYTES        = 64 * 1024
