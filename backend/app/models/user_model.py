from sqlalchemy import String, Integer, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from app.database import Base

class User(Base):

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    company_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("companies.id_company"),
        nullable=True
    )
    is_active:        Mapped[bool]           = mapped_column(Boolean, default=True)
    plan_blocked:     Mapped[int]            = mapped_column(Integer, default=0)
    plan_blocked_at:  Mapped[Optional[object]] = mapped_column(DateTime, nullable=True)

    # =========================================
    # PERFIL / TEMA
    # =========================================
    topbar_color: Mapped[str] = mapped_column(String(20), nullable=True)
    sidebar_color: Mapped[str] = mapped_column(String(20), nullable=True)
    bg_color: Mapped[str] = mapped_column(String(20), nullable=True)
    logo: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # =========================================
    # RELATIONSHIPS
    # =========================================

    role = relationship("Role", back_populates="users", lazy="selectin")
    