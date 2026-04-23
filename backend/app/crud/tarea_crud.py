from sqlalchemy.orm import Session
from app.models.tarea import Tarea


def obtener_tareas(db: Session):
    return db.query(Tarea).all()


def crear_tarea(db: Session, tarea):
    nueva = Tarea(**tarea.dict())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva
