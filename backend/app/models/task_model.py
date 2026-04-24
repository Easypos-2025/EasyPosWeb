from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Float, func
from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Multi-tenant — empresa a la que pertenece la tarea
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id_company"), nullable=True, index=True
    )

    # Activo relacionado (edificio, vehículo, equipo, etc.)
    asset_id: Mapped[int] = mapped_column(
        ForeignKey("assets.id"), nullable=True
    )

    # Título y descripción
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Estado (FK a task_status)
    status_id: Mapped[int] = mapped_column(
        ForeignKey("task_status.id"), default=1, nullable=True
    )

    # Porcentaje de avance (0-100)
    progress: Mapped[int] = mapped_column(Integer, default=0)

    # Usuarios (Task Leader que crea + Task Leader asignado)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    assigned_to: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    # Ejecutor principal (worker, sin acceso al sistema)
    worker_id: Mapped[int] = mapped_column(
        ForeignKey("workers.id"), nullable=True
    )

    # Presupuesto y costos
    budget_labor_cost: Mapped[float] = mapped_column(Float, default=0)
    actual_labor_cost: Mapped[float] = mapped_column(Float, default=0)

    # Fechas
    start_date: Mapped[object] = mapped_column(DateTime, nullable=True)
    due_date:   Mapped[object] = mapped_column(DateTime, nullable=True)
    closed_at:  Mapped[object] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relaciones
    status = relationship("TaskStatus", foreign_keys=[status_id], lazy="joined")
