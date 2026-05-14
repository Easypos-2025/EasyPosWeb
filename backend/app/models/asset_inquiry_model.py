from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Boolean, Integer, String, Text, ForeignKey, TIMESTAMP, func, UniqueConstraint
from app.database import Base


class AssetInquiry(Base):
    """Consulta de interesado generada desde la página pública del activo (QR)."""
    __tablename__ = "asset_inquiries"

    __table_args__ = (
        UniqueConstraint("asset_id", "email", name="uq_inquiry_asset_email"),
    )

    id:              Mapped[int]           = mapped_column(Integer, primary_key=True)
    asset_id:        Mapped[int]           = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id:      Mapped[Optional[int]] = mapped_column(ForeignKey("companies.id_company"), nullable=True, index=True)
    list_code:       Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    name:            Mapped[str]           = mapped_column(String(100), nullable=False)
    phone:           Mapped[str]           = mapped_column(String(20), nullable=False)
    email:           Mapped[str]           = mapped_column(String(150), nullable=False)
    interest:        Mapped[str]           = mapped_column(String(20), nullable=False)   # 'arriendo' | 'compra' | 'info'
    message:         Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confirm_token:   Mapped[str]           = mapped_column(String(64), unique=True, nullable=False)
    status:          Mapped[str]           = mapped_column(String(20), nullable=False, default="pending")  # pending | confirmed | expired
    ip_address:      Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    notified:        Mapped[bool]           = mapped_column(Boolean, default=False, nullable=False)
    confirmed_at:    Mapped[Optional[object]] = mapped_column(TIMESTAMP, nullable=True)
    created_at:      Mapped[object]        = mapped_column(TIMESTAMP, server_default=func.now())
