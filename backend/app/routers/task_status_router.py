from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.task_status_model import TaskStatus

router = APIRouter(prefix="/task-status", tags=["Task Status"])


@router.post("/")
async def create_status(name: str, description: str, db: AsyncSession = Depends(get_db)):
    new_status = TaskStatus(name=name, description=description)
    db.add(new_status)
    await db.commit()
    await db.refresh(new_status)
    return new_status


@router.get("/")
async def get_status_list(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskStatus))
    return result.scalars().all()


@router.get("/{status_id}")
async def get_status(status_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskStatus).where(TaskStatus.id == status_id))
    status = result.scalar_one_or_none()
    if not status:
        return {"error": "Status not found"}
    return status


@router.put("/{status_id}")
async def update_status(status_id: int, name: str, description: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskStatus).where(TaskStatus.id == status_id))
    status = result.scalar_one_or_none()
    if not status:
        return {"error": "Status not found"}
    status.name = name
    status.description = description
    await db.commit()
    return status


@router.delete("/{status_id}")
async def delete_status(status_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskStatus).where(TaskStatus.id == status_id))
    status = result.scalar_one_or_none()
    if not status:
        return {"error": "Status not found"}
    await db.delete(status)
    await db.commit()
    return {"message": "Status deleted"}
