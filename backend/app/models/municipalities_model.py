"""
========================================================
MUNICIPALITY MODEL
========================================================
"""

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, String, TIMESTAMP, ForeignKey
from app.database import Base


class Municipality(Base):

    __tablename__ = "municipalities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    department_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("departments.id"),
        nullable=True
    )
    name: Mapped[str] = mapped_column(String(191), nullable=False)

    code: Mapped[str] = mapped_column(String(191), nullable=True)

    created_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=True)

    updated_at: Mapped[str] = mapped_column(TIMESTAMP, nullable=True)
    
    codefacturador: Mapped[BigInteger] = mapped_column(BigInteger)
    
    