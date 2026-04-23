"""
========================================================
COUNTRY MODEL
========================================================
"""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, String, TIMESTAMP
from app.database import Base


class Country(Base):

    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(191), nullable=False)

    code: Mapped[str] = mapped_column(String(191), nullable=True)

    created_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=True)

    updated_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=True)