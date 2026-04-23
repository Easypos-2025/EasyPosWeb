"""
========================================================
MODELO TASK COMMENT
========================================================

Comentarios asociados a una tarea.
"""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Text, ForeignKey
from app.database import Base


class TaskComment(Base):

    __tablename__ = "task_comments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id")
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id")
    )

    comment: Mapped[str] = mapped_column(
        Text
    )