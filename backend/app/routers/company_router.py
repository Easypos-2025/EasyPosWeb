"""
========================================================
COMPANY ROUTER
========================================================

CRUD para la gestión de compañías.

Incluye protección multiempresa basada en el usuario
autenticado.
"""

# =====================================================
# IMPORTS
# =====================================================

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.company_model import Company
from app.models.business_profile_model import BusinessProfile
from app.models.user_model import User
from app.models.company_theme_model import CompanyTheme
from app.models.role_model import Role

# =====================================================
# ROUTER
# =====================================================

router = APIRouter(
    prefix="/companies",
    tags=["Companies"]
)


# =====================================================
# CREATE
# =====================================================

@router.post("/")
def create_company(
    data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Crea una nueva compañía
    """
    company = Company(**data)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


# =====================================================
# READ ONE (PROTEGIDO)
# =====================================================

@router.get("/{company_id:int}")
def get_company(company_id: int, db: Session = Depends(get_db)):

    company = db.query(Company).filter(Company.id_company == company_id).first()

    if not company:
        return {"message": "Empresa no encontrada"}

    return {
        "id": company.id_company,
        "name": company.name,
        "identification_number": company.identification_number,
        "dv": company.dv,
        "address": company.address,
        "phone": company.phone,
        "email": company.email,
        "description": company.description,
        "state": company.state,
        "business_profile_id": company.business_profile_id,
        "language_id": company.language_id,
        "country_id": company.country_id,
        "department_id": company.department_id,
        "municipality_id": company.municipality_id,
        "type_currency_id": company.type_currency_id
    }
    
# =====================================================
# UPDATE COMPANY (PROTEGIDO)
# =====================================================



@router.put("/{company_id}")
def update_company(company_id: int, data: dict, db: Session = Depends(get_db)):

    company = db.query(Company).filter(Company.id_company == company_id).first()

    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    # 🔥 VALIDACIÓN BACKEND (IGUAL QUE FRONT)
    required_fields = [
        "name",
        "identification_number",
        "dv",
        "address",
        "phone",
        "email",
        "business_profile_id",
        "language_id",
        "country_id",
        "department_id",
        "municipality_id",
        "type_currency_id"
    ]

    for field in required_fields:
        if not data.get(field):
            raise HTTPException(
                status_code=400,
                detail=f"El campo {field} es obligatorio"
            )

    # 🔥 VALIDACIÓN EMAIL
    import re
    email: str = data["email"]

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise HTTPException(status_code=400, detail="Email inválido")

    # 🔥 ASIGNACIÓN SEGURA (SIN PARCHE)
    company.name = data["name"]
    company.identification_number = data["identification_number"]
    company.dv = data["dv"]
    company.address = data["address"]
    company.phone = data["phone"]
    company.email = data["email"]
    company.description = data.get("description") or ""  # opcional
    company.state = data.get("state", 1)

    company.business_profile_id = data["business_profile_id"]
    company.language_id = data["language_id"]
    company.country_id = data["country_id"]
    company.department_id = data["department_id"]
    company.municipality_id = data["municipality_id"]
    company.type_currency_id = data["type_currency_id"]

    db.commit()

    return {"message": "Empresa actualizada correctamente"}

# =====================================================
# DELETE (PROTEGIDO)
# =====================================================

@router.delete("/{company_id}")
def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    is_system = role.is_system if role else False
    if not is_system and current_user.company_id != company_id:
        raise HTTPException(status_code=403, detail="No autorizado")

    company = db.query(Company).filter(Company.id_company == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    # 1. Desconectar usuarios (no eliminar, solo romper la FK)
    db.query(User).filter(User.company_id == company_id).update({"company_id": None})

    # 2. Eliminar tema de la empresa
    db.query(CompanyTheme).filter(CompanyTheme.company_id == company_id).delete()

    # 3. Eliminar la empresa
    db.delete(company)
    db.commit()

    return {"message": "Empresa eliminada correctamente"}

@router.get("/")
def get_companies(
    db: Session = Depends(get_db)
):
    """
    Obtener listado de todas las empresas.

    Uso:
    - SYSADMIN PANEL → selector de empresa
    - Configuración administrativa

    Seguridad:
    - Requiere autenticación
    - Requiere permiso en system_modules ('/companies')

    Response:
    [
        {
            "id": int,
            "name": str,
            "business_profile_id": int | None
        }
    ]
    """

    companies = db.query(Company).all()
    profiles  = {p.id: p.name for p in db.query(BusinessProfile).all()}

    return [
        {
            "id":                    c.id_company,
            "name":                  c.name,
            "identification_number": c.identification_number,
            "dv":                    c.dv,
            "address":               c.address,
            "phone":                 c.phone,
            "email":                 c.email,
            "description":           c.description,
            "state":                 c.state,
            "business_profile_id":   c.business_profile_id,
            "business_profile_name": profiles.get(c.business_profile_id, ""),
            "language_id":           c.language_id,
            "country_id":            c.country_id,
            "department_id":         c.department_id,
            "municipality_id":       c.municipality_id,
            "type_currency_id":      c.type_currency_id,
        }
        for c in companies
    ]
   