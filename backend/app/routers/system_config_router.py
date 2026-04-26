from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.system_config_model import SystemConfig
from app.models.user_model import User
from app.models.role_model import Role
from app.models.user_session_model import UserSession
from app.auth.jwt_handler import decode_access_token
from app.schemas.system_config_schema import SystemConfigUpdate

router = APIRouter(prefix="/system-config", tags=["SystemConfig"])


def _get_user(authorization: str, db: Session):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    session = db.query(UserSession).filter(
        UserSession.token == token, UserSession.is_active == True
    ).first()
    if not session or not payload:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


def _is_sysadmin(user: User, db: Session) -> bool:
    role = db.query(Role).filter(Role.id == user.role_id).first()
    return role.is_system if role else False


def _ser(cfg: SystemConfig):
    return {
        "id": cfg.id,
        "config_key": cfg.config_key,
        "config_value": cfg.config_value,
        "description": cfg.description,
        "config_type": cfg.config_type,
        "is_active": cfg.is_active,
    }


# -------------------------------------------------------
# GET ALL — SYSADMIN: todas las configuraciones
# -------------------------------------------------------
@router.get("")
def get_all_configs(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)
    if not _is_sysadmin(user, db):
        raise HTTPException(status_code=403, detail="Acceso restringido a SYSADMIN")

    configs = db.query(SystemConfig).order_by(SystemConfig.config_key).all()
    return [_ser(c) for c in configs]


# -------------------------------------------------------
# GET /{key} — obtener valor de una clave (interno/frontend)
# -------------------------------------------------------
@router.get("/{key}")
def get_config(
    key: str,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    _get_user(authorization, db)
    cfg = db.query(SystemConfig).filter(
        SystemConfig.config_key == key,
        SystemConfig.is_active == True
    ).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    return _ser(cfg)


# -------------------------------------------------------
# PUT /{key} — SYSADMIN: actualizar valor
# -------------------------------------------------------
@router.put("/{key}")
def update_config(
    key: str,
    data: SystemConfigUpdate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)
    if not _is_sysadmin(user, db):
        raise HTTPException(status_code=403, detail="Acceso restringido a SYSADMIN")

    cfg = db.query(SystemConfig).filter(SystemConfig.config_key == key).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")

    cfg.config_value = data.config_value
    if data.description is not None:
        cfg.description = data.description
    if data.is_active is not None:
        cfg.is_active = data.is_active

    db.commit()
    db.refresh(cfg)
    return _ser(cfg)
