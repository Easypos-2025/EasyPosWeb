"""
========================================================
ROLE MODEL
========================================================

Modelo de base de datos para la tabla de roles.

Los roles determinan los permisos y módulos a los que
puede acceder un usuario dentro del sistema.

Ejemplos de roles:
- ADMIN
- SUPERVISOR
- USER
- TECHNICIAN

Tabla: roles
"""

# =====================================================
# IMPORTS
# =====================================================

from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from sqlalchemy import Integer, String, Boolean, ForeignKey

# =====================================================
# ROLE MODEL
# =====================================================

class Role(Base):
    """
    Modelo ORM para la tabla roles.

    Cada registro representa un rol dentro del sistema.
    """

    __tablename__ = "roles"
    # =================================================
    # COLUMNS
    # =================================================
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )
    description: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"),
        nullable=False
    )

    is_system: Mapped[bool] = mapped_column(
    Boolean,
    default=False
    )    


    # =================================================
    # RELATIONSHIPS
    # =================================================

    users = relationship("User", back_populates="role")

    role_modules = relationship(
        "RoleModule",
        back_populates="role",
        cascade="all, delete-orphan"
    )
