from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from sqlalchemy import Boolean

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
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

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

    role = relationship("Role", back_populates="users")
    