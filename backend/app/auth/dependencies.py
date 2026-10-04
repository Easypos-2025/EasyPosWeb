from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user_model import User
from app.models.role_model import Role
from app.auth.jwt_handler import decode_access_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    try:
        if not credentials or not credentials.credentials:
            raise HTTPException(status_code=401, detail="Not authenticated")

        token = credentials.credentials
        payload = decode_access_token(token)

        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        if not payload.get("sub"):
            raise HTTPException(status_code=401, detail="Token inválido")

        user_id = payload.get("user_id")
        if user_id:
            user = await db.get(User, int(user_id))
        else:
            result = await db.execute(select(User).where(User.email == payload.get("sub")))
            user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")

        # Empresa elegida en el topbar (validada; solo en memoria para esta petición)
        from app.auth.tenant import apply_selected_company
        return await apply_selected_company(db, user)

    except HTTPException:
        raise
    except Exception as e:
        from app.services.error_log import log_error
        log_error(e, tipo="SERVIDOR", contexto={"etapa": "autenticacion"})
        raise HTTPException(status_code=401, detail="No autorizado")


async def require_admin(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    role = await db.get(Role, current_user.role_id)
    if not role:
        raise HTTPException(status_code=403, detail="Rol no válido")
    if role.is_system:
        return current_user
    raise HTTPException(status_code=403, detail="Acceso solo para administradores")


async def require_sysadmin(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    role = await db.get(Role, current_user.role_id)
    if not role or not role.is_system:
        raise HTTPException(status_code=403, detail="Solo SYSADMIN")
    return current_user


def require_role(role_name: str):
    async def checker(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ):
        role = await db.get(Role, current_user.role_id)
        if not role or role.name != role_name:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        return current_user
    return checker
