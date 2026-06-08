from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, delete
from app.models.role_module_model import RoleModule
from app.database import get_db
from app.models.system_module_model import SystemModule
from app.schemas.system_module_schema import SystemModuleCreate, SystemModuleOut, SystemModuleUpdate
from app.models.business_profile_module import BusinessProfileModule
from app.models.company_model import Company
from app.auth.dependencies import get_current_user
from app.models.role_model import Role

router = APIRouter(prefix="/system-modules", tags=["System Modules"])


def build_tree(modules):
    module_dict = {
        m.id: {"id": m.id, "name": m.name, "route": m.route, "icon": m.icon,
               "parent_id": m.parent_id, "is_active": m.is_active, "children": []}
        for m in modules
    }
    tree = []
    for m in module_dict.values():
        if m["parent_id"] and m["parent_id"] != 0:
            parent = module_dict.get(m["parent_id"])
            if parent:
                parent["children"].append(m)
        else:
            tree.append(m)
    return tree


@router.post("/", response_model=SystemModuleOut)
async def create_module(data: SystemModuleCreate, db: AsyncSession = Depends(get_db)):
    payload = data.dict()
    payload["route"] = payload.get("route") or ""
    if payload["route"] and payload.get("parent_id"):
        existing = await db.execute(
            select(SystemModule).where(
                SystemModule.route == payload["route"],
                SystemModule.parent_id == payload["parent_id"]
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=422, detail=f"Ya existe un módulo con la ruta '{payload['route']}' bajo ese mismo padre.")
    module = SystemModule(**payload)
    db.add(module)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=422, detail="Error de integridad al crear el módulo. Verifica los datos.")
    await db.refresh(module)
    return {"id": module.id, "name": module.name, "route": module.route, "icon": module.icon,
            "parent_id": module.parent_id, "is_active": module.is_active, "children": []}


def _ser_mod(m: SystemModule) -> dict:
    return {"id": m.id, "name": m.name, "route": m.route, "icon": m.icon,
            "parent_id": m.parent_id, "is_active": m.is_active,
            "order_index": m.order_index, "is_sysadmin": m.is_sysadmin, "children": []}


@router.get("/flat/")
async def get_all_modules_flat(
    company_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    role = await db.get(Role, user.role_id)
    is_sysadmin = role and role.is_system

    # Resolver qué company_id usar: parámetro explícito o el del usuario
    effective_company_id = company_id or (user.company_id if not is_sysadmin else None)

    if effective_company_id:
        company = await db.get(Company, effective_company_id)
        if company and company.business_profile_id:
            result = await db.execute(
                select(SystemModule)
                .join(BusinessProfileModule, BusinessProfileModule.module_id == SystemModule.id)
                .where(BusinessProfileModule.business_profile_id == company.business_profile_id)
                .where(SystemModule.is_active == True)
                .order_by(SystemModule.order_index)
            )
            return [_ser_mod(m) for m in result.scalars().all()]

    # SYSADMIN sin empresa seleccionada → todos los módulos
    result = await db.execute(select(SystemModule).order_by(SystemModule.order_index))
    return [_ser_mod(m) for m in result.scalars().all()]


@router.get("/", response_model=list[SystemModuleOut])
async def list_modules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemModule).order_by(SystemModule.order_index))
    return build_tree(result.scalars().all())


@router.get("/{module_id}", response_model=SystemModuleOut)
async def get_module(module_id: int, db: AsyncSession = Depends(get_db)):
    module = await db.get(SystemModule, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return _ser_mod(module)


@router.put("/{module_id}", response_model=SystemModuleOut)
async def update_module(module_id: int, data: SystemModuleUpdate, db: AsyncSession = Depends(get_db)):
    module = await db.get(SystemModule, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(module, key, value)
    await db.commit()
    await db.refresh(module)
    return {"id": module.id, "name": module.name, "route": module.route, "icon": module.icon,
            "parent_id": module.parent_id, "is_active": module.is_active, "children": []}


@router.delete("/{module_id}")
async def delete_module(module_id: int, db: AsyncSession = Depends(get_db)):
    module = await db.get(SystemModule, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    result = await db.execute(select(SystemModule).where(SystemModule.parent_id == module_id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Tiene módulos hijos")

    await db.execute(delete(RoleModule).where(RoleModule.module_id == module_id))
    await db.execute(delete(BusinessProfileModule).where(BusinessProfileModule.module_id == module_id))
    await db.delete(module)
    await db.commit()
    return {"message": "Module deleted"}
