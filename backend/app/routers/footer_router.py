from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
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


async def _get_user(authorization: str, db: AsyncSession):
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


async def _is_sysadmin(user: User, db: AsyncSession) -> bool:
    result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = result.scalar_one_or_none()
    return role.is_system if role else False


async def _get_config_int(db: AsyncSession, key: str, default: int) -> int:
    result = await db.execute(select(SystemConfig).where(SystemConfig.config_key == key, SystemConfig.is_active == True))
    cfg = result.scalar_one_or_none()
    try:
        return int(cfg.config_value) if cfg else default
    except (ValueError, TypeError):
        return default


@router.get("/online-companies")
async def get_online_companies(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    if not await _is_sysadmin(user, db):
        raise HTTPException(status_code=403, detail="Acceso restringido a SYSADMIN")

    cutoff = datetime.utcnow() - timedelta(minutes=ONLINE_THRESHOLD_MINUTES)
    result = await db.execute(select(UserSession).where(UserSession.is_active == True, UserSession.last_seen >= cutoff))
    active_sessions = result.scalars().all()

    user_ids = list({s.user_id for s in active_sessions})
    if not user_ids:
        return {"count": 0, "companies": []}

    result = await db.execute(select(User).where(User.id.in_(user_ids)))
    users_online = result.scalars().all()
    company_ids = list({u.company_id for u in users_online if u.company_id})

    result = await db.execute(select(Company).where(Company.id_company.in_(company_ids), Company.state == 1))
    companies = result.scalars().all()

    return {"count": len(companies), "companies": [{"id": c.id_company, "name": c.name} for c in companies]}


@router.get("/new-associates")
async def get_new_associates(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_user(authorization, db)

    days = await _get_config_int(db, "footer_new_associates_days", 30)
    result = await db.execute(select(SystemConfig).where(SystemConfig.config_key == "footer_ticker_enabled", SystemConfig.is_active == True))
    ticker_cfg = result.scalar_one_or_none()
    if ticker_cfg and ticker_cfg.config_value == "0":
        return {"interval_sec": 45, "associates": []}

    cutoff = datetime.utcnow() - timedelta(days=days)
    interval_sec = await _get_config_int(db, "footer_ticker_interval_sec", 45)

    result = await db.execute(
        select(Company, BusinessProfile, Plan)
        .outerjoin(BusinessProfile, Company.business_profile_id == BusinessProfile.id)
        .outerjoin(CompanyPlan, (CompanyPlan.company_id == Company.id_company) & (CompanyPlan.is_active == True))
        .outerjoin(Plan, CompanyPlan.plan_id == Plan.id)
        .where(Company.created_at >= cutoff, Company.state == 1)
        .order_by(Company.created_at.desc())
    )

    result_list = []
    for company, profile, plan in result.all():
        result_list.append({
            "id": company.id_company, "name": company.name,
            "business_profile": profile.name if profile else None,
            "plan": plan.name if plan else "Sin plan",
        })

    return {"interval_sec": interval_sec, "associates": result_list}


@router.get("/online-users")
async def get_online_users(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    is_sys = await _is_sysadmin(user, db)

    cutoff = datetime.utcnow() - timedelta(minutes=ONLINE_THRESHOLD_MINUTES)
    result = await db.execute(select(UserSession).where(UserSession.is_active == True, UserSession.last_seen >= cutoff))
    active_sessions = result.scalars().all()

    user_ids = list({s.user_id for s in active_sessions})
    if not user_ids:
        return {"count": 0, "users": []}

    stmt = select(User, Role).join(Role, User.role_id == Role.id).where(User.id.in_(user_ids), User.is_active == True)
    if not is_sys:
        stmt = stmt.where(User.company_id == user.company_id)

    result = await db.execute(stmt)
    rows = result.all()

    return {"count": len(rows), "users": [{"id": u.id, "nombre": u.nombre, "role": r.name} for u, r in rows]}
