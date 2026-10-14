from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.business_profile_model import BusinessProfile
from app.schemas.business_profile_schema import (
    BusinessProfileCreate, BusinessProfileUpdate,
    BusinessProfileResponse, BusinessProfileListResponse
)
from app.auth.dependencies import get_current_user, require_sysadmin

router = APIRouter(prefix="/business-profiles", tags=["Business Profiles"])


@router.get("/", response_model=BusinessProfileListResponse)
async def get_business_profiles(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(BusinessProfile).order_by(BusinessProfile.name))
    return {"data": result.scalars().all()}


@router.get("/{profile_id}", response_model=BusinessProfileResponse)
async def get_business_profile(profile_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(BusinessProfile).where(BusinessProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return profile


@router.post("/", response_model=BusinessProfileResponse)
async def create_business_profile(data: BusinessProfileCreate, db: AsyncSession = Depends(get_db), user=Depends(require_sysadmin)):
    new_profile = BusinessProfile(**data.dict())
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)
    return new_profile


@router.put("/{profile_id}", response_model=BusinessProfileResponse)
async def update_business_profile(profile_id: int, data: BusinessProfileUpdate, db: AsyncSession = Depends(get_db), user=Depends(require_sysadmin)):
    result = await db.execute(select(BusinessProfile).where(BusinessProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(profile, key, value)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.delete("/{profile_id}")
async def delete_business_profile(profile_id: int, db: AsyncSession = Depends(get_db), user=Depends(require_sysadmin)):
    result = await db.execute(select(BusinessProfile).where(BusinessProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    await db.delete(profile)
    await db.commit()
    return {"message": "Perfil eliminado correctamente"}


@router.get("/{profile_id}/modules/")
async def get_modules_by_profile(profile_id: int, db: AsyncSession = Depends(get_db), user=Depends(require_sysadmin)):
    result = await db.execute(text("""
        SELECT sm.id, sm.name FROM system_modules sm
        JOIN business_profile_modules bpm ON bpm.module_id = sm.id
        WHERE bpm.business_profile_id = :profile_id
    """), {"profile_id": profile_id})
    return [{"id": r.id, "name": r.name} for r in result.fetchall()]


@router.post("/{profile_id}/modules/")
async def assign_modules_to_profile(profile_id: int, module_ids: list[int], db: AsyncSession = Depends(get_db), user=Depends(require_sysadmin)):
    """Asigna módulos al perfil de forma no-destructiva: solo agrega los nuevos y elimina los quitados,
    preservando parent_id, sort_order y display_name de los módulos que permanecen.
    Los módulos nuevos se ubican en el menú del perfil bajo su padre del catálogo (system_modules.parent_id)
    cuando ese padre también queda en el perfil; si no, quedan en la raíz."""
    if not await db.get(BusinessProfile, profile_id):
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    new_ids = set(module_ids)
    # Catálogo completo: valida los ids recibidos y da la jerarquía global
    cat_rows = (await db.execute(text("SELECT id, parent_id, order_index FROM system_modules"))).fetchall()
    catalog = {r.id: r for r in cat_rows}
    if new_ids - catalog.keys():
        raise HTTPException(status_code=400, detail="Uno o más módulos no existen")

    try:
        current_result = await db.execute(
            text("SELECT id, module_id, parent_id FROM business_profile_modules WHERE business_profile_id = :pid"),
            {"pid": profile_id}
        )
        current = {row.module_id: row for row in current_result.fetchall()}
        current_ids = set(current)

        # Eliminar solo los que se quitaron; sus hijos en el menú suben al padre del eliminado
        to_remove = current_ids - new_ids
        for mid in to_remove:
            bpm = current[mid]
            await db.execute(
                text("UPDATE business_profile_modules SET parent_id = :np WHERE parent_id = :bid"),
                {"np": bpm.parent_id, "bid": bpm.id}
            )
            await db.execute(
                text("DELETE FROM business_profile_modules WHERE id = :bid"),
                {"bid": bpm.id}
            )

        to_add = new_ids - current_ids
        if to_add:
            # module_id → bpm.id de lo que queda en el perfil (para colgar los nuevos de su padre)
            bpm_of = {mid: current[mid].id for mid in current_ids - to_remove}

            def depth(mid):
                d, seen = 0, set()
                while catalog[mid].parent_id in catalog and mid not in seen:
                    seen.add(mid)
                    mid = catalog[mid].parent_id
                    d += 1
                return d

            # Padres antes que hijos, y dentro de cada nivel en el orden del catálogo
            for mid in sorted(to_add, key=lambda m: (depth(m), catalog[m].order_index or 0, m)):
                parent_bpm = bpm_of.get(catalog[mid].parent_id)
                so = await db.execute(text("""
                    SELECT COALESCE(MAX(sort_order), -1) + 1 FROM business_profile_modules
                    WHERE business_profile_id = :pid AND parent_id <=> :par
                """), {"pid": profile_id, "par": parent_bpm})
                ins = await db.execute(text("""
                    INSERT INTO business_profile_modules (business_profile_id, module_id, parent_id, sort_order)
                    VALUES (:pid, :mid, :par, :so)
                """), {"pid": profile_id, "mid": mid, "par": parent_bpm, "so": so.scalar()})
                bpm_of[mid] = ins.lastrowid

            # Auto-permisos can_view para roles del perfil solo en los módulos nuevos
            for mid in to_add:
                await db.execute(text("""
                    INSERT INTO role_modules (role_id, module_id, can_view, can_create, can_edit, can_delete)
                    SELECT DISTINCT r.id, :mid, 1, 0, 0, 0
                    FROM roles r
                    JOIN companies c ON c.id_company = r.company_id
                    WHERE c.business_profile_id = :pid
                      AND NOT EXISTS (SELECT 1 FROM role_modules rm2 WHERE rm2.role_id = r.id AND rm2.module_id = :mid)
                """), {"pid": profile_id, "mid": mid})

        await db.commit()
        return {"message": "Módulos asignados correctamente", "added": len(to_add), "removed": len(to_remove)}
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Ya existen módulos duplicados para este perfil")
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="No se pudieron asignar los módulos. Intente de nuevo.")
