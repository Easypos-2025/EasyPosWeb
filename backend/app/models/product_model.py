from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, SmallInteger, ForeignKey, TIMESTAMP, DECIMAL, DateTime, func
from app.database import Base

INVENTORY_BEHAVIORS = ("recipe", "presentation", "serialized", "weight", "direct")


class Product(Base):
    __tablename__ = "products"

    id:                  Mapped[int]           = mapped_column(Integer, primary_key=True)
    company_id:          Mapped[int]           = mapped_column(ForeignKey("companies.id_company"), nullable=False, index=True)
    code:                Mapped[Optional[str]] = mapped_column(String(50),  nullable=True, index=True)
    name:                Mapped[str]           = mapped_column(String(200), nullable=False)
    description:         Mapped[Optional[str]] = mapped_column(Text,        nullable=True)
    photo_url:           Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    category_id:         Mapped[Optional[int]] = mapped_column(ForeignKey("product_categories.id"), nullable=True)
    reference_id:        Mapped[Optional[int]] = mapped_column(ForeignKey("product_references.id"), nullable=True)
    inventory_behavior:  Mapped[str]           = mapped_column(String(20), nullable=False, default="direct")
    base_price:          Mapped[object]        = mapped_column(DECIMAL(14, 2), default=0)
    cost_price:          Mapped[object]        = mapped_column(DECIMAL(14, 2), default=0)
    tax_rate:            Mapped[object]        = mapped_column(DECIMAL(5, 2),  default=0)
    min_stock:           Mapped[object]        = mapped_column(DECIMAL(14, 4), default=0)
    ask_price:           Mapped[int]           = mapped_column(SmallInteger, default=0)
    ask_description:     Mapped[int]           = mapped_column(SmallInteger, default=0)
    is_active:           Mapped[int]           = mapped_column(SmallInteger, default=1)
    plan_blocked:        Mapped[int]           = mapped_column(SmallInteger, default=0)
    plan_blocked_at:     Mapped[Optional[object]] = mapped_column(DateTime, nullable=True)
    created_at:          Mapped[object]        = mapped_column(TIMESTAMP, server_default=func.now())
