from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Text, ForeignKey, TIMESTAMP, func
from app.database import Base


class TaskProgressReport(Base):
    """Reporte parcial de avance de una tarea registrado por el Task Leader."""
    __tablename__ = "task_progress_reports"

    id:               Mapped[int]   = mapped_column(Integer, primary_key=True)
    task_id:          Mapped[int]   = mapped_column(ForeignKey("tasks.id"), nullable=False, index=True)
    progress_percent: Mapped[int]   = mapped_column(Integer, default=0)   # % en el momento del reporte
    description:      Mapped[str]   = mapped_column(Text, nullable=False)  # qué se hizo
    created_by:       Mapped[int]   = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at:       Mapped[object]= mapped_column(TIMESTAMP, server_default=func.now())
