from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, SmallInteger, ForeignKey, TIMESTAMP, func
from app.database import Base


class AssetMedia(Base):
    __tablename__ = "asset_media"

    id:          Mapped[int]           = mapped_column(Integer, primary_key=True)
    asset_id:    Mapped[int]           = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True)
    file_url:    Mapped[str]           = mapped_column(String(500), nullable=False)
    file_name:   Mapped[str]           = mapped_column(String(200), nullable=False)
    file_type:   Mapped[str]           = mapped_column(String(10), nullable=False)   # 'image' | 'video'
    file_size:   Mapped[int]           = mapped_column(Integer, nullable=False, default=0)
    sort_order:  Mapped[int]           = mapped_column(SmallInteger, nullable=False, default=0)
    uploaded_by: Mapped[int]           = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at:  Mapped[object]        = mapped_column(TIMESTAMP, server_default=func.now())
