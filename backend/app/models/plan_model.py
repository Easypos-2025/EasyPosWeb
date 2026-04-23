from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Float, Boolean, Text, TIMESTAMP, func
from app.database import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Límites — -1 significa ilimitado
    max_users: Mapped[int] = mapped_column(Integer, default=1)
    max_products: Mapped[int] = mapped_column(Integer, default=-1)
    max_categories: Mapped[int] = mapped_column(Integer, default=-1)

    price: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
