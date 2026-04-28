"""
Payment Router — gestión de pagos de activación de planes.

Endpoints de asociado (JWT requerido):
  GET  /payments/my-status           → estado actual del pago de mi empresa
  POST /payments/submit-receipt      → sube comprobante y cambia estado a 'submitted'

Endpoints SYSADMIN (JWT SYSADMIN requerido):
  GET  /payments/pending             → lista pagos pending/submitted
  PUT  /payments/{id}/approve        → aprueba pago → empresa queda 'active'
  PUT  /payments/{id}/reject         → rechaza pago + razón → email al asociado
"""
import uuid
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_sysadmin, get_db
from app.models.company_model import Company
from app.models.company_payment_model import CompanyPayment
from app.models.plan_model import Plan
from app.models.user_model import User
from app.utils.email_service import send_payment_approved, send_payment_rejected

router = APIRouter(prefix="/payments", tags=["Payments"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PAYMENTS_DIR = BASE_DIR / "backend" / "app" / "uploads" / "payments"

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

VALID_TRANSITIONS = {
    "pending":          ["submitted"],
    "submitted":        [],           # Solo SYSADMIN puede cambiar desde aquí
    "approved":         [],
    "rejected":         ["submitted"],
}


def _get_company_payment(company_id: int, db: Session) -> CompanyPayment | None:
    return (
        db.query(CompanyPayment)
        .filter(CompanyPayment.company_id == company_id)
        .order_by(CompanyPayment.id.desc())
        .first()
    )


# ─── Asociado: ver estado de su pago ──────────────────────────────────────────

@router.get("/my-status")
def get_my_payment_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    payment = _get_company_payment(company.id_company, db)
    plan = db.get(Plan, payment.plan_id) if payment else None

    return {
        "payment_status": company.payment_status,
        "payment": {
            "id":               payment.id if payment else None,
            "status":           payment.status if payment else None,
            "amount":           payment.amount if payment else None,
            "receipt_url":      payment.receipt_url if payment else None,
            "rejection_reason": payment.rejection_reason if payment else None,
            "submitted_at":     payment.submitted_at if payment else None,
            "reviewed_at":      payment.reviewed_at if payment else None,
        } if payment else None,
        "plan": {
            "id":    plan.id if plan else None,
            "name":  plan.name if plan else None,
            "price": plan.price if plan else None,
        } if plan else None,
    }


# ─── Asociado: subir comprobante ──────────────────────────────────────────────

@router.post("/submit-receipt")
async def submit_receipt(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    company = db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    if company.payment_status not in ("pending_payment", "payment_rejected"):
        raise HTTPException(status_code=400, detail="Tu empresa no tiene un pago pendiente")

    payment = _get_company_payment(company.id_company, db)
    if not payment:
        raise HTTPException(status_code=404, detail="Registro de pago no encontrado")

    if payment.status not in VALID_TRANSITIONS or "submitted" not in VALID_TRANSITIONS[payment.status]:
        raise HTTPException(status_code=400, detail="No puedes enviar un comprobante en este estado")

    # Validar MIME
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=400,
            detail="Tipo de archivo no permitido. Sube una imagen (JPG, PNG, WEBP) o PDF."
        )

    # Leer y validar tamaño
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="El archivo supera el límite de 5 MB")

    # Guardar con UUID (sin nombre del usuario en el path)
    ext = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "application/pdf": ".pdf",
    }.get(file.content_type, ".bin")
    filename = f"{uuid.uuid4().hex}{ext}"
    PAYMENTS_DIR.mkdir(parents=True, exist_ok=True)
    dest = PAYMENTS_DIR / filename
    dest.write_bytes(content)

    # Eliminar comprobante anterior si existe
    if payment.receipt_url:
        old_name = payment.receipt_url.split("/")[-1]
        old_path = PAYMENTS_DIR / old_name
        if old_path.exists():
            old_path.unlink(missing_ok=True)

    # Actualizar registro
    payment.receipt_url = f"/uploads/payments/{filename}"
    payment.status = "submitted"
    payment.submitted_at = datetime.now(timezone.utc)
    payment.rejection_reason = None
    company.payment_status = "payment_submitted"

    db.commit()

    return {"message": "Comprobante enviado. Estamos revisando tu pago.", "status": "submitted"}


# ─── SYSADMIN: listar pagos pendientes/enviados ────────────────────────────────

@router.get("/pending")
def list_pending_payments(
    _: User = Depends(require_sysadmin),
    db: Session = Depends(get_db),
):
    payments = (
        db.query(CompanyPayment)
        .filter(CompanyPayment.status.in_(["pending", "submitted"]))
        .order_by(CompanyPayment.created_at.desc())
        .all()
    )

    result = []
    for p in payments:
        company = db.get(Company, p.company_id)
        plan    = db.get(Plan, p.plan_id)
        # Email del admin de la empresa
        admin = (
            db.query(User)
            .filter(User.company_id == p.company_id)
            .order_by(User.id)
            .first()
        )
        result.append({
            "id":            p.id,
            "status":        p.status,
            "amount":        p.amount,
            "receipt_url":   p.receipt_url,
            "submitted_at":  p.submitted_at,
            "created_at":    p.created_at,
            "company": {
                "id":   company.id_company if company else None,
                "name": company.name if company else "—",
                "nit":  company.identification_number if company else "—",
            },
            "plan": {
                "id":   plan.id if plan else None,
                "name": plan.name if plan else "—",
            },
            "admin_email": admin.email if admin else "—",
            "admin_name":  admin.nombre if admin else "—",
        })

    return result


# ─── SYSADMIN: contar pagos pendientes (para KPI) ─────────────────────────────

@router.get("/pending-count")
def pending_count(
    _: User = Depends(require_sysadmin),
    db: Session = Depends(get_db),
):
    count = db.query(CompanyPayment).filter(
        CompanyPayment.status.in_(["pending", "submitted"])
    ).count()
    return {"count": count}


# ─── SYSADMIN: aprobar pago ────────────────────────────────────────────────────

@router.put("/{payment_id}/approve")
def approve_payment(
    payment_id: int,
    sysadmin: User = Depends(require_sysadmin),
    db: Session = Depends(get_db),
):
    payment = db.get(CompanyPayment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    if payment.status not in ("pending", "submitted"):
        raise HTTPException(status_code=400, detail="Este pago no puede aprobarse en su estado actual")

    company = db.get(Company, payment.company_id)
    plan    = db.get(Plan, payment.plan_id)
    admin   = (
        db.query(User)
        .filter(User.company_id == payment.company_id)
        .order_by(User.id)
        .first()
    )

    payment.status      = "approved"
    payment.reviewed_at = datetime.now(timezone.utc)
    payment.reviewed_by = sysadmin.id

    if company:
        company.payment_status = "active"

    db.commit()

    if admin and company and plan:
        try:
            send_payment_approved(
                to_email=admin.email,
                company_name=company.name,
                plan_name=plan.name,
            )
        except Exception:
            pass

    return {"message": "Pago aprobado. La empresa ya está activa."}


# ─── SYSADMIN: rechazar pago ───────────────────────────────────────────────────

class RejectRequest(BaseModel):
    reason: str

    def model_post_init(self, __context):
        if not self.reason or not self.reason.strip():
            raise ValueError("La razón de rechazo es obligatoria")
        self.reason = self.reason.strip()[:1000]


@router.put("/{payment_id}/reject")
def reject_payment(
    payment_id: int,
    body: RejectRequest,
    sysadmin: User = Depends(require_sysadmin),
    db: Session = Depends(get_db),
):
    payment = db.get(CompanyPayment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    if payment.status not in ("pending", "submitted"):
        raise HTTPException(status_code=400, detail="Este pago no puede rechazarse en su estado actual")

    company = db.get(Company, payment.company_id)
    plan    = db.get(Plan, payment.plan_id)
    admin   = (
        db.query(User)
        .filter(User.company_id == payment.company_id)
        .order_by(User.id)
        .first()
    )

    payment.status           = "rejected"
    payment.rejection_reason = body.reason
    payment.reviewed_at      = datetime.now(timezone.utc)
    payment.reviewed_by      = sysadmin.id

    if company:
        company.payment_status = "payment_rejected"

    db.commit()

    if admin and company and plan:
        try:
            send_payment_rejected(
                to_email=admin.email,
                company_name=company.name,
                plan_name=plan.name,
                reason=body.reason,
            )
        except Exception:
            pass

    return {"message": "Pago rechazado. Se notificó al asociado."}
