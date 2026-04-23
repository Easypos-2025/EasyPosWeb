"""
========================================================
MODELO TASK MATERIAL
========================================================

Representa materiales o gastos asociados
a una tarea.
"""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Float, ForeignKey
from app.database import Base


class TaskMaterial(Base):

    __tablename__ = "task_materials"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id")
    )

    name: Mapped[str] = mapped_column(
        String(200)
    )

    quantity: Mapped[int] = mapped_column(
        Integer
    )

    unit_cost: Mapped[float] = mapped_column(
        Float
    )

    total_cost: Mapped[float] = mapped_column(
        Float
    )