from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Date, Integer, String, Text, Float, DateTime, ForeignKey, func
from app.database import Base


class CompanyPayment(Base):
    """
    Registro de pagos de activación de planes.
    Ciclo de vida: pending → submitted → approved | rejected → submitted (reenvío).
    """
    __tablename__ = "company_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id_company"), nullable=False, index=True
    )
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("plans.id"), nullable=False)

    # Plan anterior (para tracking de renovación/upgrade/downgrade)
    previous_plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("plans.id"), nullable=True)

    amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Tipo: activation | upgrade | renewal | downgrade
    payment_type: Mapped[str] = mapped_column(String(20), nullable=False, default="activation")

    # Moneda en que se acordó el pago
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="COP")

    # Estados: pending | submitted | approved | rejected
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    # Comprobante subido por el asociado
    receipt_url: Mapped[str] = mapped_column(String(500), nullable=True)

    # ── Evidencia de revisión (llenada por SYSADMIN al aprobar o rechazar) ──
    receipt_number:      Mapped[str]   = mapped_column(String(100), nullable=True)   # N° comprobante banco
    bank_origin:         Mapped[str]   = mapped_column(String(100), nullable=True)   # Banco del asociado
    payment_date:        Mapped[object]= mapped_column(Date,        nullable=True)   # Fecha del pago
    confirmed_amount:    Mapped[float] = mapped_column(Float,       nullable=True)   # Monto confirmado
    review_description:  Mapped[str]   = mapped_column(Text,        nullable=True)   # Observaciones
    review_evidence_url: Mapped[str]   = mapped_column(String(500), nullable=True)   # Archivo del revisor

    # Razón de rechazo (breve, enviada al asociado)
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=True)

    submitted_at: Mapped[object] = mapped_column(DateTime, nullable=True)
    reviewed_at:  Mapped[object] = mapped_column(DateTime, nullable=True)

    # SYSADMIN que procesó el pago
    reviewed_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
