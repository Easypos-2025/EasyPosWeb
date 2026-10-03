"""
Monitor de Errores.

- POST /api/error-log/client       → errores del navegador (VISTA / RED) y marca de toast mostrado.
                                     Sesión opcional (pantallas públicas: cocina, TV, mesero).
                                     Límites: tamaño, cantidad por envío y rate limit por IP (main.py).
- /api/error-log/summary|groups…   → consulta y gestión, SOLO SYSADMIN.
"""
import re
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_sysadmin
from app.auth.jwt_handler import decode_access_token
from app.auth.tenant import tenant_guard, user_from_token, apply_selected_company
from app.database import get_db
from app.services import error_log

router = APIRouter(prefix="/api/error-log", tags=["Monitor de Errores"],
                   dependencies=[Depends(tenant_guard)])

MAX_CLIENT_BODY = 32 * 1024
MAX_EVENTS = 10
MAX_EVENTS_ANON = 3
RETENCION_DIAS = 120
_RE_REF = re.compile(r"^ERR-[0-9A-F]{8}$")


# ─── Errores del navegador ───────────────────────────────────────────────────
class ClientEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["error", "toast"] = "error"
    tipo: Literal["VISTA", "RED"] = "VISTA"
    clase: Optional[str] = Field(None, max_length=150)
    mensaje: Optional[str] = Field(None, max_length=4000)
    stack: Optional[str] = Field(None, max_length=16000)
    vista: Optional[str] = Field(None, max_length=500)
    componente: Optional[str] = Field(None, max_length=200)
    endpoint: Optional[str] = Field(None, max_length=500)
    http_status: Optional[int] = Field(None, ge=0, le=599)
    toast: Optional[str] = Field(None, max_length=500)
    ref: Optional[str] = Field(None, max_length=12)


class ClientBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    events: list[ClientEvent] = Field(..., min_length=1, max_length=MAX_EVENTS)


async def _client_identity(request: Request, db: AsyncSession) -> bool:
    """Identidad SOLO desde el token (validado en servidor). Devuelve True si hay sesión."""
    auth = request.headers.get("authorization") or ""
    if not auth.lower().startswith("bearer "):
        return False
    token = auth[7:].strip()
    payload = decode_access_token(token) or {}
    if payload.get("type") == "waiter":
        error_log.set_identity(company_id=error_log._int(payload.get("company_id")),
                               username=str(payload.get("waiter_name") or "")[:150] or None, rol="MESERO")
        return True
    try:
        user = await user_from_token(db, token)
        await apply_selected_company(db, user)       # registra user_id + empresa efectiva validada
        return True
    except HTTPException:
        return False


@router.post("/client")
async def report_client_errors(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        clen = int(request.headers.get("content-length") or 0)
    except ValueError:
        clen = 0
    if clen <= 0 or clen > MAX_CLIENT_BODY:
        raise HTTPException(status_code=413, detail="Reporte inválido o demasiado grande")
    raw = await request.body()
    if len(raw) > MAX_CLIENT_BODY:
        raise HTTPException(status_code=413, detail="Reporte demasiado grande")
    try:
        batch = ClientBatch.model_validate_json(raw)
    except ValidationError:
        raise HTTPException(status_code=422, detail="Formato de reporte inválido")

    authed = await _client_identity(request, db)
    events = batch.events if authed else batch.events[:MAX_EVENTS_ANON]

    ctx = error_log._request_ctx.get()
    base = error_log.build_request_info(request.scope, ctx)
    base["payload"] = None                     # el cuerpo es el propio reporte, no un payload
    refs = []
    for ev in events:
        if ev.kind == "toast":
            # Marca "toast mostrado" en el detalle del grupo (solo con sesión)
            if authed and ev.ref and _RE_REF.match(ev.ref) and ev.toast:
                await db.execute(text("""
                    UPDATE system_error_details d
                      JOIN system_error_groups g ON g.id = d.group_id
                       SET d.toast_mostrado = 1, d.toast_mensaje = :msg
                     WHERE g.ref_code = :ref AND d.toast_mostrado = 0
                """), {"ref": ev.ref, "msg": error_log.scrub_text(ev.toast, 500)})
            continue
        info = dict(base)
        info["vista_real"] = (ev.vista or "")[:500] or None
        info["vista"] = error_log.normalize_path(ev.vista)
        info["method"] = None
        if ev.tipo == "RED":
            info["path_real"] = error_log.scrub_text(ev.endpoint, 500)
            info["endpoint"] = error_log.normalize_path(ev.endpoint)
        else:
            info["path_real"] = None
            info["endpoint"] = None
        clase = (ev.clase or ("NetworkError" if ev.tipo == "RED" else "Error"))[:150]
        mensaje = ev.mensaje or clase
        refs.append(error_log.record(
            tipo=ev.tipo, nivel="ADVERTENCIA" if ev.tipo == "RED" else "ERROR",
            titulo=f"{clase}: {mensaje.splitlines()[0] if mensaje else ''}",
            clase=clase, mensaje=mensaje, stack=ev.stack, info=info, http_status=ev.http_status,
            componente=ev.componente, toast_mostrado=bool(ev.toast), toast_mensaje=ev.toast,
        ))
    await db.commit()
    return {"ok": True, "refs": [r for r in refs if r]}


# ─── SYSADMIN: resumen para el dashboard ─────────────────────────────────────
_ABIERTO = "estado IN ('NUEVO','EN_REVISION')"


@router.get("/summary")
async def summary(db: AsyncSession = Depends(get_db), _=Depends(require_sysadmin)):
    row = (await db.execute(text(f"""
        SELECT
          COALESCE(SUM({_ABIERTO} AND tipo_error <> 'VERSION_DESACTUALIZADA'), 0)                AS sin_resolver,
          COALESCE(SUM({_ABIERTO} AND tipo_error <> 'VERSION_DESACTUALIZADA' AND nivel='CRITICO'), 0) AS criticos,
          COALESCE(SUM({_ABIERTO} AND tipo_error <> 'VERSION_DESACTUALIZADA' AND nivel='ERROR'), 0)   AS errores,
          COALESCE(SUM({_ABIERTO} AND tipo_error <> 'VERSION_DESACTUALIZADA' AND nivel='ADVERTENCIA'), 0) AS advertencias,
          COALESCE(SUM(estado = 'NUEVO' AND first_seen >= NOW() - INTERVAL 24 HOUR), 0)              AS nuevos_24h,
          COALESCE(SUM({_ABIERTO} AND regresiones > 0), 0)                                          AS regresiones,
          COALESCE(SUM({_ABIERTO} AND tipo_error = 'VERSION_DESACTUALIZADA'), 0)                    AS version,
          COALESCE(SUM({_ABIERTO} AND tipo_error = 'SEGURIDAD'), 0)                                 AS seguridad,
          COALESCE(SUM(CASE WHEN {_ABIERTO} THEN total_empresas ELSE 0 END), 0)                     AS empresas_afectadas
        FROM system_error_groups
    """))).mappings().first()
    por_tipo = (await db.execute(text(f"""
        SELECT tipo_error, COUNT(*) AS n FROM system_error_groups
         WHERE {_ABIERTO} GROUP BY tipo_error ORDER BY n DESC
    """))).mappings().all()
    ultimo = (await db.execute(text(f"""
        SELECT id, ref_code, tipo_error, nivel, titulo, last_seen FROM system_error_groups
         WHERE {_ABIERTO} ORDER BY last_seen DESC LIMIT 1
    """))).mappings().first()
    return {**{k: int(v or 0) for k, v in dict(row).items()},
            "por_tipo": [dict(r) for r in por_tipo],
            "ultimo": dict(ultimo) if ultimo else None}


# ─── SYSADMIN: listado de grupos ─────────────────────────────────────────────
_TABS = {
    "sin_resolver": ("estado IN ('NUEVO','EN_REVISION')",
                     "FIELD(g.nivel,'CRITICO','ERROR','ADVERTENCIA'), g.last_seen DESC"),
    "resueltos": (f"estado = 'RESUELTO' AND g.resuelto_en >= NOW() - INTERVAL {RETENCION_DIAS} DAY",
                  "g.resuelto_en DESC"),
    "ignorados": (f"estado = 'IGNORADO' AND g.resuelto_en >= NOW() - INTERVAL {RETENCION_DIAS} DAY",
                  "g.resuelto_en DESC"),
}


@router.get("/groups")
async def list_groups(
    tab: Literal["sin_resolver", "resueltos", "ignorados"] = "sin_resolver",
    tipo: Optional[str] = Query(None, max_length=30),
    nivel: Optional[str] = Query(None, max_length=15),
    q: Optional[str] = Query(None, max_length=100),
    company: Optional[int] = Query(None, ge=1),
    desde: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    hasta: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    page: int = Query(1, ge=1, le=10000),
    page_size: int = Query(25, ge=5, le=100),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_sysadmin),
):
    where, order = _TABS[tab]
    conds, params = [where.replace("estado", "g.estado", 1)], {}
    from app.models.system_error_model import ERROR_TYPES, ERROR_LEVELS
    if tipo:
        if tipo not in ERROR_TYPES:
            raise HTTPException(status_code=400, detail="Tipo de error inválido")
        conds.append("g.tipo_error = :tipo"); params["tipo"] = tipo
    if nivel:
        if nivel not in ERROR_LEVELS:
            raise HTTPException(status_code=400, detail="Nivel inválido")
        conds.append("g.nivel = :nivel"); params["nivel"] = nivel
    if q:
        conds.append("(g.ref_code LIKE :q OR g.titulo LIKE :q OR g.endpoint LIKE :q OR g.vista LIKE :q)")
        params["q"] = f"%{q.strip()}%"
    if company:
        conds.append("EXISTS (SELECT 1 FROM system_error_companies c WHERE c.group_id = g.id AND c.company_id = :company)")
        params["company"] = company
    if desde:
        conds.append("g.last_seen >= :desde"); params["desde"] = f"{desde} 00:00:00"
    if hasta:
        conds.append("g.last_seen <= :hasta"); params["hasta"] = f"{hasta} 23:59:59"
    w = " AND ".join(conds)
    total = (await db.execute(text(f"SELECT COUNT(*) FROM system_error_groups g WHERE {w}"), params)).scalar()
    rows = (await db.execute(text(f"""
        SELECT g.id, g.ref_code, g.tipo_error, g.nivel, g.titulo, g.clase_error, g.endpoint, g.vista, g.modulo,
               g.first_seen, g.last_seen, g.total_ocurrencias, g.total_empresas, g.estado, g.regresiones,
               g.resuelto_en, g.version_solucion, fc.name AS first_company
          FROM system_error_groups g
          LEFT JOIN companies fc ON fc.id_company = g.first_company_id
         WHERE {w}
         ORDER BY {order}
         LIMIT :lim OFFSET :off
    """), {**params, "lim": page_size, "off": (page - 1) * page_size})).mappings().all()
    counts = (await db.execute(text(f"""
        SELECT
          SUM(estado IN ('NUEVO','EN_REVISION')) AS sin_resolver,
          SUM(estado = 'RESUELTO' AND resuelto_en >= NOW() - INTERVAL {RETENCION_DIAS} DAY) AS resueltos,
          SUM(estado = 'IGNORADO' AND resuelto_en >= NOW() - INTERVAL {RETENCION_DIAS} DAY) AS ignorados
        FROM system_error_groups
    """))).mappings().first()
    return {"total": int(total or 0), "page": page, "page_size": page_size,
            "counts": {k: int(v or 0) for k, v in dict(counts).items()},
            "items": [dict(r) for r in rows]}


# ─── SYSADMIN: detalle de un grupo ───────────────────────────────────────────
@router.get("/groups/{group_id}")
async def get_group(group_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_sysadmin)):
    g = (await db.execute(text("""
        SELECT g.*, fc.name AS first_company, lc.name AS last_company, u.nombre AS resuelto_por_nombre
          FROM system_error_groups g
          LEFT JOIN companies fc ON fc.id_company = g.first_company_id
          LEFT JOIN companies lc ON lc.id_company = g.last_company_id
          LEFT JOIN users u ON u.id = g.resuelto_por
         WHERE g.id = :id
    """), {"id": group_id})).mappings().first()
    if not g:
        raise HTTPException(status_code=404, detail="Error no encontrado")
    details = (await db.execute(text("""
        SELECT d.*, c.name AS company_name, bp.name AS perfil
          FROM system_error_details d
          LEFT JOIN companies c ON c.id_company = d.company_id
          LEFT JOIN business_profiles bp ON bp.id = d.business_profile_id
         WHERE d.group_id = :id ORDER BY d.id DESC LIMIT 20
    """), {"id": group_id})).mappings().all()
    companies = (await db.execute(text("""
        SELECT sc.company_id, c.name AS company_name, sc.ocurrencias, sc.first_seen, sc.last_seen
          FROM system_error_companies sc
          LEFT JOIN companies c ON c.id_company = sc.company_id
         WHERE sc.group_id = :id ORDER BY sc.last_seen DESC LIMIT 300
    """), {"id": group_id})).mappings().all()
    return {"group": dict(g), "details": [dict(d) for d in details], "companies": [dict(c) for c in companies]}


# ─── SYSADMIN: cambiar estado ────────────────────────────────────────────────
class EstadoIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    estado: Literal["NUEVO", "EN_REVISION", "RESUELTO", "IGNORADO"]
    nota: Optional[str] = Field(None, max_length=2000)
    version: Optional[str] = Field(None, max_length=40)


@router.patch("/groups/{group_id}/estado")
async def set_estado(group_id: int, data: EstadoIn, db: AsyncSession = Depends(get_db),
                     user=Depends(require_sysadmin)):
    nota = (data.nota or "").strip() or None
    if data.estado == "RESUELTO" and (not nota or len(nota) < 3):
        raise HTTPException(status_code=400, detail="La nota de la solución es obligatoria")
    cerrar = data.estado in ("RESUELTO", "IGNORADO")
    res = await db.execute(text("""
        UPDATE system_error_groups
           SET estado = :estado,
               nota_solucion = COALESCE(:nota, nota_solucion),
               version_solucion = CASE WHEN :estado = 'RESUELTO' THEN :version ELSE version_solucion END,
               resuelto_por = CASE WHEN :cerrar THEN :uid ELSE resuelto_por END,
               resuelto_en  = CASE WHEN :cerrar THEN NOW() ELSE NULL END
         WHERE id = :id
    """), {"estado": data.estado, "nota": nota, "cerrar": cerrar, "uid": user.id, "id": group_id,
           "version": (data.version or error_log.server_version() or "")[:40] or None})
    if not res.rowcount:
        raise HTTPException(status_code=404, detail="Error no encontrado")
    await db.commit()
    return {"ok": True}


class ResolverVersionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nota: Optional[str] = Field(None, max_length=2000)


@router.post("/groups/resolver-version")
async def resolver_version(data: ResolverVersionIn, db: AsyncSession = Depends(get_db),
                           user=Depends(require_sysadmin)):
    """Resuelve de una vez los errores por versión desactualizada (el cliente ya recargó)."""
    res = await db.execute(text("""
        UPDATE system_error_groups
           SET estado = 'RESUELTO', resuelto_por = :uid, resuelto_en = NOW(), version_solucion = :v,
               nota_solucion = :nota
         WHERE tipo_error = 'VERSION_DESACTUALIZADA' AND estado IN ('NUEVO','EN_REVISION')
    """), {"uid": user.id, "v": error_log.server_version(),
           "nota": (data.nota or "").strip() or "Cliente con compilación anterior: se resolvió al recargar."})
    await db.commit()
    return {"ok": True, "resueltos": res.rowcount}
