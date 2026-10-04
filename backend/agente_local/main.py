"""
Aplicación del Agente Local.
Arranque: desde backend/  →  python -m agente_local
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import VERSION, config, errores, nube
from .db import motor_empresa, motor_temp
from .esquema import crear_esquema
from .seguridad import ip_cliente
from .routers import admin, catalogo, dispositivos, mesas, pedidos

_dir_logs = config.BASE / "logs"
_dir_logs.mkdir(exist_ok=True)
log = logging.getLogger("agente_local")
if not log.handlers:
    _h = RotatingFileHandler(_dir_logs / "agente.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    _h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(_h)
    log.setLevel(logging.INFO)


@asynccontextmanager
async def _ciclo(app: FastAPI):
    await crear_esquema()
    log.info("Agente Local %s iniciado en el puerto %s", VERSION, config.PUERTO)
    tarea_nube = asyncio.create_task(nube.ciclo())      # latido, errores a la nube y fotos de la web
    yield
    tarea_nube.cancel()
    await motor_empresa.dispose()
    await motor_temp.dispose()


# Sin documentación pública: el agente queda expuesto en la red del negocio
app = FastAPI(title="EasyPos Agente Local", version=VERSION, lifespan=_ciclo,
              docs_url=None, redoc_url=None, openapi_url=None)


@app.middleware("http")
async def _proteccion(request: Request, call_next):
    largo = request.headers.get("content-length")
    if largo and (not largo.isdigit() or int(largo) > config.MAX_CUERPO_BYTES):
        return JSONResponse(status_code=413, content={"detail": "La petición es demasiado grande."})

    respuesta = await call_next(request)
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["X-Frame-Options"] = "DENY"
    respuesta.headers["Referrer-Policy"] = "no-referrer"
    respuesta.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.path.startswith("/api/"):
        respuesta.headers.setdefault("Cache-Control", "no-store")
    else:
        # Mini-app: solo código propio (sin CDN ni scripts en línea)
        respuesta.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
            "connect-src 'self'; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        if not request.url.path.startswith("/assets/"):
            respuesta.headers["Cache-Control"] = "no-cache"     # una compilación nueva se ve al recargar
    return respuesta


@app.exception_handler(RequestValidationError)
async def _datos_invalidos(request: Request, exc: RequestValidationError):
    # No se devuelve el detalle de pydantic (revela la estructura interna)
    return JSONResponse(status_code=422, content={"detail": "Datos inválidos. Revise la información enviada."})


@app.exception_handler(Exception)
async def _error_interno(request: Request, exc: Exception):
    log.exception("Error en %s %s", request.method, request.url.path)
    import traceback
    await errores.registrar(origen="agente", tipo=errores.tipo_de_excepcion(exc), nivel="ERROR",
                            titulo=f"{type(exc).__name__}: {str(exc).splitlines()[0][:150] if str(exc) else ''}",
                            mensaje=str(exc)[:2000], vista=f"{request.method} {request.url.path}",
                            detalle="".join(traceback.format_exception(exc))[-6000:], ip=ip_cliente(request))
    return JSONResponse(status_code=500, content={"detail": "Error interno del agente. Intente de nuevo."})


app.include_router(dispositivos.router)
app.include_router(catalogo.router)
app.include_router(mesas.router)
app.include_router(pedidos.router)
app.include_router(admin.router)


@app.get("/api/ag/salud")
async def salud():
    return {"ok": True, "version": VERSION}


# Mini-app de toma de pedidos (frontend: npm run build:tomapedido). Va de último: no tapa la API.
if config.DIR_APP.is_dir():
    app.mount("/", StaticFiles(directory=config.DIR_APP, html=True), name="tomapedido")
else:
    log.warning("No se encontró la mini-app en %s (solo queda la API)", config.DIR_APP)
