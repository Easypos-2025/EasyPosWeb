from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.database import get_db
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.user_model import User

router = APIRouter(prefix="/api/pos-catalogo/lista-precios", tags=["POS Customer Price List"])


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


class PrecioUpdateIn(BaseModel):
    precio_producto: float
    id_presentacion: Optional[int] = None
    activa: Optional[int] = 1


# ── Lista general (id_lista=0, id_cliente=0) ───────────────────────────────────
@router.get("")
async def listar_general(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    rows = (await db.execute(text("""
        SELECT
            cpl.id, cpl.id_lista, cpl.id_cliente, cpl.id_producto,
            cpl.id_presentacion, cpl.precio_producto, cpl.fecha, cpl.activa,
            d.name   AS item_name,
            d.active AS item_active,
            c.name   AS category_name,
            mu.name  AS presentation_name
        FROM pos_customer_price_list cpl
        LEFT JOIN pos_dishes d
               ON d.id = cpl.id_producto AND d.company_id = cpl.company_id
        LEFT JOIN pos_item_categories c
               ON c.id = d.category_id AND c.company_id = cpl.company_id
        LEFT JOIN measurement_units mu
               ON mu.id = cpl.id_presentacion
        WHERE cpl.company_id = :cid AND cpl.id_lista = 0 AND cpl.id_cliente = 0
        ORDER BY c.name, d.name
    """), {"cid": user.company_id})).mappings().all()
    return [dict(r) for r in rows]


# ── Actualizar precio ─────────────────────────────────────────────────────────
@router.put("/{item_id}")
async def actualizar_precio(
    item_id: int,
    data: PrecioUpdateIn,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    await db.execute(text("""
        UPDATE pos_customer_price_list
        SET precio_producto=:precio, id_presentacion=:pres,
            activa=:activa, fecha=:fecha, updated_at=NOW()
        WHERE id=:id AND company_id=:cid
    """), {
        "id": item_id, "cid": user.company_id,
        "precio": data.precio_producto,
        "pres": data.id_presentacion,
        "activa": data.activa,
        "fecha": date.today().isoformat(),
    })
    await db.commit()
    return {"ok": True}


# ── Toggle activa ─────────────────────────────────────────────────────────────
@router.patch("/{item_id}/toggle")
async def toggle_activa(item_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    await db.execute(text(
        "UPDATE pos_customer_price_list SET activa = 1 - activa "
        "WHERE id=:id AND company_id=:cid"
    ), {"id": item_id, "cid": user.company_id})
    await db.commit()
    return {"ok": True}
