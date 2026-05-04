from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, SmallInteger, ForeignKey, DECIMAL
from app.database import Base


class ProductPresentation(Base):
    __tablename__ = "product_presentations"

    id:             Mapped[int]           = mapped_column(Integer, primary_key=True)
    product_id:     Mapped[int]           = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    supply_item_id: Mapped[Optional[int]] = mapped_column(ForeignKey("supply_items.id"), nullable=True)
    name:           Mapped[str]           = mapped_column(String(100), nullable=False)
    factor:         Mapped[object]        = mapped_column(DECIMAL(14, 4), nullable=False, default=1)
    barcode:        Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    price:          Mapped[Optional[object]] = mapped_column(DECIMAL(14, 2), nullable=True)
    is_active:      Mapped[int]           = mapped_column(SmallInteger, default=1)
