from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.municipalities_model import Municipality

router = APIRouter(prefix="/municipalities", tags=["Municipalities"])


@router.get("/")
async def get_municipalities(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Municipality).order_by(Municipality.name))
    return result.scalars().all()
