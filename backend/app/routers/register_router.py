import re
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth.password_utils import hash_password
from app.database import get_db
from app.models.business_profile_module import BusinessProfileModule
from app.models.company_model import Company
from app.models.company_payment_model import CompanyPayment
from app.models.company_plan_model import CompanyPlan
from app.models.company_theme_model import CompanyTheme
from app.models.password_reset_token import PasswordResetToken
from app.models.plan_model import Plan
from app.models.role_model import Role
from app.models.role_module_model import RoleModule
from app.models.user_model import User
from app.utils.email_service import send_payment_received, send_verification_email

router = APIRouter(prefix="/register", tags=["Register"])

PW_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'
DEFAULT_THEME = {"topbar_color": "#1e3a5f", "sidebar_color": "#1a2535", "bg_color": "#f1f5f9",
                 "font_size": "16", "font_color": "#1e293b"}
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
    website: str = ""

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
async def register_associate(data: AssociateRegisterRequest, request: Request,
                              background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    if data.website:
        raise HTTPException(status_code=400, detail="Solicitud no válida")
    if not re.match(PW_REGEX, data.admin_password):
        raise HTTPException(status_code=400, detail="La contraseña debe tener mín. 8 caracteres, una mayúscula, una minúscula, un número y un símbolo (@$!%*?&)")

    result = await db.execute(select(User).where(User.email == data.admin_email))
    existing_user = result.scalars().first()
    if existing_user and not existing_user.is_test_account:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    result = await db.execute(select(Company).where(Company.identification_number == data.identification_number))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El NIT ya está registrado")

    result = await db.execute(select(Plan).where(Plan.id == data.plan_id, Plan.is_active == True))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=400, detail="Plan no disponible. Selecciona otro.")

    is_paid = plan.price > 0
    result = await db.execute(select(BusinessProfileModule).where(BusinessProfileModule.business_profile_id == data.business_profile_id))
    profile_modules = result.scalars().all()

    try:
        company = Company(name=data.company_name, identification_number=data.identification_number,
                          business_profile_id=data.business_profile_id, state=1,
                          payment_status="pending_payment" if is_paid else "active")
        db.add(company)
        await db.flush()

        role = Role(name="Admin", description="Administrador principal",
                    company_id=company.id_company, is_system=False)
        db.add(role)
        await db.flush()

        user = User(nombre=data.admin_nombre, email=data.admin_email,
                    password_hash=hash_password(data.admin_password),
                    role_id=role.id, company_id=company.id_company, is_active=False)
        db.add(user)
        await db.flush()

        db.add(CompanyPlan(company_id=company.id_company, plan_id=plan.id, is_active=True))

        for bpm in profile_modules:
            db.add(RoleModule(role_id=role.id, module_id=bpm.module_id,
                              can_view=True, can_create=True, can_edit=True, can_delete=True))

        db.add(CompanyTheme(company_id=company.id_company, **DEFAULT_THEME, logo=None))

        if is_paid:
            from app.models.plan_price_model import PlanPrice as PP
            currency = data.currency_code.upper()[:3]
            result = await db.execute(select(PP).where(PP.plan_id == plan.id, PP.currency_code == currency, PP.is_active == True))
            pp = result.scalar_one_or_none()
            amount = pp.amount if pp else plan.price
            db.add(CompanyPayment(company_id=company.id_company, plan_id=plan.id, amount=amount,
                                  currency_code=currency, status="pending", payment_type="activation"))

        await db.commit()

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error al crear la cuenta. Intenta de nuevo.") from e

    # Crear token de verificación de email (48h)
    verify_token = secrets.token_urlsafe(32)
    db_token = PasswordResetToken(
        user_id    = user.id,
        token      = verify_token,
        expires_at = datetime.utcnow() + timedelta(hours=48),
    )
    db.add(db_token)
    await db.commit()

    background_tasks.add_task(send_verification_email, data.admin_email, verify_token, data.company_name)

    if is_paid:
        background_tasks.add_task(send_payment_received, company_name=data.company_name,
                                  plan_name=plan.name, amount=plan.price, admin_email=data.admin_email)

    return {"message": "Revisa tu correo para activar la cuenta", "company": data.company_name,
            "email": data.admin_email, "payment_status": "pending_payment" if is_paid else "active",
            "plan_name": plan.name, "is_paid": is_paid, "requires_verification": True}


@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token == token,
            PasswordResetToken.expires_at > datetime.utcnow(),
        )
    )
    db_token = result.scalar_one_or_none()
    if not db_token:
        raise HTTPException(status_code=400, detail="El enlace de verificación es inválido o ha expirado.")

    user = await db.get(User, db_token.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user.is_active = True
    await db.delete(db_token)
    await db.commit()
    return {"message": "Cuenta activada exitosamente. Ya puedes iniciar sesión.", "email": user.email}
