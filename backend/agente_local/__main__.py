"""
python -m agente_local                 arranca el agente (desde la carpeta backend/)
python -m agente_local --clave-admin   crea o cambia la clave del panel de administración
"""
import sys

import uvicorn

from . import config


def _clave_admin() -> None:
    import asyncio
    from getpass import getpass

    from .db import SesionTemp, motor_empresa, motor_temp
    from .esquema import crear_esquema
    from .routers.admin import fijar_clave_admin

    clave = getpass("Nueva clave del administrador (mínimo 6): ")
    if len(clave) < 6 or clave != getpass("Repítala: "):
        sys.exit("Las claves no coinciden o son muy cortas.")

    async def guardar():
        await crear_esquema()
        async with SesionTemp() as s:
            await fijar_clave_admin(s, clave)
        await motor_empresa.dispose(); await motor_temp.dispose()
    asyncio.run(guardar())
    print("Clave del administrador guardada.")


if __name__ == "__main__":
    if "--clave-admin" in sys.argv:
        _clave_admin()
    else:
        # Un solo proceso: el límite de intentos y los bloqueos viven en la BD, no en memoria
        uvicorn.run("agente_local.main:app", host=config.HOST, port=config.PUERTO, workers=1,
                    proxy_headers=False, server_header=False, date_header=False)
