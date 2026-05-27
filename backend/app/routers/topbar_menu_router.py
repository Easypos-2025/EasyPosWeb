from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.database import get_db
from app.models.topbar_menu_item_model import TopbarMenuItem
from app.models.user_model import User
from app.models.role_model import Role
from app.models.user_session_model import UserSession
from app.models.company_plan_model import CompanyPlan
from app.auth.jwt_handler import decode_access_token
from app.schemas.topbar_menu_schema import TopbarMenuItemCreate, TopbarMenuItemUpdate

router = APIRouter(prefix="/topbar-menu", tags=["TopbarMenu"])


async def _get_user(authorization: str, db: AsyncSession):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    result = await db.execute(select(UserSession).where(UserSession.token == token, UserSession.is_active == True))
    if not result.scalar_one_or_none() or not payload:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    uid = payload.get("user_id")
    user = await db.get(User, int(uid)) if uid else None
    if not user:
        result = await db.execute(select(User).where(User.email == payload.get("sub")))
        user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


async def _is_sysadmin(user: User, db: AsyncSession) -> bool:
    result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = result.scalar_one_or_none()
    return role.is_system if role else False


def _ser(item: TopbarMenuItem):
    return {"id": item.id, "name": item.name, "key": item.key, "icon": item.icon,
            "route": item.route, "has_evidence": item.has_evidence, "min_plan_id": item.min_plan_id,
            "is_active": item.is_active, "order_index": item.order_index}


@router.get("")
async def get_menu_items(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    result = await db.execute(select(CompanyPlan).where(CompanyPlan.company_id == user.company_id, CompanyPlan.is_active == True))
    company_plan = result.scalar_one_or_none()
    plan_id = company_plan.plan_id if company_plan else 1

    result = await db.execute(
        select(TopbarMenuItem).where(
            TopbarMenuItem.is_active == True,
            or_(TopbarMenuItem.min_plan_id == None, TopbarMenuItem.min_plan_id <= plan_id)
        ).order_by(TopbarMenuItem.order_index)
    )
    return [_ser(i) for i in result.scalars().all()]


@router.get("/all")
async def get_all_menu_items(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    if not await _is_sysadmin(user, db):
        raise HTTPException(status_code=403, detail="Acceso restringido a SYSADMIN")
    result = await db.execute(select(TopbarMenuItem).order_by(TopbarMenuItem.order_index))
    return [_ser(i) for i in result.scalars().all()]


@router.post("")
async def create_menu_item(data: TopbarMenuItemCreate, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    if not await _is_sysadmin(user, db):
        raise HTTPException(status_code=403, detail="Acceso restringido a SYSADMIN")
    result = await db.execute(select(TopbarMenuItem).where(TopbarMenuItem.key == data.key))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya existe un ítem con esa clave")
    item = TopbarMenuItem(**data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return _ser(item)


@router.put("/{item_id}")
async def update_menu_item(item_id: int, data: TopbarMenuItemUpdate, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    if not await _is_sysadmin(user, db):
        raise HTTPException(status_code=403, detail="Acceso restringido a SYSADMIN")
    result = await db.execute(select(TopbarMenuItem).where(TopbarMenuItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.commit()
    await db.refresh(item)
    return _ser(item)


@router.delete("/{item_id}")
async def delete_menu_item(item_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    if not await _is_sysadmin(user, db):
        raise HTTPException(status_code=403, detail="Acceso restringido a SYSADMIN")
    result = await db.execute(select(TopbarMenuItem).where(TopbarMenuItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    await db.delete(item)
    await db.commit()
    return {"ok": True}
