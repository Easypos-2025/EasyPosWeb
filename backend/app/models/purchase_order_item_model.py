from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, ForeignKey, DECIMAL
from app.database import Base


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id:                Mapped[int]           = mapped_column(Integer, primary_key=True)
    purchase_order_id: Mapped[int]           = mapped_column(ForeignKey("purchase_orders.id"), nullable=False, index=True)
    supply_item_id:    Mapped[int]           = mapped_column(ForeignKey("supply_items.id"), nullable=False)
    qty:               Mapped[object]        = mapped_column(DECIMAL(14, 4), nullable=False, default=0)
    unit_price:        Mapped[object]        = mapped_column(DECIMAL(14, 4), nullable=False, default=0)
    subtotal:          Mapped[object]        = mapped_column(DECIMAL(14, 2), nullable=False, default=0)
    presentation_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
