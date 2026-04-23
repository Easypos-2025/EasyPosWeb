from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.models.system_module_model import SystemModule
from app.database import get_db
from app.models.role_model import Role
from app.models.role_module_model import RoleModule

router = APIRouter(
    prefix="/roles",
    tags=["Roles"]
)


# =========================
# ASIGNAR MÓDULOS A ROL
# =========================
@router.post("/{role_id}/modules/")
def assign_modules_to_role(
    role_id: int,
    modules: List[dict],
    db: Session = Depends(get_db)
):

    role = db.get(Role, role_id)

    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    # 🔥 eliminar permisos actuales
    #db.query(RoleModule).filter(RoleModule.role_id == role_id).delete()
    # 🔥 BORRAR BIEN (CLAVE)
    db.query(RoleModule).filter(RoleModule.role_id == role_id).delete(synchronize_session=False)
    
    # 🔥 insertar nuevos
    for m in modules:
        new_rm = RoleModule(
            role_id=role_id,
            module_id=m["module_id"],
            can_view=m.get("can_view", True),
            can_create=m.get("can_create", False),
            can_edit=m.get("can_edit", False),
            can_delete=m.get("can_delete", False),
        )
        db.add(new_rm)

    db.commit()

    return {"message": "Módulos asignados correctamente"}

# =========================
# LISTAR ROLES
# =========================
@router.get("/")
def get_roles(db: Session = Depends(get_db)):
    roles = db.query(Role).filter(
        Role.is_system == False
    ).all()
    return roles

# =========================
# OBTENER MÓDULOS DE UN ROL
# =========================

@router.get("/{role_id}/modules/")
def get_modules_by_role(
    role_id: int,
    db: Session = Depends(get_db)
):
    role = db.get(Role, role_id)

    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    # 🔥 traer TODOS los módulos
    modules = db.query(SystemModule).all()

    # 🔥 traer permisos del rol
    role_modules = db.query(RoleModule).filter(
        RoleModule.role_id == role_id
    ).all()

    # 🔥 convertir a lookup
    permissions_map = {
        rm.module_id: rm for rm in role_modules
    }

    result = []

    for m in modules:
        rm = permissions_map.get(m.id)

        result.append({
            "module_id": m.id,
            "module_name": m.name,
            "can_view": rm.can_view if rm else False,
            "can_create": rm.can_create if rm else False,
            "can_edit": rm.can_edit if rm else False,
            "can_delete": rm.can_delete if rm else False,
        })

    return result


    