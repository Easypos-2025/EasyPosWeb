"""
========================================================
MODELO TASK STATUS
========================================================

Estados posibles de las tareas.
"""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String
from app.database import Base


class TaskStatus(Base):

    __tablename__ = "task_status"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True
    )

    description: Mapped[str] = mapped_column(
        String(255)
    )