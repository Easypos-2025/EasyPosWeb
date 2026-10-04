"""
Panel de administración local del agente (dashboard de la empresa en el PC de caja).
Protegido con la clave de administrador (ag_config.clave_admin, cifrada); no es para meseros.
Aquí irán llegando utilidades que hoy están en el programa de escritorio.

  POST /api/ag/admin/ingresar          clave → token de administrador
  POST /api/ag/admin/clave             cambiar la clave (invalida las sesiones abiertas)
  GET  /api/ag/admin/resumen           indicadores del dashboard
  GET  /api/ag/admin/errores           errores del agente y de los dispositivos
  POST /api/ag/admin/errores/{id}/resolver | reabrir
  GET  /api/ag/admin/dispositivos      dispositivos con su conexión
  POST /api/ag/admin/dispositivos/{id}/bloquear | habilitar
  POST /api/ag/admin/fotos/sincronizar copiar las fotos de la web al escritorio
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .. import VERSION, auditoria, config, nube
from ..db import get_emp, get_tmp
from ..seguridad import cifrar_clave, gastar_tiempo_clave, ip_cliente, verificar_clave

router = APIRouter(prefix="/api/ag/admin", tags=["admin"])
_bearer = HTTPBearer(auto_error=False)
_TIPO = "agadm"
SEGUNDOS_CONECTADO = 90


# ───────────────────────────── clave de administrador ─────────────────────────────

async def leer_config(tmp, clave: str) -> str | None:
    return (await tmp.execute(text("SELECT valor FROM ag_config WHERE clave = :c"), {"c": clave})).scalar()


async def guardar_config(tmp, clave: str, valor: str) -> None:
    await tmp.execute(text("""
        INSERT INTO ag_config (clave, valor) VALUES (:c, :v) ON DUPLICATE KEY UPDATE valor = :v
    """), {"c": clave, "v": valor})


async def fijar_clave_admin(tmp, nueva: str) -> None:
    """La usa el instalador / `python -m agente_local --clave-admin` y el cambio de clave."""
    version = int(await leer_config(tmp, "admin_version") or 0) + 1
    await guardar_config(tmp, "clave_admin", cifrar_clave(nueva))
    await guardar_config(tmp, "admin_version", str(version))
    await tmp.commit()


def _token(version: int) -> str:
    ahora = datetime.now(timezone.utc)
    return jwt.encode({"typ": _TIPO, "ver": version, "iat": ahora, "exp": ahora + timedelta(hours=12)},
                      config.SECRETO, algorithm="HS256")


async def admin_actual(cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
                       tmp: AsyncSession = Depends(get_tmp)) -> bool:
    try:
        datos = jwt.decode(cred.credentials, config.SECRETO, algorithms=["HS256"]) if cred else None
    except JWTError:
        datos = None
    if not datos or datos.get("typ") != _TIPO or str(datos.get("ver")) != str(await leer_config(tmp, "admin_version")):
        raise HTTPException(status_code=401, detail="Sesión de administrador no válida. Ingrese de nuevo.")
    return True


class ClaveIn(BaseModel):
    clave: str = Field(min_length=1, max_length=64)


class CambioClaveIn(BaseModel):
    actual: str = Field(min_length=1, max_length=64)
    nueva: str = Field(min_length=6, max_length=64)


@router.post("/ingresar")
async def ingresar(data: ClaveIn, request: Request, tmp: AsyncSession = Depends(get_tmp)):
    ip = ip_cliente(request)
    if await auditoria.contar("admin", "fallo", config.LOGIN_VENTANA_MIN, ip=ip) >= config.LOGIN_MAX_FALLOS:
        raise HTTPException(status_code=429, detail=f"Demasiados intentos. Intente en {config.LOGIN_VENTANA_MIN} minutos.")
    hash_guardado = await leer_config(tmp, "clave_admin")
    if not hash_guardado:
        raise HTTPException(status_code=409, detail="El administrador aún no tiene clave. Se crea con el instalador del agente.")
    if not verificar_clave(data.clave, hash_guardado):
        gastar_tiempo_clave(data.clave)
        await auditoria.registrar("admin", "fallo", ip)
        raise HTTPException(status_code=401, detail="Clave incorrecta.")
    await auditoria.registrar("admin", "ok", ip)
    return {"token": _token(int(await leer_config(tmp, "admin_version") or 0))}


@router.post("/clave")
async def cambiar_clave(data: CambioClaveIn, request: Request, _=Depends(admin_actual),
                        tmp: AsyncSession = Depends(get_tmp)):
    if not verificar_clave(data.actual, await leer_config(tmp, "clave_admin")):
        raise HTTPException(status_code=400, detail="La clave actual no es correcta.")
    await fijar_clave_admin(tmp, data.nueva)
    await auditoria.registrar("admin_clave", "ok", ip_cliente(request))
    return {"ok": True, "token": _token(int(await leer_config(tmp, "admin_version") or 0))}


# ───────────────────────────── dashboard ─────────────────────────────

@router.get("/resumen")
async def resumen(_=Depends(admin_actual), emp: AsyncSession = Depends(get_emp), tmp: AsyncSession = Depends(get_tmp)):
    empresa = None
    try:
        empresa = (await emp.execute(text("SELECT Nombre_Almacen FROM configuracion_sede LIMIT 1"))).scalar()
    except Exception:
        pass
    e = (await tmp.execute(text("""
        SELECT COALESCE(SUM(estado <> 'RESUELTO'), 0) AS sin_resolver,
               COALESCE(SUM(estado <> 'RESUELTO' AND nivel = 'CRITICO'), 0) AS criticos,
               COALESCE(SUM(estado <> 'RESUELTO' AND nivel = 'ERROR'), 0) AS errores,
               COALESCE(SUM(estado <> 'RESUELTO' AND nivel = 'ADVERTENCIA'), 0) AS advertencias,
               COALESCE(SUM(estado <> 'RESUELTO' AND tipo = 'RED'), 0) AS conexion,
               COALESCE(SUM(primera >= NOW() - INTERVAL 1 DAY), 0) AS nuevos_24h,
               COALESCE(SUM(regresiones > 0 AND estado <> 'RESUELTO'), 0) AS regresiones
        FROM ag_errores
    """))).mappings().first()
    limite = datetime.now() - timedelta(seconds=SEGUNDOS_CONECTADO)
    d = (await tmp.execute(text("""
        SELECT COUNT(*) AS total, COALESCE(SUM(ultimo_acceso >= :l), 0) AS conectados,
               COALESCE(SUM(revocado = 1), 0) AS bloqueados
        FROM ag_dispositivos
    """), {"l": limite})).mappings().first()
    pedidos = (await tmp.execute(text(
        "SELECT COUNT(*) FROM temp_comanda WHERE Movil = 1 AND Salio = 0"))).scalar() or 0
    n = nube.estado
    return {
        "empresa": (empresa or "").strip() or None, "version": VERSION,
        "direccion": f"http://{nube.ip_local()}:{config.PUERTO}",
        "errores": {k: int(v) for k, v in dict(e).items()},
        "dispositivos": {k: int(v or 0) for k, v in dict(d).items()},
        "pedidos_abiertos": int(pedidos),
        "nube": {"configurada": n["configurada"], "mensaje": n["mensaje"], "empresa": n["empresa"],
                 "ultimo_ok": n["ultimo_ok"], "ultimo_error": n["ultimo_error"], "fotos": n["fotos"]},
    }


# ───────────────────────────── errores ─────────────────────────────

class ResolverIn(BaseModel):
    nota: str = Field(min_length=3, max_length=2000)


@router.get("/errores")
async def listar_errores(estado: str = Query("abiertos", pattern="^(abiertos|resueltos|todos)$"),
                         _=Depends(admin_actual), tmp: AsyncSession = Depends(get_tmp)):
    filtro = {"abiertos": "WHERE estado <> 'RESUELTO'", "resueltos": "WHERE estado = 'RESUELTO'", "todos": ""}[estado]
    filas = (await tmp.execute(text(f"""
        SELECT id, origen, tipo, nivel, titulo, mensaje, detalle, vista, dispositivo, ip, ocurrencias,
               primera, ultima, estado, regresiones, nota, resuelto_en, pendiente_nube
        FROM ag_errores {filtro}
        ORDER BY FIELD(nivel, 'CRITICO', 'ERROR', 'ADVERTENCIA'), ultima DESC
        LIMIT 300
    """))).mappings().all()
    return [dict(f) for f in filas]


@router.post("/errores/{id_error}/resolver")
async def resolver_error(id_error: int, data: ResolverIn, request: Request, _=Depends(admin_actual),
                         tmp: AsyncSession = Depends(get_tmp)):
    n = (await tmp.execute(text("""
        UPDATE ag_errores SET estado = 'RESUELTO', nota = :n, resuelto_en = NOW() WHERE id = :id
    """), {"n": data.nota.strip(), "id": id_error})).rowcount
    if not n:
        raise HTTPException(status_code=404, detail="Error no encontrado.")
    await tmp.commit()
    await auditoria.registrar("admin_resolver", "ok", ip_cliente(request), detalle=f"error {id_error}")
    return {"ok": True}


@router.post("/errores/{id_error}/reabrir")
async def reabrir_error(id_error: int, _=Depends(admin_actual), tmp: AsyncSession = Depends(get_tmp)):
    n = (await tmp.execute(text("UPDATE ag_errores SET estado = 'NUEVO', resuelto_en = NULL WHERE id = :id"),
                           {"id": id_error})).rowcount
    if not n:
        raise HTTPException(status_code=404, detail="Error no encontrado.")
    await tmp.commit()
    return {"ok": True}


# ───────────────────────────── dispositivos ─────────────────────────────

@router.get("/dispositivos")
async def listar_dispositivos(_=Depends(admin_actual), emp: AsyncSession = Depends(get_emp),
                              tmp: AsyncSession = Depends(get_tmp)):
    filas = (await tmp.execute(text("""
        SELECT d.id, d.usuario, d.cod_empleado, d.nombre_dispositivo, d.revocado, d.creado,
               d.ultimo_acceso, d.ultima_ip,
               (SELECT COUNT(*) FROM temp_comanda c WHERE c.Mesero = d.cod_empleado AND c.Salio = 0) AS pedidos
        FROM ag_dispositivos d ORDER BY d.ultimo_acceso DESC
    """))).mappings().all()
    activos = {u for (u,) in (await emp.execute(text(
        "SELECT Usuario FROM registro_dispositivos WHERE Activo = 1"))).all()}
    limite = datetime.now() - timedelta(seconds=SEGUNDOS_CONECTADO)
    return [{**dict(f), "activo_escritorio": f["usuario"] in activos,
             "conectado": bool(f["ultimo_acceso"] and f["ultimo_acceso"] >= limite)} for f in filas]


async def _bloqueo(tmp, id_disp: int, valor: int) -> None:
    n = (await tmp.execute(text("""
        UPDATE ag_dispositivos SET revocado = :v, version_token = version_token + 1 WHERE id = :id
    """), {"v": valor, "id": id_disp})).rowcount
    if not n:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado.")
    await tmp.commit()


@router.post("/dispositivos/{id_disp}/bloquear")
async def bloquear_dispositivo(id_disp: int, request: Request, _=Depends(admin_actual), tmp: AsyncSession = Depends(get_tmp)):
    await _bloqueo(tmp, id_disp, 1)
    await auditoria.registrar("admin_bloquear", "ok", ip_cliente(request), id_dispositivo=id_disp)
    return {"ok": True}


@router.post("/dispositivos/{id_disp}/habilitar")
async def habilitar_dispositivo(id_disp: int, request: Request, _=Depends(admin_actual), tmp: AsyncSession = Depends(get_tmp)):
    await _bloqueo(tmp, id_disp, 0)
    await auditoria.registrar("admin_habilitar", "ok", ip_cliente(request), id_dispositivo=id_disp)
    return {"ok": True}


# ───────────────────────────── QR de la dirección ─────────────────────────────

@router.get("/qr.png")
async def qr_direccion(_=Depends(admin_actual)):
    """QR con la dirección de la toma de pedidos (se escanea con el celular del mesero)."""
    import io

    import qrcode
    from fastapi.responses import Response
    img = qrcode.make(f"http://{nube.ip_local()}:{config.PUERTO}/", box_size=8, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


# ───────────────────────────── fotos de la web ─────────────────────────────

@router.post("/fotos/sincronizar")
async def sincronizar_fotos(_=Depends(admin_actual)):
    if not config.NUBE_CLAVE:
        raise HTTPException(status_code=409, detail="El agente no tiene clave de la nube (AG_NUBE_CLAVE).")
    from ..servicios import fotos_web
    try:
        r = await fotos_web.sincronizar()
    except nube.ErrorNube as e:
        raise HTTPException(status_code=502, detail=str(e))
    nube.estado["fotos"] = r
    return r
