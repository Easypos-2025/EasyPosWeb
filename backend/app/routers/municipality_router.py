from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.municipalities_model import Municipality

router = APIRouter(prefix="/municipalities", tags=["Municipalities"])


@router.get("/")
def get_municipalities(db: Session = Depends(get_db)):
   
    return db.query(Municipality).order_by(Municipality.name).all()