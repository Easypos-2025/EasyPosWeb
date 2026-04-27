import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.database import get_db
from app.models.invitation_model import InvitationToken
from app.models.user_model import User
from app.models.role_model import Role
from app.models.company_model import Company
from app.models.user_session_model import UserSession
from app.auth.jwt_handler import decode_access_token

router = APIRouter(prefix="/invitations", tags=["Invitations"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
TOKEN_TTL_HOURS = 48


# ── Auth helper ──────────────────────────────────────────────────────────────
def _get_user(authorization: str, db: Session) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token   = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    session = db.query(UserSession).filter(
        UserSession.token == token, UserSession.is_active == True
    ).first()
    if not session or not payload:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


def _can_invite(user: User, db: Session) -> bool:
    role = db.query(Role).filter(Role.id == user.role_id).first()
    if not role:
        return False
    if role.is_system:
        return True
    return "admin" in role.name.lower()


# ── POST /invitations — generar token ───────────────────────────────────────
@router.post("")
def create_invitation(
    data: dict,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)
    if not _can_invite(user, db):
        raise HTTPException(status_code=403, detail="Sin permiso para generar invitaciones")

    role_id    = data.get("role_id")
    company_id = data.get("company_id")  # SYSADMIN puede especificar empresa destino
    if not role_id:
        raise HTTPException(status_code=400, detail="role_id es requerido")

    # Determinar empresa destino
    is_sys = _can_invite(user, db) and (
        db.query(Role).filter(Role.id == user.role_id).first().is_system
    )
    target_company_id = company_id if (is_sys and company_id) else user.company_id

    role = db.query(Role).filter(
        Role.id == role_id,
        Role.company_id == target_company_id
    ).first()
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    token      = uuid.uuid4().hex
    expires_at = datetime.utcnow() + timedelta(hours=TOKEN_TTL_HOURS)

    inv = InvitationToken(
        token=token,
        company_id=target_company_id,
        role_id=role_id,
        created_by=user.id,
        expires_at=expires_at,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)

    return {
        "token":      token,
        "expires_at": expires_at.isoformat(),
        "role_name":  role.name,
    }


# ── GET /invitations/:token — info pública del token ────────────────────────
@router.get("/{token}")
def get_invitation(token: str, db: Session = Depends(get_db)):
    inv = db.query(InvitationToken).filter(InvitationToken.token == token).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invitación no válida")
    if inv.used_at:
        raise HTTPException(status_code=410, detail="Esta invitación ya fue utilizada")
    if datetime.utcnow() > inv.expires_at:
        raise HTTPException(status_code=410, detail="Esta invitación ha expirado")

    company = db.query(Company).filter(Company.id_company == inv.company_id).first()
    role    = db.query(Role).filter(Role.id == inv.role_id).first()

    return {
        "company_name": company.name if company else "Empresa",
        "role_name":    role.name    if role    else "Usuario",
        "expires_at":   inv.expires_at.isoformat(),
    }


# ── POST /invitations/:token/register — registrar usuario ───────────────────
@router.post("/{token}/register")
def register_via_invitation(token: str, data: dict, db: Session = Depends(get_db)):
    inv = db.query(InvitationToken).filter(InvitationToken.token == token).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invitación no válida")
    if inv.used_at:
        raise HTTPException(status_code=410, detail="Esta invitación ya fue utilizada")
    if datetime.utcnow() > inv.expires_at:
        raise HTTPException(status_code=410, detail="Esta invitación ha expirado")

    nombre   = (data.get("nombre") or "").strip()
    email    = (data.get("email")  or "").strip().lower()
    password = (data.get("password") or "")

    if not nombre:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Email inválido")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Ya existe un usuario con ese email")

    new_user = User(
        nombre=nombre,
        email=email,
        password_hash=pwd_context.hash(password),
        role_id=inv.role_id,
        company_id=inv.company_id,
        is_active=True,
    )
    db.add(new_user)

    inv.used_at = datetime.utcnow()
    db.commit()

    return {"ok": True, "message": "Cuenta creada. Ya puedes iniciar sesión."}
