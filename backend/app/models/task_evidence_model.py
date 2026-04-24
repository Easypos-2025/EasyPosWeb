from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey, TIMESTAMP, func
from app.database import Base


class TaskEvidence(Base):
    __tablename__ = "task_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False, index=True)

    # image | video | audio | text
    file_type: Mapped[str] = mapped_column(String(20), nullable=False, default="image")

    # Ruta del archivo en disco (vacío para tipo text)
    file_path: Mapped[str] = mapped_column(String(500), nullable=True)

    # Descripción / contenido de texto
    description: Mapped[str] = mapped_column(Text, nullable=True)

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now())
