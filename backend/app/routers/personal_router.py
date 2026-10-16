"""
Meseros y Empleados (pantalla /configuration/meseros).

Escritorio → web:  empleados → pos_employees · meseros → pos_waiters · tipo_empleado → pos_employee_types
Un registro de la web se guarda en AMBAS tablas con el mismo código (cod_empleado = id).

  · Empresas con escritorio (Agente Local activo): los administra el escritorio y se suben solos;
    en la web solo se consultan.
  · Empresas solo web: se crean aquí. "Agregarme como mesero" crea al usuario logueado (user_id).
  · La clave/PIN se guarda tal cual porque el escritorio la lee así; nunca se devuelve en las consultas.
"""
import re
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, StringConstraints, field_validator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.tenant import tenant_guard
from app.database import get_db
from app.models.role_model import Role
from app.models.user_model import User

router = APIRouter(prefix="/api/personal", tags=["Meseros y Empleados"], dependencies=[Depends(tenant_guard)])

RUTA = "/configuration/meseros"
ID_PROVISIONAL = 900_000_000
# Tipos con que arranca una empresa sin escritorio (los mismos del escritorio)
TIPOS_BASE = ((0, "DOMICILIARIO"), (2, "ASESORES"), (5, "ADMINISTRATIVO"))

Txt50 = Annotated[str, StringConstraints(strip_whitespace=True, max_length=50)]
_PIN = re.compile(r"^\d{4,8}$")
_LOGIN = re.compile(r"^[A-Za-z0-9._@-]{2,25}$")


class PersonaIn(BaseModel):
    name:          Optional[Txt50] = None
    phone:         Optional[Txt50] = None
    address:       Optional[Txt50] = None
    login:         Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=25)]] = None
    pin:           Optional[str] = None
    employee_type: Optional[Annotated[int, Field(ge=0, le=999)]] = None
    status:        Optional[Annotated[int, Field(ge=0, le=1)]] = None
    role_id:       Optional[Annotated[int, Field(ge=1)]] = None

    @field_validator("pin")
    @classmethod
    def _pin(cls, v):
        if v is not None and not _PIN.match(v):
            raise ValueError("La clave debe tener de 4 a 8 números")
        return v

    @field_validator("login")
    @classmethod
    def _login(cls, v):
        if v and not _LOGIN.match(v):
            raise ValueError("El usuario solo admite letras, números y . _ @ -")
        return v


class AgregarmeIn(BaseModel):
    phone:         Txt50
    pin:           str
    employee_type: Annotated[int, Field(ge=0, le=999)]

    @field_validator("pin")
    @classmethod
    def _pin(cls, v):
        if not _PIN.match(v):
            raise ValueError("La clave debe tener de 4 a 8 números")
        return v


# ───────────────────────────── utilidades ─────────────────────────────

async def _con_escritorio(db: AsyncSession, cid: int) -> bool:
    from app.services import sede_pedidos
    return await sede_pedidos.tiene_sede(db, cid)


async def _permiso(db: AsyncSession, user: User, escribir: bool) -> None:
    """Admin / sistema: todo. Otros roles: según su permiso en esta pantalla (Roles → Control de Acceso)."""
    role = await db.get(Role, user.role_id) if user.role_id else None
    if not role:
        raise HTTPException(status_code=403, detail="Usuario sin rol")
    if role.is_system or "ADMIN" in (role.name or "").upper():
        return
    p = (await db.execute(text("""
        SELECT MAX(rm.can_view), MAX(rm.can_create), MAX(rm.can_edit) FROM role_modules rm
        JOIN system_modules sm ON sm.id = rm.module_id AND sm.route = :ruta
        WHERE rm.role_id = :r
    """), {"r": role.id, "ruta": RUTA})).first()
    if not p or not p[0]:
        raise HTTPException(status_code=403, detail="Su rol no tiene acceso a Meseros y Empleados")
    if escribir and not (p[1] or p[2]):
        raise HTTPException(status_code=403, detail="Su rol solo puede consultar Meseros y Empleados")


async def _solo_web(db: AsyncSession, cid: int) -> None:
    if await _con_escritorio(db, cid):
        raise HTTPException(status_code=409, detail="Esta empresa trabaja con escritorio: los meseros y empleados "
                                                    "se crean allí y se suben solos a la web")


async def tipos(db: AsyncSession, cid: int) -> list[dict]:
    filas = (await db.execute(text(
        "SELECT cod_tipo, name, porcentaje FROM pos_employee_types WHERE company_id = :c ORDER BY name"
    ), {"c": cid})).mappings().all()
    if not filas and not await _con_escritorio(db, cid):
        for cod, nombre in TIPOS_BASE:
            await db.execute(text(
                "INSERT IGNORE INTO pos_employee_types (company_id, cod_tipo, name, porcentaje) VALUES (:c, :t, :n, 0)"
            ), {"c": cid, "t": cod, "n": nombre})
        await db.commit()
        return await tipos(db, cid)
    return [{"cod_tipo": int(f["cod_tipo"]), "name": f["name"], "porcentaje": float(f["porcentaje"] or 0)} for f in filas]


async def _validar_tipo(db: AsyncSession, cid: int, tipo: Optional[int]) -> int:
    if tipo is None:
        raise HTTPException(status_code=400, detail="El tipo de empleado es obligatorio")
    if not (await db.execute(text("SELECT 1 FROM pos_employee_types WHERE company_id = :c AND cod_tipo = :t"),
                             {"c": cid, "t": tipo})).scalar():
        raise HTTPException(status_code=400, detail="Tipo de empleado no válido para esta empresa")
    return tipo


async def _validar_rol(db: AsyncSession, cid: int, role_id: Optional[int]) -> Optional[int]:
    if not role_id:
        return None
    if not (await db.execute(text("SELECT 1 FROM roles WHERE id = :r AND company_id = :c"),
                             {"r": role_id, "c": cid})).scalar():
        raise HTTPException(status_code=400, detail="Rol no válido para esta empresa")
    return role_id


async def _rol_mesero(db: AsyncSession, cid: int) -> Optional[int]:
    return (await db.execute(text(
        "SELECT id FROM roles WHERE company_id = :c AND UPPER(name) = 'VENDEDOR-MESERO' ORDER BY id LIMIT 1"
    ), {"c": cid})).scalar()


async def _login_libre(db: AsyncSession, cid: int, login: str, excepto: int = 0) -> None:
    if (await db.execute(text(
        "SELECT 1 FROM pos_employees WHERE company_id = :c AND UPPER(login) = UPPER(:l) AND id <> :e LIMIT 1"
    ), {"c": cid, "l": login, "e": excepto})).scalar():
        raise HTTPException(status_code=409, detail="Ese usuario de ingreso ya lo tiene otro empleado")


async def _login_auto(db: AsyncSession, cid: int, nombre: str, cod: int) -> str:
    base = re.sub(r"[^A-Za-z0-9]", "", (nombre.split() or ["EMPLEADO"])[0].upper())[:18] or "EMPLEADO"
    for candidato in (base, f"{base}{cod}"[:25]):
        if not (await db.execute(text(
            "SELECT 1 FROM pos_employees WHERE company_id = :c AND UPPER(login) = :l LIMIT 1"
        ), {"c": cid, "l": candidato})).scalar():
            return candidato
    return f"E{cod}"[:25]


async def _cupo(db: AsyncSession, cid: int) -> None:
    from app.services.plan_limits_service import get_limits
    maximo = (await get_limits(cid, db)).get("max_waiters", -1)
    if maximo is None or maximo == -1:
        return
    usados = (await db.execute(text(
        "SELECT COUNT(*) FROM pos_waiters WHERE company_id = :c AND plan_blocked = 0"), {"c": cid})).scalar() or 0
    if usados >= maximo:
        raise HTTPException(status_code=409, detail="Se alcanzó el límite de meseros de su plan")


async def _siguiente_codigo(db: AsyncSession, cid: int) -> int:
    """Siguiente código libre entre empleados y meseros (FOR UPDATE: sin repetidos en concurrencia)."""
    a = (await db.execute(text(
        "SELECT COALESCE(MAX(id), 0) FROM pos_waiters WHERE company_id = :c AND id < :p FOR UPDATE"
    ), {"c": cid, "p": ID_PROVISIONAL})).scalar() or 0
    b = (await db.execute(text(
        "SELECT COALESCE(MAX(id), 0) FROM pos_employees WHERE company_id = :c AND id < :p FOR UPDATE"
    ), {"c": cid, "p": ID_PROVISIONAL})).scalar() or 0
    return int(max(a, b)) + 1


async def _guardar(db: AsyncSession, cid: int, cod: int, d: dict) -> None:
    """Deja el registro en las dos tablas (crea la que falte)."""
    p = {"id": cod, "c": cid, **d}
    await db.execute(text("""
        INSERT INTO pos_employees (id, company_id, name, phone, address, login, password, status, employee_type,
                                   personal_skin, synced, user_id)
        VALUES (:id, :c, :name, :phone, :address, :login, :pin, :status, :employee_type, 0, 0, :user_id)
        ON DUPLICATE KEY UPDATE name = VALUES(name), phone = VALUES(phone), address = VALUES(address),
            login = VALUES(login), password = VALUES(password), status = VALUES(status),
            employee_type = VALUES(employee_type), user_id = COALESCE(VALUES(user_id), user_id), synced = 0
    """), p)
    await db.execute(text("""
        INSERT INTO pos_waiters (id, company_id, name, phone, address, password, status, employee_type,
                                 synced, role_id, user_id, updated_at)
        VALUES (:id, :c, :name, :phone, :address, :pin, :status, :employee_type, 0, :role_id, :user_id, NOW())
        ON DUPLICATE KEY UPDATE name = VALUES(name), phone = VALUES(phone), address = VALUES(address),
            password = VALUES(password), status = VALUES(status), employee_type = VALUES(employee_type),
            role_id = VALUES(role_id), user_id = COALESCE(VALUES(user_id), user_id), synced = 0, updated_at = NOW()
    """), p)


_LISTA = """
    SELECT ids.id,
           COALESCE(w.name, e.name)                 AS name,
           COALESCE(w.phone, e.phone)               AS phone,
           COALESCE(w.address, e.address)           AS address,
           e.login,
           COALESCE(e.status, w.status, 0)          AS status,
           COALESCE(e.employee_type, w.employee_type, 0) AS employee_type,
           t.name                                   AS tipo,
           w.role_id, r.name                        AS rol,
           COALESCE(w.user_id, e.user_id)           AS user_id,
           w.id IS NOT NULL                         AS es_mesero,
           e.id IS NOT NULL                         AS es_empleado,
           GREATEST(COALESCE(w.updated_at, '1970-01-01'), COALESCE(e.updated_at, '1970-01-01')) AS updated_at
    FROM (SELECT id FROM pos_waiters WHERE company_id = :c
          UNION SELECT id FROM pos_employees WHERE company_id = :c) ids
    LEFT JOIN pos_waiters w   ON w.company_id = :c AND w.id = ids.id
    LEFT JOIN pos_employees e ON e.company_id = :c AND e.id = ids.id
    LEFT JOIN pos_employee_types t ON t.company_id = :c AND t.cod_tipo = COALESCE(e.employee_type, w.employee_type)
    LEFT JOIN roles r ON r.id = w.role_id AND r.company_id = :c
"""


def _fila(f) -> dict:
    d = dict(f)
    d["es_mesero"], d["es_empleado"] = bool(d["es_mesero"]), bool(d["es_empleado"])
    d["updated_at"] = d["updated_at"].isoformat() if hasattr(d["updated_at"], "isoformat") else None
    return d


async def _uno(db: AsyncSession, cid: int, cod: int) -> dict:
    f = (await db.execute(text(_LISTA + " WHERE ids.id = :id"), {"c": cid, "id": cod})).mappings().first()
    if not f:
        raise HTTPException(status_code=404, detail="Mesero / empleado no encontrado")
    return _fila(f)


async def crear_persona(db: AsyncSession, cid: int, d: PersonaIn, user_id: Optional[int] = None) -> dict:
    """Crea el registro en empleados y meseros (empresas solo web). Usada también por el Dashboard."""
    await _solo_web(db, cid)
    if not d.name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")
    if not d.phone:
        raise HTTPException(status_code=400, detail="El teléfono es obligatorio")
    if not d.pin:
        raise HTTPException(status_code=400, detail="La clave (PIN) es obligatoria")
    tipo = await _validar_tipo(db, cid, d.employee_type)
    rol = await _validar_rol(db, cid, d.role_id) or await _rol_mesero(db, cid)
    if (await db.execute(text(
        "SELECT 1 FROM pos_waiters WHERE company_id = :c AND UPPER(name) = UPPER(:n) AND status = 1 LIMIT 1"
    ), {"c": cid, "n": d.name})).scalar():
        raise HTTPException(status_code=409, detail="Ya existe un mesero activo con ese nombre")
    await _cupo(db, cid)
    cod = await _siguiente_codigo(db, cid)
    login = d.login or await _login_auto(db, cid, d.name, cod)
    await _login_libre(db, cid, login)
    await _guardar(db, cid, cod, {"name": d.name, "phone": d.phone, "address": d.address or None, "login": login,
                                  "pin": d.pin, "status": 1 if d.status is None else d.status,
                                  "employee_type": tipo, "role_id": rol, "user_id": user_id})
    await db.commit()
    return await _uno(db, cid, cod)


# ───────────────────────────── rutas ─────────────────────────────

@router.get("/")
async def listar(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await _permiso(db, user, False)
    cid = user.company_id
    filas = (await db.execute(text(_LISTA + " ORDER BY name"), {"c": cid})).mappings().all()
    return {"con_escritorio": await _con_escritorio(db, cid), "items": [_fila(f) for f in filas]}


@router.get("/tipos")
async def listar_tipos(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await tipos(db, user.company_id)


@router.get("/yo")
async def mi_registro(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """Registro de mesero/empleado ligado al usuario logueado (o null) y si la empresa trabaja con escritorio."""
    cid = user.company_id
    cod = (await db.execute(text("""
        SELECT id FROM pos_waiters WHERE company_id = :c AND user_id = :u
        UNION SELECT id FROM pos_employees WHERE company_id = :c AND user_id = :u
        LIMIT 1
    """), {"c": cid, "u": user.id})).scalar()
    return {"registro": await _uno(db, cid, int(cod)) if cod else None,
            "con_escritorio": await _con_escritorio(db, cid),
            "nombre": (user.nombre or "").strip()[:50], "email": user.email}


@router.post("/", status_code=201)
async def crear(data: PersonaIn, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await _permiso(db, user, True)
    return await crear_persona(db, user.company_id, data)


@router.put("/{cod}")
async def editar(cod: int, data: PersonaIn, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await _permiso(db, user, True)
    cid = user.company_id
    await _solo_web(db, cid)
    actual = await _uno(db, cid, cod)
    sent = data.model_fields_set
    nombre = data.name if "name" in sent else actual["name"]
    telefono = data.phone if "phone" in sent else actual["phone"]
    if not nombre:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")
    if not telefono:
        raise HTTPException(status_code=400, detail="El teléfono es obligatorio")
    tipo = await _validar_tipo(db, cid, data.employee_type if "employee_type" in sent else actual["employee_type"])
    rol = await _validar_rol(db, cid, data.role_id) if "role_id" in sent else actual["role_id"]
    login = (data.login if "login" in sent and data.login else actual["login"]) or await _login_auto(db, cid, nombre, cod)
    await _login_libre(db, cid, login, excepto=cod)
    pin = data.pin
    if not pin:      # se conserva la clave actual (nunca sale de la base de datos)
        pin = (await db.execute(text(
            "SELECT COALESCE((SELECT password FROM pos_employees WHERE company_id = :c AND id = :id),"
            "                (SELECT password FROM pos_waiters WHERE company_id = :c AND id = :id))"
        ), {"c": cid, "id": cod})).scalar()
        if not pin:
            raise HTTPException(status_code=400, detail="La clave (PIN) es obligatoria")
    await _guardar(db, cid, cod, {"name": nombre, "phone": telefono,
                                  "address": (data.address if "address" in sent else actual["address"]) or None,
                                  "login": login, "pin": pin,
                                  "status": data.status if "status" in sent and data.status is not None else actual["status"],
                                  "employee_type": tipo, "role_id": rol, "user_id": None})
    await db.commit()
    return await _uno(db, cid, cod)


@router.post("/agregarme", status_code=201)
async def agregarme(data: AgregarmeIn, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """El usuario logueado queda como mesero y empleado (ligado por user_id)."""
    cid = user.company_id
    ya = (await db.execute(text(
        "SELECT id FROM pos_waiters WHERE company_id = :c AND user_id = :u LIMIT 1"), {"c": cid, "u": user.id})).scalar()
    if ya:
        raise HTTPException(status_code=409, detail="Usted ya está registrado como mesero")
    nombre = (user.nombre or "").strip()[:50] or f"Usuario {user.id}"
    login = re.sub(r"[^A-Za-z0-9._@-]", "", (user.email or "").split("@")[0])[:25] or None
    if login and (await db.execute(text(
        "SELECT 1 FROM pos_employees WHERE company_id = :c AND UPPER(login) = UPPER(:l) LIMIT 1"
    ), {"c": cid, "l": login})).scalar():
        login = None      # se genera uno libre
    return await crear_persona(db, cid, PersonaIn(name=nombre, phone=data.phone, pin=data.pin, login=login,
                                                  employee_type=data.employee_type), user_id=user.id)
