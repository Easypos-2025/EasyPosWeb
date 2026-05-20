from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, UniqueConstraint
from app.database import Base


class Profession(Base):

    __tablename__ = "professions"
    __table_args__ = (UniqueConstraint("name", "company_id", name="uq_profession_name_company"),)

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    name:       Mapped[str]           = mapped_column(String(100), nullable=False)
    description:Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    workers = relationship("Worker", back_populates="profession", lazy="selectin")
