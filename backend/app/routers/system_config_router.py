from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.system_config_model import SystemConfig
from app.models.user_model import User
from app.models.role_model import Role
from app.models.user_session_model import UserSession
from app.auth.jwt_handler import decode_access_token
from app.schemas.system_config_schema import SystemConfigUpdate

router = APIRouter(prefix="/system-config", tags=["SystemConfig"])


async def _get_user(authorization: str, db: AsyncSession):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    result = await db.execute(select(UserSession).where(UserSession.token == token, UserSession.is_active == True))
    if not result.scalar_one_or_none() or not payload:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    result = await db.execute(select(User).where(User.email == payload.get("sub")))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


async def _is_sysadmin(user: User, db: AsyncSession) -> bool:
    result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = result.scalar_one_or_none()
    return role.is_system if role else False


def _ser(cfg: SystemConfig):
    return {"id": cfg.id, "config_key": cfg.config_key, "config_value": cfg.config_value,
            "description": cfg.description, "config_type": cfg.config_type, "is_active": cfg.is_active}


@router.get("")
async def get_all_configs(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    if not await _is_sysadmin(user, db):
        raise HTTPException(status_code=403, detail="Acceso restringido a SYSADMIN")
    result = await db.execute(select(SystemConfig).order_by(SystemConfig.config_key))
    return [_ser(c) for c in result.scalars().all()]


@router.get("/{key}")
async def get_config(key: str, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_user(authorization, db)
    result = await db.execute(select(SystemConfig).where(SystemConfig.config_key == key, SystemConfig.is_active == True))
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    return _ser(cfg)


@router.put("/{key}")
async def update_config(key: str, data: SystemConfigUpdate, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    if not await _is_sysadmin(user, db):
        raise HTTPException(status_code=403, detail="Acceso restringido a SYSADMIN")
    result = await db.execute(select(SystemConfig).where(SystemConfig.config_key == key))
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    cfg.config_value = data.config_value
    if data.description is not None:
        cfg.description = data.description
    if data.is_active is not None:
        cfg.is_active = data.is_active
    await db.commit()
    await db.refresh(cfg)
    return _ser(cfg)
