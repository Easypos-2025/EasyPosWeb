"""
Registro, activación e ingreso de dispositivos (mismo flujo de la app Android anterior):

  1. registro  → crea temp_registro_dispositivos (Activo=0) para que el escritorio lo vea
                 en "Dispositivos nuevos", y ag_dispositivos con la clave cifrada.
  2. estado    → el dispositivo espera hasta que el escritorio lo active
                 (registro_dispositivos.Activo = 1 en la BD de la empresa).
  3. ingresar  → usuario + clave → token de sesión. Cada ingreso invalida la sesión anterior.

Los dispositivos creados por la app anterior (sin fila en ag_dispositivos) se adoptan al
primer ingreso validando la clave del escritorio, sin modificar su fila.
"""
import hmac
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from typing import Literal

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .. import VERSION, auditoria, config, errores
from ..db import get_emp, get_tmp
from ..seguridad import (cadena_aleatoria, cifrar_clave, crear_token, gastar_tiempo_clave,
                         hash_secreto, ip_cliente, leer_token, nuevo_secreto, verificar_clave)
from ..sesion import Mesero, activacion_escritorio, estado_de, mesero_actual

router = APIRouter(prefix="/api/ag", tags=["dispositivos"])

_USUARIO = r"^[A-Za-z0-9._-]{3,25}$"
_NOMBRE  = r"^[A-Za-z0-9 ._-]{2,40}$"   # va dentro del Nro_Pedido: sin caracteres raros


class RegistroIn(BaseModel):
    nombre_dispositivo: str = Field(pattern=_NOMBRE)
    usuario: str = Field(pattern=_USUARIO)
    clave: str = Field(min_length=4, max_length=64)

    @field_validator("nombre_dispositivo")
    @classmethod
    def _limpiar(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 2:
            raise ValueError("Nombre de dispositivo muy corto")
        return v


class IngresoIn(BaseModel):
    usuario: str = Field(pattern=_USUARIO)
    clave: str = Field(min_length=1, max_length=64)


# ───────────────────────────── utilidades ─────────────────────────────

async def _nombre_mesero(emp: AsyncSession, cod: int) -> str:
    nombre = (await emp.execute(text("SELECT nombres FROM meseros WHERE cod_empleado = :c"),
                                {"c": cod})).scalar()
    return (nombre or "").strip()


async def _codigo_empleado_libre(emp: AsyncSession, tmp: AsyncSession) -> int:
    """Código de empleado que no exista en ninguna tabla de empleados/meseros/dispositivos."""
    for _ in range(30):
        cod = 10000 + secrets.randbelow(90000)
        p = {"c": cod}
        ocupado = (await emp.execute(text("""
            SELECT (SELECT COUNT(*) FROM empleados WHERE cod_empleado = :c)
                 + (SELECT COUNT(*) FROM meseros WHERE cod_empleado = :c)
                 + (SELECT COUNT(*) FROM registro_dispositivos WHERE Cod_Empleado = :c)
        """), p)).scalar() or 0
        ocupado += (await tmp.execute(text("""
            SELECT (SELECT COUNT(*) FROM temp_registro_dispositivos WHERE Cod_Empleado = :c)
                 + (SELECT COUNT(*) FROM temp_empleados WHERE cod_empleado = :c)
                 + (SELECT COUNT(*) FROM temp_meseros WHERE cod_empleado = :c)
                 + (SELECT COUNT(*) FROM ag_dispositivos WHERE cod_empleado = :c)
        """), p)).scalar() or 0
        if not ocupado:
            return cod
    raise HTTPException(status_code=503, detail="No fue posible asignar un código de mesero. Intente de nuevo.")


async def _disp_por_secreto(tmp: AsyncSession, secreto: str | None):
    if not secreto or len(secreto) > 100:
        return None
    return (await tmp.execute(text("""
        SELECT id, usuario, cod_empleado, nombre_dispositivo, revocado
        FROM ag_dispositivos WHERE secreto_hash = :h
    """), {"h": hash_secreto(secreto)})).mappings().first()


# ───────────────────────────── rutas ─────────────────────────────

@router.post("/dispositivos/registro")
async def registrar_dispositivo(data: RegistroIn, request: Request,
                                tmp: AsyncSession = Depends(get_tmp),
                                emp: AsyncSession = Depends(get_emp)):
    ip = ip_cliente(request)
    if await auditoria.contar("registro", "ok", 60, ip=ip) >= config.REGISTRO_MAX_POR_IP:
        raise HTTPException(status_code=429, detail="Demasiados registros desde este equipo. Intente más tarde.")

    pendientes = (await tmp.execute(text(
        "SELECT COUNT(*) FROM temp_registro_dispositivos WHERE Activo = 0"))).scalar() or 0
    if pendientes >= config.REGISTRO_MAX_PENDIENTES:
        raise HTTPException(status_code=429, detail="Hay demasiados dispositivos esperando activación en el escritorio.")

    p = {"u": data.usuario, "n": data.nombre_dispositivo}
    usuario_existe = (await emp.execute(text(
        "SELECT COUNT(*) FROM registro_dispositivos WHERE Usuario = :u"), p)).scalar() \
        or (await tmp.execute(text("""
            SELECT (SELECT COUNT(*) FROM temp_registro_dispositivos WHERE Usuario = :u)
                 + (SELECT COUNT(*) FROM ag_dispositivos WHERE usuario = :u)
        """), p)).scalar()
    if usuario_existe:
        raise HTTPException(status_code=409, detail="Ese usuario ya está registrado. Use Ingresar.")

    nombre_existe = (await emp.execute(text(
        "SELECT COUNT(*) FROM registro_dispositivos WHERE Nombre_Dispositivo = :n"), p)).scalar() \
        or (await tmp.execute(text("""
            SELECT (SELECT COUNT(*) FROM temp_registro_dispositivos WHERE Nombre_Dispositivo = :n)
                 + (SELECT COUNT(*) FROM ag_dispositivos WHERE nombre_dispositivo = :n)
        """), p)).scalar()
    if nombre_existe:
        raise HTTPException(status_code=409, detail="Ya hay un dispositivo registrado con ese nombre.")

    cod = await _codigo_empleado_libre(emp, tmp)
    secreto = nuevo_secreto()
    ahora = datetime.now()
    try:
        # Igual que la app anterior: el escritorio lo lista en "Dispositivos nuevos"
        await tmp.execute(text("""
            INSERT INTO temp_registro_dispositivos
                (Nombre_Dispositivo, Usuario, Contrasena, Activo, Fecha_Activacion, Cod_Empleado)
            VALUES (:n, :u, :c, 0, :f, :cod)
        """), {"n": data.nombre_dispositivo, "u": data.usuario, "c": cadena_aleatoria(25),
               "f": ahora.strftime("%Y-%m-%d %H:%M:%S"), "cod": cod})
        await tmp.execute(text("""
            INSERT INTO ag_dispositivos
                (usuario, cod_empleado, nombre_dispositivo, clave_hash, secreto_hash, creado, ultima_ip)
            VALUES (:u, :cod, :n, :h, :s, :f, :ip)
        """), {"u": data.usuario, "cod": cod, "n": data.nombre_dispositivo,
               "h": cifrar_clave(data.clave), "s": hash_secreto(secreto), "f": ahora, "ip": ip})
        await tmp.commit()
    except IntegrityError:
        await tmp.rollback()
        raise HTTPException(status_code=409, detail="Ese usuario ya está registrado. Use Ingresar.")

    await auditoria.registrar("registro", "ok", ip, data.usuario, cod, detalle=data.nombre_dispositivo)
    return {"estado": "pendiente", "secreto": secreto, "usuario": data.usuario,
            "nombre_dispositivo": data.nombre_dispositivo, "cod_empleado": cod}


@router.get("/dispositivos/estado")
async def estado_dispositivo(x_ag_dispositivo: str | None = Header(default=None),
                             tmp: AsyncSession = Depends(get_tmp),
                             emp: AsyncSession = Depends(get_emp)):
    """Consulta del dispositivo mientras espera la activación en el escritorio."""
    disp = await _disp_por_secreto(tmp, x_ag_dispositivo)
    if not disp or disp["revocado"]:
        raise HTTPException(status_code=401, detail="Dispositivo no reconocido. Regístrelo o ingrese de nuevo.")
    estado = estado_de(await activacion_escritorio(emp, disp["usuario"]))
    return {"estado": estado, "usuario": disp["usuario"], "nombre_dispositivo": disp["nombre_dispositivo"]}


@router.post("/sesion/ingresar")
async def ingresar(data: IngresoIn, request: Request,
                   tmp: AsyncSession = Depends(get_tmp),
                   emp: AsyncSession = Depends(get_emp)):
    ip = ip_cliente(request)
    if await auditoria.contar("ingreso", "fallo", config.LOGIN_VENTANA_MIN, ip=ip, usuario=data.usuario) \
            >= config.LOGIN_MAX_FALLOS:
        raise HTTPException(status_code=429,
                            detail=f"Demasiados intentos fallidos. Intente en {config.LOGIN_VENTANA_MIN} minutos.")

    async def _fallo(motivo: str):
        await auditoria.registrar("ingreso", "fallo", ip, data.usuario, detalle=motivo)
        raise HTTPException(status_code=401, detail="Usuario o clave incorrectos.")

    disp = (await tmp.execute(text("""
        SELECT id, usuario, cod_empleado, nombre_dispositivo, clave_hash, version_token, revocado
        FROM ag_dispositivos WHERE usuario = :u
    """), {"u": data.usuario})).mappings().first()
    escritorio = await activacion_escritorio(emp, data.usuario)

    if disp:
        if not verificar_clave(data.clave, disp["clave_hash"]):
            await _fallo("clave")
        if disp["revocado"]:
            await auditoria.registrar("ingreso", "fallo", ip, data.usuario, detalle="revocado")
            raise HTTPException(status_code=403, detail="Este dispositivo está bloqueado.")
    else:
        # Dispositivo de la app anterior: se valida con la clave guardada por el escritorio
        clave_escritorio = (escritorio or {}).get("Contrasena") or ""
        if not escritorio or not clave_escritorio or \
                not hmac.compare_digest(clave_escritorio.encode("utf-8"), data.clave.encode("utf-8")):
            gastar_tiempo_clave(data.clave)
            await _fallo("usuario o clave")
        try:
            await tmp.execute(text("""
                INSERT INTO ag_dispositivos (usuario, cod_empleado, nombre_dispositivo, clave_hash, creado)
                VALUES (:u, :cod, :n, :h, :f)
            """), {"u": data.usuario, "cod": int(escritorio["Cod_Empleado"] or 0),
                   "n": (escritorio["Nombre_Dispositivo"] or data.usuario)[:150],
                   "h": cifrar_clave(data.clave), "f": datetime.now()})
            await tmp.commit()
        except IntegrityError:
            await tmp.rollback()
        disp = (await tmp.execute(text("""
            SELECT id, usuario, cod_empleado, nombre_dispositivo, clave_hash, version_token, revocado
            FROM ag_dispositivos WHERE usuario = :u
        """), {"u": data.usuario})).mappings().first()
        await auditoria.registrar("adopcion", "ok", ip, data.usuario, disp["cod_empleado"], disp["id"])

    # Nuevo secreto en cada ingreso: si se borraron los datos del navegador, se recupera aquí
    secreto = nuevo_secreto()
    estado = estado_de(escritorio)
    if estado != "activo":
        await tmp.execute(text("UPDATE ag_dispositivos SET secreto_hash = :s WHERE id = :id"),
                          {"s": hash_secreto(secreto), "id": disp["id"]})
        await tmp.commit()
        await auditoria.registrar("ingreso", estado, ip, data.usuario, disp["cod_empleado"], disp["id"])
        return {"estado": estado, "secreto": secreto}

    # El código de empleado que vale es el que quedó en el escritorio al activarlo
    cod = int(escritorio["Cod_Empleado"] or disp["cod_empleado"])
    version = int(disp["version_token"]) + 1
    await tmp.execute(text("""
        UPDATE ag_dispositivos
        SET version_token = :v, secreto_hash = :s, cod_empleado = :cod, ultimo_acceso = :f, ultima_ip = :ip
        WHERE id = :id
    """), {"v": version, "s": hash_secreto(secreto), "cod": cod, "f": datetime.now(), "ip": ip, "id": disp["id"]})
    await tmp.commit()
    await auditoria.registrar("ingreso", "ok", ip, data.usuario, cod, disp["id"])

    return {
        "estado": "activo",
        "token": crear_token(disp["id"], cod, version),
        "secreto": secreto,
        "mesero": {"cod_empleado": cod, "usuario": disp["usuario"],
                   "nombre": await _nombre_mesero(emp, cod) or disp["usuario"],
                   "nombre_dispositivo": disp["nombre_dispositivo"]},
    }


@router.post("/sesion/salir")
async def salir(request: Request, mesero: Mesero = Depends(mesero_actual),
                tmp: AsyncSession = Depends(get_tmp)):
    await tmp.execute(text("UPDATE ag_dispositivos SET version_token = version_token + 1 WHERE id = :id"),
                      {"id": mesero.id_dispositivo})
    await tmp.commit()
    await auditoria.registrar("salida", "ok", ip_cliente(request), mesero.usuario,
                              mesero.cod_empleado, mesero.id_dispositivo)
    return {"ok": True}


@router.get("/sesion/yo")
async def yo(mesero: Mesero = Depends(mesero_actual), emp: AsyncSession = Depends(get_emp)):
    return {"cod_empleado": mesero.cod_empleado, "usuario": mesero.usuario,
            "nombre": await _nombre_mesero(emp, mesero.cod_empleado) or mesero.usuario,
            "nombre_dispositivo": mesero.nombre_dispositivo}


# ───────────────────────────── conexión y errores del dispositivo ─────────────────────────────

@router.post("/sesion/latido")
async def latido(request: Request, mesero: Mesero = Depends(mesero_actual), tmp: AsyncSession = Depends(get_tmp)):
    """El dispositivo avisa que sigue conectado (el panel muestra quién perdió la conexión)."""
    await tmp.execute(text("UPDATE ag_dispositivos SET ultimo_acceso = :f, ultima_ip = :ip WHERE id = :id"),
                      {"f": datetime.now(), "ip": ip_cliente(request), "id": mesero.id_dispositivo})
    await tmp.commit()
    return {"ok": True, "version": VERSION}        # la mini-app se recarga sola si el agente se actualizó


class EventoDispositivoIn(BaseModel):
    tipo: Literal["RED", "VISTA"] = "VISTA"
    nivel: Literal["ERROR", "ADVERTENCIA"] = "ERROR"
    titulo: str = Field(min_length=1, max_length=200)
    mensaje: str | None = Field(default=None, max_length=2000)
    detalle: str | None = Field(default=None, max_length=4000)
    vista: str | None = Field(default=None, max_length=200)
    cuando: str | None = Field(default=None, max_length=40)


class ErroresDispositivoIn(BaseModel):
    eventos: list[EventoDispositivoIn] = Field(min_length=1, max_length=20)


@router.post("/errores")
async def errores_dispositivo(data: ErroresDispositivoIn, request: Request, tmp: AsyncSession = Depends(get_tmp),
                              authorization: str | None = Header(default=None)):
    """Errores que vio el dispositivo (incluidos los guardados mientras no tenía conexión).
    Se aceptan con o sin sesión (sin conexión pudo vencerse), con límite por IP."""
    ip = ip_cliente(request)
    if await auditoria.contar("error_dispositivo", "ok", 10, ip=ip) >= 30:
        return {"ok": True, "registrados": 0}           # silencioso: no se le da información a un abusador
    dispositivo = f"IP {ip}"
    datos = leer_token(authorization[7:]) if authorization and authorization.lower().startswith("bearer ") else None
    if datos:
        nombre = (await tmp.execute(text("SELECT nombre_dispositivo FROM ag_dispositivos WHERE id = :id"),
                                    {"id": datos["dsp"]})).scalar()
        if nombre:
            dispositivo = f"{nombre} ({ip})"
    for ev in data.eventos:
        mensaje = (ev.mensaje or "") + (f"\nOcurrió: {ev.cuando}" if ev.cuando else "")
        await errores.registrar(origen="dispositivo", tipo=ev.tipo, nivel=ev.nivel, titulo=ev.titulo,
                                mensaje=mensaje.strip() or None, detalle=ev.detalle, vista=ev.vista,
                                dispositivo=dispositivo, ip=ip)
    await auditoria.registrar("error_dispositivo", "ok", ip, detalle=f"{len(data.eventos)} eventos")
    return {"ok": True, "registrados": len(data.eventos)}
