"""
Monitor de Errores (solo SYSADMIN).

Registra los errores de cualquier perfil SIN repetir el mismo error:
- Un error se identifica por su huella (fingerprint): tipo + clase + endpoint/vista + mensaje
  normalizado (sin números, ids ni textos entre comillas). El mismo error en 1000 empresas
  es UN solo grupo.
- Primera ocurrencia → encabezado (system_error_groups) + detalle completo (system_error_details).
- Ocurrencias siguientes → solo contadores del encabezado y de la empresa (system_error_companies).
- Si el grupo estaba RESUELTO y vuelve a ocurrir → se reabre (regresión) con un detalle nuevo.

Reglas de seguridad:
- La empresa / usuario SIEMPRE se resuelven en el servidor (sesión o token), nunca del cuerpo.
- Todo payload, mensaje y traza se sanea (contraseñas, tokens, ext_db_*, tarjetas, cadenas de
  conexión) y se trunca antes de guardarse.
- Los eventos se acumulan en memoria y se escriben agrupados cada pocos segundos: una tormenta
  del mismo error (o un bot) no multiplica escrituras en la BD.
- Registrar un error NUNCA lanza excepción ni rompe la petición original.
"""
import asyncio
import hashlib
import json
import logging
import re
import time
import traceback
from contextvars import ContextVar
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional
from urllib.parse import unquote, parse_qsl

from sqlalchemy import text

logger = logging.getLogger("error_log")

# Respaldo en archivo si la BD no responde
_LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
_fallback: Optional[logging.Logger] = None


def _fallback_logger() -> logging.Logger:
    global _fallback
    if _fallback is None:
        _fallback = logging.getLogger("error_log.fallback")
        _fallback.propagate = False
        try:
            _LOG_DIR.mkdir(parents=True, exist_ok=True)
            h = RotatingFileHandler(_LOG_DIR / "error_log_fallback.log",
                                    maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
            h.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
            _fallback.addHandler(h)
        except Exception:
            pass
    return _fallback


# ─── Límites ─────────────────────────────────────────────────────────────────
MAX_BODY_CAPTURE = 16 * 1024      # bytes del cuerpo de la petición que se leen para el detalle
MAX_PAYLOAD_JSON = 8 * 1024       # tamaño máximo del payload guardado
MAX_STACK = 16 * 1024
MAX_MESSAGE = 4000
MAX_STR_VALUE = 500
MAX_PENDING = 500                 # huellas distintas en memoria por ventana (protección anti-tormenta)
FLUSH_INTERVAL = 5                # segundos entre escrituras agrupadas
VERSION_CACHE_TTL = 60

# ─── Contexto de la petición ─────────────────────────────────────────────────
# El middleware crea un dict mutable por petición; la autenticación le agrega la identidad
# (user_id / company_id efectivo). Al ser el mismo objeto, el middleware lo ve al terminar.
_request_ctx: ContextVar[Optional[dict]] = ContextVar("error_log_ctx", default=None)


def set_identity(**kw) -> None:
    """Llamado desde la autenticación (servidor) con la identidad ya validada."""
    ctx = _request_ctx.get()
    if ctx is not None:
        ctx.setdefault("identity", {}).update({k: v for k, v in kw.items() if v is not None})


# ─── Saneado ─────────────────────────────────────────────────────────────────
_SENSITIVE_SUBSTR = (
    "password", "passwd", "contrasena", "contraseña", "token", "secret", "authorization",
    "api_key", "apikey", "ext_db", "card_number", "numero_tarjeta", "private_key",
    "certificate", "certificado", "cookie", "session",
)
_SENSITIVE_TOKENS = {"pin", "cvv", "cvc", "otp", "pwd", "clave", "pass"}

_RE_CONN = re.compile(r"(\w+(?:\+\w+)?://)([^:/@\s]+):([^@\s]+)@")
_RE_JWT = re.compile(r"eyJ[\w-]{8,}\.[\w-]{8,}\.[\w-]{8,}")
_RE_BEARER = re.compile(r"(?i)bearer\s+[\w\-.~+/]+=*")
_RE_CARD = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
_RE_PWD_KV = re.compile(r"(?i)((?:password|passwd|pwd|contrase[ñn]a|clave)\s*[=:]\s*)(['\"]?)[^'\"\s,;)]+")


def _is_sensitive_key(key: str) -> bool:
    k = str(key).lower()
    if any(s in k for s in _SENSITIVE_SUBSTR):
        return True
    return any(t in _SENSITIVE_TOKENS for t in re.split(r"[^a-z0-9ñ]+", k) if t)


def scrub_text(value: Optional[str], limit: int = MAX_MESSAGE) -> Optional[str]:
    if value is None:
        return None
    s = str(value)
    s = _RE_CONN.sub(r"\1***:***@", s)
    s = _RE_JWT.sub("[JWT]", s)
    s = _RE_BEARER.sub("Bearer [REDACTED]", s)
    s = _RE_PWD_KV.sub(r"\1\2[REDACTED]", s)
    s = _RE_CARD.sub(lambda m: "[TARJETA]" if len(re.sub(r"\D", "", m.group())) >= 13 else m.group(), s)
    if len(s) > limit:
        s = s[:limit] + "…[truncado]"
    return s


def sanitize(obj: Any, depth: int = 0) -> Any:
    if depth > 6:
        return "[profundidad]"
    if isinstance(obj, dict):
        out = {}
        for i, (k, v) in enumerate(obj.items()):
            if i >= 80:
                out["_mas_campos"] = len(obj) - 80
                break
            out[str(k)[:100]] = "***" if _is_sensitive_key(k) else sanitize(v, depth + 1)
        return out
    if isinstance(obj, (list, tuple)):
        items = [sanitize(v, depth + 1) for v in list(obj)[:50]]
        if len(obj) > 50:
            items.append(f"…{len(obj) - 50} más")
        return items
    if isinstance(obj, str):
        return scrub_text(obj, MAX_STR_VALUE)
    if obj is None or isinstance(obj, (int, float, bool)):
        return obj
    return scrub_text(repr(obj), MAX_STR_VALUE)


def _limit_json(obj: Any) -> Any:
    if obj in (None, {}, []):
        return None
    try:
        raw = json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        return None
    if len(raw) <= MAX_PAYLOAD_JSON:
        return obj
    return {"_truncado": True, "vista_previa": raw[:MAX_PAYLOAD_JSON]}


def payload_from_body(body: bytes, content_type: str) -> Any:
    if not body:
        return None
    ct = (content_type or "").lower()
    try:
        if "application/json" in ct:
            return _limit_json(sanitize(json.loads(body.decode("utf-8", "replace"))))
        if "application/x-www-form-urlencoded" in ct:
            return _limit_json(sanitize(dict(parse_qsl(body.decode("utf-8", "replace")))))
        if "multipart/form-data" in ct:
            return {"_multipart": True, "bytes": len(body)}     # archivos: no se guardan
    except Exception:
        pass
    return {"_no_json": True, "bytes": len(body)}


# ─── Huella y clasificación ──────────────────────────────────────────────────
_RE_QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")
_RE_HEX = re.compile(r"\b[0-9a-f]{8,}\b|\b[0-9a-f]{8}-[0-9a-f-]{27,}\b", re.I)
_RE_NUM = re.compile(r"\d+")


def normalize_message(msg: str) -> str:
    s = (msg or "").strip()[:500]
    s = _RE_QUOTED.sub("'?'", s)
    s = _RE_HEX.sub("H", s)
    s = _RE_NUM.sub("N", s)
    return re.sub(r"\s+", " ", s)[:300]


def normalize_path(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    parts = []
    for seg in path.split("?")[0].split("/"):
        if seg.isdigit() or _RE_HEX.fullmatch(seg or "-"):
            parts.append("{id}")
        else:
            parts.append(seg[:60])
    return "/".join(parts)[:255]


def fingerprint(tipo: str, clase: str, endpoint: Optional[str], vista: Optional[str], message: str) -> str:
    raw = "|".join([tipo or "", clase or "", endpoint or "", vista or "", normalize_message(message)])
    return hashlib.sha1(raw.encode("utf-8", "replace")).hexdigest()


def ref_from_fp(fp: str) -> str:
    return "ERR-" + fp[:8].upper()


def _exc_chain(exc: BaseException):
    seen = set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        yield exc
        exc = exc.__cause__ or exc.__context__


def classify_exception(exc: Optional[BaseException], path: str) -> str:
    p = (path or "").lower()
    if exc is not None:
        for e in _exc_chain(exc):
            mod = type(e).__module__ or ""
            if mod.startswith(("sqlalchemy", "pymysql", "aiomysql", "asyncmy")):
                return "BASE_DATOS"
            if mod.startswith(("httpx", "requests", "aiohttp", "smtplib", "urllib3")):
                return "INTEGRACION"
    if "/sync" in p:
        return "SINCRONIZACION"
    if "impres" in p or "/print" in p:
        return "IMPRESION"
    if "apidian" in p:
        return "INTEGRACION"
    return "SERVIDOR"


def device_from_ua(ua: str) -> str:
    u = (ua or "").lower()
    if "ipad" in u or "tablet" in u or ("android" in u and "mobile" not in u):
        return "tablet"
    if "mobi" in u or "iphone" in u or "android" in u:
        return "movil"
    return "pc"


# ─── Versión del servidor (system_config.app_version) ───────────────────────
_version_cache = {"value": None, "at": 0.0}


async def _refresh_server_version() -> None:
    from app.database import AsyncSessionLocal
    try:
        async with AsyncSessionLocal() as db:
            v = (await db.execute(text(
                "SELECT config_value FROM system_config WHERE config_key='app_version' LIMIT 1"
            ))).scalar()
        _version_cache["value"] = (v or "").strip() or None
    except Exception:
        pass
    _version_cache["at"] = time.time()


async def warmup() -> None:
    """Startup: carga la versión del servidor para clasificar desde el primer error."""
    await _refresh_server_version()


def server_version() -> Optional[str]:
    """Versión en caché (se refresca en segundo plano cada 60 s)."""
    if time.time() - _version_cache["at"] > VERSION_CACHE_TTL:
        _version_cache["at"] = time.time()          # evita refrescos simultáneos
        _spawn(_refresh_server_version())
    return _version_cache["value"]


def is_stale_client(client_v: Optional[str], server_v: Optional[str]) -> bool:
    if not client_v or not server_v or client_v == server_v:
        return False
    # Formato YY.MM.DD·hash. Si el cliente es de una fecha POSTERIOR, el servidor aún no
    # actualizó app_version (ventana del deploy): no es un cliente desactualizado.
    c_date, s_date = client_v.split("·")[0], server_v.split("·")[0]
    return not (c_date > s_date)


# ─── Captura de datos de la petición ─────────────────────────────────────────
def _headers(scope) -> dict:
    out = {}
    for k, v in scope.get("headers") or []:
        try:
            out[k.decode("latin-1").lower()] = v.decode("latin-1")
        except Exception:
            pass
    return out


def _client_ip(scope, headers: dict) -> Optional[str]:
    ip = headers.get("x-forwarded-for") or (scope.get("client") or [None])[0] or ""
    return str(ip).split(",")[0].strip()[:64] or None


def _identity_from_token(headers: dict) -> dict:
    """Respaldo si la autenticación no alcanzó a correr: identidad del token firmado."""
    auth = headers.get("authorization") or ""
    if not auth.lower().startswith("bearer "):
        return {}
    try:
        from app.auth.jwt_handler import decode_access_token
        payload = decode_access_token(auth[7:].strip()) or {}
    except Exception:
        return {}
    if payload.get("type") == "waiter":
        return {"company_id": _int(payload.get("company_id")),
                "username": str(payload.get("waiter_name") or "")[:150] or None,
                "rol": "MESERO"}
    return {"user_id": _int(payload.get("user_id"))}


def _int(v) -> Optional[int]:
    try:
        return int(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _route_template(scope) -> Optional[str]:
    route = scope.get("route")
    path = getattr(route, "path", None)
    return path[:255] if path else normalize_path(scope.get("path"))


def build_request_info(scope, ctx: Optional[dict]) -> dict:
    headers = _headers(scope)
    ctx = ctx or {}
    ident = dict(ctx.get("identity") or {})
    if not ident:
        ident = _identity_from_token(headers)
    client_v = unquote(headers.get("x-app-build", ""))[:40] or None
    vista = unquote(headers.get("x-view", ""))[:500] or None
    qs = scope.get("query_string", b"").decode("latin-1", "replace")
    return {
        "identity": ident,
        "method": scope.get("method"),
        "path_real": (scope.get("path") or "")[:500],
        "endpoint": _route_template(scope),
        "query_params": _limit_json(sanitize(dict(parse_qsl(qs)))) if qs else None,
        "payload": payload_from_body(bytes(ctx.get("body") or b""), headers.get("content-type", "")),
        "vista_real": vista,
        "vista": normalize_path(vista),
        "id_caja": re.sub(r"[^\w\-]", "", headers.get("x-id-caja", ""))[:30] or None,
        "version_cliente": client_v,
        "user_agent": (headers.get("user-agent") or "")[:400] or None,
        "ip": _client_ip(scope, headers),
    }


# ─── Registro (en memoria) ───────────────────────────────────────────────────
_pending: dict[str, dict] = {}
_dropped = 0
_flusher_task: Optional[asyncio.Task] = None
_bg_tasks: set = set()


def _spawn(coro) -> None:
    try:
        t = asyncio.get_running_loop().create_task(coro)
        _bg_tasks.add(t)
        t.add_done_callback(_bg_tasks.discard)
    except RuntimeError:
        coro.close()


def record(*, tipo: str, nivel: str, titulo: str, clase: Optional[str], mensaje: Optional[str],
           stack: Optional[str], info: dict, http_status: Optional[int] = None,
           codigo_error: Optional[str] = None, componente: Optional[str] = None,
           toast_mostrado: bool = False, toast_mensaje: Optional[str] = None) -> Optional[str]:
    """Agrega una ocurrencia al buffer. Devuelve la referencia ERR-XXXXXXXX. Nunca lanza."""
    global _dropped
    try:
        server_v = server_version()
        client_v = info.get("version_cliente")
        real_tipo = tipo
        if tipo not in ("SEGURIDAD",) and is_stale_client(client_v, server_v):
            tipo, nivel = "VERSION_DESACTUALIZADA", "ADVERTENCIA"

        endpoint = info.get("endpoint")
        vista = info.get("vista")
        mensaje = scrub_text(mensaje) or ""
        fp = fingerprint(tipo + ":" + real_tipo, clase or "", endpoint, vista, mensaje)
        ref = ref_from_fp(fp)

        ident = info.get("identity") or {}
        company_id = _int(ident.get("company_id"))
        now = datetime.now()

        entry = _pending.get(fp)
        if entry is None:
            if len(_pending) >= MAX_PENDING:
                _dropped += 1
                return ref
            entry = _pending[fp] = {
                "count": 0, "companies": {}, "last_company_id": None, "last_seen": now,
                "group": {
                    "fingerprint": fp, "ref_code": ref, "tipo_error": tipo, "nivel": nivel,
                    "titulo": (scrub_text(titulo, 250) or "Error")[:255],
                    "clase_error": (clase or "")[:150] or None,
                    "endpoint": endpoint, "vista": vista,
                },
                "detail": {
                    "fecha_hora": now,
                    "company_id": company_id,
                    "user_id": _int(ident.get("user_id")),
                    "username": ident.get("username"),
                    "rol": ident.get("rol"),
                    "id_caja": info.get("id_caja"),
                    "http_method": info.get("method"),
                    "path_real": info.get("path_real"),
                    "http_status": http_status,
                    "codigo_error": (codigo_error or "")[:60] or None,
                    "mensaje": mensaje,
                    "stack_trace": scrub_text(stack, MAX_STACK),
                    "payload": info.get("payload"),
                    "query_params": info.get("query_params"),
                    "vista_real": info.get("vista_real"),
                    "componente": (componente or "")[:200] or None,
                    "toast_mostrado": bool(toast_mostrado),
                    "toast_mensaje": scrub_text(toast_mensaje, 500),
                    "version_cliente": client_v,
                    "version_servidor": server_v,
                    "dispositivo": device_from_ua(info.get("user_agent") or ""),
                    "user_agent": info.get("user_agent"),
                    "ip": info.get("ip"),
                },
            }
        entry["count"] += 1
        entry["last_seen"] = now
        if company_id:
            entry["companies"][company_id] = entry["companies"].get(company_id, 0) + 1
            entry["last_company_id"] = company_id
        _ensure_flusher()
        return ref
    except Exception:
        logger.exception("error_log.record falló")
        return None


def record_exception(exc: BaseException, scope, ctx: Optional[dict], *, unhandled: bool,
                     http_status: int = 500, tipo: Optional[str] = None,
                     nivel: Optional[str] = None) -> Optional[str]:
    """Error del backend. Si es un HTTPException lanzado dentro de un except, se usa la
    excepción original (__cause__/__context__) para clase, mensaje y traza."""
    try:
        info = build_request_info(scope, ctx)
        orig = exc
        if not unhandled:
            orig = exc.__cause__ or exc.__context__ or exc
        clase = type(orig).__name__
        if unhandled or orig is not exc:
            mensaje = str(orig) or clase
        else:
            mensaje = str(getattr(exc, "detail", "") or exc) or clase
        stack = "".join(traceback.format_exception(type(orig), orig, orig.__traceback__))
        t = tipo or classify_exception(orig, info.get("path_real") or "")
        n = nivel or ("CRITICO" if unhandled or t == "BASE_DATOS" else "ERROR")
        titulo = f"{clase}: {mensaje.splitlines()[0] if mensaje else ''}"
        return record(tipo=t, nivel=n, titulo=titulo, clase=clase, mensaje=mensaje, stack=stack,
                      info=info, http_status=http_status)
    except Exception:
        logger.exception("error_log.record_exception falló")
        return None


def record_security(motivo: str, extra: Optional[dict] = None, http_status: int = 403) -> Optional[str]:
    """Evento de seguridad dentro de una petición (acceso a otra empresa, ids ajenos, etc.)."""
    ctx = _request_ctx.get()
    scope = (ctx or {}).get("scope")
    if not scope:
        return None
    info = build_request_info(scope, ctx)
    return record(tipo="SEGURIDAD", nivel="ADVERTENCIA", titulo=motivo, clase="SecurityEvent",
                  mensaje=f"{motivo} {json.dumps(sanitize(extra or {}), ensure_ascii=False, default=str)}",
                  stack=None, info=info, http_status=http_status)


def log_error(exc: BaseException, *, tipo: Optional[str] = None, nivel: Optional[str] = None,
              contexto: Optional[dict] = None) -> Optional[str]:
    """Helper para los `except` de routers/servicios (sync, impresión, integraciones):
        except Exception as e:
            ref = log_error(e, tipo="IMPRESION", contexto={"pedido": nro})
    Usa la petición en curso si existe. Nunca lanza."""
    try:
        ctx = _request_ctx.get()
        scope = (ctx or {}).get("scope") or {"type": "http", "path": "", "headers": []}
        info = build_request_info(scope, ctx)
        if contexto:
            info["payload"] = _limit_json({"contexto": sanitize(contexto), "peticion": info.get("payload")})
        clase = type(exc).__name__
        mensaje = str(exc) or clase
        stack = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        t = tipo or classify_exception(exc, info.get("path_real") or "")
        ref = record(tipo=t, nivel=nivel or ("CRITICO" if t == "BASE_DATOS" else "ERROR"),
                     titulo=f"{clase}: {mensaje.splitlines()[0]}", clase=clase, mensaje=mensaje,
                     stack=stack, info=info)
        if ctx is not None and ref:
            ctx["logged_ref"] = ref
        return ref
    except Exception:
        logger.exception("error_log.log_error falló")
        return None


# ─── Escritura agrupada en BD ────────────────────────────────────────────────
def _ensure_flusher() -> None:
    global _flusher_task
    if _flusher_task is None or _flusher_task.done():
        try:
            _flusher_task = asyncio.get_running_loop().create_task(_flusher_loop())
        except RuntimeError:
            pass


async def _flusher_loop() -> None:
    while True:
        await asyncio.sleep(FLUSH_INTERVAL)
        if not _pending:
            return                        # se vuelve a crear con el siguiente error
        await flush()


async def flush() -> None:
    global _pending, _dropped
    batch, _pending = _pending, {}
    dropped, _dropped = _dropped, 0
    if dropped:
        logger.warning("error_log: %s eventos descartados por tope de memoria", dropped)
    if not batch:
        return
    from app.database import AsyncSessionLocal
    for fp, entry in batch.items():
        try:
            async with AsyncSessionLocal() as db:
                await _write_entry(db, entry)
                await db.commit()
        except Exception as e:
            try:
                _fallback_logger().error(json.dumps(
                    {"error_guardando": str(e)[:300], "entry": entry}, ensure_ascii=False, default=str))
            except Exception:
                pass


async def _identity_details(db, d: dict) -> None:
    """Completa username, rol, empresa y perfil desde la BD (fuente confiable)."""
    if d.get("user_id"):
        row = (await db.execute(text("""
            SELECT u.nombre, u.email, u.company_id, r.name AS rol
            FROM users u LEFT JOIN roles r ON r.id = u.role_id
            WHERE u.id = :id
        """), {"id": d["user_id"]})).mappings().first()
        if row:
            d["username"] = d.get("username") or (row["nombre"] or row["email"] or "")[:150]
            d["rol"] = d.get("rol") or (row["rol"] or "")[:100] or None
            d["company_id"] = d.get("company_id") or row["company_id"]
    if d.get("company_id"):
        d["business_profile_id"] = (await db.execute(text(
            "SELECT business_profile_id FROM companies WHERE id_company = :c"
        ), {"c": d["company_id"]})).scalar()


async def _write_entry(db, entry: dict) -> None:
    g, d = entry["group"], dict(entry["detail"])
    count, now = entry["count"], entry["last_seen"]
    await _identity_details(db, d)

    # La empresa resuelta del usuario también cuenta como afectada
    companies = dict(entry["companies"])
    if d.get("company_id") and not companies:
        companies[d["company_id"]] = count
    last_company = entry["last_company_id"] or d.get("company_id")

    row = (await db.execute(text(
        "SELECT id, estado FROM system_error_groups WHERE fingerprint = :fp FOR UPDATE"
    ), {"fp": g["fingerprint"]})).mappings().first()

    save_detail, regresion = False, False
    if row is None:
        modulo = None
        if g.get("vista"):
            modulo = (await db.execute(text(
                "SELECT name FROM system_modules WHERE route = :r LIMIT 1"), {"r": g["vista"]})).scalar()
        try:
            res = await db.execute(text("""
                INSERT INTO system_error_groups
                  (fingerprint, ref_code, tipo_error, nivel, titulo, clase_error, endpoint, vista, modulo,
                   first_seen, first_company_id, first_user_id, last_seen, last_company_id,
                   total_ocurrencias, total_empresas, estado, regresiones)
                VALUES
                  (:fingerprint, :ref_code, :tipo_error, :nivel, :titulo, :clase_error, :endpoint, :vista, :modulo,
                   :first_seen, :first_company_id, :first_user_id, :last_seen, :last_company_id,
                   :count, 0, 'NUEVO', 0)
            """), {**g, "modulo": modulo, "first_seen": d["fecha_hora"],
                   "first_company_id": d.get("company_id"), "first_user_id": d.get("user_id"),
                   "last_seen": now, "last_company_id": last_company, "count": count})
            group_id = res.lastrowid
            save_detail = True
        except Exception:
            # Otro worker lo insertó al mismo tiempo: se trata como existente
            await db.rollback()
            row = (await db.execute(text(
                "SELECT id, estado FROM system_error_groups WHERE fingerprint = :fp FOR UPDATE"
            ), {"fp": g["fingerprint"]})).mappings().first()
            if row is None:
                raise
    if row is not None:
        group_id = row["id"]
        await db.execute(text("""
            UPDATE system_error_groups
               SET total_ocurrencias = total_ocurrencias + :n, last_seen = :now,
                   last_company_id = COALESCE(:lc, last_company_id)
             WHERE id = :id
        """), {"n": count, "now": now, "lc": last_company, "id": group_id})
        if row["estado"] == "RESUELTO":
            res = await db.execute(text("""
                UPDATE system_error_groups
                   SET estado = 'NUEVO', regresiones = regresiones + 1
                 WHERE id = :id AND estado = 'RESUELTO'
            """), {"id": group_id})
            if res.rowcount:
                save_detail, regresion = True, True

    for cid, n in companies.items():
        res = await db.execute(text("""
            INSERT IGNORE INTO system_error_companies (group_id, company_id, ocurrencias, first_seen, last_seen)
            VALUES (:g, :c, :n, :now, :now)
        """), {"g": group_id, "c": cid, "n": n, "now": now})
        if res.rowcount:
            await db.execute(text(
                "UPDATE system_error_groups SET total_empresas = total_empresas + 1 WHERE id = :id"
            ), {"id": group_id})
        else:
            await db.execute(text("""
                UPDATE system_error_companies SET ocurrencias = ocurrencias + :n, last_seen = :now
                 WHERE group_id = :g AND company_id = :c
            """), {"n": n, "now": now, "g": group_id, "c": cid})

    if save_detail:
        await db.execute(text("""
            INSERT INTO system_error_details
              (group_id, es_regresion, fecha_hora, company_id, business_profile_id, user_id, username, rol,
               id_caja, http_method, path_real, http_status, codigo_error, mensaje, stack_trace, payload,
               query_params, vista_real, componente, toast_mostrado, toast_mensaje, version_cliente,
               version_servidor, dispositivo, user_agent, ip)
            VALUES
              (:group_id, :es_regresion, :fecha_hora, :company_id, :business_profile_id, :user_id, :username, :rol,
               :id_caja, :http_method, :path_real, :http_status, :codigo_error, :mensaje, :stack_trace, :payload,
               :query_params, :vista_real, :componente, :toast_mostrado, :toast_mensaje, :version_cliente,
               :version_servidor, :dispositivo, :user_agent, :ip)
        """), {**d, "group_id": group_id, "es_regresion": regresion,
               "business_profile_id": d.get("business_profile_id"),
               "payload": json.dumps(d["payload"], ensure_ascii=False, default=str) if d.get("payload") else None,
               "query_params": json.dumps(d["query_params"], ensure_ascii=False, default=str) if d.get("query_params") else None})


# ─── Middleware ASGI ─────────────────────────────────────────────────────────
class ErrorLogMiddleware:
    """Captura errores no controlados (500), respuestas 5xx y 429 (exceso de peticiones).
    Al cliente nunca se le devuelve la traza: solo un mensaje y la referencia ERR-XXXXXXXX."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)

        ctx = {"scope": scope, "body": bytearray(), "status": None}
        token = _request_ctx.set(ctx)
        started = False

        # Cuerpos JSON/form pequeños se leen de antemano (y se re-entregan intactos) para tener
        # el payload aunque el endpoint falle antes de leerlo. Archivos y cuerpos grandes: no.
        replay: list = []
        hdrs = _headers(scope)
        ct = hdrs.get("content-type", "").lower()
        try:
            clen = int(hdrs.get("content-length") or -1)
        except ValueError:
            clen = -1
        if scope.get("method") in ("POST", "PUT", "PATCH", "DELETE") and 0 < clen <= MAX_BODY_CAPTURE \
                and ("application/json" in ct or "application/x-www-form-urlencoded" in ct):
            more = True
            while more:
                msg = await receive()
                replay.append(msg)
                if msg.get("type") != "http.request":
                    break
                ctx["body"] += (msg.get("body") or b"")[:MAX_BODY_CAPTURE - len(ctx["body"])]
                more = msg.get("more_body", False)

        async def receive_wrapper():
            if replay:
                return replay.pop(0)
            msg = await receive()
            if msg.get("type") == "http.request":
                room = MAX_BODY_CAPTURE - len(ctx["body"])
                if room > 0:
                    ctx["body"] += (msg.get("body") or b"")[:room]
            return msg

        async def send_wrapper(msg):
            nonlocal started
            if msg.get("type") == "http.response.start":
                started = True
                ctx["status"] = msg.get("status")
                ref = ctx.get("error_ref")
                if ref and (ctx["status"] or 0) >= 500:
                    msg = dict(msg)
                    msg["headers"] = list(msg.get("headers") or []) + [(b"x-error-ref", ref.encode())]
            await send(msg)

        try:
            await self.app(scope, receive_wrapper, send_wrapper)
        except Exception as exc:
            ref = record_exception(exc, scope, ctx, unhandled=True)
            logger.exception("Error no controlado %s %s (ref %s)", scope.get("method"), scope.get("path"), ref)
            if started:
                raise
            body = json.dumps({"detail": f"Error interno del servidor. Ref: {ref or '-'}",
                               "error_ref": ref}).encode()
            headers = [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]
            if ref:
                headers.append((b"x-error-ref", ref.encode()))
            await send({"type": "http.response.start", "status": 500, "headers": headers})
            await send({"type": "http.response.body", "body": body})
        else:
            status = ctx.get("status") or 0
            try:
                if status >= 500 and not ctx.get("error_ref") and not ctx.get("logged_ref"):
                    # 5xx devuelto sin excepción (JSONResponse manual, etc.)
                    info = build_request_info(scope, ctx)
                    record(tipo=classify_exception(None, scope.get("path") or ""), nivel="ERROR",
                           titulo=f"Respuesta {status} en {info.get('endpoint')}", clase=f"HTTP{status}",
                           mensaje=f"Respuesta {status}", stack=None, info=info, http_status=status)
                elif status == 429:
                    info = build_request_info(scope, ctx)
                    record(tipo="SEGURIDAD", nivel="ADVERTENCIA",
                           titulo=f"Exceso de peticiones en {info.get('endpoint')}", clase="RateLimit",
                           mensaje="Demasiadas solicitudes (posible bot)", stack=None, info=info,
                           http_status=429)
            except Exception:
                logger.exception("ErrorLogMiddleware post-proceso falló")
        finally:
            _request_ctx.reset(token)


def mark_http_exception(scope, exc) -> Optional[str]:
    """Llamado por el manejador de HTTPException (status >= 500) ANTES de responder,
    para que la respuesta lleve la referencia."""
    ctx = _request_ctx.get()
    if ctx is not None and ctx.get("logged_ref"):
        ctx["error_ref"] = ctx["logged_ref"]
        return ctx["logged_ref"]
    ref = record_exception(exc, scope, ctx, unhandled=False, http_status=exc.status_code)
    if ctx is not None:
        ctx["error_ref"] = ref
    return ref
