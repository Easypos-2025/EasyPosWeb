"""
========================================================
ESQUEMAS DE AUTENTICACIÓN
========================================================

Estos esquemas definen la estructura de datos
para login y autenticación.

FastAPI usa estos modelos para:

- validar datos
- generar documentación Swagger
"""

from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):

    email: str
    password: str
    company_id: Optional[int] = None


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

        