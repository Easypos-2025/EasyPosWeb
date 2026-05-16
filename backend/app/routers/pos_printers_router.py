from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.database import get_db
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.user_model import User

router = APIRouter(prefix="/api/pos-catalogo/impresoras", tags=["POS Printers"])


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
    r = await db.execute(select(User).where(User.email == payload.get("sub")))
    user = r.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not user.company_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asignada")
    return user


class PrinterIn(BaseModel):
    name: str
    ip: Optional[str] = None
    port: Optional[int] = 9100
    type: Optional[str] = None
    is_active: Optional[int] = 1


@router.get("")
async def listar(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    rows = (await db.execute(text(
        "SELECT * FROM pos_printers WHERE company_id=:cid ORDER BY name"
    ), {"cid": user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.post("", status_code=201)
async def crear(data: PrinterIn, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    await db.execute(text("""
        INSERT INTO pos_printers (company_id, name, ip, port, type, is_active)
        VALUES (:cid, :name, :ip, :port, :type, :active)
    """), {"cid": user.company_id, "name": data.name, "ip": data.ip,
           "port": data.port, "type": data.type, "active": data.is_active})
    await db.commit()
    row = (await db.execute(text(
        "SELECT * FROM pos_printers WHERE company_id=:cid ORDER BY id DESC LIMIT 1"
    ), {"cid": user.company_id})).mappings().one()
    return dict(row)


@router.put("/{printer_id}")
async def actualizar(printer_id: int, data: PrinterIn, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    await db.execute(text("""
        UPDATE pos_printers
        SET name=:name, ip=:ip, port=:port, type=:type, is_active=:active
        WHERE id=:id AND company_id=:cid
    """), {"id": printer_id, "cid": user.company_id, "name": data.name,
           "ip": data.ip, "port": data.port, "type": data.type, "active": data.is_active})
    await db.commit()
    return {"ok": True}


@router.delete("/{printer_id}")
async def eliminar(printer_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    await db.execute(text(
        "UPDATE pos_printers SET is_active=0 WHERE id=:id AND company_id=:cid"
    ), {"id": printer_id, "cid": user.company_id})
    await db.commit()
    return {"ok": True}
