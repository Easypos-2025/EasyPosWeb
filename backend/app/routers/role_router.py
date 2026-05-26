from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database import get_db
from app.models.role_model import Role
from app.models.role_module_model import RoleModule
from app.models.system_module_model import SystemModule
from app.models.user_model import User
from app.auth.dependencies import get_current_user
from app.services.plan_limits_service import check_limit

router = APIRouter(prefix="/roles", tags=["Roles"])


def _ser(r: Role) -> dict:
    return {"id": r.id, "name": r.name, "description": r.description,
            "company_id": r.company_id, "is_system": r.is_system}


async def _is_system(user: User, db: AsyncSession) -> bool:
    role = await db.get(Role, user.role_id)
    return role.is_system if role else False


@router.get("/")
async def get_roles(
    company_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if await _is_system(current_user, db):
        if company_id is None:
            raise HTTPException(status_code=400, detail="Se requiere company_id para consultar roles")
        cid = company_id
    else:
        cid = current_user.company_id

    result = await db.execute(
        select(Role).where(Role.company_id == cid, Role.is_system == False).order_by(Role.name)
    )
    return [_ser(r) for r in result.scalars().all()]


@router.post("/")
async def create_role(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if await _is_system(current_user, db):
        cid = data.get("company_id")
        if not cid:
            raise HTTPException(status_code=400, detail="company_id requerido")
    else:
        cid = current_user.company_id
        await check_limit(cid, "max_roles", Role, db)

    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    result = await db.execute(select(Role).where(Role.name == name, Role.company_id == cid))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Ya existe un rol '{name}' en esta empresa")

    role = Role(name=name, description=(data.get("description") or "").strip(), company_id=cid, is_system=False)
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return _ser(role)


@router.put("/{role_id}")
async def update_role(
    role_id: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    if not await _is_system(current_user, db) and role.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Sin permisos")

    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    result = await db.execute(select(Role).where(Role.name == name, Role.company_id == role.company_id, Role.id != role_id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Ya existe un rol '{name}'")

    role.name = name
    role.description = (data.get("description") or "").strip()
    await db.commit()
    await db.refresh(role)
    return _ser(role)


@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    if not await _is_system(current_user, db) and role.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Sin permisos")
    await db.delete(role)
    await db.commit()
    return {"message": "Rol eliminado"}


@router.get("/{role_id}/modules/")
async def get_modules_by_role(
    role_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    if await _is_system(current_user, db):
        result = await db.execute(select(SystemModule).order_by(SystemModule.order_index))
    else:
        result = await db.execute(select(SystemModule).where(SystemModule.is_sysadmin == False).order_by(SystemModule.order_index))
    modules = result.scalars().all()

    result = await db.execute(select(RoleModule).where(RoleModule.role_id == role_id))
    permissions_map = {rm.module_id: rm for rm in result.scalars().all()}

    return [
        {
            "module_id":    m.id,
            "module_name":  m.name,
            "module_route": m.route or "",
            "can_view":     permissions_map[m.id].can_view     if m.id in permissions_map else False,
            "can_view_all": permissions_map[m.id].can_view_all if m.id in permissions_map else False,
            "can_create":   permissions_map[m.id].can_create   if m.id in permissions_map else False,
            "can_edit":     permissions_map[m.id].can_edit     if m.id in permissions_map else False,
            "can_delete":   permissions_map[m.id].can_delete   if m.id in permissions_map else False,
        }
        for m in modules
    ]


@router.post("/{role_id}/modules/")
async def assign_modules_to_role(
    role_id: int,
    modules: List[dict],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    if not await _is_system(current_user, db) and role.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Sin permisos")

    await db.execute(delete(RoleModule).where(RoleModule.role_id == role_id))

    for m in modules:
        db.add(RoleModule(
            role_id=role_id, module_id=m["module_id"],
            can_view=m.get("can_view", True), can_view_all=m.get("can_view_all", False),
            can_create=m.get("can_create", False),
            can_edit=m.get("can_edit", False), can_delete=m.get("can_delete", False),
        ))

    await db.commit()
    return {"message": "Módulos asignados correctamente"}
