from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, SmallInteger, ForeignKey, TIMESTAMP, DateTime, func
from app.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id:           Mapped[int]           = mapped_column(Integer, primary_key=True)
    company_id:   Mapped[int]           = mapped_column(ForeignKey("companies.id_company"), nullable=False, index=True)
    # id_proveedor = Id_Proveedor del escritorio (consecutivo por empresa)
    id_proveedor: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    name:         Mapped[str]           = mapped_column(String(200), nullable=False)
    nit:          Mapped[Optional[str]] = mapped_column(String(50),  nullable=True)
    contact_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    email:        Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    phone:        Mapped[Optional[str]] = mapped_column(String(30),  nullable=True)
    telefono_celular: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address:      Mapped[Optional[str]] = mapped_column(Text,        nullable=True)
    notes:        Mapped[Optional[str]] = mapped_column(Text,        nullable=True)
    is_active:    Mapped[int]           = mapped_column(SmallInteger, default=1)
    synced:       Mapped[int]           = mapped_column(SmallInteger, default=0)
    created_at:   Mapped[object]        = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at:   Mapped[Optional[object]] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
