"""
Payment Router — gestión de pagos de planes.

Asociado:
  GET  /payments/my-status              → estado del pago activo de mi empresa
  GET  /payments/my-history             → historial completo de pagos de mi empresa
  GET  /payments/available-upgrades     → planes superiores disponibles para upgrade
  POST /payments/submit-receipt         → sube comprobante (activación / renovación)
  POST /payments/request-upgrade        → solicita upgrade de plan (no bloqueante)
  POST /payments/submit-upgrade-receipt → sube comprobante de upgrade
  POST /payments/request-downgrade      → solicita cambio a plan inferior (con aceptación legal)

SYSADMIN:
  GET  /payments/pending                → lista pagos pending/submitted (todos los tipos)
  GET  /payments/pending-count          → conteo para KPI dashboard
  GET  /payments/history                → historial de pagos aprobados/rechazados con filtros
  PUT  /payments/{id}/approve           → aprueba → activa empresa + fija expiration_date
  PUT  /payments/{id}/reject            → rechaza + razón + email al asociado
"""
import uuid
from datetime import datetime, timezone, date, timedelta
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_sysadmin, get_db
from app.models.company_model import Company
from app.models.company_payment_model import CompanyPayment
from app.models.company_plan_model import CompanyPlan
from app.models.plan_model import Plan
from app.models.plan_price_model import PlanPrice
from app.models.user_model import User
from app.utils.email_service import send_payment_approved, send_payment_rejected

router = APIRouter(prefix="/payments", tags=["Payments"])

BASE_DIR      = Path(__file__).resolve().parent.parent.parent.parent
PAYMENTS_DIR  = BASE_DIR / "backend" / "app" / "uploads" / "payments"
REVIEWS_DIR   = BASE_DIR / "backend" / "app" / "uploads" / "payment_reviews"

ALLOWED_MIME   = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_FILE_SIZE  = 5 * 1024 * 1024   # 5 MB
PLAN_DURATION_DAYS = 365


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_latest_payment(company_id: int, db: Session) -> CompanyPayment | None:
    return (
        db.query(CompanyPayment)
        .filter(CompanyPayment.company_id == company_id)
        .order_by(CompanyPayment.id.desc())
        .first()
    )


def _get_active_plan(company_id: int, db: Session) -> CompanyPlan | None:
    return (
        db.query(CompanyPlan)
        .filter(CompanyPlan.company_id == company_id, CompanyPlan.is_active == True)
        .order_by(CompanyPlan.id.desc())
        .first()
    )


def _plan_price_for(plan: Plan, currency_code: str, db: Session) -> float:
    pp = db.query(PlanPrice).filter(
        PlanPrice.plan_id == plan.id,
        PlanPrice.currency_code == currency_code.upper(),
        PlanPrice.is_active == True,
    ).first()
    return pp.amount if pp else plan.price


async def _save_receipt(file: UploadFile, payment: CompanyPayment) -> str:
    """Valida, guarda y retorna la ruta relativa del comprobante."""
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=400,
            detail="Tipo de archivo no permitido. Usa JPG, PNG, WEBP o PDF."
        )
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="El archivo supera el límite de 5 MB.")

    ext = {
        "image/jpeg": ".jpg", "image/png": ".png",
        "image/webp": ".webp", "application/pdf": ".pdf",
    }.get(file.content_type, ".bin")
    filename = f"{uuid.uuid4().hex}{ext}"
    PAYMENTS_DIR.mkdir(parents=True, exist_ok=True)

    # Eliminar comprobante anterior si existe
    if payment.receipt_url:
        old = PAYMENTS_DIR / payment.receipt_url.split("/")[-1]
        old.unlink(missing_ok=True)

    (PAYMENTS_DIR / filename).write_bytes(content)
    return f"/uploads/payments/{filename}"


def _serialize_payment(p: CompanyPayment, db: Session) -> dict:
    company  = db.get(Company, p.company_id)
    plan     = db.get(Plan, p.plan_id)
    prev_plan = db.get(Plan, p.previous_plan_id) if p.previous_plan_id else None
    admin    = (
        db.query(User)
        .filter(User.company_id == p.company_id)
        .order_by(User.id)
        .first()
    )
    reviewer = db.get(User, p.reviewed_by) if p.reviewed_by else None

    # Para upgrades pendientes (aún no aprobados): mostrar plan activo actual
    current_plan_data = None
    if p.payment_type == "upgrade" and p.status in ("pending", "submitted"):
        active_cp = _get_active_plan(p.company_id, db)
        if active_cp:
            cp = db.get(Plan, active_cp.plan_id)
            if cp:
                current_plan_data = {"id": cp.id, "name": cp.name, "price": cp.price}
    elif prev_plan:
        current_plan_data = {"id": prev_plan.id, "name": prev_plan.name, "price": prev_plan.price}

    return {
        "id":            p.id,
        "payment_type":  p.payment_type,
        "currency_code": p.currency_code,
        "status":        p.status,
        "amount":        p.amount,
        "receipt_url":   p.receipt_url,
        "submitted_at":  p.submitted_at,
        "created_at":    p.created_at,
        # Evidencia de revisión
        "receipt_number":      p.receipt_number,
        "bank_origin":         p.bank_origin,
        "payment_date":        str(p.payment_date) if p.payment_date else None,
        "confirmed_amount":    p.confirmed_amount,
        "review_description":  p.review_description,
        "review_evidence_url": p.review_evidence_url,
        "rejection_reason":    p.rejection_reason,
        "reviewed_at":         p.reviewed_at,
        "reviewed_by_name":    reviewer.nombre if reviewer else None,
        "company": {
            "id":   company.id_company if company else None,
            "name": company.name if company else "—",
            "nit":  company.identification_number if company else "—",
        },
        "plan": {
            "id":    plan.id if plan else None,
            "name":  plan.name if plan else "—",
            "price": plan.price if plan else 0,
        },
        "current_plan": current_plan_data,
        "admin_email": admin.email if admin else "—",
        "admin_name":  admin.nombre if admin else "—",
    }


# ── Asociado: estado de su pago ───────────────────────────────────────────────

@router.get("/my-status")
def get_my_payment_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    payment      = _get_latest_payment(company.id_company, db)
    active_plan  = _get_active_plan(company.id_company, db)
    plan         = db.get(Plan, payment.plan_id) if payment else None
    active_plan_data = db.get(Plan, active_plan.plan_id) if active_plan else None

    return {
        "payment_status": company.payment_status,
        "upgrade_status": company.upgrade_status,
        "payment": {
            "id":                   payment.id,
            "payment_type":         payment.payment_type,
            "status":               payment.status,
            "amount":               payment.amount,
            "currency_code":        payment.currency_code,
            "receipt_url":          payment.receipt_url,
            "rejection_reason":     payment.rejection_reason,
            "review_description":   payment.review_description,
            "review_evidence_url":  payment.review_evidence_url,
            "submitted_at":         payment.submitted_at,
        } if payment else None,
        "plan": {
            "id":    plan.id if plan else None,
            "name":  plan.name if plan else None,
            "price": plan.price if plan else None,
        } if plan else None,
        "active_plan": {
            "id":              active_plan_data.id if active_plan_data else None,
            "name":            active_plan_data.name if active_plan_data else None,
            "expiration_date": str(active_plan.expiration_date) if active_plan and active_plan.expiration_date else None,
        } if active_plan else None,
    }


# ── Asociado: planes disponibles para upgrade ──────────────────────────────────

@router.get("/available-upgrades")
def available_upgrades(
    currency: str = "COP",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    active_plan = _get_active_plan(current_user.company_id, db)
    current_price = 0.0
    if active_plan:
        plan = db.get(Plan, active_plan.plan_id)
        if plan:
            current_price = plan.price

    all_plans = db.query(Plan).filter(Plan.is_active == True).all()
    upgrades = []
    for p in all_plans:
        if p.price > current_price:
            price_in_currency = _plan_price_for(p, currency, db)
            upgrades.append({
                "id":          p.id,
                "name":        p.name,
                "description": p.description,
                "price":       price_in_currency,
                "currency":    currency.upper(),
                "max_users":   p.max_users,
            })
    upgrades.sort(key=lambda x: x["price"])
    return upgrades


# ── Asociado: planes disponibles para downgrade ────────────────────────────────

@router.get("/available-downgrades")
def available_downgrades(
    currency: str = "COP",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    active_plan = _get_active_plan(current_user.company_id, db)
    current_price = 0.0
    if active_plan:
        plan = db.get(Plan, active_plan.plan_id)
        if plan:
            current_price = plan.price

    all_plans = db.query(Plan).filter(Plan.is_active == True).all()
    result = []
    for p in all_plans:
        if p.price < current_price:
            price_in_currency = _plan_price_for(p, currency, db)
            result.append({
                "id":          p.id,
                "name":        p.name,
                "description": p.description,
                "price":       price_in_currency,
                "currency":    currency.upper(),
                "is_free":     p.price == 0,
            })
    result.sort(key=lambda x: x["price"], reverse=True)
    return result


# ── Asociado: subir comprobante (activación / renovación — bloquea) ────────────

@router.post("/submit-receipt")
async def submit_receipt(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    allowed_statuses = ("pending_payment", "payment_rejected", "expired")
    if company.payment_status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Tu empresa no tiene un pago pendiente")

    payment = _get_latest_payment(company.id_company, db)
    if not payment:
        raise HTTPException(status_code=404, detail="Registro de pago no encontrado")

    if payment.status not in ("pending", "rejected"):
        raise HTTPException(status_code=400, detail="No puedes enviar un comprobante en este estado")

    payment.receipt_url  = await _save_receipt(file, payment)
    payment.status       = "submitted"
    payment.submitted_at = datetime.now(timezone.utc)
    payment.rejection_reason = None
    company.payment_status   = "payment_submitted"

    db.commit()
    return {"message": "Comprobante enviado. Estamos revisando tu pago.", "status": "submitted"}


# ── Asociado: solicitar upgrade de plan ────────────────────────────────────────

class UpgradeRequest(BaseModel):
    plan_id: int
    currency_code: str = "COP"


@router.post("/request-upgrade")
def request_upgrade(
    body: UpgradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    if company.upgrade_status == "upgrade_pending":
        raise HTTPException(status_code=400, detail="Ya tienes un upgrade en proceso")

    new_plan = db.get(Plan, body.plan_id)
    if not new_plan or not new_plan.is_active:
        raise HTTPException(status_code=400, detail="Plan no disponible")

    # Verificar que es realmente superior
    active_plan = _get_active_plan(company.id_company, db)
    current_price = 0.0
    if active_plan:
        cp = db.get(Plan, active_plan.plan_id)
        if cp:
            current_price = cp.price

    if new_plan.price <= current_price:
        raise HTTPException(status_code=400, detail="El plan seleccionado no es superior al actual")

    amount = _plan_price_for(new_plan, body.currency_code, db)

    db.add(CompanyPayment(
        company_id    = company.id_company,
        plan_id       = new_plan.id,
        amount        = amount,
        currency_code = body.currency_code.upper(),
        status        = "pending",
        payment_type  = "upgrade",
    ))
    company.upgrade_status = "upgrade_pending"
    db.commit()

    return {
        "message": f"Solicitud de upgrade al plan {new_plan.name} registrada.",
        "plan_name": new_plan.name,
        "amount": amount,
        "currency": body.currency_code.upper(),
    }


# ── Asociado: subir comprobante de upgrade (NO bloqueante) ────────────────────

@router.post("/submit-upgrade-receipt")
async def submit_upgrade_receipt(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    if company.upgrade_status != "upgrade_pending":
        raise HTTPException(status_code=400, detail="No tienes un upgrade pendiente")

    # Buscar el payment de upgrade más reciente
    payment = (
        db.query(CompanyPayment)
        .filter(
            CompanyPayment.company_id == company.id_company,
            CompanyPayment.payment_type == "upgrade",
            CompanyPayment.status.in_(["pending", "rejected"]),
        )
        .order_by(CompanyPayment.id.desc())
        .first()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="Registro de upgrade no encontrado")

    payment.receipt_url  = await _save_receipt(file, payment)
    payment.status       = "submitted"
    payment.submitted_at = datetime.now(timezone.utc)
    payment.rejection_reason = None

    db.commit()
    return {"message": "Comprobante de upgrade enviado. Seguirás con tu plan actual mientras revisamos.", "status": "submitted"}


# ── Asociado: solicitar downgrade (inmediato si es Free, pago si es de pago) ─

class DowngradeRequest(BaseModel):
    plan_id: int
    currency_code: str = "COP"
    legal_accepted: bool  # Checkbox de cláusula legal

    def model_post_init(self, __context):
        if not self.legal_accepted:
            raise ValueError("Debes aceptar las condiciones para cambiar de plan")


@router.post("/request-downgrade")
def request_downgrade(
    body: DowngradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    new_plan = db.get(Plan, body.plan_id)
    if not new_plan or not new_plan.is_active:
        raise HTTPException(status_code=400, detail="Plan no disponible")

    active_cp = _get_active_plan(company.id_company, db)
    current_price = 0.0
    if active_cp:
        cp = db.get(Plan, active_cp.plan_id)
        if cp:
            current_price = cp.price

    if new_plan.price >= current_price:
        raise HTTPException(status_code=400, detail="El plan seleccionado no es inferior al actual")

    # Desactivar plan actual
    if active_cp:
        active_cp.is_active = False

    if new_plan.price == 0:
        # Downgrade a Free: inmediato, sin pago
        db.add(CompanyPlan(
            company_id=company.id_company,
            plan_id=new_plan.id,
            is_active=True,
        ))
        company.payment_status = "active"
        company.upgrade_status = None
        db.commit()
        return {"message": f"Cambiado al plan {new_plan.name} exitosamente.", "requires_payment": False}

    else:
        # Downgrade a plan de pago inferior: requiere pago
        amount = _plan_price_for(new_plan, body.currency_code, db)
        db.add(CompanyPayment(
            company_id    = company.id_company,
            plan_id       = new_plan.id,
            amount        = amount,
            currency_code = body.currency_code.upper(),
            status        = "pending",
            payment_type  = "downgrade",
        ))
        company.payment_status = "pending_payment"
        db.commit()
        return {"message": f"Solicitud de cambio al plan {new_plan.name} registrada. Completa el pago.", "requires_payment": True}


# ── Asociado: planes disponibles (actual + superiores) ────────────────────────

@router.get("/available-plans")
def available_plans(
    currency: str = "COP",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Devuelve el plan actual + todos los de precio mayor, para el selector de renovación."""
    active_cp = _get_active_plan(current_user.company_id, db)
    current_plan_id = active_cp.plan_id if active_cp else None
    current_price   = 0.0
    if active_cp:
        cp = db.get(Plan, active_cp.plan_id)
        if cp:
            current_price = cp.price

    all_plans = db.query(Plan).filter(Plan.is_active == True).order_by(Plan.price).all()
    result = []
    for p in all_plans:
        if p.price >= current_price:
            price_val = _plan_price_for(p, currency, db)
            result.append({
                "id":          p.id,
                "name":        p.name,
                "description": p.description,
                "price":       price_val,
                "currency":    currency.upper(),
                "max_users":   p.max_users,
                "is_current":  p.id == current_plan_id,
            })
    return result


# ── Asociado: solicitar renovación (plan vencido — bloquea) ───────────────────

class RenewalRequest(BaseModel):
    currency_code: str = "COP"
    plan_id: int | None = None   # None = renovar con el mismo plan; int = cambiar a plan igual o superior


@router.post("/request-renewal")
def request_renewal(
    body: RenewalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    allowed_statuses = ("expired", "pending_payment")
    if company.payment_status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="No tienes un pago de renovación pendiente")

    active_cp = _get_active_plan(company.id_company, db)
    if not active_cp:
        raise HTTPException(status_code=404, detail="Plan activo no encontrado")

    current_plan = db.get(Plan, active_cp.plan_id)
    if not current_plan:
        raise HTTPException(status_code=404, detail="Plan actual no encontrado")

    # Determinar qué plan se va a pagar
    if body.plan_id and body.plan_id != current_plan.id:
        target_plan = db.get(Plan, body.plan_id)
        if not target_plan or not target_plan.is_active:
            raise HTTPException(status_code=400, detail="Plan seleccionado no disponible")
        if target_plan.price < current_plan.price:
            raise HTTPException(status_code=400, detail="No puedes seleccionar un plan inferior en la renovación")
        payment_type = "upgrade" if target_plan.price > current_plan.price else "renewal"
    else:
        target_plan  = current_plan
        payment_type = "renewal"

    amount = _plan_price_for(target_plan, body.currency_code, db)

    # Si ya existe un pending para esta empresa (del mismo tipo), reutilizarlo
    existing = (
        db.query(CompanyPayment)
        .filter(
            CompanyPayment.company_id == company.id_company,
            CompanyPayment.status.in_(["pending", "rejected"]),
            CompanyPayment.payment_type == payment_type,
        )
        .order_by(CompanyPayment.id.desc())
        .first()
    )
    if existing:
        existing.plan_id       = target_plan.id
        existing.amount        = amount
        existing.currency_code = body.currency_code.upper()
        existing.status        = "pending"
    else:
        db.add(CompanyPayment(
            company_id    = company.id_company,
            plan_id       = target_plan.id,
            amount        = amount,
            currency_code = body.currency_code.upper(),
            status        = "pending",
            payment_type  = payment_type,
        ))

    company.payment_status = "pending_payment"
    db.commit()

    return {
        "message":      f"Solicitud de {payment_type} al plan {target_plan.name} registrada.",
        "plan_name":    target_plan.name,
        "payment_type": payment_type,
        "amount":       amount,
    }


# ── SYSADMIN: listar pagos pendientes ─────────────────────────────────────────

@router.get("/pending")
def list_pending_payments(
    payment_type: str = None,   # filtro opcional: activation|upgrade|renewal|downgrade
    _: User = Depends(require_sysadmin),
    db: Session = Depends(get_db),
):
    q = db.query(CompanyPayment).filter(
        CompanyPayment.status.in_(["pending", "submitted"])
    )
    if payment_type:
        q = q.filter(CompanyPayment.payment_type == payment_type)

    payments = q.order_by(CompanyPayment.created_at.desc()).all()
    return [_serialize_payment(p, db) for p in payments]


# ── SYSADMIN: conteo KPI ──────────────────────────────────────────────────────

@router.get("/pending-count")
def pending_count(
    _: User = Depends(require_sysadmin),
    db: Session = Depends(get_db),
):
    count = db.query(CompanyPayment).filter(
        CompanyPayment.status.in_(["pending", "submitted"])
    ).count()
    return {"count": count}


# ── SYSADMIN: aprobar pago ────────────────────────────────────────────────────

@router.put("/{payment_id}/approve")
async def approve_payment(
    payment_id: int,
    background_tasks: BackgroundTasks,
    receipt_number:     str        = Form(...),
    bank_origin:        str        = Form(...),
    payment_date:       date       = Form(...),
    confirmed_amount:   float      = Form(None),
    review_description: str        = Form(None),
    file:               UploadFile = File(None),
    sysadmin: User    = Depends(require_sysadmin),
    db: Session       = Depends(get_db),
):
    payment = db.get(CompanyPayment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    if payment.status not in ("pending", "submitted"):
        raise HTTPException(status_code=400, detail="Este pago no puede aprobarse en su estado actual")

    # Validar unicidad: receipt_number + bank_origin no pueden repetirse en pagos aprobados
    rn = receipt_number.strip()
    bo = bank_origin.strip()
    duplicate = (
        db.query(CompanyPayment)
        .filter(
            CompanyPayment.receipt_number == rn,
            CompanyPayment.bank_origin    == bo,
            CompanyPayment.status         == "approved",
            CompanyPayment.id             != payment_id,
        )
        .first()
    )
    if duplicate:
        dup_company = db.get(Company, duplicate.company_id)
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Este número de recibo ya fue registrado para otro pago aprobado.",
                "duplicate": {
                    "payment_id":   duplicate.id,
                    "company_name": dup_company.name if dup_company else "—",
                    "payment_date": str(duplicate.payment_date) if duplicate.payment_date else None,
                    "amount":       duplicate.confirmed_amount or duplicate.amount,
                    "receipt_number": duplicate.receipt_number,
                    "bank_origin":    duplicate.bank_origin,
                },
            },
        )

    # Guardar evidencia del revisor si se adjuntó archivo
    evidence_url = None
    if file and file.filename:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="El archivo de evidencia supera 5 MB.")
        if file.content_type not in ALLOWED_MIME:
            raise HTTPException(status_code=400, detail="Tipo de archivo no permitido.")
        ext      = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "application/pdf": ".pdf"}.get(file.content_type, ".bin")
        fname    = f"rev_{uuid.uuid4().hex}{ext}"
        REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
        (REVIEWS_DIR / fname).write_bytes(content)
        evidence_url = f"/uploads/payment_reviews/{fname}"

    company = db.get(Company, payment.company_id)
    plan    = db.get(Plan, payment.plan_id)
    admin   = (
        db.query(User)
        .filter(User.company_id == payment.company_id)
        .order_by(User.id).first()
    )

    # Guardar plan anterior antes de cambiar
    active_cp = _get_active_plan(payment.company_id, db)
    if active_cp and active_cp.plan_id != payment.plan_id:
        payment.previous_plan_id = active_cp.plan_id

    # Evidencia de revisión
    payment.receipt_number     = rn
    payment.bank_origin        = bo
    payment.payment_date       = payment_date
    payment.confirmed_amount   = confirmed_amount
    payment.review_description = review_description.strip() if review_description else None
    payment.review_evidence_url = evidence_url
    payment.status             = "approved"
    payment.reviewed_at        = datetime.now(timezone.utc)
    payment.reviewed_by        = sysadmin.id

    if company:
        ptype = payment.payment_type
        if ptype in ("activation", "renewal", "downgrade", "upgrade"):
            db.query(CompanyPlan).filter(
                CompanyPlan.company_id == company.id_company,
                CompanyPlan.is_active  == True,
            ).update({"is_active": False})
            db.add(CompanyPlan(
                company_id      = company.id_company,
                plan_id         = payment.plan_id,
                is_active       = True,
                expiration_date = date.today() + timedelta(days=PLAN_DURATION_DAYS),
            ))
            if ptype == "upgrade":
                company.upgrade_status = None
            else:
                company.payment_status = "active"

    db.commit()

    if admin and company and plan:
        background_tasks.add_task(
            send_payment_approved,
            to_email     = admin.email,
            company_name = company.name,
            plan_name    = plan.name,
        )

    return {"message": "Pago aprobado. Plan activado correctamente."}


# ── SYSADMIN: historial de pagos (aprobados / rechazados) ────────────────────

@router.get("/history")
def list_payment_history(
    status:       str = None,   # approved | rejected  (None = ambos)
    payment_type: str = None,   # activation|upgrade|renewal|downgrade
    company_id:   int = None,
    date_from:    str = None,   # YYYY-MM-DD
    date_to:      str = None,
    page:         int = 1,
    page_size:    int = 20,
    _: User = Depends(require_sysadmin),
    db: Session = Depends(get_db),
):
    q = db.query(CompanyPayment).filter(
        CompanyPayment.status.in_(["approved", "rejected"])
    )
    if status and status in ("approved", "rejected"):
        q = q.filter(CompanyPayment.status == status)
    if payment_type:
        q = q.filter(CompanyPayment.payment_type == payment_type)
    if company_id:
        q = q.filter(CompanyPayment.company_id == company_id)
    if date_from:
        try:
            q = q.filter(CompanyPayment.reviewed_at >= datetime.fromisoformat(date_from))
        except ValueError:
            pass
    if date_to:
        try:
            q = q.filter(CompanyPayment.reviewed_at <= datetime.fromisoformat(date_to + "T23:59:59"))
        except ValueError:
            pass

    total = q.count()
    payments = (
        q.order_by(CompanyPayment.reviewed_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "total":    total,
        "page":     page,
        "pages":    max(1, -(-total // page_size)),
        "items":    [_serialize_payment(p, db) for p in payments],
    }


# ── Asociado: historial completo de sus pagos ─────────────────────────────────

@router.get("/my-history")
def get_my_payment_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payments = (
        db.query(CompanyPayment)
        .filter(CompanyPayment.company_id == current_user.company_id)
        .order_by(CompanyPayment.id.desc())
        .all()
    )
    result = []
    for p in payments:
        plan      = db.get(Plan, p.plan_id)
        prev_plan = db.get(Plan, p.previous_plan_id) if p.previous_plan_id else None
        result.append({
            "id":                  p.id,
            "payment_type":        p.payment_type,
            "status":              p.status,
            "amount":              p.amount,
            "currency_code":       p.currency_code,
            "receipt_url":         p.receipt_url,
            "rejection_reason":    p.rejection_reason,
            "review_description":  p.review_description,
            "review_evidence_url": p.review_evidence_url,
            "receipt_number":      p.receipt_number,
            "bank_origin":         p.bank_origin,
            "payment_date":        str(p.payment_date) if p.payment_date else None,
            "confirmed_amount":    p.confirmed_amount,
            "submitted_at":        p.submitted_at,
            "reviewed_at":         p.reviewed_at,
            "created_at":          p.created_at,
            "plan": {
                "id":   plan.id if plan else None,
                "name": plan.name if plan else "—",
            },
            "previous_plan": {
                "id":   prev_plan.id if prev_plan else None,
                "name": prev_plan.name if prev_plan else None,
            } if prev_plan else None,
        })
    return result


# ── SYSADMIN: rechazar pago ───────────────────────────────────────────────────

@router.put("/{payment_id}/reject")
async def reject_payment(
    payment_id: int,
    background_tasks: BackgroundTasks,
    reason:             str        = Form(...),
    review_description: str        = Form(None),
    file:               UploadFile = File(None),
    sysadmin: User  = Depends(require_sysadmin),
    db: Session     = Depends(get_db),
):
    if not reason or not reason.strip():
        raise HTTPException(status_code=422, detail="La razón de rechazo es obligatoria")

    payment = db.get(CompanyPayment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    if payment.status not in ("pending", "submitted"):
        raise HTTPException(status_code=400, detail="Este pago no puede rechazarse en su estado actual")

    # Evidencia del revisor (opcional)
    evidence_url = None
    if file and file.filename:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="El archivo de evidencia supera 5 MB.")
        if file.content_type not in ALLOWED_MIME:
            raise HTTPException(status_code=400, detail="Tipo de archivo no permitido.")
        ext   = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "application/pdf": ".pdf"}.get(file.content_type, ".bin")
        fname = f"rev_{uuid.uuid4().hex}{ext}"
        REVIEWS_DIR.mkdir(parents=True, exist_ok=True)
        (REVIEWS_DIR / fname).write_bytes(content)
        evidence_url = f"/uploads/payment_reviews/{fname}"

    company = db.get(Company, payment.company_id)
    plan    = db.get(Plan, payment.plan_id)
    admin   = (
        db.query(User)
        .filter(User.company_id == payment.company_id)
        .order_by(User.id).first()
    )

    payment.status             = "rejected"
    payment.rejection_reason   = reason.strip()[:1000]
    payment.review_description = review_description.strip() if review_description else None
    payment.review_evidence_url = evidence_url
    payment.reviewed_at        = datetime.now(timezone.utc)
    payment.reviewed_by        = sysadmin.id

    if company:
        if payment.payment_type == "upgrade":
            company.upgrade_status = None
        elif payment.payment_type in ("activation", "renewal", "downgrade"):
            company.payment_status = "payment_rejected"

    db.commit()

    if admin and company and plan:
        background_tasks.add_task(
            send_payment_rejected,
            to_email     = admin.email,
            company_name = company.name,
            plan_name    = plan.name,
            reason       = reason.strip(),
        )

    return {"message": "Pago rechazado. Se notificó al asociado."}
