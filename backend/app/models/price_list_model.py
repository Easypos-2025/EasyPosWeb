from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, SmallInteger, ForeignKey, TIMESTAMP, func
from app.database import Base


class PriceList(Base):
    __tablename__ = "price_lists"

    id:          Mapped[int]           = mapped_column(Integer, primary_key=True)
    company_id:  Mapped[int]           = mapped_column(ForeignKey("companies.id_company"), nullable=False, index=True)
    name:        Mapped[str]           = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_default:  Mapped[int]           = mapped_column(SmallInteger, default=0)
    is_active:   Mapped[int]           = mapped_column(SmallInteger, default=1)
    created_at:  Mapped[object]        = mapped_column(TIMESTAMP, server_default=func.now())
