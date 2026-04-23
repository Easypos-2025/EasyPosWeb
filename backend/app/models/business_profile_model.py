from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base

class BusinessProfile(Base):
    __tablename__ = "business_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    

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
    