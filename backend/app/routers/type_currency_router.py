from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.type_currency_model import TypeCurrency

router = APIRouter(prefix="/type-currencies", tags=["TypeCurrencies"])


@router.get("/")
def get_currencies(db: Session = Depends(get_db)):
    
    return db.query(TypeCurrency).order_by(TypeCurrency.name).all()