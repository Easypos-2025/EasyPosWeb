from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database import Base


class UserSession(Base):

    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id")
    )

    token: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )

    ip: Mapped[str] = mapped_column(
        String(100),
        nullable=True
    )

    user_agent: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )