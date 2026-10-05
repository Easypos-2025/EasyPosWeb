"""
Arranque del agente (lo usan `python -m agente_local` y el ejecutable EasyPosAgente.exe).

python -m agente_local                 arranca el agente (desde la carpeta backend/)
python -m agente_local --clave-admin   crea o cambia la clave del panel de administración
python -m agente_local --clave-admin-stdin   igual, leyendo la clave de la entrada estándar (instalador)
"""
import sys

import uvicorn

from . import config


def _clave_admin(desde_stdin: bool = False) -> None:
    import asyncio
    from getpass import getpass

    from .db import SesionTemp, motor_empresa, motor_temp
    from .esquema import crear_esquema
    from .routers.admin import fijar_clave_admin

    if desde_stdin:
        clave = sys.stdin.readline().strip("\r\n")
        if len(clave) < 6:
            sys.exit("La clave debe tener mínimo 6 caracteres.")
    else:
        clave = getpass("Nueva clave del administrador (mínimo 6): ")
        if len(clave) < 6 or clave != getpass("Repítala: "):
            sys.exit("Las claves no coinciden o son muy cortas.")

    async def guardar():
        await crear_esquema()
        async with SesionTemp() as s:
            await fijar_clave_admin(s, clave)
        await motor_empresa.dispose(); await motor_temp.dispose()
    try:
        asyncio.run(guardar())
    except Exception as e:
        # Mensaje corto con la causa real (ej. acceso denegado a la BD), no el rastro completo
        causa = getattr(e, "orig", None) or e
        sys.exit(f"No fue posible guardar la clave del administrador: {type(causa).__name__}: {causa}")
    print("Clave del administrador guardada.")


def principal() -> None:
    if "--clave-admin-stdin" in sys.argv:
        _clave_admin(desde_stdin=True)
    elif "--clave-admin" in sys.argv:
        _clave_admin()
    else:
        from .main import app
        # Un solo proceso: el límite de intentos y los bloqueos viven en la BD, no en memoria
        uvicorn.run(app, host=config.HOST, port=config.PUERTO, workers=1,
                    proxy_headers=False, server_header=False, date_header=False)
