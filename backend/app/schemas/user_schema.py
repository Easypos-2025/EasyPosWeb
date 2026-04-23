from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import re
from pydantic import validator

# =========================
# CREATE
# =========================
from pydantic import BaseModel, EmailStr, validator
import re

class UserCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    role_id: int
    company_id: int

    @validator("password")
    def validar_password(cls, value):

        if len(value) < 8:
            raise ValueError("Debe tener mínimo 8 caracteres")

        if not re.search(r"[A-Z]", value):
            raise ValueError("Debe tener al menos una mayúscula")

        if not re.search(r"[a-z]", value):
            raise ValueError("Debe tener al menos una minúscula")

        if not re.search(r"[0-9]", value):
            raise ValueError("Debe tener al menos un número")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("Debe tener un carácter especial")

        return value
    
# =========================
# UPDATE
# =========================
class UserUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    role_id: Optional[int] = None
    company_id: Optional[int] = None
    is_active: Optional[bool] = None

    

# =========================
# RESPONSE
# =========================
class UserResponse(BaseModel):
    id: int
    nombre: str
    email: str
    role_id: int
    company_id: int
    is_active: bool
    class Config:
        from_attributes = True

        