from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Float, ForeignKey, TIMESTAMP, func
from app.database import Base


class TaskMaterial(Base):
    __tablename__ = "task_materials"

    id:         Mapped[int]   = mapped_column(Integer, primary_key=True)
    task_id:    Mapped[int]   = mapped_column(ForeignKey("tasks.id"), nullable=False, index=True)
    name:       Mapped[str]   = mapped_column(String(200), nullable=False)
    unit:       Mapped[str]   = mapped_column(String(30),  nullable=True)   # kg, m, unidad, etc.
    quantity:   Mapped[float] = mapped_column(Float, default=1)
    unit_cost:  Mapped[float] = mapped_column(Float, default=0)
    total_cost: Mapped[float] = mapped_column(Float, default=0)
    created_by: Mapped[int]   = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[object]= mapped_column(TIMESTAMP, server_default=func.now())
