"""
========================================================
UTILIDADES DE SEGURIDAD DE CONTRASEÑAS
========================================================

Este módulo maneja todo lo relacionado con:

- generación de hash de contraseñas
- verificación de contraseñas

Nunca se guarda la contraseña real en la base de datos.

Se utiliza bcrypt a través de passlib.

Esto es un estándar de seguridad moderno.
"""

"""
========================================================
PASSWORD UTILS
========================================================

Funciones para encriptar y verificar contraseñas
usando passlib bcrypt
"""

from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str):

    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):

    return pwd_context.verify(plain_password, hashed_password)