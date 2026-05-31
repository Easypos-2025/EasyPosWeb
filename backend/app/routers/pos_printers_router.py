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
    uid = payload.get("user_id")
    user = await db.get(User, int(uid)) if uid else None
    if not user:
        r = await db.execute(select(User).where(User.email == payload.get("sub")))
        user = r.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not user.company_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asignada")
    return user


class PrinterIn(BaseModel):
    name: str
    connection_type: Optional[str] = "network"   # usb | network | bluetooth
    ip: Optional[str] = None
    bluetooth_address: Optional[str] = None
    usb_device_id: Optional[str] = None
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
        INSERT INTO pos_printers
            (company_id, name, connection_type, ip, bluetooth_address, usb_device_id, is_active)
        VALUES
            (:cid, :name, :ctype, :ip, :bt, :usb, :active)
    """), {
        "cid":    user.company_id,
        "name":   data.name,
        "ctype":  data.connection_type,
        "ip":     data.ip,
        "bt":     data.bluetooth_address,
        "usb":    data.usb_device_id,
        "active": data.is_active,
    })
    await db.commit()
    row = (await db.execute(text(
        "SELECT * FROM pos_printers WHERE company_id=:cid ORDER BY id DESC LIMIT 1"
    ), {"cid": user.company_id})).mappings().one()
    return dict(row)


@router.put("/{printer_id}")
async def actualizar(
    printer_id: int, data: PrinterIn,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    await db.execute(text("""
        UPDATE pos_printers
        SET name=:name, connection_type=:ctype, ip=:ip,
            bluetooth_address=:bt, usb_device_id=:usb, is_active=:active
        WHERE id=:id AND company_id=:cid
    """), {
        "id":     printer_id,
        "cid":    user.company_id,
        "name":   data.name,
        "ctype":  data.connection_type,
        "ip":     data.ip,
        "bt":     data.bluetooth_address,
        "usb":    data.usb_device_id,
        "active": data.is_active,
    })
    await db.commit()
    return {"ok": True}


@router.patch("/{printer_id}/toggle")
async def toggle_activa(
    printer_id: int,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    await db.execute(text(
        "UPDATE pos_printers SET is_active = 1 - is_active WHERE id=:id AND company_id=:cid"
    ), {"id": printer_id, "cid": user.company_id})
    await db.commit()
    row = (await db.execute(text(
        "SELECT id, is_active FROM pos_printers WHERE id=:id AND company_id=:cid"
    ), {"id": printer_id, "cid": user.company_id})).mappings().first()
    return {"id": int(row["id"]), "is_active": int(row["is_active"])}


@router.delete("/{printer_id}")
async def eliminar(
    printer_id: int,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    # Eliminar asignaciones artículo→impresora antes de borrar
    await db.execute(text(
        "DELETE FROM pos_item_printers WHERE printer_id=:id AND company_id=:cid"
    ), {"id": printer_id, "cid": user.company_id})
    # Eliminar registro definitivamente
    await db.execute(text(
        "DELETE FROM pos_printers WHERE id=:id AND company_id=:cid"
    ), {"id": printer_id, "cid": user.company_id})
    await db.commit()
    return {"ok": True}
