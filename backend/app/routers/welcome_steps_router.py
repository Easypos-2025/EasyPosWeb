from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.profile_welcome_step_model import ProfileWelcomeStep
from app.models.user_model import User
from app.models.role_model import Role
from app.models.user_session_model import UserSession
from app.auth.jwt_handler import decode_access_token

router = APIRouter(prefix="/welcome-steps", tags=["Welcome Steps"])


async def _get_user(authorization: str, db: AsyncSession) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    result = await db.execute(select(UserSession).where(UserSession.token == token, UserSession.is_active == True))
    if not result.scalar_one_or_none() or not payload:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    uid = payload.get("user_id")
    user = await db.get(User, int(uid)) if uid else None
    if not user:
        result = await db.execute(select(User).where(User.email == payload.get("sub")))
        user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


async def _is_sysadmin(user: User, db: AsyncSession) -> bool:
    role = (await db.execute(select(Role).where(Role.id == user.role_id))).scalar_one_or_none()
    return bool(role and role.is_system)


def _ser(s: ProfileWelcomeStep) -> dict:
    return {
        "id":                  s.id,
        "business_profile_id": s.business_profile_id,
        "step_number":         s.step_number,
        "icon":                s.icon,
        "title":               s.title,
        "description":         s.description,
        "route_hint":          s.route_hint,
        "is_active":           s.is_active,
    }


# ── GET para el usuario actual (filtra por business_profile_id de su empresa) ──
@router.get("")
async def get_welcome_steps(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)

    from app.models.company_model import Company
    company = (await db.execute(select(Company).where(Company.id_company == user.company_id))).scalar_one_or_none()
    profile_id = company.business_profile_id if company else None

    if not profile_id:
        return []

    result = await db.execute(
        select(ProfileWelcomeStep)
        .where(ProfileWelcomeStep.business_profile_id == profile_id, ProfileWelcomeStep.is_active == True)
        .order_by(ProfileWelcomeStep.step_number)
    )
    return [_ser(s) for s in result.scalars().all()]


# ── SYSADMIN: listar todos los pasos de un perfil ──
@router.get("/profile/{profile_id}")
async def list_steps_by_profile(profile_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    if not await _is_sysadmin(user, db):
        raise HTTPException(status_code=403, detail="Solo SYSADMIN")
    result = await db.execute(
        select(ProfileWelcomeStep)
        .where(ProfileWelcomeStep.business_profile_id == profile_id)
        .order_by(ProfileWelcomeStep.step_number)
    )
    return [_ser(s) for s in result.scalars().all()]


# ── SYSADMIN: crear paso ──
@router.post("")
async def create_step(data: dict, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    if not await _is_sysadmin(user, db):
        raise HTTPException(status_code=403, detail="Solo SYSADMIN")
    s = ProfileWelcomeStep(
        business_profile_id=data.get("business_profile_id"),
        step_number=data.get("step_number", 0),
        icon=data.get("icon", "bi-star"),
        title=data.get("title", ""),
        description=data.get("description", ""),
        route_hint=data.get("route_hint"),
        is_active=data.get("is_active", True),
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return _ser(s)


# ── SYSADMIN: editar paso ──
@router.put("/{step_id}")
async def update_step(step_id: int, data: dict, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    if not await _is_sysadmin(user, db):
        raise HTTPException(status_code=403, detail="Solo SYSADMIN")
    s = await db.get(ProfileWelcomeStep, step_id)
    if not s:
        raise HTTPException(status_code=404, detail="Paso no encontrado")
    for field in ("step_number", "icon", "title", "description", "route_hint", "is_active"):
        if field in data:
            setattr(s, field, data[field])
    await db.commit()
    await db.refresh(s)
    return _ser(s)


# ── SYSADMIN: eliminar paso ──
@router.delete("/{step_id}")
async def delete_step(step_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    if not await _is_sysadmin(user, db):
        raise HTTPException(status_code=403, detail="Solo SYSADMIN")
    s = await db.get(ProfileWelcomeStep, step_id)
    if not s:
        raise HTTPException(status_code=404, detail="Paso no encontrado")
    await db.delete(s)
    await db.commit()
    return {"ok": True}
