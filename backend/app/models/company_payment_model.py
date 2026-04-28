from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Float, DateTime, ForeignKey, func
from app.database import Base


class CompanyPayment(Base):
    """
    Registro de pagos de activación de planes (planes de pago, no Free).
    Ciclo de vida: pending → submitted → approved | rejected → submitted (reenvío).
    """
    __tablename__ = "company_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id_company"), nullable=False, index=True
    )
    plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("plans.id"), nullable=False
    )

    amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Tipo: activation | upgrade | renewal | downgrade
    payment_type: Mapped[str] = mapped_column(String(20), nullable=False, default="activation")

    # Moneda en que se acordó el pago
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="COP")

    # Estados: pending | submitted | approved | rejected
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    receipt_url: Mapped[str] = mapped_column(String(500), nullable=True)

    # Razón de rechazo enviada al asociado
    rejection_reason: Mapped[str] = mapped_column(Text, nullable=True)

    submitted_at: Mapped[object] = mapped_column(DateTime, nullable=True)
    reviewed_at: Mapped[object] = mapped_column(DateTime, nullable=True)

    # SYSADMIN que procesó el pago
    reviewed_by: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )

    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
