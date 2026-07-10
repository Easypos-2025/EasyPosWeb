from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import Optional
from datetime import datetime, timezone, timedelta
import calendar
from app.database import get_db
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.user_model import User
from app.models.role_model import Role
from app.models.company_model import Company
from app.models.company_config_model import CompanyConfig

_BOG = timezone(timedelta(hours=-5))

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
            "has_tip": 0,
            "tip_percentage": 0.0,
            "tip_label": "Propina",
        }
    return {
        "has_pos_electronico": cfg.has_pos_electronico or 0,
        "pos_electronico_token": cfg.pos_electronico_token,
        "has_tip": cfg.has_tip or 0,
        "tip_percentage": float(cfg.tip_percentage or 0),
        "tip_label": cfg.tip_label or "Propina",
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
            c.business_profile_id,
            bp.name             AS profile_name,
            bp.name             AS business_profile_name,
            c.ext_db_host,
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

    # Campos Facturación / Propina
    if "has_tip" in body:
        cfg.has_tip = int(bool(body["has_tip"]))
    if "tip_percentage" in body:
        cfg.tip_percentage = float(body["tip_percentage"] or 0)
    if "tip_label" in body:
        cfg.tip_label = (body["tip_label"] or "Propina")[:50]

    await db.commit()
    await db.refresh(cfg)
    return _config_dict(cfg)


# ─── GET conteo de pendientes DIAN por empresa ───────────────────────────────

@router.get("/pe-pendientes-count")
async def get_pe_pendientes_count(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    await _require_sysadmin(authorization, db)
    rows = (await db.execute(text("""
        SELECT company_id, COUNT(*) AS pendientes
        FROM apidian_facturas_cufe
        WHERE FEExitosa = 0
        GROUP BY company_id
    """))).mappings().all()
    return {r["company_id"]: int(r["pendientes"]) for r in rows}


# ─── GET facturas DIAN de la BD externa de la empresa ────────────────────────

@router.get("/{company_id}/pe-facturas")
async def get_pe_facturas(
    company_id: int,
    date: Optional[str] = None,
    mode: Optional[str] = "day",
    fe: int = 0,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    await _require_sysadmin(authorization, db)

    target = date or datetime.now(_BOG).date().isoformat()

    if mode == "month":
        ym  = target[:7]
        y, m = int(ym[:4]), int(ym[5:7])
        d1  = f"{ym}-01"
        d2  = f"{ym}-{calendar.monthrange(y, m)[1]:02d}"
    else:
        d1 = d2 = target

    if fe == 0:
        # Pendientes: mostrar todos sin importar fecha
        rows = (await db.execute(text("""
            SELECT
                DATE_FORMAT(Fecha, '%Y-%m-%d') AS fecha,
                Prefix                         AS prefijo,
                Nro_Factura                    AS nro_folio,
                Valor                          AS valor,
                Nro_Caja                       AS cuenta,
                Cedula                         AS cliente
            FROM apidian_facturas_cufe
            WHERE company_id = :cid
              AND FEExitosa  = 0
            ORDER BY Fecha, Nro_Factura
            LIMIT 1000
        """), {"cid": company_id})).mappings().all()
    else:
        rows = (await db.execute(text("""
            SELECT
                DATE_FORMAT(Fecha, '%Y-%m-%d') AS fecha,
                Prefix                         AS prefijo,
                Nro_Factura                    AS nro_folio,
                Valor                          AS valor,
                Nro_Caja                       AS cuenta,
                Cedula                         AS cliente
            FROM apidian_facturas_cufe
            WHERE company_id = :cid
              AND FEExitosa  = 1
              AND Fecha BETWEEN :d1 AND :d2
            ORDER BY Fecha, Nro_Factura
            LIMIT 500
        """), {"cid": company_id, "d1": d1, "d2": d2})).mappings().all()
    return [dict(r) for r in rows]
