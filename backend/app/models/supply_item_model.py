from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, SmallInteger, ForeignKey, TIMESTAMP, DECIMAL, func
from app.database import Base


class SupplyItem(Base):
    __tablename__ = "supply_items"

    id:              Mapped[int]           = mapped_column(Integer, primary_key=True)
    company_id:      Mapped[int]           = mapped_column(ForeignKey("companies.id_company"), nullable=False, index=True)
    code:            Mapped[Optional[str]] = mapped_column(String(50),  nullable=True, index=True)
    name:            Mapped[str]           = mapped_column(String(200), nullable=False)
    description:     Mapped[Optional[str]] = mapped_column(Text,        nullable=True)
    unit_id:         Mapped[Optional[int]] = mapped_column(ForeignKey("unidades_medida.id"), nullable=True)
    cost_price:      Mapped[object]        = mapped_column(DECIMAL(14, 4), default=0)
    stock_qty:       Mapped[object]        = mapped_column(DECIMAL(14, 4), default=0)
    min_stock:       Mapped[object]        = mapped_column(DECIMAL(14, 4), default=0)
    waste_pct:       Mapped[object]        = mapped_column(DECIMAL(5, 2),  default=0)
    control_stock:   Mapped[int]           = mapped_column(SmallInteger, default=1)
    is_active:       Mapped[int]           = mapped_column(SmallInteger, default=1)
    created_at:      Mapped[object]        = mapped_column(TIMESTAMP, server_default=func.now())
