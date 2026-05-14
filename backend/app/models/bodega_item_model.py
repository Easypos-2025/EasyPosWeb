from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, SmallInteger, ForeignKey, TIMESTAMP, DateTime, func
from app.database import Base


class BodegaItem(Base):
    __tablename__ = "bodega_items"

    id:                  Mapped[int]           = mapped_column(Integer, primary_key=True)
    company_id:          Mapped[int]           = mapped_column(ForeignKey("companies.id_company"), nullable=False, index=True)
    nombre:              Mapped[str]           = mapped_column(String(150), nullable=False)
    descripcion:         Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    codigo:              Mapped[Optional[str]] = mapped_column(String(50),  nullable=True)
    cantidad_total:      Mapped[int]           = mapped_column(Integer, default=1)
    cantidad_disponible: Mapped[int]           = mapped_column(Integer, default=1)
    unidad_id:           Mapped[Optional[int]] = mapped_column(ForeignKey("measurement_units.id"), nullable=True)
    ubicacion_bodega:    Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    is_active:           Mapped[int]              = mapped_column(SmallInteger, default=1)
    plan_blocked:        Mapped[int]              = mapped_column(SmallInteger, default=0)
    plan_blocked_at:     Mapped[Optional[object]] = mapped_column(DateTime, nullable=True)
    created_at:          Mapped[object]           = mapped_column(TIMESTAMP, server_default=func.now())
