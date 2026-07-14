"""
POS TPV — Configuración y gestión de empleados del módulo Tomar Pedido.
Endpoints de admin (JWT estándar), separados del flujo kiosk de pos_comanda_router.
"""
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Body, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.database import get_db
from app.auth.jwt_handler import decode_access_token
from app.models.user_model import User
from app.models.user_session_model import UserSession

router = APIRouter(prefix="/api/pos/tpv", tags=["POS TPV Config"])

_BOG = timezone(timedelta(hours=-5))


async def _get_company(authorization: str, db: AsyncSession) -> int:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    session = (await db.execute(
        select(UserSession).where(UserSession.token == token, UserSession.is_active == True)
    )).scalar_one_or_none()
    if not session or payload is None:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    user = (await db.execute(select(User).where(User.email == payload.get("sub")))).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user.company_id


# ── Empleados TPV (employee_type=2) ──────────────────────────────────────────

@router.get("/config/empleados")
async def list_tpv_empleados(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    cid = await _get_company(authorization, db)
    rows = (await db.execute(text(
        "SELECT id, name, phone, status, plan_blocked "
        "FROM pos_waiters "
        "WHERE company_id=:cid AND employee_type=2 "
        "ORDER BY name"
    ), {"cid": cid})).mappings().all()
    return [dict(r) for r in rows]


@router.post("/config/empleados")
async def create_tpv_empleado(
    data: dict = Body(...),
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    cid = await _get_company(authorization, db)
    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")
    pin = (data.get("password") or "").strip()
    if not pin:
        raise HTTPException(status_code=400, detail="El PIN es obligatorio")

    await db.execute(text(
        "INSERT INTO pos_waiters (company_id, name, phone, password, status, employee_type, synced) "
        "VALUES (:cid, :name, :phone, :pin, 1, 2, 0)"
    ), {"cid": cid, "name": name, "phone": (data.get("phone") or "").strip() or None, "pin": pin})
    await db.commit()
    return {"ok": True}


@router.put("/config/empleados/{emp_id}")
async def update_tpv_empleado(
    emp_id: int,
    data: dict = Body(...),
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    cid = await _get_company(authorization, db)
    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    existing = (await db.execute(text(
        "SELECT id FROM pos_waiters WHERE id=:id AND company_id=:cid AND employee_type=2"
    ), {"id": emp_id, "cid": cid})).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")

    fields = "name=:name, phone=:phone"
    params: dict = {"id": emp_id, "cid": cid, "name": name, "phone": (data.get("phone") or "").strip() or None}
    pin = (data.get("password") or "").strip()
    if pin:
        fields += ", password=:pin"
        params["pin"] = pin

    await db.execute(text(f"UPDATE pos_waiters SET {fields} WHERE id=:id AND company_id=:cid"), params)
    await db.commit()
    return {"ok": True}


@router.patch("/config/empleados/{emp_id}/status")
async def toggle_tpv_empleado_status(
    emp_id: int,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    cid = await _get_company(authorization, db)
    row = (await db.execute(text(
        "SELECT status FROM pos_waiters WHERE id=:id AND company_id=:cid AND employee_type=2"
    ), {"id": emp_id, "cid": cid})).first()
    if not row:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    new_status = 0 if row.status == 1 else 1
    await db.execute(text(
        "UPDATE pos_waiters SET status=:s WHERE id=:id AND company_id=:cid"
    ), {"s": new_status, "id": emp_id, "cid": cid})
    await db.commit()
    return {"status": new_status}


@router.delete("/config/empleados/{emp_id}")
async def delete_tpv_empleado(
    emp_id: int,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    cid = await _get_company(authorization, db)
    existing = (await db.execute(text(
        "SELECT id FROM pos_waiters WHERE id=:id AND company_id=:cid AND employee_type=2"
    ), {"id": emp_id, "cid": cid})).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Empleado no encontrado")
    await db.execute(text(
        "DELETE FROM pos_waiters WHERE id=:id AND company_id=:cid"
    ), {"id": emp_id, "cid": cid})
    await db.commit()
    return {"ok": True}
