"""
Conexiones del agente: BD real de la empresa y datatemppos.
Las BD del escritorio están en latin1; la conexión va en utf8mb4 y MariaDB convierte.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from . import config


def _motor(url: str):
    return create_async_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=5,
        max_overflow=5,
        # Modo no estricto como la app anterior (Laravel strict=false): las tablas del escritorio
        # tienen columnas NOT NULL sin valor por defecto que el VB6 nunca llena
        connect_args={"charset": "utf8mb4", "init_command": "SET SESSION sql_mode='NO_ENGINE_SUBSTITUTION'"},
    )


motor_empresa = _motor(config.DB_EMPRESA_URL)
motor_temp    = _motor(config.DB_TEMP_URL)

SesionEmpresa = async_sessionmaker(motor_empresa, expire_on_commit=False)
SesionTemp    = async_sessionmaker(motor_temp, expire_on_commit=False)


async def get_emp() -> AsyncSession:
    async with SesionEmpresa() as s:
        yield s


async def get_tmp() -> AsyncSession:
    async with SesionTemp() as s:
        yield s
