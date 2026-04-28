"""
Register Router — auto-registro de Asociados nuevos.
Endpoint público (sin autenticación).

Al registrar crea en una sola transacción:
  1. Company
  2. Role "Admin"
  3. User (administrador)
  4. CompanyPlan  (plan seleccionado)
  5. RoleModules  (todos los módulos del perfil con permisos completos)
  6. CompanyTheme (colores por defecto)
  7. CompanyPayment (solo si el plan es de pago)
"""
import re

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.auth.password_utils import hash_password
from app.database import get_db
from app.models.business_profile_module import BusinessProfileModule
from app.models.company_model import Company
from app.models.company_payment_model import CompanyPayment
from app.models.company_plan_model import CompanyPlan
from app.models.company_theme_model import CompanyTheme
from app.models.plan_model import Plan
from app.models.role_model import Role
from app.models.role_module_model import RoleModule
from app.models.user_model import User
from app.utils.email_service import send_payment_received

router = APIRouter(prefix="/register", tags=["Register"])

PW_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'

DEFAULT_THEME = {
    "topbar_color":  "#1e3a5f",
    "sidebar_color": "#1a2535",
    "bg_color":      "#f1f5f9",
    "font_size":     "16",
    "font_color":    "#1e293b",
}

# Campo honeypot — si viene relleno es un bot
HONEYPOT_FIELD = "website"


class AssociateRegisterRequest(BaseModel):
    company_name: str
    identification_number: str
    business_profile_id: int
    plan_id: int
    currency_code: str = "COP"
    admin_nombre: str
    admin_email: str
    admin_password: str
    website: str = ""   # honeypot anti-bot

    @field_validator("company_name", "identification_number", "admin_nombre", "admin_email")
    @classmethod
    def no_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Este campo es obligatorio")
        return v.strip()

    @field_validator("admin_email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Correo inválido")
        return v.lower()


@router.post("/associate/")
def register_associate(
    data: AssociateRegisterRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # ── Anti-bot: campo honeypot relleno → rechazar silenciosamente ──
    if data.website:
        raise HTTPException(status_code=400, detail="Solicitud no válida")

    # ── Validación de contraseña ─────────────────────────────────────
    if not re.match(PW_REGEX, data.admin_password):
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe tener mín. 8 caracteres, una mayúscula, una minúscula, un número y un símbolo (@$!%*?&)"
        )

    # ── Unicidad ─────────────────────────────────────────────────────
    if db.query(User).filter(User.email == data.admin_email).first():
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    if db.query(Company).filter(
        Company.identification_number == data.identification_number
    ).first():
        raise HTTPException(status_code=400, detail="El NIT ya está registrado")

    # ── Validar plan ─────────────────────────────────────────────────
    plan = db.query(Plan).filter(Plan.id == data.plan_id, Plan.is_active == True).first()
    if not plan:
        raise HTTPException(status_code=400, detail="Plan no disponible. Selecciona otro.")

    is_paid = plan.price > 0

    # ── Módulos del perfil ────────────────────────────────────────────
    profile_modules = db.query(BusinessProfileModule).filter(
        BusinessProfileModule.business_profile_id == data.business_profile_id
    ).all()

    try:
        # 1. Empresa
        company = Company(
            name=data.company_name,
            identification_number=data.identification_number,
            business_profile_id=data.business_profile_id,
            state=1,
            payment_status="pending_payment" if is_paid else "active",
        )
        db.add(company)
        db.flush()

        # 2. Rol Admin
        role = Role(
            name="Admin",
            description="Administrador principal",
            company_id=company.id_company,
            is_system=False,
        )
        db.add(role)
        db.flush()

        # 3. Usuario administrador
        user = User(
            nombre=data.admin_nombre,
            email=data.admin_email,
            password_hash=hash_password(data.admin_password),
            role_id=role.id,
            company_id=company.id_company,
            is_active=True,
        )
        db.add(user)
        db.flush()

        # 4. Plan
        db.add(CompanyPlan(
            company_id=company.id_company,
            plan_id=plan.id,
            is_active=True,
        ))

        # 5. Permisos
        for bpm in profile_modules:
            db.add(RoleModule(
                role_id=role.id,
                module_id=bpm.module_id,
                can_view=True,
                can_create=True,
                can_edit=True,
                can_delete=True,
            ))

        # 6. Tema visual
        db.add(CompanyTheme(
            company_id=company.id_company,
            topbar_color=DEFAULT_THEME["topbar_color"],
            sidebar_color=DEFAULT_THEME["sidebar_color"],
            bg_color=DEFAULT_THEME["bg_color"],
            font_size=DEFAULT_THEME["font_size"],
            font_color=DEFAULT_THEME["font_color"],
            logo=None,
        ))

        # 7. Registro de pago pendiente (solo planes de pago)
        if is_paid:
            from app.models.plan_price_model import PlanPrice as PP
            currency = data.currency_code.upper()[:3]
            pp = db.query(PP).filter(
                PP.plan_id == plan.id,
                PP.currency_code == currency,
                PP.is_active == True,
            ).first()
            amount = pp.amount if pp else plan.price
            db.add(CompanyPayment(
                company_id=company.id_company,
                plan_id=plan.id,
                amount=amount,
                currency_code=currency,
                status="pending",
                payment_type="activation",
            ))

        db.commit()

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al crear la cuenta. Intenta de nuevo."
        ) from e

    # ── Email de alerta interna en background (no bloquea la respuesta) ─
    if is_paid:
        background_tasks.add_task(
            send_payment_received,
            company_name = data.company_name,
            plan_name    = plan.name,
            amount       = plan.price,
            admin_email  = data.admin_email,
        )

    return {
        "message": "Cuenta creada exitosamente",
        "company": data.company_name,
        "email": data.admin_email,
        "payment_status": "pending_payment" if is_paid else "active",
        "plan_name": plan.name,
        "is_paid": is_paid,
    }
