"""
Register Router — auto-registro de Asociados nuevos.
Endpoint público (sin autenticación).

Al registrar crea en una sola transacción:
  1. Company
  2. Role "Admin"
  3. User (administrador)
  4. CompanyPlan  (plan Free por defecto)
  5. RoleModules  (todos los módulos del perfil con permisos completos)
  6. CompanyTheme (colores por defecto)
"""
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.password_utils import hash_password
from app.database import get_db
from app.models.business_profile_module import BusinessProfileModule
from app.models.company_model import Company
from app.models.company_plan_model import CompanyPlan
from app.models.company_theme_model import CompanyTheme
from app.models.plan_model import Plan
from app.models.role_model import Role
from app.models.role_module_model import RoleModule
from app.models.user_model import User

router = APIRouter(prefix="/register", tags=["Register"])

PW_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'

DEFAULT_THEME = {
    "topbar_color":  "#1e3a5f",
    "sidebar_color": "#1a2535",
    "bg_color":      "#f1f5f9",
    "font_size":     "16",
    "font_color":    "#1e293b",
}


class AssociateRegisterRequest(BaseModel):
    company_name: str
    identification_number: str
    business_profile_id: int
    admin_nombre: str
    admin_email: str
    admin_password: str


@router.post("/associate/")
def register_associate(data: AssociateRegisterRequest, db: Session = Depends(get_db)):

    # ── Validaciones previas ─────────────────────────────────────
    if not re.match(PW_REGEX, data.admin_password):
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe tener mín. 8 caracteres, una mayúscula, una minúscula, un número y un símbolo (@$!%*?&)"
        )

    if db.query(User).filter(User.email == data.admin_email.strip().lower()).first():
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    if db.query(Company).filter(
        Company.identification_number == data.identification_number.strip()
    ).first():
        raise HTTPException(status_code=400, detail="El NIT ya está registrado")

    free_plan = db.query(Plan).filter(Plan.price == 0, Plan.is_active == True).first()
    if not free_plan:
        raise HTTPException(status_code=500, detail="No hay planes disponibles. Contacta al administrador.")

    # Verificar que el perfil de negocio tenga módulos configurados
    profile_modules = db.query(BusinessProfileModule).filter(
        BusinessProfileModule.business_profile_id == data.business_profile_id
    ).all()

    try:
        # ── 1. Empresa ───────────────────────────────────────────
        company = Company(
            name=data.company_name.strip(),
            identification_number=data.identification_number.strip(),
            business_profile_id=data.business_profile_id,
            state=1,
        )
        db.add(company)
        db.flush()

        # ── 2. Rol Admin ─────────────────────────────────────────
        role = Role(
            name="Admin",
            description="Administrador principal",
            company_id=company.id_company,
            is_system=False,
        )
        db.add(role)
        db.flush()

        # ── 3. Usuario administrador ─────────────────────────────
        user = User(
            nombre=data.admin_nombre.strip(),
            email=data.admin_email.strip().lower(),
            password_hash=hash_password(data.admin_password),
            role_id=role.id,
            company_id=company.id_company,
            is_active=True,
        )
        db.add(user)
        db.flush()

        # ── 4. Plan (Free por defecto) ───────────────────────────
        db.add(CompanyPlan(
            company_id=company.id_company,
            plan_id=free_plan.id,
            is_active=True,
        ))

        # ── 5. Permisos: todos los módulos del perfil con acceso completo ──
        for bpm in profile_modules:
            db.add(RoleModule(
                role_id=role.id,
                module_id=bpm.module_id,
                can_view=True,
                can_create=True,
                can_edit=True,
                can_delete=True,
            ))

        # ── 6. Tema visual por defecto ───────────────────────────
        db.add(CompanyTheme(
            company_id=company.id_company,
            topbar_color=DEFAULT_THEME["topbar_color"],
            sidebar_color=DEFAULT_THEME["sidebar_color"],
            bg_color=DEFAULT_THEME["bg_color"],
            font_size=DEFAULT_THEME["font_size"],
            font_color=DEFAULT_THEME["font_color"],
            logo=None,
        ))

        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al crear la cuenta. Intenta de nuevo."
        )

    return {
        "message": "Cuenta creada exitosamente",
        "company": data.company_name,
        "email": data.admin_email,
    }
