from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, ForeignKey, TIMESTAMP, func
from app.database import Base


class InvitationToken(Base):
    __tablename__ = "invitation_tokens"

    id:          Mapped[int]    = mapped_column(Integer, primary_key=True, index=True)
    token:       Mapped[str]    = mapped_column(String(64), unique=True, index=True, nullable=False)
    company_id:  Mapped[int]    = mapped_column(Integer, ForeignKey("companies.id_company"), nullable=False)
    role_id:     Mapped[int]    = mapped_column(Integer, ForeignKey("roles.id"), nullable=False)
    created_by:  Mapped[int]    = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at:  Mapped[object] = mapped_column(TIMESTAMP, nullable=False)
    used_at:     Mapped[object] = mapped_column(TIMESTAMP, nullable=True, default=None)
    created_at:  Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now())
