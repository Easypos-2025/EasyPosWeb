"""
========================================================
COMPANY THEME ROUTER
========================================================

Gestión de tema visual por empresa
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.role_model import Role
from app.models.company_theme_model import CompanyTheme


router = APIRouter(
    prefix="/company-theme",
    tags=["Company Theme"]
)


# =====================================================
# GET COLORS ONLY — sin logo (consulta rápida)
# Úsalo para aplicar colores al cargar la página.
# Para obtener también el logo usa GET /{company_id}
# =====================================================
@router.get("/{company_id}/colors")
def get_theme_colors(
    company_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    is_system = role.is_system if role else False
    if not is_system and current_user.company_id != company_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    from sqlalchemy import select
    from app.models.company_theme_model import CompanyTheme as CT

    row = db.execute(
        select(
            CT.topbar_color, CT.sidebar_color, CT.bg_color,
            CT.font_size, CT.font_color
        ).where(CT.company_id == company_id)
    ).first()

    if not row:
        return {
            "topbar_color": "#1e3a5f", "sidebar_color": "#1a2535",
            "bg_color": "#f1f5f9", "font_size": 16, "font_color": "#1e293b"
        }

    return {
        "topbar_color":  row.topbar_color  or "#1e3a5f",
        "sidebar_color": row.sidebar_color or "#1a2535",
        "bg_color":      row.bg_color      or "#f1f5f9",
        "font_size":     row.font_size     or 16,
        "font_color":    row.font_color    or "#1e293b",
    }


# =====================================================
# GET THEME COMPLETO — incluye logo (puede ser lento)
# =====================================================
@router.get("/{company_id}")
def get_theme(
    company_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    is_system = role.is_system if role else False
    if not is_system and current_user.company_id != company_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    theme = db.query(CompanyTheme).filter(
        CompanyTheme.company_id == company_id
    ).first()

    if not theme:
        return {
            "topbar_color": "#1f2937",
            "sidebar_color": "#111827",
            "bg_color": "#f9fafb",
            "logo": None,
            "font_size": 14,
            "font_color": "#ffffff"
        }

    return theme


# =====================================================
# CREATE / UPDATE THEME
# =====================================================
from fastapi import Request

@router.put("/{company_id}")
async def save_theme(
    company_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):

    data = await request.json()

    # 🔐 VALIDACIÓN
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    is_system = role.is_system if role else False
    if not is_system and current_user.company_id != company_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    theme = db.query(CompanyTheme).filter(
        CompanyTheme.company_id == company_id
    ).first()

    # CREAR SI NO EXISTE
    if not theme:
        theme = CompanyTheme(company_id=company_id)
        db.add(theme)

    # CAMPOS PERMITIDOS
    allowed_fields = [
        "topbar_color",
        "sidebar_color",
        "bg_color",
        "logo",
        "font_size",
        "font_color"
    ]

    for key, value in data.items():
        if key in allowed_fields:
            setattr(theme, key, value)

    db.commit()
    db.refresh(theme)

    return theme
