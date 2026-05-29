from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, SmallInteger, DECIMAL, Date, TIMESTAMP, DateTime, func
from app.database import Base


class InventoryEntry(Base):
    __tablename__ = "inventory_entries"

    id:            Mapped[int]           = mapped_column(Integer, primary_key=True)
    id_entrada:    Mapped[int]           = mapped_column(Integer, nullable=False, index=True)
    id_item:       Mapped[int]           = mapped_column(Integer, nullable=False, index=True)
    id_proveedor:  Mapped[int]           = mapped_column(Integer, default=0)
    company_id:    Mapped[int]           = mapped_column(Integer, nullable=False, index=True)
    fecha:         Mapped[object]        = mapped_column(Date, nullable=False)
    cantidad:      Mapped[object]        = mapped_column(DECIMAL(14, 4), default=0)
    cod_empleado:  Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    observacion:   Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    autorizada:    Mapped[int]           = mapped_column(Integer, default=0)
    revisada:      Mapped[int]           = mapped_column(SmallInteger, default=0)
    cobrar:        Mapped[int]           = mapped_column(SmallInteger, default=0)
    agrupar:       Mapped[int]           = mapped_column(Integer, default=0)
    synced:        Mapped[int]           = mapped_column(SmallInteger, default=0)
    created_at:    Mapped[object]        = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at:    Mapped[Optional[object]] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
