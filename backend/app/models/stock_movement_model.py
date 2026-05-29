from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey, TIMESTAMP, DECIMAL, Date, func
from app.database import Base


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id:             Mapped[int]           = mapped_column(Integer, primary_key=True)
    company_id:     Mapped[int]           = mapped_column(ForeignKey("companies.id_company"), nullable=False, index=True)
    supply_item_id: Mapped[int]           = mapped_column(ForeignKey("supply_items.id"), nullable=False, index=True)
    movement_type:  Mapped[str]           = mapped_column(String(20), nullable=False)
    qty:            Mapped[object]        = mapped_column(DECIMAL(14, 4), nullable=False)
    qty_before:     Mapped[object]        = mapped_column(DECIMAL(14, 4), nullable=False, default=0)
    qty_after:      Mapped[object]        = mapped_column(DECIMAL(14, 4), nullable=False, default=0)
    reference_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    reference_id:   Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    movement_date:  Mapped[Optional[object]] = mapped_column(Date, nullable=True, index=True)
    notes:          Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by:     Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at:     Mapped[object]        = mapped_column(TIMESTAMP, server_default=func.now())
