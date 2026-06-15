import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine
from sqlalchemy.orm import declarative_base
from sqlalchemy import text

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+aiomysql://root:123456@localhost/easyposweb")
DATATEMPPOS_URL = os.getenv("DATATEMPPOS_URL", "mysql+aiomysql://root:123456@localhost/datatemppos")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=40,
    pool_timeout=30,
    pool_recycle=1800,
)

datatemppos_engine = create_async_engine(
    DATATEMPPOS_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
DatatempposSession = async_sessionmaker(datatemppos_engine, expire_on_commit=False)

Base = declarative_base()

# ── Pool de engines externos, cacheados por company_id ───────────────────────
_ext_engines: dict[int, AsyncEngine] = {}


def _build_ext_engine(host: str, port: int, db_name: str, user: str, password: str) -> AsyncEngine:
    pwd = quote_plus(password or "")
    url = f"mysql+aiomysql://{user}:{pwd}@{host}:{port}/{db_name}"
    return create_async_engine(url, echo=False, pool_size=5, max_overflow=10,
                               pool_timeout=30, pool_recycle=1800)


def get_ext_session(company_id: int, host: str, port: int,
                    db_name: str, user: str, password: str) -> AsyncSession:
    """Devuelve una sesión hacia la DB externa del company. Cachea el engine."""
    if company_id not in _ext_engines:
        _ext_engines[company_id] = _build_ext_engine(host, port, db_name, user, password)
    return AsyncSession(_ext_engines[company_id], expire_on_commit=False)


def invalidate_ext_engine(company_id: int) -> None:
    """Descarta el engine cacheado (llamar al guardar nueva config de DB)."""
    _ext_engines.pop(company_id, None)


async def test_ext_connection(host: str, port: int,
                              db_name: str, user: str, password: str) -> dict:
    """Intenta conectar y ejecutar SELECT 1. Retorna {ok, message}."""
    eng = None
    try:
        eng = _build_ext_engine(host, port, db_name, user, password)
        async with eng.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"ok": True, "message": "Conexión exitosa"}
    except Exception as e:
        return {"ok": False, "message": str(e)}
    finally:
        if eng:
            await eng.dispose()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def get_datatemppos_db():
    async with DatatempposSession() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
