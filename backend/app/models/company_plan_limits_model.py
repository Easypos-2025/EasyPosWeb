from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Boolean, Integer, String, ForeignKey, TIMESTAMP, func
from app.database import Base


class CompanyPlanLimits(Base):
    """
    Snapshot de los límites del plan en el momento en que el asociado
    fue activado o cambió de plan. Permite:
    - Que cambios globales en 'plans' no afecten a asociados ya registrados.
    - Configurar límites personalizados por asociado (is_custom=True).
    """
    __tablename__ = "company_plan_limits"

    id:                 Mapped[int]           = mapped_column(Integer, primary_key=True)
    company_id:         Mapped[int]           = mapped_column(ForeignKey("companies.id_company"), nullable=False, unique=True, index=True)
    plan_id:            Mapped[int]           = mapped_column(ForeignKey("plans.id"), nullable=False)

    # Snapshot de límites (-1 = ilimitado)
    max_users:          Mapped[int]           = mapped_column(Integer, default=1)
    max_products:       Mapped[int]           = mapped_column(Integer, default=-1)
    max_categories:     Mapped[int]           = mapped_column(Integer, default=-1)
    max_workers:        Mapped[int]           = mapped_column(Integer, default=-1)
    max_clients:        Mapped[int]           = mapped_column(Integer, default=-1)
    max_bodega_items:   Mapped[int]           = mapped_column(Integer, default=-1)
    max_tasks:          Mapped[int]           = mapped_column(Integer, default=-1)
    max_daily_invoices: Mapped[int]           = mapped_column(Integer, default=-1)
    max_assets:         Mapped[int]           = mapped_column(Integer, default=-1)

    is_custom:          Mapped[bool]          = mapped_column(Boolean, default=False)
    notes:              Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
