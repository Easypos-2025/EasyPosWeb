"""
========================================================
SYSTEM MODULE MODEL
========================================================

Define los módulos del sistema que aparecerán
en el menú lateral (Sidebar).

Ejemplos de módulos:
- Dashboard
- Assets
- Asset Categories
- Workers
- Tasks

Tabla: system_modules
"""

# =====================================================
# IMPORTS
# =====================================================

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean, ForeignKey
from app.database import Base

# =====================================================
# SYSTEM MODULE MODEL
# =====================================================

class SystemModule(Base):

    __tablename__ = "system_modules"

    # =================================================
    # COLUMNS
    # =================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    route: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    icon: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )

    parent_id: Mapped[int] = mapped_column(
        ForeignKey("system_modules.id"),
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )    

    order_index: Mapped[int] = mapped_column(
        Integer,
        default=0
        
    )

    is_sysadmin: Mapped[bool] = mapped_column(
    Boolean,
    default=False
    )    

    role_modules = relationship("RoleModule", back_populates="module")

     
    # =========================================
    # RELATIONSHIPS (JERARQUÍA)
    # =========================================

    children = relationship(
    "SystemModule",
    backref="parent",
    remote_side=[id]
    )
    
    # =========================================
    # PERMISOS
    # =========================================


