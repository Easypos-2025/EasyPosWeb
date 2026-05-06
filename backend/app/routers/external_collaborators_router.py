from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.external_collaborator_model import ExternalCollaborator
from app.auth.dependencies import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/external-collaborators", tags=["ExternalCollaborators"])


def _ser(c: ExternalCollaborator):
    return {
        "id": c.id, "company_id": c.company_id, "nombre": c.nombre,
        "dni": c.dni, "empresa": c.empresa, "telefono": c.telefono,
        "email": c.email, "notas": c.notas, "is_active": c.is_active,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


@router.get("/")
async def list_collaborators(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ExternalCollaborator)
        .where(ExternalCollaborator.company_id == current_user.company_id, ExternalCollaborator.is_active == 1)
        .order_by(ExternalCollaborator.nombre)
    )
    return [_ser(c) for c in result.scalars().all()]


@router.post("/")
async def create_collaborator(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    nombre = (data.get("nombre") or "").strip()
    dni    = (data.get("dni")    or "").strip()
    if not nombre:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")
    if not dni:
        raise HTTPException(status_code=400, detail="El DNI es obligatorio")

    result = await db.execute(
        select(ExternalCollaborator).where(
            ExternalCollaborator.company_id == current_user.company_id,
            ExternalCollaborator.dni == dni
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Ya existe un colaborador con DNI '{dni}'")

    item = ExternalCollaborator(
        company_id=current_user.company_id,
        nombre=nombre, dni=dni,
        empresa=(data.get("empresa")  or "").strip() or None,
        telefono=(data.get("telefono") or "").strip() or None,
        email=(data.get("email")    or "").strip() or None,
        notas=(data.get("notas")    or "").strip() or None,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return _ser(item)


@router.put("/{collab_id}")
async def update_collaborator(
    collab_id: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ExternalCollaborator).where(
            ExternalCollaborator.id == collab_id,
            ExternalCollaborator.company_id == current_user.company_id
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Colaborador no encontrado")

    nombre = (data.get("nombre") or "").strip()
    if not nombre:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    item.nombre   = nombre
    item.dni      = (data.get("dni")      or item.dni).strip()
    item.empresa  = (data.get("empresa")  or "").strip() or None
    item.telefono = (data.get("telefono") or "").strip() or None
    item.email    = (data.get("email")    or "").strip() or None
    item.notas    = (data.get("notas")    or "").strip() or None
    item.is_active = int(data.get("is_active", item.is_active))
    await db.commit()
    await db.refresh(item)
    return _ser(item)


@router.delete("/{collab_id}")
async def delete_collaborator(
    collab_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ExternalCollaborator).where(
            ExternalCollaborator.id == collab_id,
            ExternalCollaborator.company_id == current_user.company_id
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Colaborador no encontrado")

    from app.models.loan_model import Loan
    active = await db.execute(
        select(Loan).where(
            Loan.external_collaborator_id == collab_id,
            Loan.estado.in_(["pendiente_confirmacion", "activo", "retorno_pendiente"])
        )
    )
    if active.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Colaborador tiene préstamos activos")

    await db.delete(item)
    await db.commit()
    return {"message": "Colaborador eliminado"}
