from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.type_currency_model import TypeCurrency

router = APIRouter(prefix="/type-currencies", tags=["TypeCurrencies"])


@router.get("/")
async def get_currencies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TypeCurrency).order_by(TypeCurrency.name))
    return result.scalars().all()
