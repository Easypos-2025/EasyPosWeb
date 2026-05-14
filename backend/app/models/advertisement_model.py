from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, Float, Date, SmallInteger, TIMESTAMP, func
from app.database import Base


class Advertisement(Base):
    __tablename__ = "advertisements"

    id:                Mapped[int]    = mapped_column(Integer, primary_key=True)
    company_id:        Mapped[int]    = mapped_column(Integer, nullable=False, index=True)
    title:             Mapped[str]    = mapped_column(String(200), nullable=False)
    description:       Mapped[str]    = mapped_column(Text, nullable=True)
    cta_url:           Mapped[str]    = mapped_column(String(500), nullable=True)
    notes_to_admin:    Mapped[str]    = mapped_column(Text, nullable=True)
    target_profile_id: Mapped[int]    = mapped_column(Integer, nullable=True)
    # pending | approved | active | paused | expired | rejected
    status:            Mapped[str]    = mapped_column(String(20), nullable=False, default="pending")
    slot_position:     Mapped[int]    = mapped_column(SmallInteger, nullable=True)
    priority:          Mapped[int]    = mapped_column(SmallInteger, default=0)
    start_date:        Mapped[object] = mapped_column(Date, nullable=True)
    end_date:          Mapped[object] = mapped_column(Date, nullable=True)
    rejection_reason:  Mapped[str]    = mapped_column(Text, nullable=True)
    approved_by:       Mapped[int]    = mapped_column(Integer, nullable=True)
    approved_at:       Mapped[object] = mapped_column(TIMESTAMP, nullable=True)
    impressions:       Mapped[int]    = mapped_column(Integer, default=0)
    created_at:        Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at:        Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class AdPiece(Base):
    __tablename__ = "ad_pieces"

    id:               Mapped[int]  = mapped_column(Integer, primary_key=True)
    advertisement_id: Mapped[int]  = mapped_column(Integer, nullable=False, index=True)
    # image | video | youtube | text
    piece_type:       Mapped[str]  = mapped_column(String(20), nullable=False)
    media_url:        Mapped[str]  = mapped_column(String(500), nullable=True)
    youtube_id:       Mapped[str]  = mapped_column(String(20), nullable=True)
    text_content:     Mapped[str]  = mapped_column(Text, nullable=True)
    order_index:      Mapped[int]  = mapped_column(SmallInteger, default=0)
    created_at:       Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now())


class AdPayment(Base):
    __tablename__ = "ad_payments"

    id:               Mapped[int]    = mapped_column(Integer, primary_key=True)
    advertisement_id: Mapped[int]    = mapped_column(Integer, nullable=False, index=True)
    company_id:       Mapped[int]    = mapped_column(Integer, nullable=False, index=True)
    amount:           Mapped[float]  = mapped_column(Float, nullable=True)
    currency_code:    Mapped[str]    = mapped_column(String(3), default="COP")
    receipt_url:      Mapped[str]    = mapped_column(String(500), nullable=True)
    payment_date:     Mapped[object] = mapped_column(Date, nullable=True)
    # pending | verified | rejected
    status:           Mapped[str]    = mapped_column(String(20), default="pending")
    notes:            Mapped[str]    = mapped_column(Text, nullable=True)
    verified_by:      Mapped[int]    = mapped_column(Integer, nullable=True)
    verified_at:      Mapped[object] = mapped_column(TIMESTAMP, nullable=True)
    created_at:       Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now())
