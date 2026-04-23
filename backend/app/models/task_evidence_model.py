"""
========================================================
MODELO TASK EVIDENCE
========================================================

Evidencias asociadas a una tarea.
"""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, ForeignKey
from app.database import Base


class TaskEvidence(Base):

    __tablename__ = "task_evidence"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id")
    )

    file_type: Mapped[str] = mapped_column(
        String(50)
    )

    file_path: Mapped[str] = mapped_column(
        String(255)
    )

    description: Mapped[str] = mapped_column(
        String(255)
    )