from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.database import get_db
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.user_model import User
from app.auth.bodega_guard import bloqueo_bodega

router = APIRouter(prefix="/api/pos-catalogo/categorias", tags=["POS Item Categories"],
                   dependencies=[Depends(bloqueo_bodega("Las categorías de productos"))])


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


class CategoryIn(BaseModel):
    name: str
    is_active: Optional[int] = 1


@router.get("")
async def listar(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    rows = (await db.execute(text(
        "SELECT id, company_id, name, is_active FROM pos_dish_categories WHERE company_id=:cid ORDER BY name"
    ), {"cid": user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.post("", status_code=201)
async def crear(data: CategoryIn, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    # Antes el id quedaba en 0 (la columna no es autoincremental). Con escritorio (S3): provisional,
    # el escritorio le asigna su Cod_Categoria al sincronizar.
    from app.services import sede_maestros, sede_pedidos
    nuevo_id = await sede_maestros.siguiente_id(db, "pos_dish_categories", "id", user.company_id,
                                                await sede_pedidos.tiene_sede(db, user.company_id))
    await db.execute(text("""
        INSERT INTO pos_dish_categories (id, company_id, name, is_active, synced)
        VALUES (:id, :cid, :name, :active, 0)
    """), {"id": nuevo_id, "cid": user.company_id, "name": data.name, "active": data.is_active})
    await db.commit()
    row = (await db.execute(text(
        "SELECT id, company_id, name, is_active FROM pos_dish_categories WHERE company_id=:cid AND id=:id"
    ), {"cid": user.company_id, "id": nuevo_id})).mappings().one()
    return dict(row)


@router.put("/{cat_id}")
async def actualizar(cat_id: int, data: CategoryIn, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    await db.execute(text("""
        UPDATE pos_dish_categories SET name=:name, is_active=:active, synced=0
        WHERE id=:id AND company_id=:cid
    """), {"id": cat_id, "cid": user.company_id, "name": data.name, "active": data.is_active})
    await db.commit()
    return {"ok": True}


@router.delete("/{cat_id}")
async def eliminar(cat_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    await db.execute(text(
        "UPDATE pos_dish_categories SET is_active=0, synced=0 WHERE id=:id AND company_id=:cid"
    ), {"id": cat_id, "cid": user.company_id})
    await db.commit()
    return {"ok": True}
