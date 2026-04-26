from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Enum, ForeignKey, TIMESTAMP, func
from app.database import Base


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id_company"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("abierto", "en_proceso", "resuelto", "cerrado"), default="abierto"
    )
    priority: Mapped[str] = mapped_column(
        Enum("baja", "media", "alta", "critica"), default="media"
    )
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class TicketEvidence(Base):
    __tablename__ = "ticket_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_id: Mapped[int] = mapped_column(Integer, ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=True)
    uploaded_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now())
