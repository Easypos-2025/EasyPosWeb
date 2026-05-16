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

from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String
from app.database import Base


class AssetCategory(Base):

    __tablename__ = "asset_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
