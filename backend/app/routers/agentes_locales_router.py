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

La clave es por empresa (no la global de la sincronización del escritorio). En la BD solo queda
su SHA-256 y se muestra una sola vez al crearla o regenerarla.
"""
import hashlib
import re
import secrets
from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_sysadmin
from app.auth.tenant import tenant_guard
from app.database import get_db
from app.services import error_log

router_admin = APIRouter(prefix="/api/agentes-locales", tags=["agentes-locales"],
                         dependencies=[Depends(tenant_guard)])
router_agente = APIRouter(prefix="/api/agente", tags=["agente-local"])

_RE_CODIGO = r"^[A-Za-z0-9_-]{2,20}$"
MINUTOS_EN_LINEA = 3


def _hash(clave: str) -> str:
    return hashlib.sha256(clave.encode("utf-8")).hexdigest()


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
        SELECT a.id, a.company_id, c.name AS empresa, a.codigo, a.clave_prefijo, a.url_local, a.ip_local,
               a.ip_publica, a.version, a.ultimo_contacto, a.activo, a.created_at
        FROM company_local_agents a
        JOIN companies c ON c.id_company = a.company_id
        ORDER BY c.name
    """))).mappings().all()
    ahora = datetime.now()
    return [{**dict(f), "en_linea": bool(f["activo"] and f["ultimo_contacto"]
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
            INSERT INTO company_local_agents (company_id, codigo, clave_hash, clave_prefijo, creado_por)
            VALUES (:c, :cod, :h, :p, :u)
        """), {"c": data.company_id, "cod": data.codigo, "h": _hash(clave), "p": clave[:8], "u": user.id})
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Esa empresa ya tiene agente o el código ya está en uso.")
    return {"ok": True, "clave": clave}


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
    version: Optional[str] = Field(default=None, max_length=40)


@router_agente.post("/latido")
async def latido(data: LatidoIn, request: Request, agente: dict = Depends(agente_actual),
                 db: AsyncSession = Depends(get_db)):
    url = data.url_local if data.url_local and re.match(r"^https?://[\w.\-:]+/?$", data.url_local) else None
    await db.execute(text("""
        UPDATE company_local_agents
        SET url_local = :u, ip_local = :ip, ip_publica = :pub, version = :v, ultimo_contacto = NOW()
        WHERE id = :id
    """), {"u": url, "ip": data.ip_local, "pub": (request.client.host if request.client else None),
           "v": data.version, "id": agente["id"]})
    await db.commit()
    return {"ok": True, "empresa": agente["empresa"], "codigo": agente["codigo"]}


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


@router_agente.get("/fotos-platos")
async def fotos_platos(agente: dict = Depends(agente_actual), db: AsyncSession = Depends(get_db)):
    filas = (await db.execute(text("""
        SELECT id, photo_path, updated_at FROM pos_dishes
        WHERE company_id = :c AND photo_path LIKE 'http%'
    """), {"c": agente["company_id"]})).mappings().all()
    return [{"id_plato": int(f["id"]), "url": f["photo_path"],
             "actualizado": f["updated_at"].isoformat() if f["updated_at"] else None} for f in filas]
