from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, SmallInteger, ForeignKey, TIMESTAMP, DECIMAL, Date, func
from app.database import Base


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id:           Mapped[int]           = mapped_column(Integer, primary_key=True)
    company_id:   Mapped[int]           = mapped_column(ForeignKey("companies.id_company"), nullable=False, index=True)
    supplier_id:  Mapped[Optional[int]] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    invoice_no:   Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    order_date:   Mapped[object]        = mapped_column(Date, nullable=False)
    total_amount: Mapped[object]        = mapped_column(DECIMAL(14, 2), default=0)
    notes:        Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status:       Mapped[str]           = mapped_column(String(20), nullable=False, default="draft")
    created_by:   Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at:   Mapped[object]        = mapped_column(TIMESTAMP, server_default=func.now())
