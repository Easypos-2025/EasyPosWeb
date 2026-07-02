import re
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, or_
from app.database import get_db, test_ext_connection, invalidate_ext_engine
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
    from sqlalchemy import text
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
    from app.models.asset_category_model import AssetCategory
    from app.models.asset_sector_model import AssetSector
    from app.models.company_asset_content_model import CompanyAssetContent
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
    from app.models.password_reset_token import PasswordResetToken
    from app.models.advertisement_model import Advertisement, AdPiece, AdPayment
    from app.models.concepto_compra_model import ConceptoCompra
    from app.models.concepto_gasto_model import ConceptoGasto
    from app.models.unidad_medida_model import UnidadMedida
    from app.models.profession_model import Profession

    cid = company_id

    # 1. Sesiones y tokens de usuarios de la empresa
    user_ids = [r[0] for r in (await db.execute(
        select(User.id).where(User.company_id == cid)
    )).all()]
    if user_ids:
        await db.execute(delete(UserSession).where(UserSession.user_id.in_(user_ids)))
        await db.execute(delete(InvitationToken).where(InvitationToken.created_by.in_(user_ids)))
        await db.execute(delete(UserNotification).where(
            or_(UserNotification.sender_id.in_(user_ids), UserNotification.receiver_id.in_(user_ids))
        ))

    # 2. Tareas y sus hijos
    task_ids = [r[0] for r in (await db.execute(
        select(Task.id).where(Task.company_id == cid)
    )).all()]
    if task_ids:
        for child in (TaskComment, TaskEvidence, TaskMaterial, TaskExpense, TaskPurchase, TaskProgressReport):
            await db.execute(delete(child).where(child.task_id.in_(task_ids)))
        await db.execute(delete(Task).where(Task.company_id == cid))

    # 3. Novedades
    novelty_ids = [r[0] for r in (await db.execute(
        select(Novelty.id).where(Novelty.company_id == cid)
    )).all()]
    if novelty_ids:
        await db.execute(delete(NoveltyEvidence).where(NoveltyEvidence.novelty_id.in_(novelty_ids)))
        await db.execute(delete(NoveltyReply).where(NoveltyReply.novelty_id.in_(novelty_ids)))
    await db.execute(delete(Novelty).where(Novelty.company_id == cid))

    # 4. Tickets de soporte
    ticket_ids = [r[0] for r in (await db.execute(
        select(SupportTicket.id).where(SupportTicket.company_id == cid)
    )).all()]
    if ticket_ids:
        await db.execute(delete(TicketEvidence).where(TicketEvidence.ticket_id.in_(ticket_ids)))
    await db.execute(delete(SupportTicket).where(SupportTicket.company_id == cid))

    # 5. Préstamos y bodega
    await db.execute(delete(Loan).where(Loan.company_id == cid))
    await db.execute(delete(BodegaItem).where(BodegaItem.company_id == cid))

    # 6. Activos
    asset_ids = [r[0] for r in (await db.execute(
        select(Asset.id).where(Asset.company_id == cid)
    )).all()]
    if asset_ids:
        await db.execute(delete(AssetMedia).where(AssetMedia.asset_id.in_(asset_ids)))
        await db.execute(delete(AssetInquiry).where(AssetInquiry.asset_id.in_(asset_ids)))
    await db.execute(delete(Asset).where(Asset.company_id == cid))
    await db.execute(delete(AssetCategory).where(AssetCategory.company_id == cid))
    await db.execute(delete(AssetSector).where(AssetSector.company_id == cid))
    await db.execute(delete(CompanyAssetContent).where(CompanyAssetContent.company_id == cid))

    # 7. Inventario
    po_ids = [r[0] for r in (await db.execute(
        select(PurchaseOrder.id).where(PurchaseOrder.company_id == cid)
    )).all()]
    if po_ids:
        await db.execute(delete(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id.in_(po_ids)))
    await db.execute(delete(PurchaseOrder).where(PurchaseOrder.company_id == cid))
    await db.execute(delete(StockMovement).where(StockMovement.company_id == cid))

    pl_ids = [r[0] for r in (await db.execute(
        select(PriceList.id).where(PriceList.company_id == cid)
    )).all()]
    if pl_ids:
        await db.execute(delete(PriceListItem).where(PriceListItem.price_list_id.in_(pl_ids)))
    await db.execute(delete(PriceList).where(PriceList.company_id == cid))

    prod_ids = [r[0] for r in (await db.execute(
        select(Product.id).where(Product.company_id == cid)
    )).all()]
    if prod_ids:
        await db.execute(delete(ProductPresentation).where(ProductPresentation.product_id.in_(prod_ids)))
    await db.execute(delete(Product).where(Product.company_id == cid))
    await db.execute(delete(ProductCategory).where(ProductCategory.company_id == cid))
    await db.execute(delete(ProductReference).where(ProductReference.company_id == cid))
    await db.execute(delete(Supplier).where(Supplier.company_id == cid))
    await db.execute(delete(SupplyItem).where(SupplyItem.company_id == cid))
    await db.execute(delete(Client).where(Client.company_id == cid))
    await db.execute(delete(Worker).where(Worker.company_id == cid))
    await db.execute(delete(ExternalCollaborator).where(ExternalCollaborator.company_id == cid))

    # 8. Conceptos, unidades y profesiones
    await db.execute(delete(ConceptoCompra).where(ConceptoCompra.company_id == cid))
    await db.execute(delete(ConceptoGasto).where(ConceptoGasto.company_id == cid))
    await db.execute(delete(UnidadMedida).where(UnidadMedida.company_id == cid))
    await db.execute(delete(Profession).where(Profession.company_id == cid))

    # 9. Anuncios publicitarios
    ad_ids = [r[0] for r in (await db.execute(
        select(Advertisement.id).where(Advertisement.company_id == cid)
    )).all()]
    if ad_ids:
        await db.execute(delete(AdPiece).where(AdPiece.advertisement_id.in_(ad_ids)))
    await db.execute(delete(AdPayment).where(AdPayment.company_id == cid))
    await db.execute(delete(Advertisement).where(Advertisement.company_id == cid))

    # 10. Tablas POS (sin modelos Python — raw SQL con FK checks deshabilitado)
    await db.execute(text("SET foreign_key_checks = 0"))
    _pos_tables = [
        # Nivel más profundo primero
        "pos_dish_assembly_detail", "pos_dish_assembly",
        "pos_dish_products", "pos_dish_variants",
        "pos_item_modifier_options", "pos_item_modifiers",
        "pos_item_printers", "pos_item_categories",
        "invoice_delivery_fees", "receipt_delivery_fees",
        "pos_invoice_details", "pos_invoice_payment_methods",
        "pos_cash_register_invoices", "pos_cash_register_receipts", "pos_cash_register_closings",
        "pos_receipt_invoice_details", "pos_receipt_payment_methods",
        "pos_receipt_order_detail_products", "pos_receipt_order_details", "pos_receipt_orders",
        "pos_order_detail_products", "pos_order_details",
        "pos_invoices", "pos_receipts", "pos_cash_registers",
        "pos_orders", "pos_tables_layout", "pos_tables",
        "pos_daily_menu", "pos_customer_price_list",
        "pos_dish_categories", "pos_dishes",
        "pos_product_categories", "pos_categories",
        "pos_zones", "pos_printers",
        "pos_waiters", "pos_employees",
        "supplies_quitar",
    ]
    for tbl in _pos_tables:
        await db.execute(text(f"DELETE FROM `{tbl}` WHERE company_id = :cid"), {"cid": cid})
    await db.execute(text("SET foreign_key_checks = 1"))

    # 11. Pagos y planes
    await db.execute(delete(CompanyPayment).where(CompanyPayment.company_id == cid))
    await db.execute(delete(CompanyPlan).where(CompanyPlan.company_id == cid))
    await db.execute(delete(CompanyPlanLimits).where(CompanyPlanLimits.company_id == cid))

    # 12. Roles
    role_ids = [r[0] for r in (await db.execute(
        select(Role.id).where(Role.company_id == cid)
    )).all()]
    if role_ids:
        await db.execute(delete(RoleModule).where(RoleModule.role_id.in_(role_ids)))
    await db.execute(delete(Role).where(Role.company_id == cid))

    # 13. Usuarios
    if user_ids:
        await db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id.in_(user_ids)))
    await db.execute(delete(User).where(User.company_id == cid))

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.post("/")
async def create_company(data: dict = Body(...), db: AsyncSession = Depends(get_db)):
    data.pop("ext_db_has_password", None)   # campo virtual del frontend, no es columna
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
            "type_currency_id": company.type_currency_id,
            "ext_db_host":     company.ext_db_host,
            "ext_db_port":     company.ext_db_port or 3306,
            "ext_db_name":     company.ext_db_name,
            "ext_db_user":     company.ext_db_user,
            "ext_db_has_password": bool(company.ext_db_password),
            "show_sidebar_right": company.show_sidebar_right if company.show_sidebar_right is not None else 1}


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
    # DB externa (solo SYSADMIN la envía; si no viene en payload se ignora)
    if "ext_db_host" in data:
        new_host = data.get("ext_db_host") or None
        if new_host != company.ext_db_host:
            invalidate_ext_engine(company_id)
        company.ext_db_host     = new_host
        company.ext_db_port     = int(data.get("ext_db_port") or 3306)
        company.ext_db_name     = data.get("ext_db_name") or None
        company.ext_db_user     = data.get("ext_db_user") or None
        if data.get("ext_db_password"):
            company.ext_db_password = data["ext_db_password"]
    # Sidebar derecho (solo SYSADMIN lo envía; si no viene se ignora)
    if "show_sidebar_right" in data:
        company.show_sidebar_right = 1 if data["show_sidebar_right"] else 0
    await db.commit()
    return {"message": "Empresa actualizada correctamente"}


@router.post("/{company_id}/test-db")
async def test_company_db(
    company_id: int,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    role = await db.get(Role, current_user.role_id)
    if not (role and role.is_system):
        raise HTTPException(status_code=403, detail="Solo SYSADMIN puede probar conexiones")
    host     = data.get("ext_db_host", "").strip()
    port     = int(data.get("ext_db_port") or 3306)
    db_name  = data.get("ext_db_name", "").strip()
    user     = data.get("ext_db_user", "").strip()
    password = data.get("ext_db_password", "")
    if not all([host, db_name, user]):
        raise HTTPException(status_code=400, detail="Servidor, base de datos y usuario son obligatorios")
    result = await test_ext_connection(host, port, db_name, user, password)
    return result


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
    from app.models.company_plan_model import CompanyPlan
    from app.models.plan_model import Plan

    result = await db.execute(select(Company).order_by(Company.id_company))
    companies = result.scalars().all()

    result = await db.execute(select(BusinessProfile))
    profiles = {p.id: p.name for p in result.scalars().all()}

    cp_res = await db.execute(select(CompanyPlan).where(CompanyPlan.is_active == True))
    active_plans = {cp.company_id: cp for cp in cp_res.scalars().all()}

    plan_res = await db.execute(select(Plan))
    plan_names = {p.id: p.name for p in plan_res.scalars().all()}

    return [
        {
            "id": c.id_company,
            "name": c.name,
            "identification_number": c.identification_number,
            "dv": c.dv, "address": c.address, "phone": c.phone, "email": c.email,
            "description": c.description, "state": c.state,
            "business_profile_id": c.business_profile_id,
            "business_profile_name": profiles.get(c.business_profile_id, ""),
            "language_id": c.language_id, "country_id": c.country_id,
            "department_id": c.department_id, "municipality_id": c.municipality_id,
            "type_currency_id": c.type_currency_id,
            "show_sidebar_right": c.show_sidebar_right if c.show_sidebar_right is not None else 1,
            "ext_db_host":         c.ext_db_host,
            "ext_db_port":         c.ext_db_port or 3306,
            "ext_db_name":         c.ext_db_name,
            "ext_db_user":         c.ext_db_user,
            "ext_db_has_password": bool(c.ext_db_password),
            "plan_id":          active_plans[c.id_company].plan_id if c.id_company in active_plans else None,
            "plan_name":        plan_names.get(active_plans[c.id_company].plan_id, "—") if c.id_company in active_plans else "Sin plan",
            "expiration_date":  active_plans[c.id_company].expiration_date.isoformat() if c.id_company in active_plans and active_plans[c.id_company].expiration_date else None,
        }
        for c in companies
    ]
