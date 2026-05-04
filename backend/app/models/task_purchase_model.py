from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Float, Date, ForeignKey, TIMESTAMP, func
from app.database import Base


class TaskPurchase(Base):
    __tablename__ = "task_purchases"

    id:            Mapped[int]           = mapped_column(Integer, primary_key=True)
    task_id:       Mapped[int]           = mapped_column(ForeignKey("tasks.id"), nullable=False, index=True)
    concept:       Mapped[str]           = mapped_column(String(255), nullable=False)
    amount:        Mapped[float]         = mapped_column(Float, default=0)
    purchase_date: Mapped[object]        = mapped_column(Date, nullable=True)
    supplier:      Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    invoice_ref:   Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_by:    Mapped[int]           = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at:    Mapped[object]        = mapped_column(TIMESTAMP, server_default=func.now())
