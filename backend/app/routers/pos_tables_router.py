from datetime import date, datetime, timezone, timedelta

_BOG = timezone(timedelta(hours=-5))
def _today() -> str:
    return datetime.now(_BOG).date().isoformat()

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
    seats_count: Optional[int] = 0
    color: Optional[str] = "#1d4ed8"
    is_active: Optional[int] = 1
    description: Optional[str] = None
    icon: Optional[str] = "bi-grid"
    order_index: Optional[int] = 0


class TableIn(BaseModel):
    zone_id: int
    name: str
    capacity: Optional[int] = 4


# ── Zones ─────────────────────────────────────────────────────────────────────
# pos_zones stores zone metadata (name, color, icon).
# Table counts and occupancy always come from pos_tables_layout + pos_orders.

@router.get("/zonas")
async def list_zones(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    cid = user.company_id
    today = _today()

    # Zone metadata from pos_zones (may be empty for VB6-only companies)
    zone_rows = (await db.execute(text(
        "SELECT id, name, description, color, icon, is_active, order_index FROM pos_zones WHERE company_id=:cid"
    ), {"cid": cid})).mappings().all()
    zone_map = {z["id"]: dict(z) for z in zone_rows}

    # Table counts + real-time occupancy from pos_tables_layout + pos_orders
    counts = (await db.execute(text("""
        SELECT
            t.zone_id,
            COUNT(t.id)                                                                  AS table_count,
            COALESCE(SUM(CASE WHEN o.order_number IS NOT NULL THEN 1 ELSE 0 END), 0)   AS occupied_count,
            COALESCE(SUM(CASE WHEN o.order_number IS NULL     THEN 1 ELSE 0 END), 0)   AS free_count
        FROM pos_tables_layout t
        LEFT JOIN pos_orders o
               ON o.table_id       = t.id
              AND o.company_id     = :cid
              AND o.date           = :today
              AND o.invoice_number = '0'
              AND o.cancelled      = 0
              AND o.delivery       = 0
        WHERE t.company_id = :cid
        GROUP BY t.zone_id
        ORDER BY t.zone_id
    """), {"cid": cid, "today": today})).mappings().all()

    result = []
    for r in counts:
        zid = r["zone_id"]
        meta = zone_map.get(zid) or {
            "id": zid,
            "name": f"Zona {zid}",
            "description": None,
            "color": "#1d4ed8",
            "icon": "bi-grid",
            "is_active": 1,
            "order_index": zid,
        }
        result.append({
            **meta,
            "table_count":    int(r["table_count"]),
            "occupied_count": int(r["occupied_count"]),
            "bill_count":     0,
            "free_count":     int(r["free_count"]),
        })
    return result


@router.post("/zonas")
async def create_zone(data: ZoneIn, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    cid = user.company_id
    max_id = (await db.execute(
        text("SELECT COALESCE(MAX(id), 0) FROM pos_zones WHERE company_id=:cid"), {"cid": cid}
    )).scalar() or 0
    new_id = int(max_id) + 1
    await db.execute(text("""
        INSERT INTO pos_zones (id, company_id, name, seats_count, color, is_active, description, icon, order_index)
        VALUES (:id, :cid, :name, :seats, :color, :active, :desc, :icon, :order)
    """), {
        "id": new_id, "cid": cid, "name": data.name.strip(), "seats": data.seats_count,
        "color": data.color, "active": data.is_active,
        "desc": data.description, "icon": data.icon or "bi-grid", "order": data.order_index
    })
    await db.commit()
    return {"ok": True, "id": new_id}


@router.put("/zonas/{zone_id}")
async def update_zone(zone_id: int, data: ZoneIn, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    res = await db.execute(text("""
        UPDATE pos_zones SET name=:name, seats_count=:seats, color=:color,
               is_active=:active, description=:desc, icon=:icon, order_index=:order
        WHERE id=:id AND company_id=:cid
    """), {
        "id": zone_id, "cid": user.company_id, "name": data.name.strip(),
        "seats": data.seats_count, "color": data.color, "active": data.is_active,
        "desc": data.description, "icon": data.icon or "bi-grid", "order": data.order_index
    })
    await db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Zona no encontrada")
    return {"ok": True}


@router.delete("/zonas/{zone_id}")
async def delete_zone(zone_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    cid = user.company_id
    today = _today()

    occupied = (await db.execute(text("""
        SELECT COUNT(*) FROM pos_orders o
        JOIN pos_tables_layout t ON t.id = o.table_id AND t.company_id = o.company_id
        WHERE t.zone_id = :zid AND o.company_id = :cid
          AND o.date = :today AND o.invoice_number = '0' AND o.cancelled = 0
    """), {"zid": zone_id, "cid": cid, "today": today})).scalar()
    if occupied:
        raise HTTPException(status_code=400, detail="La zona tiene mesas con comandas abiertas.")

    await db.execute(text(
        "UPDATE pos_zones SET is_active=0 WHERE id=:id AND company_id=:cid"
    ), {"id": zone_id, "cid": cid})
    await db.commit()
    return {"ok": True}


# ── Tables (pos_tables_layout is the single source of truth) ─────────────────

@router.get("/mesas")
async def list_tables(zone_id: Optional[int] = None, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    cid = user.company_id
    today = _today()

    where = "t.company_id = :cid"
    params: dict = {"cid": cid, "today": today}
    if zone_id is not None:
        where += " AND t.zone_id = :zid"
        params["zid"] = zone_id

    rows = (await db.execute(text(f"""
        SELECT
            t.id,
            t.zone_id,
            t.name,
            COALESCE(t.seats, 0)                                                         AS capacity,
            CASE WHEN o.order_number IS NOT NULL THEN 'occupied' ELSE 'free' END         AS status,
            o.order_number                                                               AS current_order_id,
            1                                                                            AS is_active,
            0                                                                            AS order_index,
            COALESCE(z.name, CONCAT('Zona ', t.zone_id))                                 AS zone_name,
            COALESCE(z.color, '#1d4ed8')                                                 AS zone_color
        FROM pos_tables_layout t
        LEFT JOIN pos_zones z   ON z.id = t.zone_id AND z.company_id = :cid
        LEFT JOIN pos_orders o
               ON o.table_id       = t.id
              AND o.company_id     = :cid
              AND o.date           = :today
              AND o.invoice_number = '0'
              AND o.cancelled      = 0
              AND o.delivery       = 0
        WHERE {where}
        ORDER BY t.zone_id, t.name
    """), params)).mappings().all()
    return [dict(r) for r in rows]


@router.post("/mesas")
async def create_table(data: TableIn, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    cid = user.company_id

    max_id = (await db.execute(text(
        "SELECT COALESCE(MAX(id), 0) FROM pos_tables_layout WHERE company_id=:cid"
    ), {"cid": cid})).scalar() or 0
    new_id = int(max_id) + 1

    await db.execute(text("""
        INSERT INTO pos_tables_layout
            (id, company_id, zone_id, name, seats, location, active, branch_id, customer_id, dynamic_zone, synced)
        VALUES
            (:id, :cid, :zid, :name, :seats, '', 0, 0, 0, 0, 0)
    """), {"id": new_id, "cid": cid, "zid": data.zone_id,
           "name": data.name.strip(), "seats": data.capacity})
    await db.commit()
    return {"ok": True, "id": new_id}


@router.put("/mesas/{table_id}")
async def update_table(table_id: int, data: TableIn, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    res = await db.execute(text("""
        UPDATE pos_tables_layout
        SET zone_id=:zid, name=:name, seats=:seats, updated_at=NOW()
        WHERE id=:id AND company_id=:cid
    """), {"id": table_id, "cid": user.company_id,
           "zid": data.zone_id, "name": data.name.strip(), "seats": data.capacity})
    await db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    return {"ok": True}


@router.delete("/mesas/{table_id}")
async def delete_table(table_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    cid = user.company_id
    today = _today()

    occupied = (await db.execute(text("""
        SELECT COUNT(*) FROM pos_orders
        WHERE table_id=:id AND company_id=:cid
          AND date=:today AND invoice_number='0' AND cancelled=0
    """), {"id": table_id, "cid": cid, "today": today})).scalar()
    if occupied:
        raise HTTPException(status_code=400, detail="No se puede eliminar una mesa con comanda abierta.")

    res = await db.execute(text(
        "DELETE FROM pos_tables_layout WHERE id=:id AND company_id=:cid"
    ), {"id": table_id, "cid": cid})
    await db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    return {"ok": True}
