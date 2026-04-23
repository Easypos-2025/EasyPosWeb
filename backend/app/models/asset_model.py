"""
========================================================
MODEL ASSET
========================================================
Activo del sistema
"""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey
from app.database import Base


class Asset(Base):

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(200)
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("asset_categories.id")
    )

    description: Mapped[str] = mapped_column(
        Text
    )

    location: Mapped[str] = mapped_column(
        String(200)
    )
    