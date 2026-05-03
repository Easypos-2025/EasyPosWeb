from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Boolean, ForeignKey, TIMESTAMP, func
from app.database import Base


class UserNotification(Base):
    __tablename__ = "user_notifications"

    id:          Mapped[int]  = mapped_column(Integer, primary_key=True)
    sender_id:   Mapped[int]  = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    receiver_id: Mapped[int]  = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title:       Mapped[str]  = mapped_column(String(200), nullable=False)
    message:     Mapped[str]  = mapped_column(Text, nullable=False)
    is_read:     Mapped[bool] = mapped_column(Boolean, default=False)
    created_at:  Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now())
