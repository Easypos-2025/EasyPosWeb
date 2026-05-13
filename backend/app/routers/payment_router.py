import uuid
from datetime import datetime, timezone, date, timedelta
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.database import get_db
from app.auth.dependencies import get_current_user, require_sysadmin
from app.models.company_model import Company
from app.models.company_payment_model import CompanyPayment
from app.models.company_plan_model import CompanyPlan
from app.models.plan_model import Plan
from app.models.plan_price_model import PlanPrice
from app.models.user_model import User
from app.utils.email_service import send_payment_approved, send_payment_rejected
from app.utils.storage import upload_file

router = APIRouter(prefix="/payments", tags=["Payments"])

BASE_DIR      = Path(__file__).resolve().parent.parent.parent.parent
PAYMENTS_DIR  = BASE_DIR / "backend" / "app" / "uploads" / "payments"
REVIEWS_DIR   = BASE_DIR / "backend" / "app" / "uploads" / "payment_reviews"
ALLOWED_MIME  = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_FILE_SIZE = 5 * 1024 * 1024
PLAN_DURATION_DAYS = 365


async def _get_latest_payment(company_id: int, db: AsyncSession):
    result = await db.execute(
        select(CompanyPayment).where(CompanyPayment.company_id == company_id).order_by(CompanyPayment.id.desc())
    )
    return result.scalar_one_or_none()


async def _get_active_plan(company_id: int, db: AsyncSession):
    result = await db.execute(
        select(CompanyPlan).where(CompanyPlan.company_id == company_id, CompanyPlan.is_active == True).order_by(CompanyPlan.id.desc())
    )
    return result.scalar_one_or_none()


async def _plan_price_for(plan: Plan, currency_code: str, db: AsyncSession) -> float:
    result = await db.execute(
        select(PlanPrice).where(PlanPrice.plan_id == plan.id, PlanPrice.currency_code == currency_code.upper(), PlanPrice.is_active == True)
    )
    pp = result.scalar_one_or_none()
    return pp.amount if pp else plan.price


async def _save_receipt(file: UploadFile, payment: CompanyPayment) -> str:
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(status_code=400, detail="Tipo de archivo no permitido. Usa JPG, PNG, WEBP o PDF.")
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="El archivo supera el límite de 5 MB.")
    ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "application/pdf": ".pdf"}.get(file.content_type, ".bin")
    filename = f"{uuid.uuid4().hex}{ext}"
    if payment.receipt_url and payment.receipt_url.startswith("/uploads/"):
        old = PAYMENTS_DIR / payment.receipt_url.split("/")[-1]
        old.unlink(missing_ok=True)
    return await upload_file(content, f"payments/{filename}")


async def _serialize_payment(p: CompanyPayment, db: AsyncSession) -> dict:
    company   = await db.get(Company, p.company_id)
    plan      = await db.get(Plan, p.plan_id)
    prev_plan = await db.get(Plan, p.previous_plan_id) if p.previous_plan_id else None
    result    = await db.execute(select(User).where(User.company_id == p.company_id).order_by(User.id))
    admin     = result.scalars().first()
    reviewer  = await db.get(User, p.reviewed_by) if p.reviewed_by else None

    current_plan_data = None
    if p.payment_type == "upgrade" and p.status in ("pending", "submitted"):
        active_cp = await _get_active_plan(p.company_id, db)
        if active_cp:
            cp = await db.get(Plan, active_cp.plan_id)
            if cp:
                current_plan_data = {"id": cp.id, "name": cp.name, "price": cp.price}
    elif prev_plan:
        current_plan_data = {"id": prev_plan.id, "name": prev_plan.name, "price": prev_plan.price}

    return {
        "id": p.id, "payment_type": p.payment_type, "currency_code": p.currency_code,
        "status": p.status, "amount": p.amount, "receipt_url": p.receipt_url,
        "submitted_at": p.submitted_at, "created_at": p.created_at,
        "receipt_number": p.receipt_number, "bank_origin": p.bank_origin,
        "payment_date": str(p.payment_date) if p.payment_date else None,
        "confirmed_amount": p.confirmed_amount, "review_description": p.review_description,
        "review_evidence_url": p.review_evidence_url, "rejection_reason": p.rejection_reason,
        "reviewed_at": p.reviewed_at, "reviewed_by_name": reviewer.nombre if reviewer else None,
        "company": {"id": company.id_company if company else None, "name": company.name if company else "—", "nit": company.identification_number if company else "—"},
        "plan": {"id": plan.id if plan else None, "name": plan.name if plan else "—", "price": plan.price if plan else 0},
        "current_plan": current_plan_data,
        "admin_email": admin.email if admin else "—", "admin_name": admin.nombre if admin else "—",
    }


@router.get("/my-status")
async def get_my_payment_status(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    company = await db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    payment = await _get_latest_payment(company.id_company, db)
    active_plan = await _get_active_plan(company.id_company, db)
    plan = await db.get(Plan, payment.plan_id) if payment else None
    active_plan_data = await db.get(Plan, active_plan.plan_id) if active_plan else None
    return {
        "payment_status": company.payment_status, "upgrade_status": company.upgrade_status,
        "payment": {"id": payment.id, "payment_type": payment.payment_type, "status": payment.status,
                    "amount": payment.amount, "currency_code": payment.currency_code,
                    "receipt_url": payment.receipt_url, "rejection_reason": payment.rejection_reason,
                    "review_description": payment.review_description, "review_evidence_url": payment.review_evidence_url,
                    "submitted_at": payment.submitted_at} if payment else None,
        "plan": {"id": plan.id if plan else None, "name": plan.name if plan else None, "price": plan.price if plan else None} if plan else None,
        "active_plan": {"id": active_plan_data.id if active_plan_data else None,
                        "name": active_plan_data.name if active_plan_data else None,
                        "expiration_date": str(active_plan.expiration_date) if active_plan and active_plan.expiration_date else None} if active_plan else None,
    }


@router.get("/available-upgrades")
async def available_upgrades(currency: str = "COP", current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    active_plan = await _get_active_plan(current_user.company_id, db)
    current_price = 0.0
    if active_plan:
        plan = await db.get(Plan, active_plan.plan_id)
        if plan:
            current_price = plan.price
    result = await db.execute(select(Plan).where(Plan.is_active == True))
    upgrades = []
    for p in result.scalars().all():
        if p.price > current_price:
            price_in_currency = await _plan_price_for(p, currency, db)
            upgrades.append({"id": p.id, "name": p.name, "description": p.description,
                             "price": price_in_currency, "currency": currency.upper(), "max_users": p.max_users})
    upgrades.sort(key=lambda x: x["price"])
    return upgrades


@router.get("/available-downgrades")
async def available_downgrades(currency: str = "COP", current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    active_plan = await _get_active_plan(current_user.company_id, db)
    current_price = 0.0
    if active_plan:
        plan = await db.get(Plan, active_plan.plan_id)
        if plan:
            current_price = plan.price
    result = await db.execute(select(Plan).where(Plan.is_active == True))
    items = []
    for p in result.scalars().all():
        if p.price < current_price:
            price_in_currency = await _plan_price_for(p, currency, db)
            items.append({"id": p.id, "name": p.name, "description": p.description,
                          "price": price_in_currency, "currency": currency.upper(), "is_free": p.price == 0})
    items.sort(key=lambda x: x["price"], reverse=True)
    return items


@router.post("/submit-receipt")
async def submit_receipt(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    company = await db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    if company.payment_status not in ("pending_payment", "payment_rejected", "expired"):
        raise HTTPException(status_code=400, detail="Tu empresa no tiene un pago pendiente")
    payment = await _get_latest_payment(company.id_company, db)
    if not payment:
        raise HTTPException(status_code=404, detail="Registro de pago no encontrado")
    if payment.status not in ("pending", "rejected"):
        raise HTTPException(status_code=400, detail="No puedes enviar un comprobante en este estado")
    payment.receipt_url = await _save_receipt(file, payment)
    payment.status = "submitted"
    payment.submitted_at = datetime.now(timezone.utc)
    payment.rejection_reason = None
    company.payment_status = "payment_submitted"
    await db.commit()
    return {"message": "Comprobante enviado. Estamos revisando tu pago.", "status": "submitted"}


class UpgradeRequest(BaseModel):
    plan_id: int
    currency_code: str = "COP"


@router.post("/request-upgrade")
async def request_upgrade(body: UpgradeRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    company = await db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    if company.upgrade_status == "upgrade_pending":
        raise HTTPException(status_code=400, detail="Ya tienes un upgrade en proceso")
    new_plan = await db.get(Plan, body.plan_id)
    if not new_plan or not new_plan.is_active:
        raise HTTPException(status_code=400, detail="Plan no disponible")
    active_plan = await _get_active_plan(company.id_company, db)
    current_price = 0.0
    if active_plan:
        cp = await db.get(Plan, active_plan.plan_id)
        if cp:
            current_price = cp.price
    if new_plan.price <= current_price:
        raise HTTPException(status_code=400, detail="El plan seleccionado no es superior al actual")
    amount = await _plan_price_for(new_plan, body.currency_code, db)
    db.add(CompanyPayment(company_id=company.id_company, plan_id=new_plan.id, amount=amount,
                          currency_code=body.currency_code.upper(), status="pending", payment_type="upgrade"))
    company.upgrade_status = "upgrade_pending"
    await db.commit()
    return {"message": f"Solicitud de upgrade al plan {new_plan.name} registrada.",
            "plan_name": new_plan.name, "amount": amount, "currency": body.currency_code.upper()}


@router.post("/submit-upgrade-receipt")
async def submit_upgrade_receipt(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    company = await db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    if company.upgrade_status != "upgrade_pending":
        raise HTTPException(status_code=400, detail="No tienes un upgrade pendiente")
    result = await db.execute(
        select(CompanyPayment).where(CompanyPayment.company_id == company.id_company,
                                     CompanyPayment.payment_type == "upgrade",
                                     CompanyPayment.status.in_(["pending", "rejected"])).order_by(CompanyPayment.id.desc())
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Registro de upgrade no encontrado")
    payment.receipt_url = await _save_receipt(file, payment)
    payment.status = "submitted"
    payment.submitted_at = datetime.now(timezone.utc)
    payment.rejection_reason = None
    await db.commit()
    return {"message": "Comprobante de upgrade enviado.", "status": "submitted"}


class DowngradeRequest(BaseModel):
    plan_id: int
    currency_code: str = "COP"
    legal_accepted: bool

    def model_post_init(self, __context):
        if not self.legal_accepted:
            raise ValueError("Debes aceptar las condiciones para cambiar de plan")


@router.post("/request-downgrade")
async def request_downgrade(body: DowngradeRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    company = await db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    new_plan = await db.get(Plan, body.plan_id)
    if not new_plan or not new_plan.is_active:
        raise HTTPException(status_code=400, detail="Plan no disponible")
    active_cp = await _get_active_plan(company.id_company, db)
    current_price = 0.0
    if active_cp:
        cp = await db.get(Plan, active_cp.plan_id)
        if cp:
            current_price = cp.price
    if new_plan.price >= current_price:
        raise HTTPException(status_code=400, detail="El plan seleccionado no es inferior al actual")
    if active_cp:
        active_cp.is_active = False
    if new_plan.price == 0:
        db.add(CompanyPlan(company_id=company.id_company, plan_id=new_plan.id, is_active=True))
        company.payment_status = "active"
        company.upgrade_status = None
        await db.commit()
        return {"message": f"Cambiado al plan {new_plan.name} exitosamente.", "requires_payment": False}
    else:
        amount = await _plan_price_for(new_plan, body.currency_code, db)
        db.add(CompanyPayment(company_id=company.id_company, plan_id=new_plan.id, amount=amount,
                              currency_code=body.currency_code.upper(), status="pending", payment_type="downgrade"))
        company.payment_status = "pending_payment"
        await db.commit()
        return {"message": f"Solicitud de cambio al plan {new_plan.name} registrada.", "requires_payment": True}


@router.get("/available-plans")
async def available_plans(currency: str = "COP", current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    active_cp = await _get_active_plan(current_user.company_id, db)
    current_plan_id = active_cp.plan_id if active_cp else None
    current_price = 0.0
    if active_cp:
        cp = await db.get(Plan, active_cp.plan_id)
        if cp:
            current_price = cp.price
    result = await db.execute(select(Plan).where(Plan.is_active == True).order_by(Plan.price))
    items = []
    for p in result.scalars().all():
        if p.price >= current_price:
            price_val = await _plan_price_for(p, currency, db)
            items.append({"id": p.id, "name": p.name, "description": p.description,
                          "price": price_val, "currency": currency.upper(),
                          "max_users": p.max_users, "is_current": p.id == current_plan_id})
    return items


class RenewalRequest(BaseModel):
    currency_code: str = "COP"
    plan_id: int | None = None


@router.post("/request-renewal")
async def request_renewal(body: RenewalRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    company = await db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    if company.payment_status not in ("expired", "pending_payment"):
        raise HTTPException(status_code=400, detail="No tienes un pago de renovación pendiente")
    active_cp = await _get_active_plan(company.id_company, db)
    if not active_cp:
        raise HTTPException(status_code=404, detail="Plan activo no encontrado")
    current_plan = await db.get(Plan, active_cp.plan_id)
    if not current_plan:
        raise HTTPException(status_code=404, detail="Plan actual no encontrado")
    if body.plan_id and body.plan_id != current_plan.id:
        target_plan = await db.get(Plan, body.plan_id)
        if not target_plan or not target_plan.is_active:
            raise HTTPException(status_code=400, detail="Plan seleccionado no disponible")
        if target_plan.price < current_plan.price:
            raise HTTPException(status_code=400, detail="No puedes seleccionar un plan inferior en la renovación")
        payment_type = "upgrade" if target_plan.price > current_plan.price else "renewal"
    else:
        target_plan = current_plan
        payment_type = "renewal"
    amount = await _plan_price_for(target_plan, body.currency_code, db)
    result = await db.execute(
        select(CompanyPayment).where(CompanyPayment.company_id == company.id_company,
                                     CompanyPayment.status.in_(["pending", "rejected"]),
                                     CompanyPayment.payment_type == payment_type).order_by(CompanyPayment.id.desc())
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.plan_id = target_plan.id
        existing.amount = amount
        existing.currency_code = body.currency_code.upper()
        existing.status = "pending"
    else:
        db.add(CompanyPayment(company_id=company.id_company, plan_id=target_plan.id, amount=amount,
                              currency_code=body.currency_code.upper(), status="pending", payment_type=payment_type))
    company.payment_status = "pending_payment"
    await db.commit()
    return {"message": f"Solicitud de {payment_type} al plan {target_plan.name} registrada.",
            "plan_name": target_plan.name, "payment_type": payment_type, "amount": amount}


@router.get("/pending")
async def list_pending_payments(payment_type: str = None, _: User = Depends(require_sysadmin), db: AsyncSession = Depends(get_db)):
    stmt = select(CompanyPayment).where(CompanyPayment.status.in_(["pending", "submitted"]))
    if payment_type:
        stmt = stmt.where(CompanyPayment.payment_type == payment_type)
    result = await db.execute(stmt.order_by(CompanyPayment.created_at.desc()))
    payments = result.scalars().all()
    return [await _serialize_payment(p, db) for p in payments]


@router.get("/pending-count")
async def pending_count(_: User = Depends(require_sysadmin), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import func
    count = (await db.execute(
        select(func.count()).select_from(CompanyPayment).where(CompanyPayment.status.in_(["pending", "submitted"]))
    )).scalar()
    return {"count": count}


@router.put("/{payment_id}/approve")
async def approve_payment(
    payment_id: int, background_tasks: BackgroundTasks,
    receipt_number: str = Form(...), bank_origin: str = Form(...),
    payment_date: date = Form(...), confirmed_amount: float = Form(None),
    review_description: str = Form(None), file: UploadFile = File(None),
    sysadmin: User = Depends(require_sysadmin), db: AsyncSession = Depends(get_db),
):
    payment = await db.get(CompanyPayment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    if payment.status not in ("pending", "submitted"):
        raise HTTPException(status_code=400, detail="Este pago no puede aprobarse en su estado actual")

    rn, bo = receipt_number.strip(), bank_origin.strip()
    result = await db.execute(
        select(CompanyPayment).where(CompanyPayment.receipt_number == rn, CompanyPayment.bank_origin == bo,
                                     CompanyPayment.status == "approved", CompanyPayment.id != payment_id)
    )
    duplicate = result.scalar_one_or_none()
    if duplicate:
        dup_company = await db.get(Company, duplicate.company_id)
        raise HTTPException(status_code=409, detail={
            "message": "Este número de recibo ya fue registrado para otro pago aprobado.",
            "duplicate": {"payment_id": duplicate.id, "company_name": dup_company.name if dup_company else "—",
                          "payment_date": str(duplicate.payment_date) if duplicate.payment_date else None,
                          "amount": duplicate.confirmed_amount or duplicate.amount,
                          "receipt_number": duplicate.receipt_number, "bank_origin": duplicate.bank_origin},
        })

    evidence_url = None
    if file and file.filename:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="El archivo de evidencia supera 5 MB.")
        if file.content_type not in ALLOWED_MIME:
            raise HTTPException(status_code=400, detail="Tipo de archivo no permitido.")
        ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "application/pdf": ".pdf"}.get(file.content_type, ".bin")
        fname = f"rev_{uuid.uuid4().hex}{ext}"
        evidence_url = await upload_file(content, f"payment_reviews/{fname}")

    company = await db.get(Company, payment.company_id)
    plan = await db.get(Plan, payment.plan_id)
    result = await db.execute(select(User).where(User.company_id == payment.company_id).order_by(User.id))
    admin = result.scalars().first()

    active_cp = await _get_active_plan(payment.company_id, db)
    if active_cp and active_cp.plan_id != payment.plan_id:
        payment.previous_plan_id = active_cp.plan_id

    payment.receipt_number = rn
    payment.bank_origin = bo
    payment.payment_date = payment_date
    payment.confirmed_amount = confirmed_amount
    payment.review_description = review_description.strip() if review_description else None
    payment.review_evidence_url = evidence_url
    payment.status = "approved"
    payment.reviewed_at = datetime.now(timezone.utc)
    payment.reviewed_by = sysadmin.id

    if company and payment.payment_type in ("activation", "renewal", "downgrade", "upgrade"):
        await db.execute(update(CompanyPlan).where(CompanyPlan.company_id == company.id_company, CompanyPlan.is_active == True).values(is_active=False))
        db.add(CompanyPlan(company_id=company.id_company, plan_id=payment.plan_id, is_active=True,
                           expiration_date=date.today() + timedelta(days=PLAN_DURATION_DAYS)))
        if payment.payment_type == "upgrade":
            company.upgrade_status = None
        else:
            company.payment_status = "active"
        # Snapshot de límites del plan para este asociado
        from app.services.plan_limits_service import snapshot_plan_limits
        await db.flush()  # asegurar que CompanyPlan esté en sesión antes del snapshot
        await snapshot_plan_limits(company.id_company, payment.plan_id, db)

    await db.commit()
    if admin and company and plan:
        background_tasks.add_task(send_payment_approved, to_email=admin.email, company_name=company.name, plan_name=plan.name)
    return {"message": "Pago aprobado. Plan activado correctamente."}


@router.get("/history")
async def list_payment_history(
    status: str = None, payment_type: str = None, company_id: int = None,
    date_from: str = None, date_to: str = None, page: int = 1, page_size: int = 20,
    _: User = Depends(require_sysadmin), db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import func
    stmt = select(CompanyPayment).where(CompanyPayment.status.in_(["approved", "rejected"]))
    if status and status in ("approved", "rejected"):
        stmt = stmt.where(CompanyPayment.status == status)
    if payment_type:
        stmt = stmt.where(CompanyPayment.payment_type == payment_type)
    if company_id:
        stmt = stmt.where(CompanyPayment.company_id == company_id)
    if date_from:
        try:
            stmt = stmt.where(CompanyPayment.reviewed_at >= datetime.fromisoformat(date_from))
        except ValueError:
            pass
    if date_to:
        try:
            stmt = stmt.where(CompanyPayment.reviewed_at <= datetime.fromisoformat(date_to + "T23:59:59"))
        except ValueError:
            pass

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar()
    result = await db.execute(stmt.order_by(CompanyPayment.reviewed_at.desc()).offset((page - 1) * page_size).limit(page_size))
    payments = result.scalars().all()
    items = [await _serialize_payment(p, db) for p in payments]
    return {"total": total, "page": page, "pages": max(1, -(-total // page_size)), "items": items}


@router.get("/my-history")
async def get_my_payment_history(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CompanyPayment).where(CompanyPayment.company_id == current_user.company_id).order_by(CompanyPayment.id.desc())
    )
    items = []
    for p in result.scalars().all():
        plan = await db.get(Plan, p.plan_id)
        prev_plan = await db.get(Plan, p.previous_plan_id) if p.previous_plan_id else None
        items.append({
            "id": p.id, "payment_type": p.payment_type, "status": p.status,
            "amount": p.amount, "currency_code": p.currency_code, "receipt_url": p.receipt_url,
            "rejection_reason": p.rejection_reason, "review_description": p.review_description,
            "review_evidence_url": p.review_evidence_url, "receipt_number": p.receipt_number,
            "bank_origin": p.bank_origin, "payment_date": str(p.payment_date) if p.payment_date else None,
            "confirmed_amount": p.confirmed_amount, "submitted_at": p.submitted_at,
            "reviewed_at": p.reviewed_at, "created_at": p.created_at,
            "plan": {"id": plan.id if plan else None, "name": plan.name if plan else "—"},
            "previous_plan": {"id": prev_plan.id, "name": prev_plan.name} if prev_plan else None,
        })
    return items


@router.put("/{payment_id}/reject")
async def reject_payment(
    payment_id: int, background_tasks: BackgroundTasks,
    reason: str = Form(...), review_description: str = Form(None), file: UploadFile = File(None),
    sysadmin: User = Depends(require_sysadmin), db: AsyncSession = Depends(get_db),
):
    if not reason or not reason.strip():
        raise HTTPException(status_code=422, detail="La razón de rechazo es obligatoria")
    payment = await db.get(CompanyPayment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    if payment.status not in ("pending", "submitted"):
        raise HTTPException(status_code=400, detail="Este pago no puede rechazarse en su estado actual")

    evidence_url = None
    if file and file.filename:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="El archivo de evidencia supera 5 MB.")
        if file.content_type not in ALLOWED_MIME:
            raise HTTPException(status_code=400, detail="Tipo de archivo no permitido.")
        ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "application/pdf": ".pdf"}.get(file.content_type, ".bin")
        fname = f"rev_{uuid.uuid4().hex}{ext}"
        evidence_url = await upload_file(content, f"payment_reviews/{fname}")

    company = await db.get(Company, payment.company_id)
    plan = await db.get(Plan, payment.plan_id)
    result = await db.execute(select(User).where(User.company_id == payment.company_id).order_by(User.id))
    admin = result.scalars().first()

    payment.status = "rejected"
    payment.rejection_reason = reason.strip()[:1000]
    payment.review_description = review_description.strip() if review_description else None
    payment.review_evidence_url = evidence_url
    payment.reviewed_at = datetime.now(timezone.utc)
    payment.reviewed_by = sysadmin.id

    if company:
        if payment.payment_type == "upgrade":
            company.upgrade_status = None
        elif payment.payment_type in ("activation", "renewal", "downgrade"):
            company.payment_status = "payment_rejected"

    await db.commit()
    if admin and company and plan:
        background_tasks.add_task(send_payment_rejected, to_email=admin.email,
                                  company_name=company.name, plan_name=plan.name, reason=reason.strip())
    return {"message": "Pago rechazado. Se notificó al asociado."}


@router.get("/blocked-companies")
async def list_blocked_companies(_: User = Depends(require_sysadmin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).where(Company.payment_status.notin_(["active"])).order_by(Company.name))
    items = []
    for c in result.scalars().all():
        latest_r = await db.execute(select(CompanyPayment).where(CompanyPayment.company_id == c.id_company).order_by(CompanyPayment.id.desc()))
        latest = latest_r.scalar_one_or_none()
        active_cp = await _get_active_plan(c.id_company, db)
        plan_name = None
        if active_cp:
            p = await db.get(Plan, active_cp.plan_id)
            plan_name = p.name if p else None
        admin_r = await db.execute(select(User).where(User.company_id == c.id_company).order_by(User.id))
        admin = admin_r.scalars().first()
        items.append({
            "company_id": c.id_company, "company_name": c.name, "nit": c.identification_number,
            "payment_status": c.payment_status, "upgrade_status": c.upgrade_status, "plan_name": plan_name,
            "admin_email": admin.email if admin else None, "admin_name": admin.nombre if admin else None,
            "latest_payment": {"id": latest.id, "type": latest.payment_type, "status": latest.status,
                               "amount": latest.amount, "currency": latest.currency_code,
                               "submitted_at": latest.submitted_at.isoformat() if latest.submitted_at else None,
                               "created_at": latest.created_at.isoformat() if latest.created_at else None} if latest else None,
        })
    return items


class UnblockBody(BaseModel):
    reason: str = ""


@router.post("/unblock-company/{company_id}")
async def unblock_company(company_id: int, body: UnblockBody, sysadmin: User = Depends(require_sysadmin), db: AsyncSession = Depends(get_db)):
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    if company.payment_status == "active" and not company.upgrade_status:
        raise HTTPException(status_code=400, detail="Esta empresa ya está activa")

    await db.execute(
        update(CompanyPayment)
        .where(CompanyPayment.company_id == company_id, CompanyPayment.status.in_(["pending", "submitted"]))
        .values(status="rejected",
                rejection_reason=f"Cancelado por soporte al desbloquear empresa. {body.reason}".strip(". "),
                reviewed_at=datetime.now(timezone.utc), reviewed_by=sysadmin.id)
    )
    company.payment_status = "active"
    company.upgrade_status = None
    await db.commit()
    return {"message": f"Empresa '{company.name}' desbloqueada correctamente.",
            "company_id": company_id, "new_status": "active"}
