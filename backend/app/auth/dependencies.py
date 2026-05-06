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

        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Token inválido")

        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")

        return user

    except HTTPException:
        raise
    except Exception as e:
        print("ERROR REAL:", str(e))
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
