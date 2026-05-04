from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, SmallInteger, ForeignKey, TIMESTAMP, DECIMAL, func
from app.database import Base


class ProductReference(Base):
    __tablename__ = "product_references"

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int]           = mapped_column(ForeignKey("companies.id_company"), nullable=False, index=True)
    code:       Mapped[str]           = mapped_column(String(50),  nullable=False)
    name:       Mapped[str]           = mapped_column(String(200), nullable=False)
    base_price: Mapped[object]        = mapped_column(DECIMAL(14, 2), default=0)
    base_cost:  Mapped[object]        = mapped_column(DECIMAL(14, 2), default=0)
    is_active:  Mapped[int]           = mapped_column(SmallInteger, default=1)
    created_at: Mapped[object]        = mapped_column(TIMESTAMP, server_default=func.now())
