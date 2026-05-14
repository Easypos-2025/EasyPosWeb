from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, ForeignKey, DECIMAL
from app.database import Base


class ProductRecipe(Base):
    __tablename__ = "product_recipes"

    id:             Mapped[int]           = mapped_column(Integer, primary_key=True)
    product_id:     Mapped[int]           = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    supply_item_id: Mapped[int]           = mapped_column(ForeignKey("supply_items.id"), nullable=False)
    qty_required:   Mapped[object]        = mapped_column(DECIMAL(14, 4), nullable=False, default=1)
    unit_id:        Mapped[Optional[int]] = mapped_column(ForeignKey("measurement_units.id"), nullable=True)
