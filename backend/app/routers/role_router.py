from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.role_model import Role
from app.models.role_module_model import RoleModule
from app.models.system_module_model import SystemModule
from app.models.user_model import User
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/roles", tags=["Roles"])


def _is_system(user: User, db: Session) -> bool:
    role = db.get(Role, user.role_id)
    return role.is_system if role else False


# ─── GET ROLES (filtrado por empresa) ──────────────────────────
@router.get("/")
def get_roles(
    company_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    SYSADMIN: pasa ?company_id=X para ver roles de esa empresa.
    ADMIN normal: siempre ve solo los de su propia empresa.
    """
    if _is_system(current_user, db):
        if company_id is None:
            raise HTTPException(
                status_code=400,
                detail="Se requiere company_id para consultar roles"
            )
        cid = company_id
    else:
        cid = current_user.company_id

    return db.query(Role).filter(
        Role.company_id == cid,
        Role.is_system == False
    ).order_by(Role.name).all()


# ─── CREATE ROLE ────────────────────────────────────────────────
@router.post("/")
def create_role(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if _is_system(current_user, db):
        cid = data.get("company_id")
        if not cid:
            raise HTTPException(status_code=400, detail="company_id requerido")
    else:
        cid = current_user.company_id

    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    exists = db.query(Role).filter(
        Role.name == name, Role.company_id == cid
    ).first()
    if exists:
        raise HTTPException(
            status_code=409, detail=f"Ya existe un rol '{name}' en esta empresa"
        )

    role = Role(
        name=name,
        description=(data.get("description") or "").strip(),
        company_id=cid,
        is_system=False,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


# ─── DELETE ROLE ────────────────────────────────────────────────
@router.delete("/{role_id}")
def delete_role(
    role_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    if not _is_system(current_user, db) and role.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Sin permisos")

    db.delete(role)
    db.commit()
    return {"message": "Rol eliminado"}


# ─── GET MODULES OF A ROLE ──────────────────────────────────────
@router.get("/{role_id}/modules/")
def get_modules_by_role(
    role_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    # Módulos visibles según el tipo de usuario
    if _is_system(current_user, db):
        modules = db.query(SystemModule).order_by(SystemModule.order_index).all()
    else:
        modules = db.query(SystemModule).filter(
            SystemModule.is_sysadmin == False
        ).order_by(SystemModule.order_index).all()

    role_modules = db.query(RoleModule).filter(RoleModule.role_id == role_id).all()
    permissions_map = {rm.module_id: rm for rm in role_modules}

    return [
        {
            "module_id":   m.id,
            "module_name": m.name,
            "can_view":    permissions_map[m.id].can_view    if m.id in permissions_map else False,
            "can_create":  permissions_map[m.id].can_create  if m.id in permissions_map else False,
            "can_edit":    permissions_map[m.id].can_edit    if m.id in permissions_map else False,
            "can_delete":  permissions_map[m.id].can_delete  if m.id in permissions_map else False,
        }
        for m in modules
    ]


# ─── ASSIGN MODULES TO ROLE ─────────────────────────────────────
@router.post("/{role_id}/modules/")
def assign_modules_to_role(
    role_id: int,
    modules: List[dict],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    if not _is_system(current_user, db) and role.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Sin permisos")

    db.query(RoleModule).filter(
        RoleModule.role_id == role_id
    ).delete(synchronize_session=False)

    for m in modules:
        db.add(RoleModule(
            role_id=role_id,
            module_id=m["module_id"],
            can_view=m.get("can_view", True),
            can_create=m.get("can_create", False),
            can_edit=m.get("can_edit", False),
            can_delete=m.get("can_delete", False),
        ))

    db.commit()
    return {"message": "Módulos asignados correctamente"}
