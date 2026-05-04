from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, SmallInteger, ForeignKey, DECIMAL
from app.database import Base


class PriceListItem(Base):
    __tablename__ = "price_list_items"

    id:               Mapped[int]           = mapped_column(Integer, primary_key=True)
    price_list_id:    Mapped[int]           = mapped_column(ForeignKey("price_lists.id"), nullable=False, index=True)
    product_id:       Mapped[int]           = mapped_column(ForeignKey("products.id"), nullable=False)
    presentation_id:  Mapped[Optional[int]] = mapped_column(ForeignKey("product_presentations.id"), nullable=True)
    price:            Mapped[object]        = mapped_column(DECIMAL(14, 2), nullable=False, default=0)
    is_active:        Mapped[int]           = mapped_column(SmallInteger, default=1)
