"""
========================================================
MODELO WORKER
========================================================

Representa el profesional que ejecuta una tarea.

Ejemplos:

electricista
plomero
tecnico
auxiliar
"""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String
from app.database import Base


class Worker(Base):

    __tablename__ = "workers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100)
    )

    profession: Mapped[str] = mapped_column(
        String(100)
    )

    phone: Mapped[str] = mapped_column(
        String(50)
    )
    