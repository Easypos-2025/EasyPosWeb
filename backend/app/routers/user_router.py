# =====================================================
# IMPORTS
# =====================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Union
from app.models.role_model import Role
from app.database import get_db
from app.models.user_model import User
from app.schemas.user_schema import UserResponse, UserCreate, UserUpdate
from app.models.role_module_model import RoleModule
from app.models.system_module_model import SystemModule
from app.models.company_plan_model import CompanyPlan
from app.models.plan_model import Plan
from passlib.context import CryptContext
from app.auth.dependencies import get_current_user
from sqlalchemy.exc import IntegrityError

# =====================================================
# CONFIG
# =====================================================

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# =====================================================
# HELPER — límite de usuarios según plan
# =====================================================

def _get_plan_limit(company_id: int, db: Session):
    """Retorna (max_users, plan_name). -1 = ilimitado."""
    cp = (
        db.query(CompanyPlan)
        .filter(CompanyPlan.company_id == company_id, CompanyPlan.is_active == True)
        .order_by(CompanyPlan.id.desc())
        .first()
    )
    if not cp:
        return 1, "Sin plan"
    plan = db.query(Plan).filter(Plan.id == cp.plan_id).first()
    return (plan.max_users if plan else 1), (plan.name if plan else "Sin plan")


# =====================================================
# ENDPOINT — consultar uso actual del plan (usuarios)
# IMPORTANTE: debe ir ANTES de /{user_id}
# =====================================================

@router.get("/plan-limit")
def get_plan_limit(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    role = db.get(Role, current_user.role_id)
    is_system = role.is_system if role else False

    if is_system:
        return {"current": 0, "max": -1, "plan_name": "SYSADMIN", "can_add": True}

    company_id  = current_user.company_id
    max_users, plan_name = _get_plan_limit(company_id, db)
    current_count = db.query(User).filter(User.company_id == company_id).count()

    can_add = (max_users == -1) or (current_count < max_users)

    return {
        "current":   current_count,
        "max":       max_users,
        "plan_name": plan_name,
        "can_add":   can_add
    }


# =====================================================
# CREATE USER
# =====================================================

@router.post("/", response_model=UserResponse)
def crear_user(
    usuario: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verificar límite del plan (excepto SYSADMIN)
    role = db.get(Role, current_user.role_id)
    if not (role and role.is_system):
        company_id = usuario.company_id or current_user.company_id
        max_users, plan_name = _get_plan_limit(company_id, db)
        if max_users != -1:
            current_count = db.query(User).filter(User.company_id == company_id).count()
            if current_count >= max_users:
                raise HTTPException(
                    status_code=403,
                    detail=f"Límite de {max_users} usuario(s) alcanzado para el plan {plan_name}. "
                           f"Actualiza tu plan para agregar más usuarios."
                )

    hashed_password = pwd_context.hash(usuario.password)

    nuevo_usuario = User(
        nombre=    usuario.nombre,
        email=     usuario.email,
        password_hash= hashed_password,
        role_id=   usuario.role_id,
        company_id=usuario.company_id
    )

    try:
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)
        return nuevo_usuario

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="El email ya está registrado")


# =====================================================
# GET USERS (MULTIEMPRESA LIMPIO Y SIN REMIENDOS)
# =====================================================

@router.get("/", response_model=list[UserResponse])
def get_user_list(
    company_id: Optional[Union[int, str]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    print("CURRENT USER COMPANY:", current_user.company_id)
    print("REQUEST COMPANY:", company_id)

    # 🔐 Usuario normal → SIEMPRE su empresa
    role = db.get(Role, current_user.role_id)

    if role and not role.is_system:
        return db.query(User).filter(
            User.company_id == current_user.company_id
        ).all()

    # 👑 SYSADMIN

    # 🔥 Caso: todas las empresas
    if isinstance(company_id, str) and company_id.lower() == "all":
        return db.query(User).all()

    # 🔥 Caso: no envían company_id → empresa logueada
    if company_id is None:
        company_id = current_user.company_id

    # 🔥 Normalizar tipo (string → int)
    company_id = int(company_id)

    return db.query(User).filter(
        User.company_id == company_id
    ).all()
    
# =====================================================
# GET USER BY ID
# =====================================================

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):

    usuario = db.get(User, user_id)

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return usuario


# =====================================================
# UPDATE USER
# =====================================================

@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db)):

    usuario = db.get(User, user_id)

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(usuario, key, value)

    try:
        db.commit()
        db.refresh(usuario)
        return usuario

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="El email ya está registrado"
        )
    



# =====================================================
# GET MODULES BY USER (SIDEBAR)
# =====================================================

@router.get("/{user_id}/modules/")
def get_user_modules(user_id: int, db: Session = Depends(get_db)):

    # 🔹 Obtener usuario
    user = db.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # 🔹 Obtener módulos permitidos
    role_modules = (
        db.query(RoleModule)
        .join(SystemModule, RoleModule.module_id == SystemModule.id)
        .filter(
            RoleModule.role_id == user.role_id,
            RoleModule.can_view == True,
            SystemModule.is_active == True
        )
        .all()
    )

    # 🔹 Convertir a lista simple
    modules = [rm.module for rm in role_modules]

    # 🔹 Construir árbol (parent → children)
    module_dict = {m.id: {
        "id": m.id,
        "name": m.name,
        "route": m.route,
        "icon": m.icon,
        "parent_id": m.parent_id,
        "children": []
    } for m in modules}

    tree = []

    for m in module_dict.values():
        if m["parent_id"] and m["parent_id"] in module_dict:
            module_dict[m["parent_id"]]["children"].append(m)
        else:
            tree.append(m)

    return tree


# =========================
# ELIMINAR USUARIO
# =========================
@router.delete("/{id}")
def delete_user(id: int, db: Session = Depends(get_db)):
    user = db.get(User, id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    db.delete(user)
    db.commit()

    return {"message": "Usuario eliminado"}

