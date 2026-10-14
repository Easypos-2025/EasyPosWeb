"""
Agentes Locales: el servicio que corre en el PC de caja de cada empresa (toma de pedidos contra la
BD del escritorio, backend/agente_local).

  SYSADMIN  /api/agentes-locales          asignar agente a una empresa (código + clave propia),
                                          regenerar clave, activar/desactivar, ver último contacto.
  Agente    /api/agente/*                 autenticado con SU clave (encabezado X-Agente-Clave):
                                          solo ve y escribe datos de su propia empresa.
     POST latido        URL/IP local y versión (cada minuto; reemplaza el directorio easypos_api)
     POST errores       errores del agente y de sus dispositivos → Monitor de Errores (AGENTE_LOCAL)
     GET  fotos-platos  fotos subidas en la web para copiarlas al PC (pos_dishes.id = Id_Plato)
     GET  pedidos/pendientes · POST pedidos/recibidos · POST pedidos/resultado
                        pedidos web que esperan la aceptación en caja (sede_pedidos.py)
     POST pedidos/eliminados-caja  productos de pedidos web que el cajero eliminó en el escritorio
     GET  maestros/pendientes · POST maestros/aplicados
                        S3: platos y datos de la sede que la web cambió (sede_maestros.py)

  Público   /c/{enlace}                   QR fijo de la toma de pedidos: redirige a la IP local que el agente
                                          reportó en su último latido (solo IP privada). Sin sesión, con límite
                                          de peticiones; <enlace> es aleatorio (migración 041).

La clave es por empresa (no la global de la sincronización del escritorio). En la BD solo queda
su SHA-256 y se muestra una sola vez al crearla o regenerarla.
"""
import hashlib
import io
import json
import logging
import os
import re
import secrets
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_sysadmin
from app.auth.tenant import tenant_guard
from app.database import get_datatemppos_db, get_db
from app.services import error_log

log = logging.getLogger(__name__)

router_admin = APIRouter(prefix="/api/agentes-locales", tags=["agentes-locales"],
                         dependencies=[Depends(tenant_guard)])
router_agente = APIRouter(prefix="/api/agente", tags=["agente-local"])

_RE_CODIGO = r"^[A-Za-z0-9_-]{2,20}$"
MINUTOS_EN_LINEA = 3
# Mismos estilos de pos_dashboard_router.VALID_CARD_STYLES (company_configs.pos_card_style)
ESTILOS_TARJETAS = {"oval-wood", "circular-gold", "checkered", "minimal-card", "ticket", "bubble"}
# Paquetes de actualización del agente (privados: solo se entregan a un agente con su clave)
DIR_DESCARGAS = Path(os.getenv("AGENTE_DESCARGAS_DIR", "/var/www/easyposweb/descargas_agente"))


async def version_vigente(db: AsyncSession) -> Optional[dict]:
    fila = (await db.execute(text("""
        SELECT id, version, archivo, sha256, tamano, notas, publicado_en FROM agente_versiones
        WHERE vigente = 1 ORDER BY publicado_en DESC LIMIT 1
    """))).mappings().first()
    return dict(fila) if fila else None


def _hash(clave: str) -> str:
    return hashlib.sha256(clave.encode("utf-8")).hexdigest()


def _nuevo_enlace() -> str:
    return secrets.token_urlsafe(9)          # 12 caracteres [A-Za-z0-9_-]: no se puede adivinar


def enlace_qr(enlace: Optional[str]) -> Optional[str]:
    return (os.getenv("APP_PUBLIC_URL", "https://easyposweb.com").rstrip("/") + "/c/" + enlace) if enlace else None


def _nueva_clave() -> str:
    return "ag_" + secrets.token_urlsafe(32)


# ───────────────────────────── SYSADMIN ─────────────────────────────

class AgenteNuevoIn(BaseModel):
    company_id: int = Field(gt=0)
    codigo: str = Field(pattern=_RE_CODIGO)


class AgenteCambioIn(BaseModel):
    codigo: Optional[str] = Field(default=None, pattern=_RE_CODIGO)
    activo: Optional[bool] = None


@router_admin.get("")
async def listar(db: AsyncSession = Depends(get_db), _=Depends(require_sysadmin)):
    filas = (await db.execute(text("""
        SELECT a.id, a.company_id, c.name AS empresa, a.codigo, a.clave_prefijo, a.url_local, a.url_pc, a.ip_local,
               a.ip_publica, a.version, a.ultimo_contacto, a.activo, a.created_at,
               a.actualizacion, a.actualizacion_en, a.forzar_actualizacion
        FROM company_local_agents a
        JOIN companies c ON c.id_company = a.company_id
        ORDER BY c.name
    """))).mappings().all()
    ahora = datetime.now()
    vigente = await version_vigente(db)
    return [{**dict(f), "version_vigente": vigente["version"] if vigente else None,
             "al_dia": bool(vigente and f["version"] == vigente["version"]), "en_linea": bool(f["activo"] and f["ultimo_contacto"]
                                           and (ahora - f["ultimo_contacto"]).total_seconds() < MINUTOS_EN_LINEA * 60)}
            for f in filas]


@router_admin.post("")
async def crear(data: AgenteNuevoIn, db: AsyncSession = Depends(get_db), user=Depends(require_sysadmin)):
    existe = (await db.execute(text("SELECT COUNT(*) FROM companies WHERE id_company = :c"),
                               {"c": data.company_id})).scalar()
    if not existe:
        raise HTTPException(status_code=404, detail="La empresa no existe.")
    clave = _nueva_clave()
    try:
        await db.execute(text("""
            INSERT INTO company_local_agents (company_id, codigo, clave_hash, clave_prefijo, creado_por, enlace)
            VALUES (:c, :cod, :h, :p, :u, :e)
        """), {"c": data.company_id, "cod": data.codigo, "h": _hash(clave), "p": clave[:8], "u": user.id,
               "e": _nuevo_enlace()})
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Esa empresa ya tiene agente o el código ya está en uso.")
    return {"ok": True, "clave": clave}


@router_admin.get("/versiones")
async def listar_versiones(db: AsyncSession = Depends(get_db), _=Depends(require_sysadmin)):
    filas = (await db.execute(text("""
        SELECT v.id, v.version, v.sha256, v.tamano, v.notas, v.vigente, v.publicado_en,
               (SELECT COUNT(*) FROM company_local_agents a WHERE a.version = v.version AND a.activo = 1) AS sedes
        FROM agente_versiones v ORDER BY v.publicado_en DESC
    """))).mappings().all()
    return [dict(f) for f in filas]


@router_admin.post("/versiones/{id_version}/vigente")
async def hacer_vigente(id_version: int, db: AsyncSession = Depends(get_db), _=Depends(require_sysadmin)):
    """Permite volver a una versión anterior: las sedes la toman como actualización."""
    existe = (await db.execute(text("SELECT archivo FROM agente_versiones WHERE id = :id"), {"id": id_version})).scalar()
    if not existe or not (DIR_DESCARGAS / existe).is_file():
        raise HTTPException(status_code=404, detail="Versión no encontrada o sin archivo en el servidor.")
    await db.execute(text("UPDATE agente_versiones SET vigente = (id = :id)"), {"id": id_version})
    await db.commit()
    return {"ok": True}


@router_admin.post("/{agente_id}/forzar")
async def forzar_actualizacion(agente_id: int, db: AsyncSession = Depends(get_db), user=Depends(require_sysadmin)):
    """El agente aplica la versión vigente apenas la tenga descargada (la recibe en el próximo latido).
    Se desmarca sola cuando el agente reporta la versión vigente."""
    n = (await db.execute(text("UPDATE company_local_agents SET forzar_actualizacion = 1 WHERE id = :id"),
                          {"id": agente_id})).rowcount
    if not n:
        raise HTTPException(status_code=404, detail="Agente no encontrado.")
    await db.commit()
    log.info("Actualización forzada del agente id=%s por usuario=%s", agente_id, getattr(user, "id", None))
    return {"ok": True}


@router_admin.post("/{agente_id}/clave")
async def regenerar_clave(agente_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_sysadmin)):
    clave = _nueva_clave()
    n = (await db.execute(text("""
        UPDATE company_local_agents SET clave_hash = :h, clave_prefijo = :p WHERE id = :id
    """), {"h": _hash(clave), "p": clave[:8], "id": agente_id})).rowcount
    if not n:
        raise HTTPException(status_code=404, detail="Agente no encontrado.")
    await db.commit()
    return {"ok": True, "clave": clave}


@router_admin.patch("/{agente_id}")
async def cambiar(agente_id: int, data: AgenteCambioIn, db: AsyncSession = Depends(get_db),
                  _=Depends(require_sysadmin)):
    campos, p = [], {"id": agente_id}
    if data.codigo is not None:
        campos.append("codigo = :cod"); p["cod"] = data.codigo
    if data.activo is not None:
        campos.append("activo = :act"); p["act"] = 1 if data.activo else 0
    if not campos:
        return {"ok": True}
    try:
        n = (await db.execute(text(f"UPDATE company_local_agents SET {', '.join(campos)} WHERE id = :id"), p)).rowcount
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="El código ya está en uso.")
    if not n:
        raise HTTPException(status_code=404, detail="Agente no encontrado.")
    return {"ok": True}


class AgenteEliminarIn(BaseModel):
    codigo: str = Field(min_length=1, max_length=20)     # confirmación: se escribe el código del agente


@router_admin.delete("/{agente_id}")
async def eliminar(agente_id: int, data: AgenteEliminarIn, db: AsyncSession = Depends(get_db),
                   user=Depends(require_sysadmin)):
    """Libera la empresa y el código (p. ej. un agente de prueba). La clave queda inválida: el agente
    instalado con ella es rechazado de inmediato. Las versiones publicadas no se tocan."""
    fila = (await db.execute(text("SELECT company_id, codigo FROM company_local_agents WHERE id = :id"),
                             {"id": agente_id})).mappings().first()
    if not fila:
        raise HTTPException(status_code=404, detail="Agente no encontrado.")
    if data.codigo.strip() != fila["codigo"]:
        raise HTTPException(status_code=422, detail="El código escrito no coincide con el del agente.")
    await db.execute(text("DELETE FROM company_local_agents WHERE id = :id"), {"id": agente_id})
    await db.commit()
    log.warning("Agente local eliminado: id=%s empresa=%s codigo=%s por usuario=%s",
                agente_id, fila["company_id"], fila["codigo"], getattr(user, "id", None))
    return {"ok": True}


# ───────────────────────────── Agente (clave propia) ─────────────────────────────

async def agente_actual(x_agente_clave: Optional[str] = Header(default=None),
                        db: AsyncSession = Depends(get_db)) -> dict:
    if not x_agente_clave or len(x_agente_clave) > 100:
        raise HTTPException(status_code=401, detail="Clave de agente requerida.")
    fila = (await db.execute(text("""
        SELECT a.id, a.company_id, a.codigo, c.name AS empresa
        FROM company_local_agents a JOIN companies c ON c.id_company = a.company_id
        WHERE a.clave_hash = :h AND a.activo = 1
    """), {"h": _hash(x_agente_clave)})).mappings().first()
    if not fila:
        error_log.record_security("Clave de agente local inválida o inactiva", http_status=401)
        raise HTTPException(status_code=401, detail="Clave de agente inválida o inactiva.")
    error_log.set_identity(company_id=fila["company_id"], username=f"agente:{fila['codigo']}", rol="AGENTE_LOCAL")
    return dict(fila)


class LatidoIn(BaseModel):
    url_local: Optional[str] = Field(default=None, max_length=200)
    ip_local: Optional[str] = Field(default=None, max_length=45)
    url_pc: Optional[str] = Field(default=None, max_length=200)          # http://NOMBRE-PC:8090
    version: Optional[str] = Field(default=None, max_length=40)
    actualizacion: Optional[str] = Field(default=None, max_length=255)   # resultado de su última actualización


@router_agente.post("/latido")
async def latido(data: LatidoIn, request: Request, agente: dict = Depends(agente_actual),
                 db: AsyncSession = Depends(get_db)):
    url = data.url_local if data.url_local and re.match(r"^https?://[\w.\-:]+/?$", data.url_local) else None
    url_pc = data.url_pc if data.url_pc and re.match(r"^http://[A-Za-z0-9_\-]{1,63}:\d{2,5}/?$", data.url_pc) else None
    await db.execute(text("""
        UPDATE company_local_agents
        SET url_local = :u, url_pc = :upc, ip_local = :ip, ip_publica = :pub, version = :v, ultimo_contacto = NOW()
        WHERE id = :id
    """), {"u": url, "upc": url_pc, "ip": data.ip_local, "pub": (request.client.host if request.client else None),
           "v": data.version, "id": agente["id"]})
    if data.actualizacion:
        await db.execute(text("""
            UPDATE company_local_agents SET actualizacion = :a, actualizacion_en = NOW() WHERE id = :id
        """), {"a": data.actualizacion, "id": agente["id"]})
    vigente = await version_vigente(db)
    # Forzar actualización: se desmarca cuando el agente ya tiene la versión vigente
    if vigente and data.version == vigente["version"]:
        await db.execute(text("UPDATE company_local_agents SET forzar_actualizacion = 0 WHERE id = :id"),
                         {"id": agente["id"]})
    forzar = (await db.execute(text("SELECT forzar_actualizacion FROM company_local_agents WHERE id = :id"),
                               {"id": agente["id"]})).scalar()
    await db.commit()
    # Estilo de tarjetas de las cuentas abiertas que la empresa escogió en la web (también en la mini-app)
    estilo = (await db.execute(text("SELECT pos_card_style FROM company_configs WHERE company_id = :c"),
                               {"c": agente["company_id"]})).scalar()
    enlace = (await db.execute(text("SELECT enlace FROM company_local_agents WHERE id = :id"), {"id": agente["id"]})).scalar()
    if not enlace:
        enlace = _nuevo_enlace()
        await db.execute(text("UPDATE company_local_agents SET enlace = :e WHERE id = :id"), {"e": enlace, "id": agente["id"]})
        await db.commit()
    return {"ok": True, "empresa": agente["empresa"], "codigo": agente["codigo"],
            "enlace_qr": enlace_qr(enlace),
            "estilo_tarjetas": estilo if estilo in ESTILOS_TARJETAS else "oval-wood",
            "forzar_actualizacion": bool(forzar),
            "version_vigente": {k: vigente[k] for k in ("version", "sha256", "tamano", "notas")} if vigente else None}


@router_agente.get("/descarga/{version}")
async def descargar_version(version: str, agente: dict = Depends(agente_actual), db: AsyncSession = Depends(get_db)):
    """Paquete de actualización (solo a un agente con su clave; la versión debe estar publicada)."""
    from fastapi.responses import FileResponse
    archivo = (await db.execute(text("SELECT archivo FROM agente_versiones WHERE version = :v"),
                                {"v": version[:40]})).scalar()
    ruta = (DIR_DESCARGAS / archivo).resolve() if archivo else None
    if not ruta or ruta.parent != DIR_DESCARGAS.resolve() or not ruta.is_file():
        raise HTTPException(status_code=404, detail="Versión no disponible.")
    return FileResponse(ruta, media_type="application/zip", filename=archivo)


class EventoAgenteIn(BaseModel):
    origen: Literal["agente", "dispositivo"] = "agente"
    tipo: Literal["SERVIDOR", "BASE_DATOS", "RED", "VISTA", "IMPRESION", "INTEGRACION"] = "SERVIDOR"
    nivel: Literal["CRITICO", "ERROR", "ADVERTENCIA"] = "ERROR"
    titulo: str = Field(max_length=255)
    mensaje: Optional[str] = Field(default=None, max_length=4000)
    detalle: Optional[str] = Field(default=None, max_length=8000)
    vista: Optional[str] = Field(default=None, max_length=255)
    dispositivo: Optional[str] = Field(default=None, max_length=150)
    ocurrencias: int = Field(default=1, ge=1, le=100000)
    version: Optional[str] = Field(default=None, max_length=40)


class ErroresIn(BaseModel):
    eventos: list[EventoAgenteIn] = Field(max_length=50)


@router_agente.post("/errores")
async def recibir_errores(data: ErroresIn, request: Request, agente: dict = Depends(agente_actual)):
    refs = []
    for ev in data.eventos:
        info = {
            "identity": {"company_id": agente["company_id"], "username": f"agente:{agente['codigo']}", "rol": "AGENTE_LOCAL"},
            "endpoint": None, "vista": error_log.normalize_path(ev.vista) if ev.vista else f"agente:{ev.origen}",
            "vista_real": ev.vista, "path_real": None, "method": None, "payload": None, "query_params": None,
            "version_cliente": None, "user_agent": f"EasyPos Agente Local {ev.version or ''}".strip(),
            "ip": request.client.host if request.client else None,
        }
        refs.append(error_log.record(
            tipo="AGENTE_LOCAL", nivel=ev.nivel, titulo=f"[{ev.tipo}] {ev.titulo}", clase=f"AgenteLocal.{ev.tipo}",
            mensaje=(ev.mensaje or ev.titulo) + (f"\nDispositivo: {ev.dispositivo}" if ev.dispositivo else "")
                    + (f"\nOcurrencias en el agente: {ev.ocurrencias}" if ev.ocurrencias > 1 else ""),
            stack=ev.detalle, info=info, codigo_error=f"AGENTE_{ev.tipo}", componente=ev.origen,
        ))
    return {"ok": True, "refs": [r for r in refs if r]}


# ───────────────────────────── Pedidos web → escritorio ─────────────────────────────
# Lotes pendientes de aceptar en caja (app/services/sede_pedidos.py). El agente los baja cada 10 s,
# confirma que los recibió y reporta lo que hizo el cajero. La empresa es SIEMPRE la de la clave.

MAX_LOTES_ENVIO = 20


@router_agente.get("/pedidos/pendientes")
async def pedidos_pendientes(agente: dict = Depends(agente_actual), db: AsyncSession = Depends(get_db)):
    cid = agente["company_id"]
    lotes = (await db.execute(text("""
        SELECT id, nro_pedido, tipo, canal, id_mesa, mesa, mesero, mesero_nombre, id_cliente, comensales,
               total, items, enviado_por, motivo_solicitud, creado_en
        FROM pos_sede_lotes WHERE company_id = :c AND estado = 'PENDIENTE'
        ORDER BY id LIMIT :n
    """), {"c": cid, "n": MAX_LOTES_ENVIO})).mappings().all()
    if not lotes:
        return {"lotes": []}
    ids = [int(l["id"]) for l in lotes]
    ph = ", ".join(f":l{n}" for n in range(len(ids)))
    por_lote: dict = {}
    for r in (await db.execute(text(f"""
        SELECT lote_id, item, id_plato, descripcion, cantidad, valor, novedad, cambios,
               producto_personalizado, insumos, novedades
        FROM pos_sede_lote_items WHERE company_id = :c AND lote_id IN ({ph}) ORDER BY lote_id, item
    """), {"c": cid, **{f"l{n}": v for n, v in enumerate(ids)}})).mappings().all():
        por_lote.setdefault(int(r["lote_id"]), []).append({
            "item": int(r["item"]), "id_plato": int(r["id_plato"]), "descripcion": r["descripcion"],
            "cantidad": float(r["cantidad"]), "valor": int(r["valor"]), "novedad": r["novedad"],
            "cambios": r["cambios"], "producto_personalizado": r["producto_personalizado"],
            "insumos": json.loads(r["insumos"] or "[]"), "novedades": json.loads(r["novedades"] or "[]")})
    return {"lotes": [{
        "id": int(l["id"]), "nro_pedido": l["nro_pedido"], "tipo": l["tipo"], "canal": l["canal"],
        "id_mesa": int(l["id_mesa"]), "mesa": l["mesa"], "mesero": int(l["mesero"]),
        "mesero_nombre": l["mesero_nombre"], "id_cliente": int(l["id_cliente"]), "comensales": int(l["comensales"]),
        "total": int(l["total"]), "enviado_por": l["enviado_por"], "motivo_solicitud": l["motivo_solicitud"],
        "creado_en": l["creado_en"].isoformat(timespec="seconds") if l["creado_en"] else None,
        "items": por_lote.get(int(l["id"]), [])} for l in lotes]}


class RecibidosIn(BaseModel):
    ids: list[int] = Field(max_length=MAX_LOTES_ENVIO)


@router_agente.post("/pedidos/recibidos")
async def pedidos_recibidos(data: RecibidosIn, agente: dict = Depends(agente_actual),
                            db: AsyncSession = Depends(get_db)):
    if data.ids:
        ph = ", ".join(f":l{n}" for n in range(len(data.ids)))
        await db.execute(text(f"""
            UPDATE pos_sede_lotes SET estado = 'RECIBIDO', recibido_en = NOW()
            WHERE company_id = :c AND estado = 'PENDIENTE' AND id IN ({ph})
        """), {"c": agente["company_id"], **{f"l{n}": int(v) for n, v in enumerate(data.ids)}})
        await db.commit()
    return {"ok": True}


class ResultadoLoteIn(BaseModel):
    id: int = Field(gt=0)
    estado: Literal["ACEPTADO", "APLICADO", "RECHAZADO", "ERROR"]
    por: Optional[str] = Field(default=None, max_length=150)
    desde: Optional[Literal["VB", "MINIAPP"]] = None
    pc: Optional[str] = Field(default=None, max_length=100)
    motivo: Optional[str] = Field(default=None, max_length=255)
    mensaje: Optional[str] = Field(default=None, max_length=500)


class ResultadosIn(BaseModel):
    resultados: list[ResultadoLoteIn] = Field(max_length=50)


# Desde qué estados se puede llegar a cada uno (lo repetido se ignora: el agente reintenta sin daño)
_TRANSICIONES = {
    "ACEPTADO":  ("PENDIENTE", "RECIBIDO", "ERROR"),
    "APLICADO":  ("PENDIENTE", "RECIBIDO", "ACEPTADO", "ERROR"),
    "RECHAZADO": ("PENDIENTE", "RECIBIDO", "ACEPTADO", "ERROR"),
    "ERROR":     ("PENDIENTE", "RECIBIDO", "ACEPTADO", "ERROR"),
}


@router_agente.post("/pedidos/resultado")
async def pedidos_resultado(data: ResultadosIn, agente: dict = Depends(agente_actual),
                            db: AsyncSession = Depends(get_db), db_temp: AsyncSession = Depends(get_datatemppos_db)):
    from app.services import sede_pedidos
    cid = agente["company_id"]
    aplicados = []
    for r in data.resultados:
        lote = (await db.execute(text("""
            SELECT id, company_id, nro_pedido, tipo, estado FROM pos_sede_lotes
            WHERE id = :id AND company_id = :c FOR UPDATE
        """), {"id": r.id, "c": cid})).mappings().first()
        if not lote:
            continue
        if lote["estado"] not in _TRANSICIONES[r.estado]:
            aplicados.append(r.id)          # ya estaba: se confirma para que el agente no reintente
            continue
        motivo = (r.motivo or "").strip() or None
        if r.estado == "RECHAZADO" and not motivo:
            continue                         # el rechazo siempre lleva motivo
        if r.estado == "APLICADO":
            await sede_pedidos.aplicar_en_nube(db, db_temp, dict(lote))
        elif r.estado == "RECHAZADO":
            await sede_pedidos.rechazar_en_nube(db, db_temp, dict(lote))
        await db.execute(text("""
            UPDATE pos_sede_lotes SET estado = :e,
                procesado_en    = IF(:e IN ('ACEPTADO','RECHAZADO','APLICADO') AND procesado_en IS NULL, NOW(), procesado_en),
                aplicado_en     = IF(:e = 'APLICADO', NOW(), aplicado_en),
                procesado_por   = COALESCE(:por, procesado_por),
                procesado_desde = COALESCE(:desde, procesado_desde),
                pc              = COALESCE(:pc, pc),
                motivo          = COALESCE(:motivo, motivo),
                mensaje         = IF(:e = 'ERROR', :msg, NULL)
            WHERE id = :id AND company_id = :c
        """), {"e": r.estado, "por": r.por, "desde": r.desde, "pc": r.pc, "motivo": motivo,
               "msg": r.mensaje, "id": r.id, "c": cid})
        await db_temp.commit()
        await db.commit()
        aplicados.append(r.id)
    return {"ok": True, "confirmados": aplicados}


class EliminadoCajaIn(BaseModel):
    nro_pedido: str = Field(min_length=1, max_length=255)
    items: list[int] = Field(min_length=1, max_length=200)


class EliminadosCajaIn(BaseModel):
    pedidos: list[EliminadoCajaIn] = Field(max_length=50)


@router_agente.post("/pedidos/eliminados-caja")
async def pedidos_eliminados_caja(data: EliminadosCajaIn, agente: dict = Depends(agente_actual),
                                  db_temp: AsyncSession = Depends(get_datatemppos_db)):
    """S2: el cajero eliminó en el escritorio productos de un pedido web: salen también de la web.
    Solo pedidos WEB- de la empresa de la clave; lo que tenga una solicitud pendiente no se toca."""
    from app.services import sede_pedidos
    hechos = 0
    for p in data.pedidos:
        if not p.nro_pedido.startswith("WEB-"):
            continue
        hechos += await sede_pedidos.eliminar_desde_caja(db_temp, agente["company_id"], p.nro_pedido, p.items)
    await db_temp.commit()
    return {"ok": True, "eliminados": hechos}


# ───────────────────────────── S3: tablas maestras ─────────────────────────────

@router_agente.get("/maestros/pendientes")
async def maestros_pendientes(agente: dict = Depends(agente_actual), db: AsyncSession = Depends(get_db)):
    from app.services import sede_maestros
    return await sede_maestros.pendientes(db, agente["company_id"])


@router_agente.get("/maestros/resumen")
async def maestros_resumen(agente: dict = Depends(agente_actual), db: AsyncSession = Depends(get_db)):
    """Liviano (número y nombre): el agente lo consulta cada minuto para el aviso del escritorio."""
    from app.services import sede_maestros
    return await sede_maestros.resumen(db, agente["company_id"])


class PlatoAplicadoIn(BaseModel):
    id_web: int = Field(gt=0)
    id_real: int = Field(gt=0)
    actualizado: Optional[str] = Field(default=None, max_length=30)


class FilaAplicadaIn(BaseModel):
    id: int = Field(gt=0)
    actualizado: Optional[str] = Field(default=None, max_length=30)


class MaestrosAplicadosIn(BaseModel):
    platos: list[PlatoAplicadoIn] = Field(default_factory=list, max_length=500)
    sede_actualizado: Optional[str] = Field(default=None, max_length=30)
    # S3b: catálogos con número propio, listas de precios
    entidades: dict[Literal["forma_medida", "categoria_productos", "categoria_platos", "proveedor", "insumo", "cliente"],
                    list[PlatoAplicadoIn]] = Field(default_factory=dict)
    listas: list[FilaAplicadaIn] = Field(default_factory=list, max_length=2000)
    listas_cabecera: list[FilaAplicadaIn] = Field(default_factory=list, max_length=200)


@router_agente.post("/maestros/aplicados")
async def maestros_aplicados(data: MaestrosAplicadosIn, agente: dict = Depends(agente_actual),
                             db: AsyncSession = Depends(get_db), db_temp: AsyncSession = Depends(get_datatemppos_db)):
    from app.services import sede_maestros
    if any(len(v) > 500 for v in data.entidades.values()):
        raise HTTPException(status_code=422, detail="Demasiados registros en un envío.")
    r = await sede_maestros.confirmar(
        db, agente["company_id"], [p.model_dump() for p in data.platos], data.sede_actualizado,
        entidades={k: [x.model_dump() for x in v] for k, v in data.entidades.items()},
        listas=[x.model_dump() for x in data.listas], listas_cabecera=[x.model_dump() for x in data.listas_cabecera],
        db_temp=db_temp)
    await db.commit()
    await db_temp.commit()
    return r


@router_agente.get("/fotos-platos")
async def fotos_platos(agente: dict = Depends(agente_actual), db: AsyncSession = Depends(get_db)):
    # Foto subida en la web: URL de Spaces (https://…) o ruta del servidor (/uploads/…); un nombre de
    # archivo del escritorio (ej. "aji.jpg") no es foto de la web
    filas = (await db.execute(text("""
        SELECT id, photo_path, updated_at FROM pos_dishes
        WHERE company_id = :c AND (photo_path LIKE 'http%' OR photo_path LIKE '/uploads/%')
    """), {"c": agente["company_id"]})).mappings().all()
    return [{"id_plato": int(f["id"]), "url": url_publica(f["photo_path"]),
             "actualizado": f["updated_at"].isoformat() if f["updated_at"] else None} for f in filas]


def url_publica(ruta: str) -> str:
    """Las rutas /uploads/… se sirven desde el dominio público de EasyPosWeb."""
    if ruta.startswith("/uploads/"):
        return os.getenv("APP_PUBLIC_URL", "https://easyposweb.com").rstrip("/") + ruta
    return ruta


# ───────────────────────────── Empresa (su propio agente) ─────────────────────────────
# Para el dashboard de la empresa: dirección local del agente y QR para los celulares.
# La empresa es la efectiva del usuario (topbar validada en el servidor), nunca la del navegador.


# ───────────────────────────── Traslados de la Bodega Central ─────────────────────────────
# El agente consulta sus tareas (salidas, cargues y devoluciones de traslados en su sede) y reporta el
# resultado. Todo automático (sin cajero). Ver app/services/bodega_traslados.py.

@router_agente.get("/traslados/pendientes")
async def traslados_pendientes(agente: dict = Depends(agente_actual), db: AsyncSession = Depends(get_db)):
    from app.services import bodega_traslados
    return {"tareas": await bodega_traslados.tareas_agente(db, int(agente["company_id"]))}


class TrasladoItemResultadoIn(BaseModel):
    id: int = Field(gt=0)
    destino_dish_id: Optional[int] = Field(default=None, ge=0)
    resultado: Optional[Literal["CREADO", "ACTUALIZADO"]] = None
    stock_antes: Optional[float] = None
    stock_despues: Optional[float] = None


class TrasladoResultadoIn(BaseModel):
    id: int = Field(gt=0)
    tarea: Literal["SALIDA", "CARGUE", "REVERSA"]
    ok: bool
    error: Optional[str] = Field(default=None, max_length=255)
    items: list[TrasladoItemResultadoIn] = Field(default_factory=list, max_length=300)


class TrasladosResultadoIn(BaseModel):
    resultados: list[TrasladoResultadoIn] = Field(max_length=20)


@router_agente.post("/traslados/resultado")
async def traslados_resultado(data: TrasladosResultadoIn, agente: dict = Depends(agente_actual),
                              db: AsyncSession = Depends(get_db)):
    from app.services import bodega_traslados
    out = []
    for r in data.resultados:
        out.append(await bodega_traslados.resultado_agente(db, agente, r.model_dump()))
        await db.commit()                       # uno por uno: un error no deshace los anteriores
    return {"ok": True, "resultados": out}

router_empresa = APIRouter(prefix="/api/mi-agente-local", tags=["agente-local"], dependencies=[Depends(tenant_guard)])


async def _agente_empresa(db: AsyncSession, company_id: int):
    return (await db.execute(text("""
        SELECT url_local, url_pc, version, ultimo_contacto, activo, enlace FROM company_local_agents WHERE company_id = :c
    """), {"c": company_id})).mappings().first()


@router_empresa.get("")
async def mi_agente(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    a = await _agente_empresa(db, user.company_id)
    # Solo se muestra cuando el agente ya se instaló y se conectó al menos una vez
    if not a or not a["activo"] or not a["ultimo_contacto"]:
        return {"existe": False}
    en_linea = bool(a["ultimo_contacto"] and (datetime.now() - a["ultimo_contacto"]).total_seconds() < MINUTOS_EN_LINEA * 60)
    return {"existe": True, "url_local": a["url_local"], "url_pc": a["url_pc"], "version": a["version"],
            "enlace_qr": enlace_qr(a["enlace"]),
            "ultimo_contacto": a["ultimo_contacto"], "en_linea": en_linea}


@router_empresa.get("/qr.png")
async def mi_agente_qr(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    a = await _agente_empresa(db, user.company_id)
    if not a or not a["activo"] or not a["url_local"]:
        raise HTTPException(status_code=404, detail="El agente aún no ha reportado su dirección.")
    import io

    import qrcode
    from fastapi.responses import Response
    buf = io.BytesIO()
    # QR fijo por la nube (no cambia con la IP); si aún no hay enlace, la dirección local
    destino = enlace_qr(a["enlace"]) or (a["url_local"].rstrip("/") + "/")
    qrcode.make(destino, box_size=8, border=2).save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png", headers={"Cache-Control": "no-store"})


# ───────────────────────────── Público: QR fijo de la toma de pedidos ─────────────────────────────

router_publico = APIRouter(tags=["agente-local"])
MINUTOS_REDIRECCION = 10        # sin latido en este tiempo, la caja se considera desconectada
_RE_ENLACE = re.compile(r"^[A-Za-z0-9_-]{8,24}$")
_SIN_CACHE = {"Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow", "Referrer-Policy": "no-referrer"}


def destino_local(url: Optional[str]) -> Optional[str]:
    """http://IP:PUERTO/ solo si la IP es privada (red del negocio): nunca redirige a otro sitio."""
    import ipaddress
    from urllib.parse import urlsplit
    if not url:
        return None
    try:
        partes = urlsplit(url)
        ip = ipaddress.ip_address(partes.hostname or "")
        puerto = partes.port or 80
    except ValueError:
        return None
    if partes.scheme != "http" or ip.version != 4 or not ip.is_private or ip.is_loopback or not (1 <= puerto <= 65535):
        return None
    return f"http://{ip}:{puerto}/"


def _pagina(titulo: str, texto: str, codigo: int):
    import html
    from fastapi.responses import HTMLResponse
    cuerpo = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<title>{html.escape(titulo)}</title>
<style>body{{margin:0;font-family:system-ui,Segoe UI,Roboto,sans-serif;background:#f1f5f9;color:#1e293b;display:flex;
min-height:100vh;align-items:center;justify-content:center;padding:16px;box-sizing:border-box}}
.c{{background:#fff;border-radius:18px;padding:26px 22px;max-width:420px;width:100%;text-align:center;
box-shadow:0 10px 30px rgba(15,23,42,.12)}}h1{{font-size:21px;margin:0 0 10px}}p{{color:#475569;line-height:1.5;margin:0 0 16px}}
a{{display:inline-block;background:#1d4ed8;color:#fff;text-decoration:none;padding:12px 22px;border-radius:12px;font-weight:700}}
</style></head><body><div class="c"><h1>{html.escape(titulo)}</h1><p>{texto}</p>
<a href="">Reintentar</a></div></body></html>"""
    return HTMLResponse(cuerpo, status_code=codigo, headers=_SIN_CACHE)


@router_publico.get("/c/{enlace}", include_in_schema=False)
async def qr_fijo(enlace: str, db: AsyncSession = Depends(get_db)):
    from fastapi.responses import RedirectResponse
    if not _RE_ENLACE.match(enlace):
        return _pagina("Enlace no válido", "Revise el código QR de la toma de pedidos.", 404)
    a = (await db.execute(text("""
        SELECT url_local, ultimo_contacto FROM company_local_agents WHERE enlace = :e AND activo = 1
    """), {"e": enlace})).mappings().first()
    if not a:
        return _pagina("Enlace no válido", "Revise el código QR de la toma de pedidos.", 404)
    destino = destino_local(a["url_local"])
    reciente = a["ultimo_contacto"] and (datetime.now() - a["ultimo_contacto"]).total_seconds() < MINUTOS_REDIRECCION * 60
    if not destino or not reciente:
        return _pagina("La caja no está conectada",
                       "El computador de caja está apagado o sin internet. Enciéndalo (o revise su conexión) y "
                       "vuelva a intentar en un minuto. El celular debe estar en el wifi del negocio.", 503)
    return RedirectResponse(destino, status_code=302, headers=_SIN_CACHE)
