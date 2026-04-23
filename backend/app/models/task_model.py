"""
========================================================
MODELO TASK
========================================================

Representa las tareas del sistema de mantenimiento.

Cada tarea tiene:

- responsable
- profesional ejecutor
- presupuesto
- costos reales
"""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy import func
from app.database import Base


class Task(Base):

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )
    # =================================================
    # ACTIVO RELACIONADO
    # =================================================

    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id")
    )

    # =================================================
    # TITULO
    # =================================================

    title: Mapped[str] = mapped_column(
        String(200)
    )

    # =================================================
    # DESCRIPCIÓN
    # =================================================

    description: Mapped[str] = mapped_column(
        Text
    )

    # =================================================
    # ESTADO
    # =================================================

    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING"
    )

    # =================================================
    # AVANCE
    # =================================================

    progress: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    # =================================================
    # USUARIO QUE CREA LA TAREA
    # =================================================

    created_by: Mapped[int] = mapped_column(
        ForeignKey("user.id")
    )

    # =================================================
    # USUARIO RESPONSABLE
    # =================================================

    assigned_to: Mapped[int] = mapped_column(
        ForeignKey("user.id")
    )

    # =================================================
    # PROFESIONAL EJECUTOR
    # =================================================

    worker_id: Mapped[int] = mapped_column(
        ForeignKey("workers.id")
    )

    # =================================================
    # PRESUPUESTO MANO DE OBRA
    # =================================================

    budget_labor_cost: Mapped[float] = mapped_column(
        Float,
        default=0
    )

    # =================================================
    # COSTO REAL MANO DE OBRA
    # =================================================

    actual_labor_cost: Mapped[float] = mapped_column(
        Float,
        default=0
    )

    # =================================================
    # FECHA ENTREGA
    # =================================================

    due_date: Mapped[DateTime] = mapped_column(
        DateTime
    )

    # =================================================
    # FECHA CREACIÓN
    # =================================================

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # =================================================
    # FECHA CIERRE
    # =================================================

    closed_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )