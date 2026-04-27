from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, Text
from app.database import Base

class BusinessProfile(Base):
    __tablename__ = "business_profiles"

    id                   = Column(Integer, primary_key=True, index=True)
    name                 = Column(String(150), nullable=False)
    description          = Column(String(255), nullable=True)
    is_active            = Column(Boolean, default=True)
    image_url            = Column(String(500), nullable=True)
    landing_description  = Column(Text, nullable=True)
    icon                 = Column(String(100), default="bi-building")
    color_accent         = Column(String(30), default="#0d6efd")


# 🔹 Base
class BusinessProfileBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: Optional[bool] = True
    image_url: Optional[str] = None
    landing_description: Optional[str] = None
    icon: Optional[str] = "bi-building"
    color_accent: Optional[str] = "#0d6efd"


# 🔹 Crear
class BusinessProfileCreate(BusinessProfileBase):
    pass


# 🔹 Update
class BusinessProfileUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    image_url: Optional[str] = None
    landing_description: Optional[str] = None
    icon: Optional[str] = None
    color_accent: Optional[str] = None


# 🔹 Respuesta
class BusinessProfileResponse(BusinessProfileBase):
    id: int

    class Config:
        from_attributes = True


# 🔹 Listado
class BusinessProfileListResponse(BaseModel):
    data: List[BusinessProfileResponse]
    