from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, ForeignKey
from app.database import Base


class UnidadMedida(Base):
    __tablename__ = "measurement_units"

    id:           Mapped[int]           = mapped_column(Integer, primary_key=True)
    company_id:   Mapped[int]           = mapped_column(ForeignKey("companies.id_company"), nullable=False, index=True)
    name:         Mapped[str]           = mapped_column(String(100), nullable=False)
    abreviatura:  Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
