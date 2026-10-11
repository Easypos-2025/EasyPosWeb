"""
Configuración Sede (vista /configuration/sede): datos generales de la empresa. La maneja su admin.

  GET /api/config-sede              empresa (lectura + editables), sede (documentos) y escritorio
  PUT /api/config-sede/empresa      dirección, teléfono y correo de la empresa (ADMIN / SYSADMIN)
  PUT /api/config-sede/sede         datos de la sede: espejo de configuracion_sede del escritorio
  PUT /api/config-sede/escritorio   enviar los pedidos web al escritorio (empresas con Agente Local)

Nombre, NIT, perfil y estado de la empresa son solo lectura aquí: los cambia SYSADMIN en Empresas
(el NIT define a qué empresas accede un ADMIN). La empresa sale de la sesión (topbar validada por
tenant); nunca se toma un company_id del navegador.
"""
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, StringConstraints
from typing_extensions import Annotated
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.tenant import tenant_guard
from app.database import get_db
from app.models.role_model import Role
from app.models.user_model import User

router = APIRouter(prefix="/api/config-sede", tags=["Configuración Sede"], dependencies=[Depends(tenant_guard)])

MINUTOS_EN_LINEA = 3
_RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CAMPOS_SEDE = ("Nombre_Almacen", "Nombre_Autorizado", "Nit_Autorizado", "Razon_Social", "Direccion_Sede",
               "Mail_Uno", "Mail_Dos", "Nombre_Logo_Empresa")


def _s(n: int):
    return Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=n)]]


async def _es_admin(db: AsyncSession, user: User) -> bool:
    role = await db.get(Role, user.role_id) if user.role_id else None
    return bool(role and (role.is_system or "ADMIN" in (role.name or "").upper()))


async def _exigir_admin(db: AsyncSession, user: User) -> None:
    if not await _es_admin(db, user):
        raise HTTPException(status_code=403, detail="Solo el administrador de la empresa puede modificar la configuración de la sede")


def _quien(user: User) -> str:
    return (user.nombre or user.email or f"usuario {user.id}")[:150]


async def _empresa(db: AsyncSession, cid: int) -> dict:
    fila = (await db.execute(text("""
        SELECT c.name, c.identification_number, c.dv, c.state, c.address, c.phone, c.email, bp.name AS perfil
        FROM companies c LEFT JOIN business_profiles bp ON bp.id = c.business_profile_id
        WHERE c.id_company = :cid
    """), {"cid": cid})).mappings().first()
    if not fila:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    nit = str(fila["identification_number"] or "")
    return {"nombre": fila["name"], "nit": f"{nit}-{fila['dv']}" if nit and fila["dv"] is not None else nit,
            "perfil": fila["perfil"], "activa": int(fila["state"] or 0) == 1,
            "direccion": fila["address"] or "", "telefono": fila["phone"] or "", "correo": fila["email"] or ""}


async def _sede(db: AsyncSession, cid: int, empresa: dict) -> dict:
    """Datos de la sede; la primera vez se crea con los datos de la empresa."""
    fila = (await db.execute(text(
        f"SELECT Id_Sede, {', '.join(CAMPOS_SEDE)}, actualizado_por, updated_at FROM configuracion_sede WHERE company_id = :cid"
    ), {"cid": cid})).mappings().first()
    if not fila:
        await db.execute(text("""
            INSERT IGNORE INTO configuracion_sede (company_id, Nombre_Almacen, Nit_Autorizado, Direccion_Sede, Mail_Uno)
            VALUES (:cid, :n, :nit, :dir, :mail)
        """), {"cid": cid, "n": (empresa["nombre"] or "")[:250], "nit": empresa["nit"][:250],
               "dir": empresa["direccion"][:255], "mail": empresa["correo"][:100]})
        await db.commit()
        fila = (await db.execute(text(
            f"SELECT Id_Sede, {', '.join(CAMPOS_SEDE)}, actualizado_por, updated_at FROM configuracion_sede WHERE company_id = :cid"
        ), {"cid": cid})).mappings().first()
    datos = {k: fila[k] or "" for k in CAMPOS_SEDE}
    datos.update({"Id_Sede": fila["Id_Sede"], "actualizado_por": fila["actualizado_por"],
                  "actualizado_en": fila["updated_at"].isoformat(timespec="minutes") if fila["updated_at"] else None})
    return datos


async def _escritorio(db: AsyncSession, cid: int) -> dict:
    agente = (await db.execute(text("""
        SELECT codigo, version, ultimo_contacto, activo,
               ultimo_contacto >= NOW() - INTERVAL :m MINUTE AS en_linea
        FROM company_local_agents WHERE company_id = :cid LIMIT 1
    """), {"cid": cid, "m": MINUTOS_EN_LINEA})).mappings().first()
    cfg = (await db.execute(text("""
        SELECT pedidos_web_escritorio, pedidos_web_escritorio_por, pedidos_web_escritorio_en
        FROM company_configs WHERE company_id = :cid LIMIT 1
    """), {"cid": cid})).mappings().first()
    return {
        "tiene_agente": bool(agente and int(agente["activo"] or 0) == 1),
        "agente": {"codigo": agente["codigo"], "version": agente["version"],
                   "ultimo_contacto": agente["ultimo_contacto"].isoformat(timespec="minutes") if agente["ultimo_contacto"] else None,
                   "en_linea": bool(agente["en_linea"])} if agente else None,
        "pedidos_web_escritorio": bool(cfg["pedidos_web_escritorio"]) if cfg else True,
        "cambiado_por": cfg["pedidos_web_escritorio_por"] if cfg else None,
        "cambiado_en": cfg["pedidos_web_escritorio_en"].isoformat(timespec="minutes")
                       if cfg and cfg["pedidos_web_escritorio_en"] else None,
    }


@router.get("")
async def obtener(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    cid = current_user.company_id
    empresa = await _empresa(db, cid)
    return {"empresa": empresa, "sede": await _sede(db, cid, empresa), "escritorio": await _escritorio(db, cid),
            "puede_editar": await _es_admin(db, current_user)}


class EmpresaIn(BaseModel):
    direccion: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=255)]
    telefono: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=50)]
    correo: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=150)]
    company_id: Optional[int] = None     # lo valida tenant_guard; no se usa


@router.put("/empresa")
async def guardar_empresa(body: EmpresaIn, db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    await _exigir_admin(db, current_user)
    if not _RE_EMAIL.match(body.correo):
        raise HTTPException(status_code=422, detail="Correo inválido")
    if not re.fullmatch(r"[0-9+()\-\s]{5,50}", body.telefono):
        raise HTTPException(status_code=422, detail="Teléfono inválido")
    cid = current_user.company_id
    await db.execute(text("""
        UPDATE companies SET address = :d, phone = :t, email = :e, updated_at = NOW() WHERE id_company = :cid
    """), {"d": body.direccion, "t": body.telefono, "e": body.correo, "cid": cid})
    await db.commit()
    return {"ok": True, "empresa": await _empresa(db, cid)}


class SedeIn(BaseModel):
    Nombre_Almacen: _s(250) = ""
    Nombre_Autorizado: _s(250) = ""
    Nit_Autorizado: _s(250) = ""
    Razon_Social: _s(255) = ""
    Direccion_Sede: _s(255) = ""
    Mail_Uno: _s(100) = ""
    Mail_Dos: _s(100) = ""
    Nombre_Logo_Empresa: _s(200) = ""
    company_id: Optional[int] = None     # lo valida tenant_guard; no se usa


@router.put("/sede")
async def guardar_sede(body: SedeIn, db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    await _exigir_admin(db, current_user)
    for campo in ("Mail_Uno", "Mail_Dos"):
        v = getattr(body, campo) or ""
        if v and not _RE_EMAIL.match(v):
            raise HTTPException(status_code=422, detail="Correo de la sede inválido")
    logo = body.Nombre_Logo_Empresa or ""
    if logo and not re.fullmatch(r"[\w\-. ]{1,200}\.(jpg|jpeg|png|bmp|gif)", logo, re.IGNORECASE):
        raise HTTPException(status_code=422, detail="El logo debe ser un nombre de archivo de imagen (ej. logo.jpg)")
    if not (body.Nombre_Almacen or "").strip():
        raise HTTPException(status_code=422, detail="El nombre del almacén es obligatorio")
    cid = current_user.company_id
    empresa = await _empresa(db, cid)
    await _sede(db, cid, empresa)                    # garantiza la fila
    datos = {k: (getattr(body, k) or "") for k in CAMPOS_SEDE}
    await db.execute(text(f"""
        UPDATE configuracion_sede SET {', '.join(f'{k} = :{k}' for k in CAMPOS_SEDE)},
               synced = 0, actualizado_por = :por
        WHERE company_id = :cid
    """), {**datos, "por": _quien(current_user), "cid": cid})
    await db.commit()
    return {"ok": True, "sede": await _sede(db, cid, empresa)}


class EscritorioIn(BaseModel):
    pedidos_web_escritorio: bool
    company_id: Optional[int] = None     # lo valida tenant_guard; no se usa


@router.put("/escritorio")
async def guardar_escritorio(body: EscritorioIn, db: AsyncSession = Depends(get_db),
                             current_user: User = Depends(get_current_user)):
    """Lo decide el admin de la empresa. Un pedido que ya tiene algo enviado a la caja sigue bajando."""
    await _exigir_admin(db, current_user)
    cid = current_user.company_id
    if not (await db.execute(text("SELECT 1 FROM company_configs WHERE company_id = :cid"), {"cid": cid})).scalar():
        await db.execute(text("""
            INSERT INTO company_configs (company_id, has_tip, tip_percentage, has_pos_electronico, has_parking, has_tv_cocina)
            VALUES (:cid, 0, 0, 0, 0, 0)
        """), {"cid": cid})
    await db.execute(text("""
        UPDATE company_configs SET pedidos_web_escritorio = :v, pedidos_web_escritorio_por = :por,
               pedidos_web_escritorio_en = NOW()
        WHERE company_id = :cid
    """), {"v": int(body.pedidos_web_escritorio), "por": _quien(current_user), "cid": cid})
    await db.commit()
    return {"ok": True, "escritorio": await _escritorio(db, cid)}
