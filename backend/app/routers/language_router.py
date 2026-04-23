from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.language_model import Language

router = APIRouter(prefix="/languages", tags=["Languages"])


@router.get("/")
def get_languages(db: Session = Depends(get_db)):
    
    return db.query(Language).order_by(Language.name).all()

