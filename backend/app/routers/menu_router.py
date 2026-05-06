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
from app.database import AsyncSessionLocal
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

    # 🔹 módulos por perfil — jerarquía y orden desde business_profile_modules
    modules = db.execute(text("""
        SELECT
            bpm.id        AS bpm_id,
            sm.name,
            sm.route,
            sm.icon,
            COALESCE(
                bpm.parent_id,
                parent_bpm.id
            )             AS parent_id
        FROM system_modules sm
        JOIN business_profile_modules bpm
            ON bpm.module_id = sm.id
        LEFT JOIN business_profile_modules parent_bpm
            ON parent_bpm.module_id = sm.parent_id
            AND parent_bpm.business_profile_id = bpm.business_profile_id
        WHERE bpm.business_profile_id = :profile_id
          AND sm.is_active = 1
        ORDER BY
            COALESCE(bpm.parent_id, parent_bpm.id),
            bpm.sort_order,
            sm.id
    """),
    {
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
            COALESCE(bpm.parent_id, parent_bpm.id) AS parent_id
        FROM system_modules sm
        JOIN business_profile_modules bpm
            ON bpm.module_id = sm.id
        LEFT JOIN business_profile_modules parent_bpm
            ON parent_bpm.module_id = sm.parent_id
            AND parent_bpm.business_profile_id = bpm.business_profile_id
        WHERE bpm.business_profile_id = :profile_id
          AND sm.is_active = 1
        ORDER BY COALESCE(bpm.parent_id, parent_bpm.id), bpm.sort_order
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
            sm.id  AS module_id,
            sm.name,
            sm.route,
            sm.icon,
            COALESCE(
                bpm.parent_id,
                parent_bpm.id
            ) AS parent_id
        FROM system_modules sm
        JOIN business_profile_modules bpm
            ON bpm.module_id = sm.id
        LEFT JOIN business_profile_modules parent_bpm
            ON parent_bpm.module_id = sm.parent_id
            AND parent_bpm.business_profile_id = bpm.business_profile_id
        WHERE bpm.business_profile_id = :profile_id
        ORDER BY
            COALESCE(bpm.parent_id, parent_bpm.id),
            bpm.sort_order,
            sm.id
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


# ── REPARAR PERFIL: limpia huérfanos, re-sincroniza jerarquía y permisos ───
@router.post("/repair-profile/{profile_id}")
def repair_profile_menu(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Eliminar registros de módulos inactivos (sm.is_active = 0)
    deleted = db.execute(text("""
        DELETE bpm FROM business_profile_modules bpm
        INNER JOIN system_modules sm ON sm.id = bpm.module_id
        WHERE bpm.business_profile_id = :pid AND sm.is_active = 0
    """), {"pid": profile_id})
    deleted_count = deleted.rowcount

    # 2. Re-sincronizar parent_id en bpm desde sm.parent_id
    rows = db.execute(text("""
        SELECT bpm.id AS bpm_id, sm.parent_id AS sm_parent_id
        FROM business_profile_modules bpm
        JOIN system_modules sm ON sm.id = bpm.module_id
        WHERE bpm.business_profile_id = :pid
    """), {"pid": profile_id}).fetchall()

    # Mapa sm.id → bpm.id para este perfil
    sm_to_bpm = {}
    for r in rows:
        sm_id_res = db.execute(text(
            "SELECT module_id FROM business_profile_modules WHERE id = :bid"
        ), {"bid": r.bpm_id}).fetchone()
        if sm_id_res:
            sm_to_bpm[sm_id_res.module_id] = r.bpm_id

    for r in rows:
        new_parent = sm_to_bpm.get(r.sm_parent_id)  # None si el padre no está en el perfil
        db.execute(text(
            "UPDATE business_profile_modules SET parent_id = :pid WHERE id = :bid"
        ), {"pid": new_parent, "bid": r.bpm_id})

    # 3. Inicializar sort_order secuencial por grupo de padre (ordenado por sm.id)
    #    Solo aplica a registros con sort_order = 0 para no pisar un orden ya guardado
    bpm_rows = db.execute(text("""
        SELECT bpm.id AS bpm_id, bpm.parent_id AS bpm_parent
        FROM business_profile_modules bpm
        JOIN system_modules sm ON sm.id = bpm.module_id
        WHERE bpm.business_profile_id = :pid
        ORDER BY bpm.parent_id, sm.id
    """), {"pid": profile_id}).fetchall()

    from collections import defaultdict
    groups = defaultdict(list)
    for r in bpm_rows:
        groups[r.bpm_parent].append(r.bpm_id)

    for parent_key, ids in groups.items():
        for idx, bpm_id in enumerate(ids):
            db.execute(text(
                "UPDATE business_profile_modules SET sort_order = :so WHERE id = :bid"
            ), {"so": idx, "bid": bpm_id})

    # 4. Sincronizar role_modules: insertar can_view=1 para módulos sin permiso
    #    en todos los roles de empresas con este perfil de negocio
    fixed_perms = db.execute(text("""
        INSERT INTO role_modules (role_id, module_id, can_view, can_create, can_edit, can_delete)
        SELECT DISTINCT r.id, bpm.module_id, 1, 0, 0, 0
        FROM roles r
        JOIN companies c ON c.id_company = r.company_id
        JOIN business_profile_modules bpm ON bpm.business_profile_id = c.business_profile_id
        JOIN system_modules sm ON sm.id = bpm.module_id AND sm.is_active = 1
        WHERE c.business_profile_id = :pid
          AND NOT EXISTS (
              SELECT 1 FROM role_modules rm2
              WHERE rm2.role_id = r.id AND rm2.module_id = bpm.module_id
          )
    """), {"pid": profile_id})
    perms_added = fixed_perms.rowcount

    db.commit()

    # 4. Devolver árbol actualizado y resumen
    tree = get_menu_by_profile(profile_id, db, current_user)
    return {
        "deleted_inactive": deleted_count,
        "permissions_added": perms_added,
        "tree": tree
    }

