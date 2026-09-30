from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException
from typing import Literal
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.database import get_db
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.user_model import User

router = APIRouter(prefix="/api/pos-catalogo/cajas", tags=["POS Cash Registers"])


async def _get_user(authorization: str, db: AsyncSession) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido")
    r = await db.execute(select(UserSession).where(UserSession.token == token, UserSession.is_active == True))
    if not r.scalar_one_or_none():
        raise HTTPException(status_code=401, detail="Sesión inválida")
    uid = payload.get("user_id")
    user = await db.get(User, int(uid)) if uid else None
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not user.company_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asignada")
    from app.auth.tenant import apply_selected_company
    return await apply_selected_company(db, user)   # empresa del topbar (validada)


class CashRegisterIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: Literal["main", "auxiliary"] = "auxiliary"
    is_active: Optional[int] = Field(1, ge=0, le=1)
    printer_id: Optional[int] = Field(0, ge=0)     # = cajas.Id_Impresora (impresora de recibos)


async def _validar_impresora(db: AsyncSession, cid: int, printer_id: Optional[int]) -> int:
    if not printer_id:
        return 0
    ok = (await db.execute(text(
        "SELECT 1 FROM pos_printers WHERE company_id=:cid AND id=:pid"
    ), {"cid": cid, "pid": printer_id})).scalar()
    if not ok:
        raise HTTPException(status_code=422, detail="Impresora no válida para esta empresa")
    return int(printer_id)


@router.get("/impresoras")
async def impresoras(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    rows = (await db.execute(text(
        "SELECT id, name, connection_type FROM pos_printers WHERE company_id=:cid AND is_active=1 ORDER BY name"
    ), {"cid": user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.get("")
async def listar(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    rows = (await db.execute(text(
        "SELECT * FROM pos_cash_registers WHERE company_id=:cid ORDER BY type DESC, name"
    ), {"cid": user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.post("", status_code=201)
async def crear(data: CashRegisterIn, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    if data.type == "main":
        await db.execute(text(
            "UPDATE pos_cash_registers SET type='auxiliary' WHERE company_id=:cid AND type='main'"
        ), {"cid": user.company_id})
    printer_id = await _validar_impresora(db, user.company_id, data.printer_id)
    # Llave (id, company_id) sin autoincremento: id = Nro_Caja, siguiente de la empresa
    next_id = (await db.execute(text(
        "SELECT COALESCE(MAX(id), 0) + 1 FROM pos_cash_registers WHERE company_id=:cid"
    ), {"cid": user.company_id})).scalar()
    await db.execute(text("""
        INSERT INTO pos_cash_registers (id, company_id, name, type, is_active, printer_id)
        VALUES (:id, :cid, :name, :type, :active, :pid)
    """), {"id": next_id, "cid": user.company_id, "name": data.name, "type": data.type,
           "active": data.is_active, "pid": printer_id})
    await db.commit()
    row = (await db.execute(text(
        "SELECT * FROM pos_cash_registers WHERE company_id=:cid AND id=:id"
    ), {"cid": user.company_id, "id": next_id})).mappings().one()
    return dict(row)


@router.put("/{register_id}")
async def actualizar(register_id: int, data: CashRegisterIn, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    if data.type == "main":
        await db.execute(text(
            "UPDATE pos_cash_registers SET type='auxiliary' WHERE company_id=:cid AND type='main' AND id!=:id"
        ), {"cid": user.company_id, "id": register_id})
    printer_id = await _validar_impresora(db, user.company_id, data.printer_id)
    await db.execute(text("""
        UPDATE pos_cash_registers SET name=:name, type=:type, is_active=:active, printer_id=:pid, synced=0
        WHERE id=:id AND company_id=:cid
    """), {"id": register_id, "cid": user.company_id,
           "name": data.name, "type": data.type, "active": data.is_active, "pid": printer_id})
    await db.commit()
    return {"ok": True}


@router.delete("/{register_id}")
async def eliminar(register_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    await db.execute(text(
        "UPDATE pos_cash_registers SET is_active=0 WHERE id=:id AND company_id=:cid"
    ), {"id": register_id, "cid": user.company_id})
    await db.commit()
    return {"ok": True}
