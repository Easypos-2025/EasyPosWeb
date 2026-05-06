from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.language_model import Language

router = APIRouter(prefix="/languages", tags=["Languages"])


@router.get("/")
async def get_languages(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Language).order_by(Language.name))
    return result.scalars().all()
