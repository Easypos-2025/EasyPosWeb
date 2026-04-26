from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.database import get_db
from app.models.user_model import User
from app.models.role_model import Role
from app.models.user_session_model import UserSession
from app.models.company_model import Company
from app.models.business_profile_model import BusinessProfile
from app.models.company_plan_model import CompanyPlan
from app.models.plan_model import Plan
from app.models.system_config_model import SystemConfig
from app.auth.jwt_handler import decode_access_token

router = APIRouter(prefix="/footer", tags=["Footer"])

ONLINE_THRESHOLD_MINUTES = 5


def _get_user(authorization: str, db: Session):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
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


def _is_sysadmin(user: User, db: Session) -> bool:
    role = db.query(Role).filter(Role.id == user.role_id).first()
    return role.is_system if role else False


def _get_config_int(db: Session, key: str, default: int) -> int:
    cfg = db.query(SystemConfig).filter(
        SystemConfig.config_key == key,
        SystemConfig.is_active == True
    ).first()
    try:
        return int(cfg.config_value) if cfg else default
    except (ValueError, TypeError):
        return default


# -------------------------------------------------------
# GET /online-companies — SYSADMIN: empresas con sesiones activas
# -------------------------------------------------------
@router.get("/online-companies")
def get_online_companies(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)
    if not _is_sysadmin(user, db):
        raise HTTPException(status_code=403, detail="Acceso restringido a SYSADMIN")

    cutoff = datetime.utcnow() - timedelta(minutes=ONLINE_THRESHOLD_MINUTES)

    active_sessions = db.query(UserSession).filter(
        UserSession.is_active == True,
        UserSession.last_seen >= cutoff
    ).all()

    user_ids = list({s.user_id for s in active_sessions})

    if not user_ids:
        return {"count": 0, "companies": []}

    users_online = db.query(User).filter(User.id.in_(user_ids)).all()
    company_ids = list({u.company_id for u in users_online if u.company_id})

    companies = db.query(Company).filter(
        Company.id_company.in_(company_ids),
        Company.state == 1
    ).all()

    return {
        "count": len(companies),
        "companies": [{"id": c.id_company, "name": c.name} for c in companies]
    }


# -------------------------------------------------------
# GET /new-associates — todos: nuevos asociados del último mes
# -------------------------------------------------------
@router.get("/new-associates")
def get_new_associates(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    _get_user(authorization, db)

    days = _get_config_int(db, "footer_new_associates_days", 30)
    ticker_enabled_cfg = db.query(SystemConfig).filter(
        SystemConfig.config_key == "footer_ticker_enabled",
        SystemConfig.is_active == True
    ).first()
    if ticker_enabled_cfg and ticker_enabled_cfg.config_value == "0":
        return {"interval_sec": 45, "associates": []}

    cutoff = datetime.utcnow() - timedelta(days=days)
    interval_sec = _get_config_int(db, "footer_ticker_interval_sec", 45)

    companies = (
        db.query(Company, BusinessProfile, Plan)
        .outerjoin(BusinessProfile, Company.business_profile_id == BusinessProfile.id)
        .outerjoin(
            CompanyPlan,
            (CompanyPlan.company_id == Company.id_company) & (CompanyPlan.is_active == True)
        )
        .outerjoin(Plan, CompanyPlan.plan_id == Plan.id)
        .filter(
            Company.created_at >= cutoff,
            Company.state == 1
        )
        .order_by(Company.created_at.desc())
        .all()
    )

    result = []
    for company, profile, plan in companies:
        result.append({
            "id": company.id_company,
            "name": company.name,
            "business_profile": profile.name if profile else None,
            "plan": plan.name if plan else "Sin plan",
        })

    return {"interval_sec": interval_sec, "associates": result}


# -------------------------------------------------------
# GET /online-users — usuarios conectados
# SYSADMIN: todos | resto: solo su empresa
# -------------------------------------------------------
@router.get("/online-users")
def get_online_users(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)
    is_sys = _is_sysadmin(user, db)

    cutoff = datetime.utcnow() - timedelta(minutes=ONLINE_THRESHOLD_MINUTES)

    active_sessions = db.query(UserSession).filter(
        UserSession.is_active == True,
        UserSession.last_seen >= cutoff
    ).all()

    user_ids = list({s.user_id for s in active_sessions})

    if not user_ids:
        return {"count": 0, "users": []}

    query = db.query(User, Role).join(Role, User.role_id == Role.id).filter(
        User.id.in_(user_ids),
        User.is_active == True
    )

    if not is_sys:
        query = query.filter(User.company_id == user.company_id)

    rows = query.all()

    return {
        "count": len(rows),
        "users": [
            {"id": u.id, "nombre": u.nombre, "role": r.name}
            for u, r in rows
        ]
    }
