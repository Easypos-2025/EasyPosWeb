from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey
from app.database import Base


class Worker(Base):

    __tablename__ = "workers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    profession_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("professions.id"), nullable=True
    )

    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    profession = relationship("Profession", back_populates="workers")
