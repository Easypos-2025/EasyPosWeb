from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.role_model import Role
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
    """Convierte el objeto SQLAlchemy a dict — evita serialización de relaciones."""
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


def _authorize(current_user, company_id: int, db: Session):
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    is_system = role.is_system if role else False
    if not is_system and current_user.company_id != company_id:
        raise HTTPException(status_code=403, detail="Not authorized")


# ── GET colores rápido (sin logo) ─────────────────────────────
@router.get("/{company_id}/colors")
def get_theme_colors(
    company_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    _authorize(current_user, company_id, db)
    theme = db.query(CompanyTheme).filter(CompanyTheme.company_id == company_id).first()
    d     = _serialize(theme)
    d.pop("logo", None)   # no incluir el logo en la consulta rápida
    return d


# ── GET tema completo (incluye logo) ──────────────────────────
@router.get("/{company_id}")
def get_theme(
    company_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    _authorize(current_user, company_id, db)
    theme = db.query(CompanyTheme).filter(CompanyTheme.company_id == company_id).first()
    return _serialize(theme)


# ── PUT crear / actualizar tema ───────────────────────────────
@router.put("/{company_id}")
async def save_theme(
    company_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    _authorize(current_user, company_id, db)
    data = await request.json()

    theme = db.query(CompanyTheme).filter(CompanyTheme.company_id == company_id).first()
    if not theme:
        theme = CompanyTheme(company_id=company_id)
        db.add(theme)

    allowed = ["topbar_color", "sidebar_color", "bg_color", "logo", "font_size", "font_color"]
    for key, value in data.items():
        if key in allowed:
            setattr(theme, key, value)

    db.commit()
    db.refresh(theme)
    return _serialize(theme)
