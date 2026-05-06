"""
========================================================
AUTH ROUTER
========================================================
Manejo de autenticación del sistema
"""

# =====================================================
# IMPORTS
# =====================================================

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc
from app.database import AsyncSessionLocal
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
from fastapi import Request
from app.schemas.auth_schema import ResetPasswordRequest

# =====================================================
# ROUTER
# =====================================================

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


# =====================================================
# HELPER: notificar a admins de la empresa
# =====================================================

def _notify_admins_access(db: Session, actor: User, title: str, message: str):
    """Crea UserNotification para todos los admins activos de la empresa, excepto el actor."""
    try:
        admin_role_ids = [
            r.id for r in db.query(Role.id).filter(
                Role.company_id == actor.company_id,
                sqlfunc.lower(Role.name).like("%admin%"),
            ).all()
        ]
        if not admin_role_ids:
            return
        admins = db.query(User).filter(
            User.company_id == actor.company_id,
            User.role_id.in_(admin_role_ids),
            User.is_active == True,
            User.id != actor.id,
        ).all()
        for admin in admins:
            db.add(UserNotification(
                sender_id=actor.id,
                receiver_id=admin.id,
                title=title,
                message=message,
                is_read=False,
            ))
        if admins:
            db.commit()
    except Exception:
        db.rollback()


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
# LOGIN
# =====================================================


@router.post("/login/")
def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    
    #print("EMAIL RECIBIDO:", data.email)
    
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Usuario no encontrado"
        )

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=400,
            detail="Contraseña incorrecta"
        )

    # ===============================================
    # VALIDAR USUARIO ACTIVO
    # ===============================================

    if user.is_active != True:
        raise HTTPException(
            status_code=403,
            detail="Usuario inactivo. Contacta al administrador"
        )

    # ===============================================
    # VALIDAR EMPRESA ACTIVA
    # ===============================================

    company = db.query(Company).filter(
        Company.id_company == user.company_id
    ).first()

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Empresa no encontrada"
        )

    if company.state != True:
        raise HTTPException(
            status_code=403,
            detail="Tu empresa está inactiva. Contacta al administrador"
        )
    
    # =========================================
    # CREAR TOKEN
    # =========================================

    token = create_access_token({
        "sub": user.email,
        "user_id": user.id
    })

    # =========================================
    # CREAR SESIÓN
    # =========================================

    user_agent = request.headers.get("user-agent")
    ip = request.headers.get("x-forwarded-for")
    if not ip:
        ip = request.client.host if request.client else "unknown"
    

    session = UserSession(
        user_id=user.id,
        token=token,
        ip=ip,
        user_agent=user_agent,
        is_active=True
    )

    db.add(session)
    db.commit()

    _notify_admins_access(
        db, user,
        title="Entrada al sistema",
        message=f"{user.nombre} ingresó al sistema desde {ip or 'IP desconocida'}.",
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": user.nombre
    }

# =====================================================
# FORGOT PASSWORD
# =====================================================

class ForgotPasswordRequest(BaseModel):
          email: str
          
@router.post("/forgot-password/")
def forgot_password(
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    #print("🔥 ENDPOINT FORGOT PASSWORD EJECUTADO")
    # 🔐 RESPUESTA SEGURA (SIEMPRE IGUAL)
    response_message = {
        "message": "Si el correo existe, recibirás un enlace de recuperación"
    }

    # =========================================
    # BUSCAR USUARIO
    # =========================================

    user = db.query(User).filter(User.email == data.email).first()
    print("USER:", user)
    if not user:
        return response_message

    # =========================================
    # VALIDAR USUARIO ACTIVO
    # =========================================
    #print("USER ACTIVO:", user.is_active)
    if user.is_active != True:
        return response_message

    # =========================================
    # VALIDAR EMPRESA ACTIVA
    # =========================================
    
    company = db.query(Company).filter(
        Company.id_company == user.company_id
    ).first()
    
    #print("COMPANY:", company)
    
    if not company or company.state != True:
        return response_message

    # 🔥 ELIMINAR TOKENS ANTIGUOS
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id
    ).delete()

    # =========================================
    # GENERAR TOKEN SEGURO
    # =========================================
    token = secrets.token_urlsafe(32)

    expires_at = datetime.utcnow() + timedelta(minutes=60)

    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at
    )

    db.add(reset_token)
    db.commit()

    # Enviar email en background — el cliente recibe respuesta inmediata
    # sin esperar la conexión SMTP
    background_tasks.add_task(send_reset_email, user.email, token)

    return response_message

# =====================================================
# RESET PASSWORD
# =====================================================


@router.post("/reset-password/")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):

    token = data.token
    new_password = data.new_password
    

    # =========================================
    # BUSCAR TOKEN
    # =========================================

    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == data.token
    ).first()

    if not reset_token:
        raise HTTPException(
            status_code=400,
            detail="Token inválido"
        )

    # =========================================
    # VALIDAR EXPIRACIÓN
    # =========================================

    if datetime.utcnow().timestamp() > reset_token.expires_at.timestamp():
       raise HTTPException(
            status_code=400,
            detail="Token expirado"
        )

    # =========================================
    # OBTENER USUARIO
    # =========================================

    user = db.query(User).filter(
        User.id == reset_token.user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    # =========================================
    # ACTUALIZAR CONTRASEÑA
    # =========================================


    password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'

    if not re.match(password_regex, data.new_password):
        raise HTTPException(
            status_code=400,
            detail="Contraseña insegura"
        )
    
    user.password_hash = hash_password(data.new_password)

    # =========================================
    # ELIMINAR TOKEN (SEGURIDAD)
    # =========================================

    db.delete(reset_token)
    db.commit()

    return {
        "message": "Contraseña actualizada correctamente"
    }

# =====================================================
# LOGOUT
# =====================================================

@router.post("/logout/")
def logout(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Token requerido"
        )

    token = authorization.replace("Bearer ", "")

    # =========================================
    # BUSCAR SESIÓN
    # =========================================

    session = db.query(UserSession).filter(
        UserSession.token == token,
        UserSession.is_active == True
    ).first()

    if not session:
        return {"message": "Sesión ya cerrada"}

    # =========================================
    # DESACTIVAR SESIÓN
    # =========================================

    user_out = db.query(User).filter(User.id == session.user_id).first()

    session.is_active = False
    db.commit()

    if user_out:
        _notify_admins_access(
            db, user_out,
            title="Salida del sistema",
            message=f"{user_out.nombre} cerró sesión.",
        )

    return {"message": "Sesión cerrada correctamente"}

# =====================================================
# HEALTH CHECK
# =====================================================

@router.get("/health/")
def health_check():
    return {"status": "ok"}

# =====================================================
# HEARTBEAT — actualiza last_seen de la sesión activa
# =====================================================

@router.patch("/heartbeat/")
def heartbeat(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")

    token = authorization.replace("Bearer ", "")

    session = db.query(UserSession).filter(
        UserSession.token == token,
        UserSession.is_active == True
    ).first()

    if not session:
        raise HTTPException(status_code=401, detail="Sesión inválida")

    session.last_seen = datetime.utcnow()
    db.commit()
    return {"ok": True}

    
    
# =====================================================
# HELPER: Detecta si el plan venció y actualiza payment_status
# =====================================================

def _resolve_payment_status(company, db: Session) -> str:
    """
    Si el plan activo venció → cambia payment_status a 'expired' en DB y retorna 'expired'.
    Evita necesitar un cron job: se detecta en cada llamada a /me/.
    Solo aplica a empresas que NO están en flujo de pago pendiente.
    """
    if not company:
        return "active"

    current = getattr(company, "payment_status", "active") or "active"

    # Si ya está en flujo de pago/pendiente no pisar ese estado
    if current in ("pending_payment", "payment_submitted", "payment_rejected"):
        return current

    # Buscar el plan activo con fecha de vencimiento
    active_plan = (
        db.query(CompanyPlan)
        .filter(
            CompanyPlan.company_id == company.id_company,
            CompanyPlan.is_active == True,
        )
        .order_by(CompanyPlan.id.desc())
        .first()
    )

    if (
        active_plan
        and active_plan.expiration_date
        and active_plan.expiration_date < date.today()
        and current == "active"
    ):
        company.payment_status = "expired"
        try:
            db.commit()
        except Exception:
            db.rollback()
        return "expired"

    return current


# =====================================================
# USUARIO ACTUAL
# =====================================================

@router.get("/me/")
def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):

    # =========================================
    # VALIDAR TOKEN
    # =========================================

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Token requerido"
        )

    token = authorization.replace("Bearer ", "")

    payload = decode_access_token(token)

    # =========================================
    # VALIDAR SESIÓN ACTIVA
    # =========================================

    session = db.query(UserSession).filter(
        UserSession.token == token,
        UserSession.is_active == True
    ).first()

    if not session:
        raise HTTPException(
            status_code=401,
            detail="Sesión inválida o cerrada"
        )
    
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado"
        )

    email = payload.get("sub")

    if email is None:
        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )

    # =========================================
    # OBTENER USUARIO
    # =========================================

    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    # =========================================
    # OBTENER ROL Y EMPRESA
    # =========================================

    role    = db.query(Role).filter(Role.id == user.role_id).first()
    company = db.query(Company).filter(Company.id_company == user.company_id).first()

    # =========================================
    # RESPUESTA
    # =========================================
    return {
        "id": user.id,
        "nombre": user.nombre,
        "email": user.email,
        "role_id": user.role_id,
        "role": role.name if role else None,
        "company_id": user.company_id,
        "is_active": user.is_active,
        "is_system": role.is_system if role else False,
        "business_profile_id": company.business_profile_id if company else None,
        "payment_status": _resolve_payment_status(company, db),
        "upgrade_status": getattr(company, "upgrade_status", None) if company else None,
    }
    
    