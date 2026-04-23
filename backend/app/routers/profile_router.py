# =========================================
# PROFILE ROUTER
# =========================================

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_model import User
from app.schemas.profile_schema import ProfileUpdate

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.put("/")
def update_profile(
    data: ProfileUpdate,
    db: Session = Depends(get_db)
):
    # 🔥 POR AHORA: TOMAMOS USUARIO 1 (luego JWT)
    
    user = db.query(User).filter(User.id == 5).first()

    print("USER ENCONTRADO:", user)

    if not user:
        return {"error": "Usuario no encontrado"}

    #user.topbar_color = data.topbar_color
    #user.sidebar_color = data.sidebar_color
    #user.bg_color = data.bg_color
    #if data.logo is not None:
    #    user.logo = data.logo

    #if data.font_size is not None:
    #    user.font_size = data.font_size

    #if data.font_color is not None:
    #    user.font_family = data.font_color

    # 🔥 THEME YA NO SE MANEJA AQUÍ
    # (se maneja en company_theme_router)
    
    db.commit()
    db.refresh(user)
    return {"message": "Perfil actualizado"}
    #return {
        #"perfil": {
        #    "topbar_color": user.topbar_color,
        #    "sidebar_color": user.sidebar_color,
        #    "bg_color": user.bg_color,
        #    "logo": user.logo
        #}
    #}