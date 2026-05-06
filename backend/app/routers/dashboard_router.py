from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.task_model import Task
from app.models.user_model import User
from app.models.asset_model import Asset
from app.models.company_model import Company
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.role_model import Role

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_stats(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")

    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)

    result = await db.execute(
        select(UserSession).where(UserSession.token == token, UserSession.is_active == True)
    )
    session = result.scalar_one_or_none()

    if not session or payload is None:
        raise HTTPException(status_code=401, detail="Sesión inválida")

    email = payload.get("sub")
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = result.scalar_one_or_none()
    is_system = role.is_system if role else False

    if is_system:
        total_companies = (await db.execute(select(func.count()).select_from(Company))).scalar()
        total_users     = (await db.execute(select(func.count()).select_from(User))).scalar()
        total_assets    = (await db.execute(select(func.count()).select_from(Asset))).scalar()
        total_tasks     = (await db.execute(select(func.count()).select_from(Task))).scalar()
    else:
        total_companies = 1
        total_users  = (await db.execute(select(func.count()).select_from(User).where(User.company_id == user.company_id))).scalar()
        total_assets = (await db.execute(select(func.count()).select_from(Asset).where(Asset.company_id == user.company_id))).scalar() if hasattr(Asset, 'company_id') else (await db.execute(select(func.count()).select_from(Asset))).scalar()
        total_tasks  = (await db.execute(select(func.count()).select_from(Task))).scalar()

    return {
        "total_companies": total_companies,
        "total_users":     total_users,
        "total_assets":    total_assets,
        "total_tasks":     total_tasks,
        "is_system":       is_system,
    }
