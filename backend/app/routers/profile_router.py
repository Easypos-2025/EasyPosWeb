from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user_model import User
from app.schemas.profile_schema import ProfileUpdate

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.put("/")
async def update_profile(
    data: ProfileUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == 5))
    user = result.scalar_one_or_none()

    if not user:
        return {"error": "Usuario no encontrado"}

    await db.commit()
    await db.refresh(user)
    return {"message": "Perfil actualizado"}
