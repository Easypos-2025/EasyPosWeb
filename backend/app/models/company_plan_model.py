from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, ForeignKey, Date, Boolean, TIMESTAMP, func
from app.database import Base


class CompanyPlan(Base):
    """
    Relación entre una empresa y su plan activo.
    Se crea cuando el asociado se registra o cuando SYSADMIN asigna/renueva el plan.
    expiration_date = NULL significa indefinido (plan Free).
    """
    __tablename__ = "company_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id_company"), nullable=False, index=True
    )
    plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("plans.id"), nullable=False
    )

    start_date:      Mapped[object] = mapped_column(Date, server_default=func.current_date())
    expiration_date: Mapped[object] = mapped_column(Date, nullable=True)   # NULL = indefinido

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
