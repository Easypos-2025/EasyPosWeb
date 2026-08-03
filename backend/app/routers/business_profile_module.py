from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, text
from app.database import get_db
from app.models.business_profile_module import BusinessProfileModule
from app.models.system_module_model import SystemModule
from app.auth.dependencies import get_current_user

async def _insert_role_permissions(db: AsyncSession, module_id: int, profile_id: int):
    """Inserta can_view=1 en role_modules para todos los roles del perfil que no lo tengan."""
    await db.execute(text("""
        INSERT INTO role_modules (role_id, module_id, can_view, can_create, can_edit, can_delete)
        SELECT DISTINCT r.id, :module_id, 1, 0, 0, 0
        FROM roles r
        JOIN companies c ON c.id_company = r.company_id
        WHERE c.business_profile_id = :profile_id
          AND NOT EXISTS (
              SELECT 1 FROM role_modules rm2
              WHERE rm2.role_id = r.id AND rm2.module_id = :module_id
          )
    """), {"module_id": module_id, "profile_id": profile_id})

router = APIRouter(prefix="/business-profile-module", tags=["BusinessProfileModule"])


@router.put("/reorder/")
async def reorder_modules(data: list[dict], db: AsyncSession = Depends(get_db)):
    if not data:
        return {"message": "Sin datos"}

    result = await db.execute(select(BusinessProfileModule).where(BusinessProfileModule.id == data[0]["id"]))
    first = result.scalar_one_or_none()

    if first:
        keep_ids = [item["id"] for item in data]
        await db.execute(
            delete(BusinessProfileModule).where(
                BusinessProfileModule.business_profile_id == first.business_profile_id,
                BusinessProfileModule.id.notin_(keep_ids)
            )
        )

    for item in data:
        result = await db.execute(select(BusinessProfileModule).where(BusinessProfileModule.id == item["id"]))
        module = result.scalar_one_or_none()
        if module:
            module.sort_order = item["sort_order"]
            module.parent_id = int(item["parent_id"]) if item.get("parent_id") is not None else None

    await db.commit()
    return {"message": "Orden actualizado correctamente"}


@router.get("/available-modules/{profile_id}")
async def get_available_modules(
    profile_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    """Retorna los system_modules activos que aún NO están en el perfil dado."""
    assigned = await db.execute(
        select(BusinessProfileModule.module_id).where(
            BusinessProfileModule.business_profile_id == profile_id
        )
    )
    assigned_ids = {r[0] for r in assigned.fetchall()}

    all_mods = await db.execute(
        select(SystemModule).where(SystemModule.is_active == 1).order_by(SystemModule.id)
    )
    return [
        {"id": m.id, "name": m.name, "route": m.route}
        for m in all_mods.scalars().all()
        if m.id not in assigned_ids
    ]


@router.delete("/{bpm_id}")
async def remove_module_from_profile(
    bpm_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    bpm = await db.get(BusinessProfileModule, bpm_id)
    if not bpm:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    # Reasignar hijos al padre del módulo eliminado para no romper jerarquía
    await db.execute(
        text("UPDATE business_profile_modules SET parent_id = :new_parent WHERE parent_id = :bpm_id"),
        {"new_parent": bpm.parent_id, "bpm_id": bpm_id}
    )
    await db.delete(bpm)
    await db.commit()
    return {"message": "Módulo eliminado del perfil"}


@router.patch("/{bpm_id}")
async def update_module_assignment(
    bpm_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    bpm = await db.get(BusinessProfileModule, bpm_id)
    if not bpm:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    if "parent_id" in data:
        new_parent = data["parent_id"]
        if new_parent is not None:
            # Verificar que el padre pertenece al mismo perfil
            parent = await db.get(BusinessProfileModule, new_parent)
            if not parent or parent.business_profile_id != bpm.business_profile_id:
                raise HTTPException(status_code=400, detail="El padre no pertenece al mismo perfil")
            # Evitar ciclo: el nuevo padre no puede ser un descendiente del nodo
            if new_parent == bpm_id:
                raise HTTPException(status_code=400, detail="Un módulo no puede ser su propio padre")
        bpm.parent_id = new_parent

    if "display_name" in data:
        bpm.display_name = data["display_name"] or None

    await db.commit()
    return {"message": "Asignación actualizada"}


@router.post("/add-module/")
async def add_module_to_profile(
    data: dict,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    profile_id = data.get("profile_id")
    module_id = data.get("module_id")
    parent_id = data.get("parent_id") or None
    display_name = data.get("display_name") or None

    if not profile_id or not module_id:
        raise HTTPException(status_code=400, detail="profile_id y module_id son requeridos")

    existing = await db.execute(
        select(BusinessProfileModule).where(
            BusinessProfileModule.business_profile_id == profile_id,
            BusinessProfileModule.module_id == module_id
        )
    )
    if existing.scalar_one_or_none():
        sm = await db.get(SystemModule, module_id)
        label = sm.name if sm else f"#{module_id}"
        raise HTTPException(status_code=400, detail=f"El módulo '{label}' ya está asignado a este perfil")

    max_res = await db.execute(
        select(func.max(BusinessProfileModule.sort_order)).where(
            BusinessProfileModule.business_profile_id == profile_id,
            BusinessProfileModule.parent_id == parent_id
        )
    )
    next_order = (max_res.scalar() or 0) + 1

    new_bpm = BusinessProfileModule(
        business_profile_id=profile_id,
        module_id=module_id,
        parent_id=parent_id,
        sort_order=next_order,
        display_name=display_name
    )
    db.add(new_bpm)

    await _insert_role_permissions(db, module_id, profile_id)

    await db.commit()
    return {"message": "Módulo agregado correctamente"}


@router.post("/add-parent-with-defaults/")
async def add_parent_with_defaults(
    data: dict,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    """Agrega un padre + todos sus hijos is_default_child=1 al perfil en un solo call.
    No destructivo: si el padre o algún hijo ya existen en el perfil, se omiten."""
    profile_id = data.get("profile_id")
    parent_module_id = data.get("module_id")
    display_name = data.get("display_name") or None

    if not profile_id or not parent_module_id:
        raise HTTPException(status_code=400, detail="profile_id y module_id son requeridos")

    added: list[int] = []
    skipped: list[int] = []

    # 1. Agregar el padre si no existe
    existing_parent_res = await db.execute(
        select(BusinessProfileModule).where(
            BusinessProfileModule.business_profile_id == profile_id,
            BusinessProfileModule.module_id == parent_module_id
        )
    )
    parent_bpm = existing_parent_res.scalar_one_or_none()

    if not parent_bpm:
        max_res = await db.execute(
            select(func.max(BusinessProfileModule.sort_order)).where(
                BusinessProfileModule.business_profile_id == profile_id,
                BusinessProfileModule.parent_id == None
            )
        )
        parent_bpm = BusinessProfileModule(
            business_profile_id=profile_id,
            module_id=parent_module_id,
            parent_id=None,
            sort_order=(max_res.scalar() or 0) + 1,
            display_name=display_name
        )
        db.add(parent_bpm)
        await db.flush()
        added.append(parent_module_id)
        await _insert_role_permissions(db, parent_module_id, profile_id)
    else:
        skipped.append(parent_module_id)

    # 2. Obtener hijos default via relaciones reales de BPM (no system_modules.parent_id)
    children_res = await db.execute(text("""
        SELECT DISTINCT sm.id AS id
        FROM system_modules sm
        JOIN business_profile_modules bpm_c ON bpm_c.module_id = sm.id
        JOIN business_profile_modules bpm_p ON bpm_p.id = bpm_c.parent_id
        WHERE bpm_p.module_id = :parent_mid
          AND sm.is_default_child = 1
          AND sm.is_active = 1
    """), {"parent_mid": parent_module_id})
    default_children = [await db.get(SystemModule, r.id) for r in children_res.fetchall()]
    default_children = [c for c in default_children if c]

    # 3. Agregar cada hijo default si no existe ya en el perfil
    for child in default_children:
        existing_child_res = await db.execute(
            select(BusinessProfileModule).where(
                BusinessProfileModule.business_profile_id == profile_id,
                BusinessProfileModule.module_id == child.id
            )
        )
        if existing_child_res.scalar_one_or_none():
            skipped.append(child.id)
            continue

        max_child_res = await db.execute(
            select(func.max(BusinessProfileModule.sort_order)).where(
                BusinessProfileModule.business_profile_id == profile_id,
                BusinessProfileModule.parent_id == parent_bpm.id
            )
        )
        db.add(BusinessProfileModule(
            business_profile_id=profile_id,
            module_id=child.id,
            parent_id=parent_bpm.id,
            sort_order=(max_child_res.scalar() or 0) + 1,
        ))
        added.append(child.id)
        await _insert_role_permissions(db, child.id, profile_id)

    await db.commit()
    return {
        "added": added,
        "skipped": skipped,
        "message": f"Agregados {len(added)} módulos, {len(skipped)} ya existían"
    }


@router.post("/propagate-default-child/")
async def propagate_default_child(
    data: dict,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    """Inserta un hijo default en todos los perfiles que ya tienen su padre.
    Completamente no destructivo: solo agrega donde falta, nunca elimina."""
    child_module_id = data.get("child_module_id")
    if not child_module_id:
        raise HTTPException(status_code=400, detail="child_module_id es requerido")

    child_module = await db.get(SystemModule, child_module_id)
    if not child_module:
        raise HTTPException(status_code=404, detail="Módulo hijo no encontrado")

    # parent_module_id explícito (desde el botón Propagar Todos) o fallback a system_modules.parent_id
    parent_module_id = data.get("parent_module_id") or child_module.parent_id
    if not parent_module_id:
        raise HTTPException(status_code=400, detail="No se pudo determinar el padre del módulo")

    # Todos los BPM donde el padre está asignado
    parent_bpms_res = await db.execute(
        select(BusinessProfileModule).where(
            BusinessProfileModule.module_id == parent_module_id
        )
    )
    parent_bpms = parent_bpms_res.scalars().all()

    propagated = 0
    skipped = 0

    for parent_bpm in parent_bpms:
        profile_id = parent_bpm.business_profile_id

        # ¿Ya existe el hijo en este perfil?
        existing_res = await db.execute(
            select(BusinessProfileModule).where(
                BusinessProfileModule.business_profile_id == profile_id,
                BusinessProfileModule.module_id == child_module_id
            )
        )
        if existing_res.scalar_one_or_none():
            skipped += 1
            continue

        max_res = await db.execute(
            select(func.max(BusinessProfileModule.sort_order)).where(
                BusinessProfileModule.business_profile_id == profile_id,
                BusinessProfileModule.parent_id == parent_bpm.id
            )
        )
        db.add(BusinessProfileModule(
            business_profile_id=profile_id,
            module_id=child_module_id,
            parent_id=parent_bpm.id,
            sort_order=(max_res.scalar() or 0) + 1,
        ))
        propagated += 1
        await _insert_role_permissions(db, child_module_id, profile_id)

    await db.commit()
    return {
        "propagated": propagated,
        "skipped": skipped,
        "message": f"Propagado a {propagated} perfil(es). {skipped} ya lo tenían."
    }
