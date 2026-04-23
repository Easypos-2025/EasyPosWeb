from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from sqlalchemy import text
from app.models.business_profile_model import BusinessProfile

from app.schemas.business_profile_schema import (
    BusinessProfileCreate,
    BusinessProfileUpdate,
    BusinessProfileResponse,
    BusinessProfileListResponse
)

from app.auth.dependencies import get_current_user
from sqlalchemy.exc import IntegrityError

router = APIRouter(
    prefix="/business-profiles",
    tags=["Business Profiles"]
)


# 🔹 LISTAR
@router.get("/", response_model=BusinessProfileListResponse)
def get_business_profiles(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    profiles = db.query(BusinessProfile).all()
    return {"data": profiles}


# 🔹 OBTENER POR ID
@router.get("/{profile_id}", response_model=BusinessProfileResponse)
def get_business_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    profile = db.query(BusinessProfile).filter(BusinessProfile.id == profile_id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    return profile


# 🔹 CREAR
@router.post("/", response_model=BusinessProfileResponse)
def create_business_profile(
    data: BusinessProfileCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    new_profile = BusinessProfile(**data.dict())

    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    return new_profile


# 🔹 ACTUALIZAR
@router.put("/{profile_id}", response_model=BusinessProfileResponse)
def update_business_profile(
    profile_id: int,
    data: BusinessProfileUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    profile = db.query(BusinessProfile).filter(BusinessProfile.id == profile_id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(profile, key, value)

    db.commit()
    db.refresh(profile)

    return profile


# 🔹 ELIMINAR (soft opcional luego)
@router.delete("/{profile_id}")
def delete_business_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    profile = db.query(BusinessProfile).filter(BusinessProfile.id == profile_id).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    db.delete(profile)
    db.commit()

    return {"message": "Perfil eliminado correctamente"}


# 🔹 OBTENER MÓDULOS DE UN PERFIL
@router.get("/{profile_id}/modules/")
def get_modules_by_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    results = db.execute(
        text("""
            SELECT sm.id, sm.name
            FROM system_modules sm
            JOIN business_profile_modules bpm
                ON bpm.module_id = sm.id
            WHERE bpm.business_profile_id = :profile_id
        """),
        {"profile_id": profile_id}
    ).fetchall()

    return [
        {
            "id": r.id,
            "name": r.name
        }
        for r in results
    ]


# 🔹 ASIGNAR MÓDULOS A UN PERFIL


@router.post("/{profile_id}/modules/")
def assign_modules_to_profile(
    profile_id: int,
    module_ids: list[int],
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    try:
        # 🔥 eliminar relaciones existentes
        db.execute(
            text("""
                DELETE FROM business_profile_modules
                WHERE business_profile_id = :profile_id
            """),
            {"profile_id": profile_id}
        )

        # 🔥 insertar módulos + hijos SIN duplicar
        db.execute(
            text("""
                INSERT INTO business_profile_modules (
                    business_profile_id,
                    module_id,
                    parent_id,
                    sort_order
                )
                SELECT DISTINCT
                    :profile_id,
                    sm.id,
                    sm.parent_id,
                    0
                FROM system_modules sm
                WHERE sm.id IN :module_ids
                   OR (
                        sm.parent_id IN :module_ids
                        AND sm.id NOT IN :module_ids
                   )
            """),
            {
                "profile_id": profile_id,
                "module_ids": tuple(module_ids)
            }
        )

        db.commit()

        return {"message": "Módulos asignados correctamente"}

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Ya existen módulos duplicados para este perfil"
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al asignar módulos: {str(e)}"
        )

        