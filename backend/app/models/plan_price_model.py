from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Float, Boolean, TIMESTAMP, ForeignKey, func
from app.database import Base


class PlanPrice(Base):
    """
    Precios de planes por moneda (multi-country).
    Si no existe precio para una moneda, el frontend muestra plan.price (COP por defecto).
    """
    __tablename__ = "plan_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("plans.id"), nullable=False, index=True
    )
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)   # ISO 4217: COP, USD, MXN…
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now()
    )
