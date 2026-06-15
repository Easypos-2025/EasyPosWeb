"""
========================================================
COMPANY MODEL
========================================================

Modelo de base de datos para la tabla de compañías.

Las compañías representan las diferentes empresas dentro
del sistema (multiempresa).

Cada compañía incluye configuración general, ubicación,
datos de contacto y personalización visual.

Tabla: companies
"""

# =====================================================
# IMPORTS
# =====================================================

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, BigInteger, TIMESTAMP, func
from app.database import Base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

# =====================================================
# COMPANY MODEL
# =====================================================

class Company(Base):
    """
    Modelo ORM para la tabla companies.

    Cada registro representa una empresa dentro del sistema.
    """

    __tablename__ = "companies"

    # =================================================
    # COLUMNS
    # =================================================

    id_company: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    identification_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    dv: Mapped[str] = mapped_column(
        String(5),
        nullable=True
    )

    language_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("languages.id"),
        nullable=True
    )

    country_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("countries.id"),
        nullable=True
    )

    department_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("departments.id"),
        nullable=True
    )

    municipality_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("municipalities.id"),
        nullable=True
    )

    type_currency_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("type_currencies.id"),
        nullable=True
    )

    # =================================================
    # BUSINESS PROFILE (NUEVO)
    # =================================================

    business_profile_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("business_profiles.id"),
        nullable=True
    )

    business_profile = relationship("BusinessProfile", lazy="selectin")
    
    address: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )

    phone: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )

    email: Mapped[str] = mapped_column(
        String(150),
        nullable=True
    )

    description: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )

    state: Mapped[int] = mapped_column(
        Integer,
        default=1
    )

    payment_status: Mapped[str] = mapped_column(
        String(30),
        default="active",
        nullable=False,
        server_default="active"
    )

    # NULL = sin upgrade en curso | 'upgrade_pending' = esperando aprobación
    upgrade_status: Mapped[str] = mapped_column(
        String(30),
        nullable=True,
        default=None
    )

    created_at: Mapped[str] = mapped_column(
        TIMESTAMP,
        server_default=func.now()
    )

    updated_at: Mapped[str] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now()
    )

    # =================================================
    # EXTERNAL DATABASE (opcional — NULL = usa easyposweb)
    # =================================================

    ext_db_host:     Mapped[str] = mapped_column(String(150), nullable=True)
    ext_db_port:     Mapped[int] = mapped_column(Integer,     nullable=False, default=3306)
    ext_db_name:     Mapped[str] = mapped_column(String(100), nullable=True)
    ext_db_user:     Mapped[str] = mapped_column(String(100), nullable=True)
    ext_db_password: Mapped[str] = mapped_column(String(255), nullable=True)