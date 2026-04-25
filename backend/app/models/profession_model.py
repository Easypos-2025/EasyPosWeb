from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String
from app.database import Base


class Profession(Base):

    __tablename__ = "professions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    workers = relationship("Worker", back_populates="profession")
