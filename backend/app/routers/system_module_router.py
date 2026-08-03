from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, delete, text
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


@router.get("/defaults-tree/")
async def get_defaults_tree(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """Árbol padre→hijos basado en relaciones reales de business_profile_modules.
    Muestra cualquier módulo que haya sido colocado bajo un padre en algún perfil,
    independientemente de la jerarquía global de system_modules.parent_id."""
    rows = await db.execute(text("""
        SELECT
            sm_p.id         AS parent_id,
            sm_p.name       AS parent_name,
            sm_p.icon       AS parent_icon,
            sm_p.route      AS parent_route,
            sm_c.id         AS child_id,
            sm_c.name       AS child_name,
            sm_c.icon       AS child_icon,
            sm_c.route      AS child_route,
            sm_c.is_default_child AS is_default_child,
            pc.profile_count      AS profile_count
        FROM (
            SELECT DISTINCT bpm_p.module_id AS parent_mid, bpm_c.module_id AS child_mid
            FROM business_profile_modules bpm_c
            JOIN business_profile_modules bpm_p ON bpm_p.id = bpm_c.parent_id
        ) pairs
        JOIN system_modules sm_p ON sm_p.id = pairs.parent_mid AND sm_p.is_active = 1
        JOIN system_modules sm_c ON sm_c.id = pairs.child_mid  AND sm_c.is_active = 1
        JOIN (
            SELECT module_id, COUNT(DISTINCT business_profile_id) AS profile_count
            FROM business_profile_modules GROUP BY module_id
        ) pc ON pc.module_id = pairs.parent_mid
        ORDER BY sm_p.order_index, sm_p.id, sm_c.id
    """))

    parents: dict = {}
    for r in rows.fetchall():
        pid = r.parent_id
        if pid not in parents:
            parents[pid] = {
                "id": pid,
                "name": r.parent_name,
                "icon": r.parent_icon,
                "route": r.parent_route,
                "profile_count": r.profile_count,
                "children": [],
            }
        parents[pid]["children"].append({
            "id": r.child_id,
            "name": r.child_name,
            "icon": r.child_icon,
            "route": r.child_route,
            "is_default_child": bool(r.is_default_child),
        })
    return list(parents.values())


@router.patch("/{module_id}/toggle-default")
async def toggle_default_child(module_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """Activa/desactiva is_default_child en un módulo hijo."""
    module = await db.get(SystemModule, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")
    module.is_default_child = not module.is_default_child
    await db.commit()
    return {"module_id": module_id, "is_default_child": module.is_default_child}


@router.get("/{module_id}/defaults-preview/")
async def get_defaults_preview(module_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """Retorna los hijos default (is_default_child=1) que han sido asignados bajo este padre
    en al menos un perfil. Usa relaciones reales de BPM, no system_modules.parent_id."""
    rows = await db.execute(text("""
        SELECT DISTINCT sm.id, sm.name, sm.route
        FROM system_modules sm
        JOIN business_profile_modules bpm_c ON bpm_c.module_id = sm.id
        JOIN business_profile_modules bpm_p ON bpm_p.id = bpm_c.parent_id
        WHERE bpm_p.module_id = :parent_id
          AND sm.is_default_child = 1
          AND sm.is_active = 1
    """), {"parent_id": module_id})
    return [{"id": r.id, "name": r.name, "route": r.route} for r in rows.fetchall()]


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
