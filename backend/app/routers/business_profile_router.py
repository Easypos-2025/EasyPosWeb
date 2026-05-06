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
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/business-profiles", tags=["Business Profiles"])


@router.get("/", response_model=BusinessProfileListResponse)
async def get_business_profiles(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(BusinessProfile))
    return {"data": result.scalars().all()}


@router.get("/{profile_id}", response_model=BusinessProfileResponse)
async def get_business_profile(profile_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(BusinessProfile).where(BusinessProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return profile


@router.post("/", response_model=BusinessProfileResponse)
async def create_business_profile(data: BusinessProfileCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    new_profile = BusinessProfile(**data.dict())
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)
    return new_profile


@router.put("/{profile_id}", response_model=BusinessProfileResponse)
async def update_business_profile(profile_id: int, data: BusinessProfileUpdate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
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
async def delete_business_profile(profile_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(BusinessProfile).where(BusinessProfile.id == profile_id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    await db.delete(profile)
    await db.commit()
    return {"message": "Perfil eliminado correctamente"}


@router.get("/{profile_id}/modules/")
async def get_modules_by_profile(profile_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(text("""
        SELECT sm.id, sm.name FROM system_modules sm
        JOIN business_profile_modules bpm ON bpm.module_id = sm.id
        WHERE bpm.business_profile_id = :profile_id
    """), {"profile_id": profile_id})
    return [{"id": r.id, "name": r.name} for r in result.fetchall()]


@router.post("/{profile_id}/modules/")
async def assign_modules_to_profile(profile_id: int, module_ids: list[int], db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    try:
        await db.execute(text("DELETE FROM business_profile_modules WHERE business_profile_id = :profile_id"), {"profile_id": profile_id})
        if module_ids:
            await db.execute(text("""
                INSERT INTO business_profile_modules (business_profile_id, module_id, parent_id, sort_order)
                SELECT DISTINCT :profile_id, sm.id, NULL, 0
                FROM system_modules sm WHERE sm.id IN :module_ids
            """), {"profile_id": profile_id, "module_ids": tuple(module_ids)})
            await db.execute(text("""
                INSERT INTO role_modules (role_id, module_id, can_view, can_create, can_edit, can_delete)
                SELECT DISTINCT r.id, bpm.module_id, 1, 0, 0, 0
                FROM roles r
                JOIN companies c ON c.id_company = r.company_id
                JOIN business_profile_modules bpm ON bpm.business_profile_id = c.business_profile_id
                JOIN system_modules sm ON sm.id = bpm.module_id AND sm.is_active = 1
                WHERE c.business_profile_id = :profile_id
                  AND NOT EXISTS (SELECT 1 FROM role_modules rm2 WHERE rm2.role_id = r.id AND rm2.module_id = bpm.module_id)
            """), {"profile_id": profile_id})
        await db.commit()
        return {"message": "Módulos asignados correctamente"}
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Ya existen módulos duplicados para este perfil")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al asignar módulos: {str(e)}")
