import re
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, or_
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.business_profile_module import BusinessProfileModule
from app.models.company_model import Company
from app.models.business_profile_model import BusinessProfile
from app.models.user_model import User
from app.models.company_theme_model import CompanyTheme
from app.models.role_model import Role
from app.models.role_module_model import RoleModule


async def _cascade_delete_company(company_id: int, db: AsyncSession):
    """Elimina en cascada TODOS los datos de una empresa (solo SYSADMIN)."""
    from app.models.user_session_model import UserSession
    from app.models.invitation_model import InvitationToken
    from app.models.user_notification_model import UserNotification
    from app.models.task_model import Task
    from app.models.task_comment_model import TaskComment
    from app.models.task_evidence_model import TaskEvidence
    from app.models.task_material_model import TaskMaterial
    from app.models.task_expense_model import TaskExpense
    from app.models.task_purchase_model import TaskPurchase
    from app.models.task_progress_report_model import TaskProgressReport
    from app.models.novelty_model import Novelty, NoveltyEvidence, NoveltyReply
    from app.models.support_ticket_model import SupportTicket, TicketEvidence
    from app.models.loan_model import Loan
    from app.models.asset_model import Asset
    from app.models.asset_media_model import AssetMedia
    from app.models.asset_inquiry_model import AssetInquiry
    from app.models.bodega_item_model import BodegaItem
    from app.models.external_collaborator_model import ExternalCollaborator
    from app.models.client_model import Client
    from app.models.worker_model import Worker
    from app.models.supplier_model import Supplier
    from app.models.supply_item_model import SupplyItem
    from app.models.purchase_order_model import PurchaseOrder
    from app.models.purchase_order_item_model import PurchaseOrderItem
    from app.models.stock_movement_model import StockMovement
    from app.models.product_model import Product
    from app.models.product_category_model import ProductCategory
    from app.models.product_reference_model import ProductReference
    from app.models.product_presentation_model import ProductPresentation
    from app.models.price_list_model import PriceList
    from app.models.price_list_item_model import PriceListItem
    from app.models.company_payment_model import CompanyPayment
    from app.models.company_plan_model import CompanyPlan
    from app.models.company_plan_limits_model import CompanyPlanLimits

    # 1. Sesiones y tokens de usuarios de la empresa
    user_ids = [r[0] for r in (await db.execute(
        select(User.id).where(User.company_id == company_id)
    )).all()]
    if user_ids:
        await db.execute(delete(UserSession).where(UserSession.user_id.in_(user_ids)))
        await db.execute(delete(InvitationToken).where(InvitationToken.created_by.in_(user_ids)))
        await db.execute(delete(UserNotification).where(
            or_(UserNotification.sender_id.in_(user_ids), UserNotification.receiver_id.in_(user_ids))
        ))

    # 2. Tareas y sus hijos
    task_ids = [r[0] for r in (await db.execute(
        select(Task.id).where(Task.company_id == company_id)
    )).all()]
    if task_ids:
        for child in (TaskComment, TaskEvidence, TaskMaterial, TaskExpense, TaskPurchase, TaskProgressReport):
            await db.execute(delete(child).where(child.task_id.in_(task_ids)))
        await db.execute(delete(Task).where(Task.company_id == company_id))

    # 3. Novedades (evidence y replies con CASCADE en BD)
    novelty_ids = [r[0] for r in (await db.execute(
        select(Novelty.id).where(Novelty.company_id == company_id)
    )).all()]
    if novelty_ids:
        await db.execute(delete(NoveltyEvidence).where(NoveltyEvidence.novelty_id.in_(novelty_ids)))
        await db.execute(delete(NoveltyReply).where(NoveltyReply.novelty_id.in_(novelty_ids)))
    await db.execute(delete(Novelty).where(Novelty.company_id == company_id))

    # 4. Tickets de soporte (ticket_evidence con CASCADE en BD)
    ticket_ids = [r[0] for r in (await db.execute(
        select(SupportTicket.id).where(SupportTicket.company_id == company_id)
    )).all()]
    if ticket_ids:
        await db.execute(delete(TicketEvidence).where(TicketEvidence.ticket_id.in_(ticket_ids)))
    await db.execute(delete(SupportTicket).where(SupportTicket.company_id == company_id))

    # 5. Préstamos y bodega
    await db.execute(delete(Loan).where(Loan.company_id == company_id))
    await db.execute(delete(BodegaItem).where(BodegaItem.company_id == company_id))

    # 6. Activos (asset_media y asset_inquiries con CASCADE en BD)
    asset_ids = [r[0] for r in (await db.execute(
        select(Asset.id).where(Asset.company_id == company_id)
    )).all()]
    if asset_ids:
        await db.execute(delete(AssetMedia).where(AssetMedia.asset_id.in_(asset_ids)))
        await db.execute(delete(AssetInquiry).where(AssetInquiry.asset_id.in_(asset_ids)))
    await db.execute(delete(Asset).where(Asset.company_id == company_id))

    # 7. Inventario
    po_ids = [r[0] for r in (await db.execute(
        select(PurchaseOrder.id).where(PurchaseOrder.company_id == company_id)
    )).all()]
    if po_ids:
        await db.execute(delete(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id.in_(po_ids)))
    await db.execute(delete(PurchaseOrder).where(PurchaseOrder.company_id == company_id))
    await db.execute(delete(StockMovement).where(StockMovement.company_id == company_id))

    pl_ids = [r[0] for r in (await db.execute(
        select(PriceList.id).where(PriceList.company_id == company_id)
    )).all()]
    if pl_ids:
        await db.execute(delete(PriceListItem).where(PriceListItem.price_list_id.in_(pl_ids)))
    await db.execute(delete(PriceList).where(PriceList.company_id == company_id))

    prod_ids = [r[0] for r in (await db.execute(
        select(Product.id).where(Product.company_id == company_id)
    )).all()]
    if prod_ids:
        await db.execute(delete(ProductPresentation).where(ProductPresentation.product_id.in_(prod_ids)))
    await db.execute(delete(Product).where(Product.company_id == company_id))
    await db.execute(delete(ProductCategory).where(ProductCategory.company_id == company_id))
    await db.execute(delete(ProductReference).where(ProductReference.company_id == company_id))
    await db.execute(delete(Supplier).where(Supplier.company_id == company_id))
    await db.execute(delete(SupplyItem).where(SupplyItem.company_id == company_id))
    await db.execute(delete(Client).where(Client.company_id == company_id))
    await db.execute(delete(Worker).where(Worker.company_id == company_id))
    await db.execute(delete(ExternalCollaborator).where(ExternalCollaborator.company_id == company_id))

    # 8. Pagos y planes
    await db.execute(delete(CompanyPayment).where(CompanyPayment.company_id == company_id))
    await db.execute(delete(CompanyPlan).where(CompanyPlan.company_id == company_id))
    await db.execute(delete(CompanyPlanLimits).where(CompanyPlanLimits.company_id == company_id))

    # 9. Roles (primero role_modules, luego roles)
    role_ids = [r[0] for r in (await db.execute(
        select(Role.id).where(Role.company_id == company_id)
    )).all()]
    if role_ids:
        await db.execute(delete(RoleModule).where(RoleModule.role_id.in_(role_ids)))
    await db.execute(delete(Role).where(Role.company_id == company_id))

    # 10. Usuarios y tema
    await db.execute(delete(User).where(User.company_id == company_id))

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

    # Validar solo los campos editables en el formulario de perfil
    text_required = ["name", "identification_number", "address", "phone", "email"]
    for field in text_required:
        if not data.get(field):
            raise HTTPException(status_code=400, detail=f"El campo {field} es obligatorio")

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", data["email"]):
        raise HTTPException(status_code=400, detail="Email inválido")

    company.name = data["name"]
    company.identification_number = data["identification_number"]
    # dv puede ser 0 (válido para NITs con dígito verificador = 0)
    if data.get("dv") is not None:
        company.dv = data["dv"]
    company.address = data["address"]
    company.phone = data["phone"]
    company.email = data["email"]
    company.description = data.get("description") or ""
    company.state = data.get("state", 1)
    # FK opcionales: solo actualizar si vienen en el payload y son válidos
    if data.get("business_profile_id"):
        company.business_profile_id = data["business_profile_id"]
    if data.get("language_id"):
        company.language_id = data["language_id"]
    if data.get("country_id"):
        company.country_id = data["country_id"]
    if data.get("department_id"):
        company.department_id = data["department_id"]
    if data.get("municipality_id"):
        company.municipality_id = data["municipality_id"]
    if data.get("type_currency_id"):
        company.type_currency_id = data["type_currency_id"]
    await db.commit()
    return {"message": "Empresa actualizada correctamente"}


@router.delete("/{company_id}")
async def delete_company(company_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    role = await db.get(Role, current_user.role_id)
    is_system = role.is_system if role else False
    if not is_system:
        raise HTTPException(status_code=403, detail="Solo SYSADMIN puede eliminar empresas")

    result = await db.execute(select(Company).where(Company.id_company == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    await _cascade_delete_company(company_id, db)
    await db.execute(delete(CompanyTheme).where(CompanyTheme.company_id == company_id))
    await db.delete(company)
    await db.commit()
    return {"message": "Empresa y todos sus datos eliminados correctamente"}


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
