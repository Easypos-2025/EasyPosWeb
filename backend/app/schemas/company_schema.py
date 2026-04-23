from pydantic import BaseModel
from typing import Optional


# =========================================
# BASE
# =========================================

class CompanyBase(BaseModel):
    name: str
    identification_number: str
    dv: Optional[str] = None

    language_id: Optional[int] = None
    country_id: Optional[int] = None
    department_id: Optional[int] = None
    municipality_id: Optional[int] = None
    type_currency_id: Optional[int] = None

    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

    password: Optional[str] = None
    user_name: Optional[str] = None

    description: Optional[str] = None

    # 🔥 IMPORTANTE: asegurar tipo correcto
    state: Optional[int] = 1

    business_profile_id: Optional[int] = None


# =========================================
# CREATE
# =========================================

class CompanyCreate(CompanyBase):
    pass


# =========================================
# UPDATE
# =========================================

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    identification_number: Optional[str] = None
    dv: Optional[str] = None

    language_id: Optional[int] = None
    country_id: Optional[int] = None
    department_id: Optional[int] = None
    municipality_id: Optional[int] = None
    type_currency_id: Optional[int] = None

    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

    password: Optional[str] = None
    user_name: Optional[str] = None

    description: Optional[str] = None
    state: Optional[int] = None

    business_profile_id: Optional[int] = None


# =========================================
# RESPONSE
# =========================================

class CompanyResponse(CompanyBase):
    # 🔥 CAMBIO CLAVE: frontend usa id
    id: int

    class Config:
        from_attributes = True