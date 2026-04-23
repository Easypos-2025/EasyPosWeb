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


class LoginRequest(BaseModel):

    email: str
    password: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

        