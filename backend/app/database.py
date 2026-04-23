"""
========================================================
CONFIGURACIÓN DE BASE DE DATOS
========================================================

Este archivo configura:

- conexión a MariaDB
- motor SQLAlchemy
- sesiones de base de datos
- Base para los modelos
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# =====================================================
# URL DE CONEXIÓN A LA BASE DE DATOS
# =====================================================

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:123456@localhost/easyposweb")


# =====================================================
# MOTOR DE BASE DE DATOS
# =====================================================

engine = create_engine(
    DATABASE_URL,
    echo=True
)


# =====================================================
# SESIONES DE BASE DE DATOS
# =====================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# =====================================================
# BASE PARA LOS MODELOS
# =====================================================

Base = declarative_base()


# =====================================================
# CREAR TABLAS
# =====================================================

def init_db():
    """
    Crea todas las tablas registradas en SQLAlchemy
    """
    Base.metadata.create_all(bind=engine)


# =====================================================
# DEPENDENCIA PARA FASTAPI
# =====================================================

def get_db():

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()