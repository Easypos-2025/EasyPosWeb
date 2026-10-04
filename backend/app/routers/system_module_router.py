from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, delete, text
from app.models.role_module_model import RoleModule
from app.database import get_db
from app.models.system_module_model import SystemModule
from app.schemas.system_module_schema import SystemModuleCreate, SystemModuleOut, SystemModuleUpdate
from app.models.business_profile_module import BusinessProfileModule
from app.models.company_model import Company
from app.auth.dependencies import get_current_user, require_sysadmin
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
async def create_module(data: SystemModuleCreate, db: AsyncSession = Depends(get_db), _=Depends(require_sysadmin)):
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
async def list_modules(db: AsyncSession = Depends(get_db), _=Depends(require_sysadmin)):
    result = await db.execute(select(SystemModule).order_by(SystemModule.order_index))
    return build_tree(result.scalars().all())


@router.get("/{module_id}", response_model=SystemModuleOut)
async def get_module(module_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_sysadmin)):
    module = await db.get(SystemModule, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return _ser_mod(module)


@router.put("/{module_id}", response_model=SystemModuleOut)
async def update_module(module_id: int, data: SystemModuleUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_sysadmin)):
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
async def toggle_default_child(module_id: int, db: AsyncSession = Depends(get_db), user=Depends(require_sysadmin)):
    """Activa/desactiva is_default_child en un módulo hijo."""
    module = await db.get(SystemModule, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")
    module.is_default_child = not module.is_default_child
    await db.commit()
    return {"module_id": module_id, "is_default_child": module.is_default_child}


@router.get("/{module_id}/defaults-preview/")
async def get_defaults_preview(module_id: int, db: AsyncSession = Depends(get_db), user=Depends(require_sysadmin)):
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


async def _child_ids(db: AsyncSession, module_id: int) -> list[int]:
    """Hijos directos de un módulo: por system_modules.parent_id y por la jerarquía real
    del sidebar (business_profile_modules.parent_id en cualquier perfil)."""
    rows = await db.execute(text("""
        SELECT id FROM system_modules WHERE parent_id = :mid AND id <> :mid
        UNION
        SELECT bpm_c.module_id
        FROM business_profile_modules bpm_c
        JOIN business_profile_modules bpm_p ON bpm_p.id = bpm_c.parent_id
        WHERE bpm_p.module_id = :mid AND bpm_c.module_id <> :mid
    """), {"mid": module_id})
    return [r[0] for r in rows.fetchall()]


async def _module_usage(db: AsyncSession, module_id: int) -> dict:
    prof = await db.execute(text("""
        SELECT DISTINCT bp.id, bp.name
        FROM business_profile_modules bpm
        JOIN business_profiles bp ON bp.id = bpm.business_profile_id
        WHERE bpm.module_id = :mid ORDER BY bp.name
    """), {"mid": module_id})
    roles = await db.execute(text(
        "SELECT COUNT(*) FROM role_modules WHERE module_id = :mid"
    ), {"mid": module_id})
    return {"profiles": [{"id": r.id, "name": r.name} for r in prof.fetchall()],
            "roles": roles.scalar() or 0}


async def _hard_delete(db: AsyncSession, module_id: int):
    await db.execute(delete(RoleModule).where(RoleModule.module_id == module_id))
    await db.execute(delete(BusinessProfileModule).where(BusinessProfileModule.module_id == module_id))
    await db.execute(delete(SystemModule).where(SystemModule.id == module_id))


async def _names(db: AsyncSession, ids: list[int]) -> str:
    if not ids:
        return ""
    rows = await db.execute(select(SystemModule.name).where(SystemModule.id.in_(ids[:10])))
    names = [r[0] for r in rows.fetchall()]
    extra = f" y {len(ids) - 10} más" if len(ids) > 10 else ""
    return ", ".join(names) + extra


@router.get("/{module_id}/delete-preview")
async def delete_preview(module_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_sysadmin)):
    """Qué depende de un módulo antes de eliminarlo: perfiles, roles e hijos (con sus nietos)."""
    module = await db.get(SystemModule, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")

    children = []
    for cid in await _child_ids(db, module_id):
        child = await db.get(SystemModule, cid)
        if not child:
            continue
        usage = await _module_usage(db, cid)
        children.append({
            "id": child.id, "name": child.name, "route": child.route,
            "is_active": child.is_active, **usage,
            "grandchildren": len(await _child_ids(db, cid)),
        })
    children.sort(key=lambda c: (c["name"] or "").lower())

    return {"id": module.id, "name": module.name, "route": module.route,
            **(await _module_usage(db, module_id)), "children": children}


class DeleteBatchIn(BaseModel):
    ids: list[int] = Field(..., min_length=1, max_length=50)


@router.post("/delete-batch")
async def delete_batch(data: DeleteBatchIn, db: AsyncSession = Depends(get_db), _=Depends(require_sysadmin)):
    """Elimina varios módulos en una sola transacción. Si alguno tiene hijos, no elimina ninguno."""
    ids = list(dict.fromkeys(data.ids))
    found = await db.execute(select(SystemModule.id).where(SystemModule.id.in_(ids)))
    found_ids = {r[0] for r in found.fetchall()}
    if len(found_ids) != len(ids):
        raise HTTPException(status_code=404, detail="Uno o más módulos ya no existen. Recargue la lista.")

    for mid in ids:
        pending = [c for c in await _child_ids(db, mid) if c not in ids]
        if pending:
            name = (await db.get(SystemModule, mid)).name
            raise HTTPException(status_code=400, detail=(
                f"No se eliminó nada: \"{name}\" tiene módulos hijos ({await _names(db, pending)}). "
                "Elimínelos o muévalos primero."))

    try:
        # Primero los más profundos: los que no son padres de otros del lote
        remaining = set(ids)
        while remaining:
            leaves = [m for m in remaining
                      if not any(c in remaining for c in await _child_ids(db, m))]
            if not leaves:
                raise HTTPException(status_code=400, detail="Jerarquía circular entre los módulos seleccionados.")
            for mid in leaves:
                await _hard_delete(db, mid)
                remaining.discard(mid)
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="No se pudieron eliminar los módulos: tienen datos relacionados.")
    return {"deleted": len(ids)}


class MoveModuleIn(BaseModel):
    new_parent_id: Optional[int] = None          # None = dejar como padre (raíz)
    add_parent_to_profiles: bool = False         # agregar el nuevo padre a los perfiles donde falte


@router.post("/{module_id}/move")
async def move_module(module_id: int, data: MoveModuleIn,
                      db: AsyncSession = Depends(get_db), _=Depends(require_sysadmin)):
    """Mueve un módulo a otro padre (o a la raíz) en system_modules y en el sidebar de cada perfil."""
    module = await db.get(SystemModule, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")

    new_parent = None
    if data.new_parent_id is not None:
        if data.new_parent_id == module_id:
            raise HTTPException(status_code=400, detail="Un módulo no puede ser su propio padre.")
        new_parent = await db.get(SystemModule, data.new_parent_id)
        if not new_parent:
            raise HTTPException(status_code=404, detail="El nuevo padre no existe.")
        # Evitar ciclos: el nuevo padre no puede ser descendiente del módulo
        seen, stack = set(), [module_id]
        while stack:
            for c in await _child_ids(db, stack.pop()):
                if c == data.new_parent_id:
                    raise HTTPException(status_code=400, detail="El nuevo padre es un hijo de este módulo.")
                if c not in seen:
                    seen.add(c)
                    stack.append(c)

    root_profiles, added_profiles = [], []
    try:
        module.parent_id = data.new_parent_id
        rows = await db.execute(text("""
            SELECT bpm.id, bpm.business_profile_id AS pid, bp.name AS pname
            FROM business_profile_modules bpm
            JOIN business_profiles bp ON bp.id = bpm.business_profile_id
            WHERE bpm.module_id = :mid
        """), {"mid": module_id})
        for r in rows.fetchall():
            parent_bpm = None
            if new_parent:
                found = await db.execute(text("""
                    SELECT id FROM business_profile_modules
                    WHERE business_profile_id = :pid AND module_id = :npid
                    ORDER BY id LIMIT 1
                """), {"pid": r.pid, "npid": new_parent.id})
                parent_bpm = found.scalar()
                if not parent_bpm and data.add_parent_to_profiles:
                    so = await db.execute(text("""
                        SELECT COALESCE(MAX(sort_order), -1) + 1 FROM business_profile_modules
                        WHERE business_profile_id = :pid AND parent_id IS NULL
                    """), {"pid": r.pid})
                    ins = await db.execute(text("""
                        INSERT INTO business_profile_modules (business_profile_id, module_id, parent_id, sort_order)
                        VALUES (:pid, :npid, NULL, :so)
                    """), {"pid": r.pid, "npid": new_parent.id, "so": so.scalar()})
                    parent_bpm = ins.lastrowid
                    # Roles de las empresas del perfil que ven al hijo también deben ver al padre
                    await db.execute(text("""
                        INSERT INTO role_modules (role_id, module_id, can_view, can_create, can_edit, can_delete)
                        SELECT DISTINCT rm.role_id, :npid, 1, 0, 0, 0
                        FROM role_modules rm
                        JOIN roles ro ON ro.id = rm.role_id
                        JOIN companies c ON c.id_company = ro.company_id
                        WHERE rm.module_id = :mid AND c.business_profile_id = :pid
                          AND NOT EXISTS (SELECT 1 FROM role_modules x
                                          WHERE x.role_id = rm.role_id AND x.module_id = :npid)
                    """), {"npid": new_parent.id, "mid": module_id, "pid": r.pid})
                    added_profiles.append(r.pname)
                elif not parent_bpm:
                    root_profiles.append(r.pname)
            await db.execute(text(
                "UPDATE business_profile_modules SET parent_id = :p WHERE id = :id"
            ), {"p": parent_bpm, "id": r.id})
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="No se pudo mover el módulo.")

    return {"moved": module_id, "new_parent_id": data.new_parent_id,
            "root_profiles": root_profiles, "added_parent_profiles": added_profiles}


@router.delete("/{module_id}")
async def delete_module(module_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_sysadmin)):
    module = await db.get(SystemModule, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Módulo no encontrado")

    children = await _child_ids(db, module_id)
    if children:
        raise HTTPException(status_code=400, detail=(
            f"No se puede eliminar: tiene módulos hijos ({await _names(db, children)}). "
            "Elimínelos o muévalos primero."))

    await _hard_delete(db, module_id)
    await db.commit()
    return {"message": "Módulo eliminado"}
