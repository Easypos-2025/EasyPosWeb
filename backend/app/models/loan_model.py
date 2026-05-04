from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Date, DateTime, ForeignKey, TIMESTAMP, func
from app.database import Base

# estados: pendiente_confirmacion | activo | retorno_pendiente | devuelto | devuelto_con_dano
# estado_fisico: perfecto | desgaste | dano_leve | dano_grave


class Loan(Base):
    __tablename__ = "loans"

    id:                       Mapped[int]           = mapped_column(Integer, primary_key=True)
    company_id:               Mapped[int]           = mapped_column(ForeignKey("companies.id_company"), nullable=False, index=True)
    bodega_item_id:           Mapped[int]           = mapped_column(ForeignKey("bodega_items.id"), nullable=False)
    cantidad:                 Mapped[int]           = mapped_column(Integer, default=1)
    external_collaborator_id: Mapped[int]           = mapped_column(ForeignKey("external_collaborators.id"), nullable=False)
    created_by:               Mapped[int]           = mapped_column(ForeignKey("users.id"), nullable=False)
    estado:                   Mapped[str]           = mapped_column(String(30), default="pendiente_confirmacion", nullable=False)
    qr_token:                 Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    qr_expires_at:            Mapped[Optional[object]] = mapped_column(DateTime, nullable=True)
    fecha_salida_confirmada:  Mapped[Optional[object]] = mapped_column(DateTime, nullable=True)
    fecha_retorno_esperada:   Mapped[Optional[object]] = mapped_column(Date, nullable=True)
    fecha_retorno_confirmada: Mapped[Optional[object]] = mapped_column(DateTime, nullable=True)
    estado_fisico_retorno:    Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    notas:                    Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at:               Mapped[object]        = mapped_column(TIMESTAMP, server_default=func.now())
