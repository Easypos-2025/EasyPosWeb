from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Float, Date, ForeignKey, TIMESTAMP, func
from app.database import Base


class TaskExpense(Base):
    """Gastos pagados asociados a una tarea (materiales comprados, servicios, etc.)"""
    __tablename__ = "task_expenses"

    id:           Mapped[int]   = mapped_column(Integer, primary_key=True)
    task_id:      Mapped[int]   = mapped_column(ForeignKey("tasks.id"), nullable=False, index=True)
    concept:      Mapped[str]   = mapped_column(String(255), nullable=False)  # qué se pagó
    amount:       Mapped[float] = mapped_column(Float, default=0)
    payment_date: Mapped[object]= mapped_column(Date, nullable=True)
    receipt_ref:  Mapped[str]   = mapped_column(String(100), nullable=True)   # # factura / recibo
    created_by:   Mapped[int]   = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at:   Mapped[object]= mapped_column(TIMESTAMP, server_default=func.now())
