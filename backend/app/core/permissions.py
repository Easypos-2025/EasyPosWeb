# =====================================================
# PERMISSIONS DEPENDENCY
# =====================================================

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user_model import User
from app.models.role_module_model import RoleModule
from app.models.system_module_model import SystemModule
from app.auth.dependencies import get_current_user

def check_permission(route: str, action: str):
    """
    Verifica si el usuario tiene permiso sobre un módulo
    """

    def permission_dependency(current_user: User = Depends(get_current_user),db: Session = Depends(get_db)
):
    
        # 🔹 obtener usuario
        user = current_user

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # 🔹 buscar módulo por ruta
        module = db.query(SystemModule).filter(
            SystemModule.route == route,
            SystemModule.is_active == True
        ).first()

        if not module:
            raise HTTPException(status_code=404, detail="Módulo no existe")

        # 🔹 buscar permisos
        permission = db.query(RoleModule).filter(
            RoleModule.role_id == user.role_id,
            RoleModule.module_id == module.id
        ).first()

        if not permission:
            raise HTTPException(status_code=403, detail="Sin permisos")

        # 🔹 validar acción
        if not getattr(permission, action):
            raise HTTPException(status_code=403, detail="Acceso denegado")

        return True

    return permission_dependency
