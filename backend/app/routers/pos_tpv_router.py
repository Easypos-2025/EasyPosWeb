"""
POS TPV — Configuración y gestión de empleados del módulo Tomar Pedido.
Endpoints de admin (JWT estándar), separados del flujo kiosk de pos_comanda_router.
"""
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Body, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

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
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido")
    session = (await db.execute(
        select(UserSession).where(UserSession.token == token, UserSession.is_active == True)
    )).scalars().first()
    if not session:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    user = (await db.execute(select(User).where(User.id == session.user_id))).scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    from app.auth.tenant import apply_selected_company
    return (await apply_selected_company(db, user)).company_id     # empresa del topbar (validada)


async def _rol_valido(db: AsyncSession, cid: int, role_id) -> int | None:
    """El rol del mesero debe ser de su misma empresa (y no el del sistema)."""
    if role_id in (None, "", 0, "0"):
        return None
    ok = (await db.execute(text(
        "SELECT id FROM roles WHERE id = :rid AND company_id = :cid AND COALESCE(is_system, 0) = 0"
    ), {"rid": int(role_id), "cid": cid})).scalar()
    if not ok:
        raise HTTPException(status_code=422, detail="Rol no válido para esta empresa")
    return int(ok)


@router.get("/config/roles")
async def list_roles_tpv(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Roles de la empresa para asignar a los meseros-vendedores (Control de Acceso por rol)."""
    cid = await _get_company(authorization, db)
    rows = (await db.execute(text(
        "SELECT id, name FROM roles WHERE company_id = :cid AND COALESCE(is_system, 0) = 0 ORDER BY name"
    ), {"cid": cid})).mappings().all()
    return [dict(r) for r in rows]


# ── Empleados TPV (employee_type=2) ──────────────────────────────────────────

@router.get("/config/empleados")
async def list_tpv_empleados(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    cid = await _get_company(authorization, db)
    rows = (await db.execute(text(
        "SELECT w.id, w.name, w.phone, w.status, w.plan_blocked, w.role_id, r.name AS role_name "
        "FROM pos_waiters w LEFT JOIN roles r ON r.id = w.role_id AND r.company_id = w.company_id "
        "WHERE w.company_id=:cid AND w.employee_type=2 "
        "ORDER BY w.name"
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

    role_id = await _rol_valido(db, cid, data.get("role_id"))
    if role_id is None:      # por defecto, el rol de meseros de la empresa
        role_id = (await db.execute(text(
            "SELECT id FROM roles WHERE company_id = :cid AND name = 'VENDEDOR-MESERO'"), {"cid": cid})).scalar()
    # pos_waiters.id no es autoincremental (llave id + empresa). En el escritorio el código suele ser
    # la cédula (hay hasta 2147483647): el nuevo toma el siguiente código corto libre (< 1.000.000)
    for _ in range(3):
        nuevo = int((await db.execute(text(
            "SELECT COALESCE(MAX(id), 0) + 1 FROM pos_waiters WHERE company_id = :cid AND id < 1000000"
        ), {"cid": cid})).scalar())
        try:
            await db.execute(text(
                "INSERT INTO pos_waiters (id, company_id, name, phone, password, status, employee_type, synced, role_id) "
                "VALUES (:id, :cid, :name, :phone, :pin, 1, 2, 0, :rid)"
            ), {"id": nuevo, "cid": cid, "name": name, "phone": (data.get("phone") or "").strip() or None,
                "pin": pin, "rid": role_id})
            await db.commit()
            return {"ok": True, "id": nuevo}
        except IntegrityError:
            await db.rollback()
    raise HTTPException(status_code=409, detail="No se pudo crear el empleado, intente de nuevo")


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
    if "role_id" in data:
        fields += ", role_id=:rid"
        params["rid"] = await _rol_valido(db, cid, data.get("role_id"))
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
    # Nunca se elimina (sus pedidos y recibos lo referencian): queda inactivo
    await db.execute(text(
        "UPDATE pos_waiters SET status = 0 WHERE id=:id AND company_id=:cid"
    ), {"id": emp_id, "cid": cid})
    await db.commit()
    return {"ok": True, "status": 0}
