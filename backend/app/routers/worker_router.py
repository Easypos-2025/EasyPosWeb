from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.worker_model import Worker
from app.models.task_model import Task
from app.auth.dependencies import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/workers", tags=["Workers"])


def _ser(w: Worker):
    return {
        "id":              w.id,
        "name":            w.name,
        "profession_id":   w.profession_id,
        "profession_name": w.profession.name if w.profession else None,
        "phone":           w.phone,
    }


@router.get("/")
async def get_workers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Worker).order_by(Worker.name))
    return [_ser(w) for w in result.scalars().all()]


@router.post("/")
async def create_worker(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    w = Worker(
        name=          name,
        profession_id= data.get("profession_id") or None,
        phone=         (data.get("phone") or "").strip() or None,
    )
    db.add(w)
    await db.commit()
    await db.refresh(w)
    return _ser(w)


@router.put("/{worker_id}")
async def update_worker(
    worker_id: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Worker).where(Worker.id == worker_id))
    w = result.scalar_one_or_none()
    if not w:
        raise HTTPException(status_code=404, detail="Ejecutor no encontrado")

    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    w.name          = name
    w.profession_id = data.get("profession_id") or None
    w.phone         = (data.get("phone") or "").strip() or None
    await db.commit()
    await db.refresh(w)
    return _ser(w)


@router.delete("/{worker_id}")
async def delete_worker(
    worker_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Worker).where(Worker.id == worker_id))
    w = result.scalar_one_or_none()
    if not w:
        raise HTTPException(status_code=404, detail="Ejecutor no encontrado")

    tareas = (await db.execute(
        select(func.count()).select_from(Task).where(Task.worker_id == worker_id)
    )).scalar()
    if tareas > 0:
        raise HTTPException(
            status_code=409,
            detail=f"No se puede eliminar: el ejecutor tiene {tareas} tarea(s) asignada(s)"
        )

    await db.delete(w)
    await db.commit()
    return {"message": "Ejecutor eliminado"}
