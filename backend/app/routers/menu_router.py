"""
========================================================
MENU ROUTER
========================================================

Devuelve los módulos del sistema disponibles
según el rol del usuario.

Endpoint utilizado por el Sidebar dinámico
del frontend.
"""

# =====================================================
# IMPORTS
# =====================================================
#from app.models.system_module_model import SystemModule
#from app.models.role_module_model import RoleModule
#from app.models.role_model import Role

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user_model import User
from app.models.company_model import Company
from sqlalchemy import text
from app.auth.dependencies import get_current_user
# =====================================================
# ROUTER
# =====================================================

router = APIRouter(
    prefix="/menu",
    tags=["Menu"]
)


# =====================================================
# DATABASE DEPENDENCY
# =====================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =====================================================
# GET MENU BY ROLE
# =====================================================
from sqlalchemy import text

@router.get("/my-menu/")
def get_my_menu(
    company_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    #user = db.query(User).filter(User.id == user_id).first()
    user = current_user
    
    if not user:
        return []

    # 🔹 obtener empresa
    #company = db.query(Company).filter(
    #    Company.id_company == user.company_id
    #).first()
    target_company_id = company_id if company_id else user.company_id

    company = db.query(Company).filter(
        Company.id_company == target_company_id
    ).first()

    if not company or not company.business_profile_id:
        return []

    # 🔹 módulos por perfil
    modules = db.execute(text("""
        SELECT 
            bpm.id AS bpm_id,
            sm.name,
            sm.route,
            sm.icon,
            
            parent_bpm.id AS parent_id
        FROM system_modules sm
        JOIN business_profile_modules bpm
            ON bpm.module_id = sm.id
        LEFT JOIN business_profile_modules parent_bpm
            ON parent_bpm.module_id = sm.parent_id
            AND parent_bpm.business_profile_id = bpm.business_profile_id
        WHERE bpm.business_profile_id = :profile_id AND sm.is_active = 1
        ORDER BY 
            parent_bpm.id,
            bpm.sort_order
    """), 
    {
        "profile_id": company.business_profile_id
    }).fetchall()
    print("COLUMNS:", modules[0]._mapping.keys() if modules else "VACÍO")
    return [
        {
            "id": m.bpm_id,
            "name": m.name,
            "route": m.route,
            "icon": m.icon,
            "parent_id": m.parent_id
        }
        for m in modules
    ]

@router.get("/by-company/{company_id}")
def get_menu_by_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 🔐 (opcional después) validar que sea SYSADMIN

    company = db.query(Company).filter(
        Company.id_company == company_id
    ).first()

    if not company or not company.business_profile_id:
        return []

    modules = db.execute(text("""
        SELECT 
            bpm.id AS bpm_id,
            sm.name,
            sm.route,
            sm.icon,
            bpm.parent_id
        FROM system_modules sm
        JOIN business_profile_modules bpm
            ON bpm.module_id = sm.id
        WHERE bpm.business_profile_id = :profile_id
        ORDER BY bpm.parent_id, bpm.sort_order
    """), {
        "profile_id": company.business_profile_id
    }).fetchall()

    return [
        {
            "id": m.bpm_id,
            "name": m.name,
            "route": m.route,
            "icon": m.icon,
            "parent_id": m.parent_id
        }
        for m in modules
    ]

def build_tree(modules):
    module_dict = {}
    # 🔥 crear nodos
    for m in modules:
        print("NODE:", m["id"], "PARENT:", m["parent_id"])
        module_dict[m["id"]] = {
            "id": m["id"],
            "name": m["name"],
            "route": m["route"],
            "icon": m["icon"],
            "parent_id": m["parent_id"],
            "children": []
        }

    tree = []

    # 🔥 construir árbol
    for m in module_dict.values():

        parent_id = m["parent_id"]

        # 👇 VALIDACIÓN CLAVE
        if parent_id and parent_id in module_dict:
            module_dict[parent_id]["children"].append(m)
        else:
            tree.append(m)

    return tree

    
@router.get("/by-profile/{profile_id}")
def get_menu_by_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    modules = db.execute(text("""
        SELECT 
            bpm.id AS bpm_id,
            sm.id AS module_id,
            sm.name,
            sm.route,
            sm.icon,
            parent_bpm.id AS parent_id

        FROM system_modules sm

        JOIN business_profile_modules bpm
            ON bpm.module_id = sm.id

        LEFT JOIN business_profile_modules parent_bpm
            ON parent_bpm.module_id = sm.parent_id
            AND parent_bpm.business_profile_id = bpm.business_profile_id

        WHERE bpm.business_profile_id = :profile_id

        ORDER BY 
            parent_bpm.id,
            bpm.sort_order
    
    """), {
        "profile_id": profile_id
    }).fetchall()

    data = [
        {
            "id": m.bpm_id,       # 🔥 ID REAL (system_modules)
            "name": m.name,
            "route": m.route,
            "icon": m.icon,
            "parent_id": m.parent_id  # 🔥 YA VIENE COMO bpm_id DEL PADRE
        }
        for m in modules
    ]

    return build_tree(data)

        


