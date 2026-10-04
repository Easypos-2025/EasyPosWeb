"""python -m agente_local  (desde la carpeta backend/)"""
import uvicorn

from . import config

if __name__ == "__main__":
    # Un solo proceso: el límite de intentos y los bloqueos viven en la BD, no en memoria
    uvicorn.run("agente_local.main:app", host=config.HOST, port=config.PUERTO, workers=1,
                proxy_headers=False, server_header=False, date_header=False)
