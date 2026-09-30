from fastapi import APIRouter, Depends

from app.models.user_model import User
from app.schemas.profile_schema import ProfileUpdate
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/profile", tags=["Profile"])


# Endpoint heredado sin uso en el frontend: no modifica datos. Se exige sesión
# (antes era público y apuntaba a un usuario fijo).
@router.put("/")
async def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
):
    return {"message": "Perfil actualizado"}
