from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, SmallInteger, DECIMAL, ForeignKey, UniqueConstraint
from app.database import Base


class Asset(Base):
    __tablename__ = "assets"

    __table_args__ = (
        UniqueConstraint("list_code", name="uq_assets_list_code"),
    )

    id:                   Mapped[int]           = mapped_column(Integer, primary_key=True)
    name:                 Mapped[str]           = mapped_column(String(200), nullable=False)
    short_name:           Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category_id:          Mapped[int]           = mapped_column(ForeignKey("asset_categories.id"), nullable=False)
    client_id:            Mapped[Optional[int]] = mapped_column(ForeignKey("clients.id"), nullable=True)
    owner_id:             Mapped[Optional[int]] = mapped_column(ForeignKey("clients.id"), nullable=True)
    description:          Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location:             Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    address:              Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    phone:                Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sector_id:            Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_rented:            Mapped[int]           = mapped_column(SmallInteger, nullable=False, default=0)
    is_active:            Mapped[int]           = mapped_column(SmallInteger, nullable=False, default=1)
    has_sale_option:      Mapped[int]           = mapped_column(SmallInteger, nullable=False, default=0)
    canon_value:          Mapped[Optional[object]] = mapped_column(DECIMAL(15, 2), nullable=True)
    cadastral_value:      Mapped[Optional[object]] = mapped_column(DECIMAL(15, 2), nullable=True)
    commercial_value:     Mapped[Optional[object]] = mapped_column(DECIMAL(15, 2), nullable=True)
    sale_price:           Mapped[Optional[object]] = mapped_column(DECIMAL(15, 2), nullable=True)
    appraisal_year:       Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    acquisition_type:     Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    registration:         Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    property_number:      Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    additional_reference: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    list_code:            Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
