from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.database import get_db
from app.models.task_model import Task
from app.models.user_model import User
from app.models.asset_model import Asset
from app.models.company_model import Company
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.role_model import Role
from datetime import datetime, timezone, timedelta
from typing import Optional

_BOG = timezone(timedelta(hours=-5))

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_stats(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")

    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)

    result = await db.execute(
        select(UserSession).where(UserSession.token == token, UserSession.is_active == True)
    )
    session = result.scalar_one_or_none()

    if not session or payload is None:
        raise HTTPException(status_code=401, detail="Sesión inválida")

    email = payload.get("sub")
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = result.scalar_one_or_none()
    is_system = role.is_system if role else False

    if is_system:
        total_companies = (await db.execute(select(func.count()).select_from(Company))).scalar()
        total_users     = (await db.execute(select(func.count()).select_from(User))).scalar()
        total_assets    = (await db.execute(select(func.count()).select_from(Asset))).scalar()
        total_tasks     = (await db.execute(select(func.count()).select_from(Task))).scalar()
    else:
        total_companies = 1
        total_users  = (await db.execute(select(func.count()).select_from(User).where(User.company_id == user.company_id))).scalar()
        total_assets = (await db.execute(select(func.count()).select_from(Asset).where(Asset.company_id == user.company_id))).scalar() if hasattr(Asset, 'company_id') else (await db.execute(select(func.count()).select_from(Asset))).scalar()
        total_tasks  = (await db.execute(select(func.count()).select_from(Task))).scalar()

    return {
        "total_companies": total_companies,
        "total_users":     total_users,
        "total_assets":    total_assets,
        "total_tasks":     total_tasks,
        "is_system":       is_system,
    }


# ─── Helper SYSADMIN ──────────────────────────────────────────────────────────

async def _require_sysadmin(authorization: str, db: AsyncSession) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido")
    result = await db.execute(
        select(UserSession).where(UserSession.token == token, UserSession.is_active == True)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=401, detail="Sesión inválida")
    uid = payload.get("user_id")
    user = await db.get(User, int(uid)) if uid else None
    if not user:
        r2 = await db.execute(select(User).where(User.email == payload.get("sub")))
        user = r2.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    role = await db.get(Role, user.role_id)
    if not role or not role.is_system:
        raise HTTPException(status_code=403, detail="Acceso restringido a SYSADMIN")
    return user


# ─── Sesiones activas en este momento ────────────────────────────────────────

@router.get("/sysadmin/active-sessions")
async def get_active_sessions(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    await _require_sysadmin(authorization, db)

    companies = (await db.execute(text("""
        SELECT c.id_company,
               c.name                              AS company_name,
               COUNT(DISTINCT us.user_id)          AS active_users,
               MAX(us.last_seen - INTERVAL 5 HOUR) AS last_activity
        FROM user_sessions us
        JOIN users     u ON u.id          = us.user_id
        JOIN companies c ON c.id_company  = u.company_id
        WHERE us.is_active = 1
          AND us.last_seen >= (UTC_TIMESTAMP() - INTERVAL 6 MINUTE)
        GROUP BY c.id_company, c.name
        ORDER BY active_users DESC, c.name
    """))).mappings().all()

    users_rows = (await db.execute(text("""
        SELECT u.id                                AS user_id,
               u.nombre                           AS name,
               c.name                             AS company_name,
               (us.created_at - INTERVAL 5 HOUR)  AS session_start,
               (us.last_seen  - INTERVAL 5 HOUR)  AS last_seen,
               us.ip
        FROM user_sessions us
        JOIN users     u ON u.id          = us.user_id
        JOIN companies c ON c.id_company  = u.company_id
        WHERE us.is_active = 1
          AND us.last_seen >= (UTC_TIMESTAMP() - INTERVAL 6 MINUTE)
        ORDER BY us.last_seen DESC
        LIMIT 300
    """))).mappings().all()

    def _s(v):
        return v.isoformat() if hasattr(v, "isoformat") else str(v) if v else None

    return {
        "companies": [
            {**dict(r), "last_activity": _s(r["last_activity"])}
            for r in companies
        ],
        "users": [
            {**dict(r), "session_start": _s(r["session_start"]), "last_seen": _s(r["last_seen"])}
            for r in users_rows
        ],
    }


# ─── Conexiones del día / mes ─────────────────────────────────────────────────

@router.get("/sysadmin/connections")
async def get_sysadmin_connections(
    date: Optional[str] = None,
    mode: Optional[str] = "day",
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    await _require_sysadmin(authorization, db)
    target = date or datetime.now(_BOG).date().isoformat()

    if mode == "month":
        ym = target[:7]
        f_comp = "DATE_FORMAT(us.created_at - INTERVAL 5 HOUR, '%Y-%m') = :p"
        f_user = "DATE_FORMAT(us.created_at - INTERVAL 5 HOUR, '%Y-%m') = :p"
        p = ym
    else:
        f_comp = "DATE(us.created_at - INTERVAL 5 HOUR) = :p"
        f_user = "DATE(us.created_at - INTERVAL 5 HOUR) = :p"
        p = target

    companies = (await db.execute(text(f"""
        SELECT c.id_company, c.name AS company_name,
               COUNT(us.id) AS login_count,
               MAX(us.created_at) AS last_login
        FROM user_sessions us
        JOIN users u  ON u.id          = us.user_id
        JOIN companies c ON c.id_company = u.company_id
        WHERE {f_comp}
        GROUP BY c.id_company, c.name
        ORDER BY login_count DESC
    """), {"p": p})).mappings().all()

    users_rows = (await db.execute(text(f"""
        SELECT u.id AS user_id, u.nombre AS name,
               c.name AS company_name,
               (us.created_at - INTERVAL 5 HOUR) AS login_time,
               us.ip
        FROM user_sessions us
        JOIN users u  ON u.id          = us.user_id
        JOIN companies c ON c.id_company = u.company_id
        WHERE {f_user}
        ORDER BY us.created_at DESC
        LIMIT 300
    """), {"p": p})).mappings().all()

    def _s(v):
        return v.isoformat() if hasattr(v, "isoformat") else str(v) if v else None

    return {
        "companies": [
            {**dict(r), "last_login": _s(r["last_login"])}
            for r in companies
        ],
        "users": [
            {**dict(r), "login_time": _s(r["login_time"])}
            for r in users_rows
        ],
    }


# ─── Facturación de una empresa (día / mes) ───────────────────────────────────

@router.get("/sysadmin/company-billing")
async def get_sysadmin_company_billing(
    company_id: int,
    date: Optional[str] = None,
    mode: Optional[str] = "day",
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    await _require_sysadmin(authorization, db)
    target = date or datetime.now(_BOG).date().isoformat()

    if mode == "month":
        ym = target[:7]
        df = "DATE_FORMAT(i.date, '%Y-%m') = :p"
        dr = "DATE_FORMAT(rc.date, '%Y-%m') = :p"
        p  = ym
    else:
        df = "i.date  = :p"
        dr = "rc.date = :p"
        p  = target

    fact = (await db.execute(text(f"""
        SELECT COUNT(*) AS cnt,
               COALESCE(SUM(COALESCE(cash_amount,0)+COALESCE(credit_card_amount,0)
                            +COALESCE(debit_card_amount,0)+COALESCE(adjustment,0)
                            -COALESCE(discount,0)),0) AS total
        FROM pos_invoices i
        WHERE i.company_id = :cid AND {df} AND i.voided = 0
    """), {"cid": company_id, "p": p})).mappings().one()

    rec = (await db.execute(text(f"""
        SELECT COUNT(*) AS cnt,
               COALESCE(SUM(COALESCE(cash_amount,0)+COALESCE(credit_card_amount,0)
                            +COALESCE(debit_card_amount,0)+COALESCE(adjustment,0)
                            -COALESCE(discount,0)),0) AS total
        FROM pos_receipts rc
        WHERE rc.company_id = :cid AND {dr} AND rc.voided = 0
    """), {"cid": company_id, "p": p})).mappings().one()

    return {
        "facturas": {"count": int(fact["cnt"]), "total": float(fact["total"])},
        "recibos":  {"count": int(rec["cnt"]),  "total": float(rec["total"])},
    }
