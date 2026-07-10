from sqlalchemy import Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database import Base


class CompanyConfig(Base):
    """
    Configuraciones adicionales por empresa.
    Una fila por empresa — crece con nuevos campos por módulo.
    Si no existe fila → todos los campos en su valor por defecto (0 / NULL).
    """
    __tablename__ = "company_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id_company"), unique=True, nullable=False, index=True
    )

    # ── POS Electrónico ──────────────────────────────────────────────────────
    has_pos_electronico: Mapped[int] = mapped_column(Integer, default=0)
    pos_electronico_token: Mapped[str] = mapped_column(String(255), nullable=True)

    # ── (Futuros módulos se agregan aquí agrupados por sección) ─────────────

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
