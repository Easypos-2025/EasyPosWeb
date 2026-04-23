"""
========================================================
MODELO ASSET CATEGORY
========================================================

Define categorías de activos.

Ejemplos:

Property
Vehicle
Equipment
Infrastructure
"""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String
from app.database import Base


class AssetCategory(Base):

    __tablename__ = "asset_categories"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True
    )

    description: Mapped[str] = mapped_column(
        String(255)
    )
