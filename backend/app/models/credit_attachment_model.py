from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, TIMESTAMP, func
from app.database import Base


class CreditAttachment(Base):
    __tablename__ = "credit_attachments"

    id:          Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id:  Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    nro_credito: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tipo:        Mapped[str] = mapped_column(String(20),  nullable=False, default="foto")
    filename:    Mapped[str] = mapped_column(String(255), nullable=False)
    url:         Mapped[str] = mapped_column(String(500), nullable=False)
    file_size:   Mapped[int] = mapped_column(Integer,     nullable=False, default=0)
    created_at:  Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now())
