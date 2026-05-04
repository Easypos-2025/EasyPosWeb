from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, SmallInteger, Text, ForeignKey, TIMESTAMP, func
from app.database import Base


class ExternalCollaborator(Base):
    __tablename__ = "external_collaborators"

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int]           = mapped_column(ForeignKey("companies.id_company"), nullable=False, index=True)
    nombre:     Mapped[str]           = mapped_column(String(150), nullable=False)
    dni:        Mapped[str]           = mapped_column(String(30),  nullable=False)
    empresa:    Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    telefono:   Mapped[Optional[str]] = mapped_column(String(30),  nullable=True)
    email:      Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    notas:      Mapped[Optional[str]] = mapped_column(Text,        nullable=True)
    is_active:  Mapped[int]           = mapped_column(SmallInteger, default=1)
    created_at: Mapped[object]        = mapped_column(TIMESTAMP, server_default=func.now())
