from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Text, Boolean, ForeignKey, TIMESTAMP, func
from app.database import Base


class TaskComment(Base):
    __tablename__ = "task_comments"

    id:      Mapped[int]  = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int]  = mapped_column(ForeignKey("tasks.id"), nullable=False, index=True)
    user_id: Mapped[int]  = mapped_column(ForeignKey("users.id"), nullable=True)
    comment: Mapped[str]  = mapped_column(Text, nullable=False)

    # True = mensaje/notificación del Auditor/Admin al Task Leader (va al SidebarRight)
    is_notification: Mapped[bool] = mapped_column(Boolean, default=False)
    is_read:         Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now())
