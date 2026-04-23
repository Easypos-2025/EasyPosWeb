# =====================================================
# SYSTEM MODULE ROUTER
# =====================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.role_module_model import RoleModule
from app.database import get_db
from app.models.system_module_model import SystemModule
from app.schemas.system_module_schema import (
    SystemModuleCreate,
    SystemModuleOut,
    SystemModuleUpdate
)
from app.models.business_profile_module import BusinessProfileModule
from app.auth.dependencies import get_current_user
from app.models.role_model import Role


router = APIRouter(
    prefix="/system-modules",
    tags=["System Modules"]
)

# =====================================================
# BUILD TREE
# =====================================================

def build_tree(modules):
    module_dict = {
        m.id: {
            "id": m.id,
            "name": m.name,
            "route": m.route,
            "icon": m.icon,
            "parent_id": m.parent_id,
            "is_active": m.is_active,
            "children": []
        }
        for m in modules
    }

    tree = []

    for m in module_dict.values():
        if m["parent_id"] and m["parent_id"] != 0:
            parent = module_dict.get(m["parent_id"])
            if parent:
                parent["children"].append(m)
        else:
            tree.append(m)

    return tree

# =====================================================
# CREATE
# =====================================================

@router.post("/", response_model=SystemModuleOut)
def create_module(data: SystemModuleCreate, db: Session = Depends(get_db)):
    module = SystemModule(**data.dict())

    db.add(module)
    db.commit()
    db.refresh(module)

    return {
        "id": module.id,
        "name": module.name,
        "route": module.route,
        "icon": module.icon,
        "parent_id": module.parent_id,
        "is_active": module.is_active,
        "children": []
    }

# =====================================================
# 🔥 LISTAR TODOS LOS MÓDULOS (PLANO)  ← AQUÍ VA
# =====================================================

@router.get("/flat/")
def get_all_modules_flat(db: Session = Depends(get_db), user = Depends(get_current_user)):    
    role = db.get(Role, user.role_id)

    if role and role.is_system:
        modules = db.query(SystemModule).all()
    else:
        modules = db.query(SystemModule).filter(
            SystemModule.is_sysadmin == False
        ).all()
    return modules
    
   

# =====================================================
# LIST (TREE)
# =====================================================

@router.get("/", response_model=list[SystemModuleOut])
def list_modules(db: Session = Depends(get_db)):
    modules = db.query(SystemModule)\
        .order_by(SystemModule.order_index)\
        .all()

    return build_tree(modules)

# =====================================================
# GET ONE
# =====================================================

@router.get("/{module_id}", response_model=SystemModuleOut)
def get_module(module_id: int, db: Session = Depends(get_db)):
    module = db.get(SystemModule, module_id)

    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    return module

# =====================================================
# UPDATE
# =====================================================

@router.put("/{module_id}", response_model=SystemModuleOut)
def update_module(module_id: int, data: SystemModuleUpdate, db: Session = Depends(get_db)):

    module = db.get(SystemModule, module_id)

    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    update_data = data.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(module, key, value)

    db.commit()
    db.refresh(module)

    return {
        "id": module.id,
        "name": module.name,
        "route": module.route,
        "icon": module.icon,
        "parent_id": module.parent_id,
        "is_active": module.is_active,
        "children": []
    }

# =====================================================
# DELETE
# =====================================================

@router.delete("/{module_id}")
def delete_module(module_id: int, db: Session = Depends(get_db)):

    module = db.get(SystemModule, module_id)

    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    children = db.query(SystemModule)\
        .filter(SystemModule.parent_id == module_id)\
        .first()

    if children:
        raise HTTPException(status_code=400, detail="Tiene módulos hijos")

    db.query(RoleModule)\
        .filter(RoleModule.module_id == module_id)\
        .delete()

    db.query(BusinessProfileModule)\
        .filter(BusinessProfileModule.module_id == module_id)\
        .delete()

    db.delete(module)
    db.commit()

    return {"message": "Module deleted"}