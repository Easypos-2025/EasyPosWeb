"""
Sesión del mesero (dependencia de toda ruta protegida) y estado de activación
del dispositivo en el escritorio.
"""
from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .db import get_emp, get_tmp
from .seguridad import leer_token

_bearer = HTTPBearer(auto_error=False)


@dataclass
class Mesero:
    id_dispositivo: int      # ag_dispositivos.id
    cod_empleado: int
    usuario: str
    nombre_dispositivo: str


async def activacion_escritorio(emp: AsyncSession, usuario: str):
    """Fila de registro_dispositivos de la BD de la empresa (la que activa el escritorio)
    o None si el escritorio aún no lo ha registrado."""
    return (await emp.execute(text("""
        SELECT Id_Dispositivo, Activo, Cod_Empleado, Nombre_Dispositivo, Contrasena
        FROM registro_dispositivos WHERE Usuario = :u
        ORDER BY Id_Dispositivo DESC LIMIT 1
    """), {"u": usuario})).mappings().first()


def estado_de(fila) -> str:
    if not fila:
        return "pendiente"
    return "activo" if int(fila["Activo"] or 0) == 1 else "inactivo"


async def mesero_actual(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
    tmp: AsyncSession = Depends(get_tmp),
    emp: AsyncSession = Depends(get_emp),
) -> Mesero:
    datos = leer_token(cred.credentials) if cred and cred.credentials else None
    if not datos:
        raise HTTPException(status_code=401, detail="Sesión no válida. Ingrese de nuevo.")

    disp = (await tmp.execute(text("""
        SELECT id, usuario, cod_empleado, nombre_dispositivo, version_token, revocado
        FROM ag_dispositivos WHERE id = :id
    """), {"id": datos["dsp"]})).mappings().first()
    # version_token cambia en cada ingreso o salida: solo vale la sesión más reciente
    if not disp or disp["revocado"] or disp["version_token"] != datos["ver"] \
            or str(disp["cod_empleado"]) != datos.get("sub"):
        raise HTTPException(status_code=401, detail="Sesión no válida. Ingrese de nuevo.")

    # El escritorio puede desactivar el dispositivo en cualquier momento
    if estado_de(await activacion_escritorio(emp, disp["usuario"])) != "activo":
        raise HTTPException(status_code=403, detail="Este dispositivo fue desactivado en el escritorio.")

    return Mesero(id_dispositivo=disp["id"], cod_empleado=int(disp["cod_empleado"]),
                  usuario=disp["usuario"], nombre_dispositivo=disp["nombre_dispositivo"])
