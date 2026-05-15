import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

from app.database import get_db
from app.models.invitation_model import InvitationToken
from app.models.user_model import User
from app.models.role_model import Role
from app.models.company_model import Company
from app.models.user_session_model import UserSession
from app.auth.jwt_handler import decode_access_token
from app.services.plan_limits_service import check_limit

router = APIRouter(prefix="/invitations", tags=["Invitations"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
TOKEN_TTL_HOURS = 48


async def _get_user(authorization: str, db: AsyncSession) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    result = await db.execute(select(UserSession).where(UserSession.token == token, UserSession.is_active == True))
    if not result.scalar_one_or_none() or not payload:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    result = await db.execute(select(User).where(User.email == payload.get("sub")))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


async def _can_invite(user: User, db: AsyncSession) -> bool:
    result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = result.scalar_one_or_none()
    if not role:
        return False
    return role.is_system or "admin" in role.name.lower()


@router.post("")
async def create_invitation(data: dict, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    if not await _can_invite(user, db):
        raise HTTPException(status_code=403, detail="Sin permiso para generar invitaciones")

    role_id = data.get("role_id")
    company_id = data.get("company_id")
    if not role_id:
        raise HTTPException(status_code=400, detail="role_id es requerido")

    result = await db.execute(select(Role).where(Role.id == user.role_id))
    current_role = result.scalar_one_or_none()
    is_sys = current_role.is_system if current_role else False
    target_company_id = company_id if (is_sys and company_id) else user.company_id

    result = await db.execute(select(Role).where(Role.id == role_id, Role.company_id == target_company_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    token = uuid.uuid4().hex
    expires_at = datetime.utcnow() + timedelta(hours=TOKEN_TTL_HOURS)
    inv = InvitationToken(token=token, company_id=target_company_id, role_id=role_id,
                          created_by=user.id, expires_at=expires_at)
    db.add(inv)
    await db.commit()
    await db.refresh(inv)
    return {"token": token, "expires_at": expires_at.isoformat(), "role_name": role.name}


@router.get("/{token}")
async def get_invitation(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InvitationToken).where(InvitationToken.token == token))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invitación no válida")
    if inv.used_at:
        raise HTTPException(status_code=410, detail="Esta invitación ya fue utilizada")
    if datetime.utcnow() > inv.expires_at:
        raise HTTPException(status_code=410, detail="Esta invitación ha expirado")
    result = await db.execute(select(Company).where(Company.id_company == inv.company_id))
    company = result.scalar_one_or_none()
    result = await db.execute(select(Role).where(Role.id == inv.role_id))
    role = result.scalar_one_or_none()
    return {"company_name": company.name if company else "Empresa",
            "role_name": role.name if role else "Usuario", "expires_at": inv.expires_at.isoformat()}


@router.post("/{token}/register")
async def register_via_invitation(token: str, data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InvitationToken).where(InvitationToken.token == token))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invitación no válida")
    if inv.used_at:
        raise HTTPException(status_code=410, detail="Esta invitación ya fue utilizada")
    if datetime.utcnow() > inv.expires_at:
        raise HTTPException(status_code=410, detail="Esta invitación ha expirado")
    nombre = (data.get("nombre") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "")
    if not nombre:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Email inválido")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres")
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese email")
    await check_limit(inv.company_id, "max_users", User, db)
    db.add(User(nombre=nombre, email=email, password_hash=pwd_context.hash(password),
                role_id=inv.role_id, company_id=inv.company_id, is_active=True))
    inv.used_at = datetime.utcnow()
    await db.commit()
    return {"ok": True, "message": "Cuenta creada. Ya puedes iniciar sesión."}
