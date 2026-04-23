from pydantic import BaseModel
from typing import Optional, List


# 🔹 Base
class BusinessProfileBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: Optional[bool] = True


# 🔹 Crear
class BusinessProfileCreate(BusinessProfileBase):
    pass


# 🔹 Update
class BusinessProfileUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


# 🔹 Respuesta
class BusinessProfileResponse(BusinessProfileBase):
    id: int

    class Config:
        from_attributes = True


# 🔹 Listado
class BusinessProfileListResponse(BaseModel):
    data: List[BusinessProfileResponse]