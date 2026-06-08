from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, text
from app.database import get_db
from app.models.business_profile_module import BusinessProfileModule
from app.models.system_module_model import SystemModule
from app.auth.dependencies import get_current_user

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

    await db.commit()
    return {"message": "Módulo agregado correctamente"}
