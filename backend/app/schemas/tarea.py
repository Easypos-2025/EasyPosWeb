from pydantic import BaseModel
from datetime import datetime


class TareaBase(BaseModel):

    titulo: str
    descripcion: str
    costo: float
    fecha_inicio: datetime
    fecha_entrega: datetime
    fecha_finalizacion: datetime | None = None
    estado: str
    tecnico_id: int


class TareaCreate(TareaBase):
    pass


class TareaResponse(TareaBase):
    id: int
    fecha_inicio: datetime

    class Config:
        from_attributes = True

def calcular_estado(tarea):

    if tarea.fecha_finalizacion:
        return "finalizada"

    if tarea.fecha_entrega < datetime.utcnow():
        return "atrasada"

    return "pendiente"