from pydantic import BaseModel


class TecnicoBase(BaseModel):
    nombre: str
    especialidad: str
    telefono: str


class TecnicoCreate(TecnicoBase):
    pass


class TecnicoResponse(TecnicoBase):
    id: int

    class Config:
        from_attributes = True