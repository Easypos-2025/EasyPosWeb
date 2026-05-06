from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sqlfunc
from app.database import get_db
from app.models.user_model import User
from app.models.role_model import Role
from app.models.company_plan_model import CompanyPlan
from datetime import datetime, timedelta, date
import secrets
from app.models.password_reset_token import PasswordResetToken
from pydantic import BaseModel
from app.utils.email_service import send_reset_email
from app.auth.password_utils import verify_password
from app.auth.jwt_handler import create_access_token, decode_access_token
from app.schemas.auth_schema import LoginRequest
from app.models.company_model import Company
from app.auth.password_utils import hash_password
from app.models.business_profile_model import BusinessProfile
import re
from app.models.user_session_model import UserSession
from app.models.user_notification_model import UserNotification
from app.schemas.auth_schema import ResetPasswordRequest

router = APIRouter(prefix="/auth", tags=["Auth"])


async def _notify_admins_access(db: AsyncSession, actor: User, title: str, message: str):
    try:
        result = await db.execute(
            select(Role.id).where(
                Role.company_id == actor.company_id,
                sqlfunc.lower(Role.name).like("%admin%"),
            )
        )
        admin_role_ids = [r.id for r in result.all()]
        if not admin_role_ids:
            return
        result = await db.execute(
            select(User).where(
                User.company_id == actor.company_id,
                User.role_id.in_(admin_role_ids),
                User.is_active == True,
                User.id != actor.id,
            )
        )
        admins = result.scalars().all()
        for admin in admins:
            db.add(UserNotification(
                sender_id=actor.id, receiver_id=admin.id,
                title=title, message=message, is_read=False,
            ))
        if admins:
            await db.commit()
    except Exception:
        await db.rollback()


async def _resolve_payment_status(company, db: AsyncSession) -> str:
    if not company:
        return "active"
    current = getattr(company, "payment_status", "active") or "active"
    if current in ("pending_payment", "payment_submitted", "payment_rejected"):
        return current
    result = await db.execute(
        select(CompanyPlan)
        .where(CompanyPlan.company_id == company.id_company, CompanyPlan.is_active == True)
        .order_by(CompanyPlan.id.desc())
    )
    active_plan = result.scalar_one_or_none()
    if (
        active_plan
        and active_plan.expiration_date
        and active_plan.expiration_date < date.today()
        and current == "active"
    ):
        company.payment_status = "expired"
        try:
            await db.commit()
        except Exception:
            await db.rollback()
        return "expired"
    return current


@router.post("/login/")
async def login(data: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")
    if user.is_active != True:
        raise HTTPException(status_code=403, detail="Usuario inactivo. Contacta al administrador")

    result = await db.execute(select(Company).where(Company.id_company == user.company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    if company.state != True:
        raise HTTPException(status_code=403, detail="Tu empresa está inactiva. Contacta al administrador")

    token = create_access_token({"sub": user.email, "user_id": user.id})

    ip = request.headers.get("x-forwarded-for")
    if not ip:
        ip = request.client.host if request.client else "unknown"

    session = UserSession(
        user_id=user.id, token=token,
        ip=ip, user_agent=request.headers.get("user-agent"),
        is_active=True
    )
    db.add(session)
    await db.commit()

    await _notify_admins_access(
        db, user,
        title="Entrada al sistema",
        message=f"{user.nombre} ingresó al sistema desde {ip or 'IP desconocida'}.",
    )

    return {"access_token": token, "token_type": "bearer", "usuario": user.nombre}


class ForgotPasswordRequest(BaseModel):
    email: str


@router.post("/forgot-password/")
async def forgot_password(
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    response_message = {"message": "Si el correo existe, recibirás un enlace de recuperación"}

    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or user.is_active != True:
        return response_message

    result = await db.execute(select(Company).where(Company.id_company == user.company_id))
    company = result.scalar_one_or_none()
    if not company or company.state != True:
        return response_message

    result = await db.execute(select(PasswordResetToken).where(PasswordResetToken.user_id == user.id))
    old_tokens = result.scalars().all()
    for t in old_tokens:
        await db.delete(t)

    token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=user.id, token=token,
        expires_at=datetime.utcnow() + timedelta(minutes=60)
    )
    db.add(reset_token)
    await db.commit()

    background_tasks.add_task(send_reset_email, user.email, token)
    return response_message


@router.post("/reset-password/")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PasswordResetToken).where(PasswordResetToken.token == data.token))
    reset_token = result.scalar_one_or_none()
    if not reset_token:
        raise HTTPException(status_code=400, detail="Token inválido")
    if datetime.utcnow().timestamp() > reset_token.expires_at.timestamp():
        raise HTTPException(status_code=400, detail="Token expirado")

    result = await db.execute(select(User).where(User.id == reset_token.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'
    if not re.match(password_regex, data.new_password):
        raise HTTPException(status_code=400, detail="Contraseña insegura")

    user.password_hash = hash_password(data.new_password)
    await db.delete(reset_token)
    await db.commit()
    return {"message": "Contraseña actualizada correctamente"}


@router.post("/logout/")
async def logout(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")

    result = await db.execute(
        select(UserSession).where(UserSession.token == token, UserSession.is_active == True)
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"message": "Sesión ya cerrada"}

    result = await db.execute(select(User).where(User.id == session.user_id))
    user_out = result.scalar_one_or_none()

    session.is_active = False
    await db.commit()

    if user_out:
        await _notify_admins_access(db, user_out, title="Salida del sistema",
                                    message=f"{user_out.nombre} cerró sesión.")

    return {"message": "Sesión cerrada correctamente"}


@router.get("/health/")
async def health_check():
    return {"status": "ok"}


@router.patch("/heartbeat/")
async def heartbeat(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")

    result = await db.execute(
        select(UserSession).where(UserSession.token == token, UserSession.is_active == True)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=401, detail="Sesión inválida")

    session.last_seen = datetime.utcnow()
    await db.commit()
    return {"ok": True}


@router.get("/me/")
async def get_me(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")

    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)

    result = await db.execute(
        select(UserSession).where(UserSession.token == token, UserSession.is_active == True)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=401, detail="Sesión inválida o cerrada")
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = result.scalar_one_or_none()
    result = await db.execute(select(Company).where(Company.id_company == user.company_id))
    company = result.scalar_one_or_none()

    return {
        "id":                 user.id,
        "nombre":             user.nombre,
        "email":              user.email,
        "role_id":            user.role_id,
        "role":               role.name if role else None,
        "company_id":         user.company_id,
        "is_active":          user.is_active,
        "is_system":          role.is_system if role else False,
        "business_profile_id": company.business_profile_id if company else None,
        "payment_status":     await _resolve_payment_status(company, db),
        "upgrade_status":     getattr(company, "upgrade_status", None) if company else None,
    }
