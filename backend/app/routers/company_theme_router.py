from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.role_model import Role
from app.models.user_model import User
from app.models.company_theme_model import CompanyTheme

router = APIRouter(prefix="/company-theme", tags=["Company Theme"])

DEFAULTS = {
    "topbar_color":  "#1e3a5f",
    "sidebar_color": "#1a2535",
    "bg_color":      "#f1f5f9",
    "logo":          None,
    "font_size":     "16",
    "font_color":    "#1e293b",
}


def _serialize(theme) -> dict:
    if not theme:
        return DEFAULTS.copy()
    return {
        "topbar_color":  theme.topbar_color  or DEFAULTS["topbar_color"],
        "sidebar_color": theme.sidebar_color or DEFAULTS["sidebar_color"],
        "bg_color":      theme.bg_color      or DEFAULTS["bg_color"],
        "logo":          theme.logo,
        "font_size":     theme.font_size     or DEFAULTS["font_size"],
        "font_color":    theme.font_color    or DEFAULTS["font_color"],
    }


async def _authorize(current_user, company_id: int, db: AsyncSession):
    if current_user.company_id == company_id:
        return
    role = await db.get(Role, current_user.role_id)
    if role and role.is_system:
        return
    # Permite acceso si el usuario tiene una cuenta con el mismo email en la empresa destino
    # (usuario multi-sede que cambió de contexto sin cerrar sesión)
    if current_user.email:
        match = (await db.execute(
            select(User).where(User.email == current_user.email, User.company_id == company_id)
        )).scalar_one_or_none()
        if match:
            return
    raise HTTPException(status_code=403, detail="Not authorized")


@router.get("/{company_id}/colors")
async def get_theme_colors(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    await _authorize(current_user, company_id, db)
    result = await db.execute(select(CompanyTheme).where(CompanyTheme.company_id == company_id))
    theme = result.scalar_one_or_none()
    d = _serialize(theme)
    d.pop("logo", None)
    return d


@router.get("/{company_id}")
async def get_theme(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    await _authorize(current_user, company_id, db)
    result = await db.execute(select(CompanyTheme).where(CompanyTheme.company_id == company_id))
    return _serialize(result.scalar_one_or_none())


@router.put("/{company_id}")
async def save_theme(
    company_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    await _authorize(current_user, company_id, db)
    data = await request.json()
    result = await db.execute(select(CompanyTheme).where(CompanyTheme.company_id == company_id))
    theme = result.scalar_one_or_none()
    if not theme:
        theme = CompanyTheme(company_id=company_id)
        db.add(theme)
    for key, value in data.items():
        if key in ["topbar_color", "sidebar_color", "bg_color", "logo", "font_size", "font_color"]:
            setattr(theme, key, value)
    await db.commit()
    await db.refresh(theme)
    return _serialize(theme)
