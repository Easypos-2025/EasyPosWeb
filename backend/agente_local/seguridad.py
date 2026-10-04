"""
Cifrado de claves, secretos de dispositivo y tokens de sesión del agente.
"""
import hashlib
import secrets
import string
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Request
from jose import JWTError, jwt

from . import config

_ALG = "HS256"
_TIPO = "ag"

# Hash fijo para gastar el mismo tiempo cuando el usuario no existe (evita descubrir
# usuarios por la demora de la respuesta)
_HASH_SEÑUELO = bcrypt.hashpw(b"senuelo-no-usar", bcrypt.gensalt(12)).decode()


def cifrar_clave(clave: str) -> str:
    return bcrypt.hashpw(clave.encode("utf-8")[:72], bcrypt.gensalt(12)).decode()


def verificar_clave(clave: str, clave_hash: str | None) -> bool:
    try:
        return bcrypt.checkpw(clave.encode("utf-8")[:72], (clave_hash or _HASH_SEÑUELO).encode())
    except ValueError:
        return False


def gastar_tiempo_clave(clave: str) -> None:
    verificar_clave(clave, _HASH_SEÑUELO)


def nuevo_secreto() -> str:
    """Secreto que identifica al navegador del dispositivo (se guarda solo su hash)."""
    return secrets.token_urlsafe(32)


def hash_secreto(secreto: str) -> str:
    return hashlib.sha256(secreto.encode("utf-8")).hexdigest()


def cadena_aleatoria(largo: int = 25) -> str:
    """Valor para registro_dispositivos.Contrasena: el escritorio lo copia a
    meseros.Clave / empleados.clave, así que no debe ser la clave real ni adivinable."""
    alfabeto = string.ascii_letters + string.digits
    return "".join(secrets.choice(alfabeto) for _ in range(largo))


def crear_token(id_dispositivo: int, cod_empleado: int, version: int) -> str:
    ahora = datetime.now(timezone.utc)
    datos = {
        "typ": _TIPO,
        "sub": str(cod_empleado),
        "dsp": id_dispositivo,
        "ver": version,
        "iat": ahora,
        "exp": ahora + timedelta(hours=config.TOKEN_HORAS),
    }
    return jwt.encode(datos, config.SECRETO, algorithm=_ALG)


def leer_token(token: str) -> dict | None:
    try:
        datos = jwt.decode(token, config.SECRETO, algorithms=[_ALG])
    except JWTError:
        return None
    if datos.get("typ") != _TIPO or not isinstance(datos.get("dsp"), int) or not isinstance(datos.get("ver"), int):
        return None
    return datos


def ip_cliente(request: Request) -> str:
    # El agente atiende directo en la red local (sin proxy): no se confía en X-Forwarded-For
    return (request.client.host if request.client else "")[:45]
