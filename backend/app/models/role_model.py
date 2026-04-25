"""
========================================================
ROLE MODEL
========================================================
Tabla: roles
"""

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean, ForeignKey, UniqueConstraint
from app.database import Base


class Role(Base):

    __tablename__ = "roles"

    __table_args__ = (
        UniqueConstraint("name", "company_id", name="uq_role_name_company"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(50), nullable=False)

    description: Mapped[str] = mapped_column(String(255), nullable=True)

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id_company"), nullable=False
    )

    is_system: Mapped[bool] = mapped_column(Boolean, default=False)

    users = relationship("User", back_populates="role")

    role_modules = relationship(
        "RoleModule",
        back_populates="role",
        cascade="all, delete-orphan"
    )
