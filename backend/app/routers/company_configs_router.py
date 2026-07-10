from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import Optional
from app.database import get_db
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.user_model import User
from app.models.role_model import Role
from app.models.company_model import Company
from app.models.company_config_model import CompanyConfig

router = APIRouter(prefix="/company-configs", tags=["Company Configs"])


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


def _config_dict(cfg: Optional[CompanyConfig]) -> dict:
    if not cfg:
        return {
            "has_pos_electronico": 0,
            "pos_electronico_token": None,
        }
    return {
        "has_pos_electronico": cfg.has_pos_electronico or 0,
        "pos_electronico_token": cfg.pos_electronico_token,
    }


# ─── GET todas las empresas + su config (SYSADMIN) ───────────────────────────

@router.get("/")
async def list_company_configs(
    pe_only: Optional[bool] = False,
    search: Optional[str] = None,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    await _require_sysadmin(authorization, db)

    rows = (await db.execute(text("""
        SELECT
            c.id_company,
            c.name,
            c.state,
            bp.name  AS profile_name,
            COALESCE(cc.has_pos_electronico, 0)  AS has_pos_electronico,
            cc.pos_electronico_token
        FROM companies c
        LEFT JOIN business_profiles bp ON bp.id = c.business_profile_id
        LEFT JOIN company_configs   cc ON cc.company_id = c.id_company
        WHERE c.state = 1
          AND (:search IS NULL OR c.name LIKE :like)
          AND (:pe_only = 0 OR COALESCE(cc.has_pos_electronico, 0) = 1)
        ORDER BY c.name
    """), {
        "search": search,
        "like": f"%{search}%" if search else None,
        "pe_only": 1 if pe_only else 0,
    })).mappings().all()

    return [dict(r) for r in rows]


# ─── GET config de una empresa ────────────────────────────────────────────────

@router.get("/{company_id}")
async def get_company_config(
    company_id: int,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    await _require_sysadmin(authorization, db)
    result = await db.execute(
        select(CompanyConfig).where(CompanyConfig.company_id == company_id)
    )
    return _config_dict(result.scalar_one_or_none())


# ─── PUT upsert config de una empresa ────────────────────────────────────────

@router.put("/{company_id}")
async def upsert_company_config(
    company_id: int,
    body: dict,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    await _require_sysadmin(authorization, db)

    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    result = await db.execute(
        select(CompanyConfig).where(CompanyConfig.company_id == company_id)
    )
    cfg = result.scalar_one_or_none()

    if not cfg:
        cfg = CompanyConfig(company_id=company_id)
        db.add(cfg)

    # Campos POS Electrónico
    if "has_pos_electronico" in body:
        cfg.has_pos_electronico = int(bool(body["has_pos_electronico"]))
    if "pos_electronico_token" in body:
        cfg.pos_electronico_token = body["pos_electronico_token"] or None

    await db.commit()
    await db.refresh(cfg)
    return _config_dict(cfg)
