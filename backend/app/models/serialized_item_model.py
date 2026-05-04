from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, SmallInteger, ForeignKey, TIMESTAMP, DECIMAL, func
from app.database import Base


class SerializedItem(Base):
    __tablename__ = "serialized_items"

    id:            Mapped[int]           = mapped_column(Integer, primary_key=True)
    product_id:    Mapped[int]           = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    serial_code:   Mapped[str]           = mapped_column(String(100), nullable=False, index=True)
    supplier_id:   Mapped[Optional[int]] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    purchase_cost: Mapped[object]        = mapped_column(DECIMAL(14, 2), default=0)
    is_sold:       Mapped[int]           = mapped_column(SmallInteger, default=0)
    sold_at:       Mapped[Optional[object]] = mapped_column(TIMESTAMP, nullable=True)
    created_at:    Mapped[object]        = mapped_column(TIMESTAMP, server_default=func.now())
