"""
========================================================
JWT HANDLER
========================================================
Manejo de creación y decodificación de tokens
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from jose import jwt, JWTError

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))

# =========================================
# CONFIGURACION
# =========================================

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "clave-por-defecto-cambiar")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))


# =========================================
# CREAR TOKEN
# =========================================

def create_access_token(data: dict):

    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


# =========================================
# DECODIFICAR TOKEN
# =========================================
 
def decode_access_token(token: str):

    try:

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        return payload

    except JWTError:

        return None
    
