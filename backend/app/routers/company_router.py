import re
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.business_profile_module import BusinessProfileModule
from app.models.company_model import Company
from app.models.business_profile_model import BusinessProfile
from app.models.user_model import User
from app.models.company_theme_model import CompanyTheme
from app.models.role_model import Role
from app.models.role_module_model import RoleModule

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.post("/")
async def create_company(data: dict = Body(...), db: AsyncSession = Depends(get_db)):
    company = Company(**data)
    db.add(company)
    await db.flush()

    result = await db.execute(select(Role).where(Role.company_id == company.id_company, Role.name == "Admin"))
    admin_role = result.scalar_one_or_none()
    if not admin_role:
        admin_role = Role(name="Admin", description="Administrador principal",
                          company_id=company.id_company, is_system=False)
        db.add(admin_role)
        await db.flush()

    result = await db.execute(select(BusinessProfileModule).where(BusinessProfileModule.business_profile_id == company.business_profile_id))
    profile_modules = result.scalars().all()

    result = await db.execute(select(RoleModule).where(RoleModule.role_id == admin_role.id))
    existing_module_ids = {rm.module_id for rm in result.scalars().all()}

    for bpm in profile_modules:
        if bpm.module_id not in existing_module_ids:
            db.add(RoleModule(role_id=admin_role.id, module_id=bpm.module_id,
                              can_view=True, can_create=True, can_edit=True, can_delete=True))

    await db.commit()
    await db.refresh(company)
    return {"id": company.id_company, "name": company.name,
            "admin_role_id": admin_role.id, "modules_assigned": len(profile_modules)}


@router.get("/{company_id:int}")
async def get_company(company_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).where(Company.id_company == company_id))
    company = result.scalar_one_or_none()
    if not company:
        return {"message": "Empresa no encontrada"}
    return {"id": company.id_company, "name": company.name,
            "identification_number": company.identification_number, "dv": company.dv,
            "address": company.address, "phone": company.phone, "email": company.email,
            "description": company.description, "state": company.state,
            "business_profile_id": company.business_profile_id,
            "language_id": company.language_id, "country_id": company.country_id,
            "department_id": company.department_id, "municipality_id": company.municipality_id,
            "type_currency_id": company.type_currency_id}


@router.put("/{company_id}")
async def update_company(company_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).where(Company.id_company == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    required_fields = ["name", "identification_number", "dv", "address", "phone", "email",
                       "business_profile_id", "language_id", "country_id", "department_id",
                       "municipality_id", "type_currency_id"]
    for field in required_fields:
        if not data.get(field):
            raise HTTPException(status_code=400, detail=f"El campo {field} es obligatorio")

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", data["email"]):
        raise HTTPException(status_code=400, detail="Email inválido")

    company.name = data["name"]
    company.identification_number = data["identification_number"]
    company.dv = data["dv"]
    company.address = data["address"]
    company.phone = data["phone"]
    company.email = data["email"]
    company.description = data.get("description") or ""
    company.state = data.get("state", 1)
    company.business_profile_id = data["business_profile_id"]
    company.language_id = data["language_id"]
    company.country_id = data["country_id"]
    company.department_id = data["department_id"]
    company.municipality_id = data["municipality_id"]
    company.type_currency_id = data["type_currency_id"]
    await db.commit()
    return {"message": "Empresa actualizada correctamente"}


@router.delete("/{company_id}")
async def delete_company(company_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    role = await db.get(Role, current_user.role_id)
    is_system = role.is_system if role else False
    if not is_system and current_user.company_id != company_id:
        raise HTTPException(status_code=403, detail="No autorizado")

    result = await db.execute(select(Company).where(Company.id_company == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    await db.execute(update(User).where(User.company_id == company_id).values(company_id=None))
    await db.execute(delete(CompanyTheme).where(CompanyTheme.company_id == company_id))
    await db.delete(company)
    await db.commit()
    return {"message": "Empresa eliminada correctamente"}


@router.get("/")
async def get_companies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company))
    companies = result.scalars().all()
    result = await db.execute(select(BusinessProfile))
    profiles = {p.id: p.name for p in result.scalars().all()}
    return [
        {"id": c.id_company, "name": c.name, "identification_number": c.identification_number,
         "dv": c.dv, "address": c.address, "phone": c.phone, "email": c.email,
         "description": c.description, "state": c.state,
         "business_profile_id": c.business_profile_id,
         "business_profile_name": profiles.get(c.business_profile_id, ""),
         "language_id": c.language_id, "country_id": c.country_id,
         "department_id": c.department_id, "municipality_id": c.municipality_id,
         "type_currency_id": c.type_currency_id}
        for c in companies
    ]
