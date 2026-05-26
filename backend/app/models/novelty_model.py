from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Enum, ForeignKey, TIMESTAMP, func
from app.database import Base


class Novelty(Base):
    __tablename__ = "novelties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id_company"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("pendiente", "revisada", "resuelta"), default="pendiente"
    )
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class NoveltyEvidence(Base):
    __tablename__ = "novelty_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    novelty_id: Mapped[int] = mapped_column(Integer, ForeignKey("novelties.id", ondelete="CASCADE"), nullable=False, index=True)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=True)
    uploaded_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now())


class NoveltyReply(Base):
    __tablename__ = "novelty_replies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    novelty_id: Mapped[int] = mapped_column(Integer, ForeignKey("novelties.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now())
