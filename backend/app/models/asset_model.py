"""
========================================================
MODEL ASSET
========================================================
Activo del sistema
"""

from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey
from app.database import Base


class Asset(Base):

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(200))

    category_id: Mapped[int] = mapped_column(ForeignKey("asset_categories.id"))

    client_id: Mapped[Optional[int]] = mapped_column(ForeignKey("clients.id"), nullable=True)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
