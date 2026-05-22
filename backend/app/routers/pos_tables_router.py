from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.user_model import User

router = APIRouter(prefix="/api/pos", tags=["pos-tables"])


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


# ── Schemas ──────────────────────────────────────────────────────────────────

class ZoneIn(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = "#1d4ed8"
    icon: Optional[str] = "bi-grid"
    is_active: Optional[int] = 1
    order_index: Optional[int] = 0


class TableIn(BaseModel):
    zone_id: int
    name: str
    capacity: Optional[int] = 4
    is_active: Optional[int] = 1
    order_index: Optional[int] = 0


class TableStatusIn(BaseModel):
    status: str  # free | occupied | bill_requested


# ── Zones ─────────────────────────────────────────────────────────────────────

@router.get("/zonas")
async def list_zones(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    rows = await db.execute(text("""
        SELECT z.id, z.name, z.description, z.color, z.icon, z.is_active, z.order_index,
               COUNT(t.id) AS table_count,
               SUM(CASE WHEN t.is_active=1 AND t.status='occupied'       THEN 1 ELSE 0 END) AS occupied_count,
               SUM(CASE WHEN t.is_active=1 AND t.status='bill_requested' THEN 1 ELSE 0 END) AS bill_count,
               SUM(CASE WHEN t.is_active=1 AND t.status='free'           THEN 1 ELSE 0 END) AS free_count
        FROM pos_zones z
        LEFT JOIN pos_tables t ON t.zone_id=z.id AND t.company_id=z.company_id
        WHERE z.company_id=:cid
        GROUP BY z.id
        ORDER BY z.order_index, z.name
    """), {"cid": user.company_id})
    return [dict(r._mapping) for r in rows.fetchall()]


@router.post("/zonas")
async def create_zone(data: ZoneIn, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    res = await db.execute(text("""
        INSERT INTO pos_zones (company_id, name, description, color, icon, is_active, order_index)
        VALUES (:cid, :name, :desc, :color, :icon, :active, :order)
    """), {
        "cid": user.company_id, "name": data.name.strip(), "desc": data.description,
        "color": data.color, "icon": data.icon, "active": data.is_active, "order": data.order_index
    })
    await db.commit()
    return {"ok": True, "id": res.lastrowid}


@router.put("/zonas/{zone_id}")
async def update_zone(zone_id: int, data: ZoneIn, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    res = await db.execute(text("""
        UPDATE pos_zones SET name=:name, description=:desc, color=:color, icon=:icon,
               is_active=:active, order_index=:order
        WHERE id=:id AND company_id=:cid
    """), {
        "id": zone_id, "cid": user.company_id, "name": data.name.strip(),
        "desc": data.description, "color": data.color, "icon": data.icon,
        "active": data.is_active, "order": data.order_index
    })
    await db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Zona no encontrada")
    return {"ok": True}


@router.delete("/zonas/{zone_id}")
async def delete_zone(zone_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    active_tables = await db.execute(text("""
        SELECT COUNT(*) FROM pos_tables WHERE zone_id=:zid AND company_id=:cid AND is_active=1
    """), {"zid": zone_id, "cid": user.company_id})
    if active_tables.scalar() > 0:
        raise HTTPException(status_code=400, detail="La zona tiene mesas activas. Desactívalas primero.")
    await db.execute(text("""
        UPDATE pos_zones SET is_active=0 WHERE id=:id AND company_id=:cid
    """), {"id": zone_id, "cid": user.company_id})
    await db.commit()
    return {"ok": True}


# ── Tables ────────────────────────────────────────────────────────────────────

@router.get("/mesas")
async def list_tables(zone_id: Optional[int] = None, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    where = "t.company_id=:cid"
    params: dict = {"cid": user.company_id}
    if zone_id:
        where += " AND t.zone_id=:zid"
        params["zid"] = zone_id

    rows = await db.execute(text(f"""
        SELECT t.id, t.zone_id, t.name, t.capacity, t.status, t.current_order_id,
               t.is_active, t.order_index, z.name AS zone_name, z.color AS zone_color
        FROM pos_tables t
        LEFT JOIN pos_zones z ON z.id=t.zone_id AND z.company_id=t.company_id
        WHERE {where}
        ORDER BY z.order_index, z.name, t.order_index, t.name
    """), params)
    return [dict(r._mapping) for r in rows.fetchall()]


@router.post("/mesas")
async def create_table(data: TableIn, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    zone = await db.execute(text(
        "SELECT id FROM pos_zones WHERE id=:zid AND company_id=:cid AND is_active=1"
    ), {"zid": data.zone_id, "cid": user.company_id})
    if not zone.fetchone():
        raise HTTPException(status_code=404, detail="Zona no encontrada")

    res = await db.execute(text("""
        INSERT INTO pos_tables (company_id, zone_id, name, capacity, is_active, order_index)
        VALUES (:cid, :zid, :name, :cap, :active, :order)
    """), {
        "cid": user.company_id, "zid": data.zone_id, "name": data.name.strip(),
        "cap": data.capacity, "active": data.is_active, "order": data.order_index
    })
    await db.commit()
    return {"ok": True, "id": res.lastrowid}


@router.put("/mesas/{table_id}")
async def update_table(table_id: int, data: TableIn, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    res = await db.execute(text("""
        UPDATE pos_tables SET zone_id=:zid, name=:name, capacity=:cap,
               is_active=:active, order_index=:order
        WHERE id=:id AND company_id=:cid
    """), {
        "id": table_id, "cid": user.company_id, "zid": data.zone_id,
        "name": data.name.strip(), "cap": data.capacity,
        "active": data.is_active, "order": data.order_index
    })
    await db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    return {"ok": True}


@router.patch("/mesas/{table_id}/estado")
async def update_table_status(table_id: int, data: TableStatusIn, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    if data.status not in ("free", "occupied", "bill_requested"):
        raise HTTPException(status_code=400, detail="Estado inválido")
    res = await db.execute(text("""
        UPDATE pos_tables SET status=:status WHERE id=:id AND company_id=:cid
    """), {"status": data.status, "id": table_id, "cid": user.company_id})
    await db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    return {"ok": True}


@router.delete("/mesas/{table_id}")
async def delete_table(table_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    occupied = await db.execute(text("""
        SELECT status FROM pos_tables WHERE id=:id AND company_id=:cid
    """), {"id": table_id, "cid": user.company_id})
    row = occupied.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    if row[0] in ("occupied", "bill_requested"):
        raise HTTPException(status_code=400, detail="No se puede eliminar una mesa ocupada o con cuenta pendiente.")
    await db.execute(text("""
        UPDATE pos_tables SET is_active=0 WHERE id=:id AND company_id=:cid
    """), {"id": table_id, "cid": user.company_id})
    await db.commit()
    return {"ok": True}
