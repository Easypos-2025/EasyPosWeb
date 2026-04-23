from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.country_model import Country

router = APIRouter(prefix="/countries", tags=["Countries"])


@router.get("/")
def get_countries(db: Session = Depends(get_db)):
    
    return db.query(Country).order_by(Country.name).all()