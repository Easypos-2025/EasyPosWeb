"""
========================================================
ROLE MODULE MODEL
========================================================
Tabla intermedia que conecta:

ROLES
con
MÓDULOS DEL SISTEMA

Permite controlar qué rol puede ver qué módulo
en el menú lateral.

Tabla: role_modules
"""

# =====================================================
# IMPORTS
# =====================================================

from sqlalchemy import Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# =====================================================
# ROLE MODULE MODEL
# =====================================================

class RoleModule(Base):

    __tablename__ = "role_modules"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id")
    )

    module_id: Mapped[int] = mapped_column(
        ForeignKey("system_modules.id")
    )
    
    # =========================================
    # PERMISOS
    # =========================================

    can_view: Mapped[bool] = mapped_column(default=True)
    can_create: Mapped[bool] = mapped_column(default=False)
    can_edit: Mapped[bool] = mapped_column(default=False)
    can_delete: Mapped[bool] = mapped_column(default=False)

    # =========================================
    # RELATIONSHIPS
    # =========================================

    role = relationship("Role", back_populates="role_modules")
    module = relationship("SystemModule", back_populates="role_modules")



