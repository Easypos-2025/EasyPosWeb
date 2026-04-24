"""
========================================================
COMPANY THEME MODEL
========================================================

Configuración visual por empresa (multiempresa)
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from sqlalchemy import Text

# 🔥 IMPORT DEL MODELO (CORRECTO)
from app.models.company_model import Company


class CompanyTheme(Base):
    __tablename__ = "company_theme"

    id = Column(Integer, primary_key=True, index=True)

    # 🔥 CORREGIDO (NOMBRE REAL DE TABLA)
    company_id = Column(Integer, ForeignKey("companies.id_company"))

    # 🎨 COLORES
    topbar_color = Column(String(20), nullable=True)
    sidebar_color = Column(String(20), nullable=True)
    bg_color = Column(String(20), nullable=True)

    # 🖼️ LOGO
    logo = Column(Text, nullable=True)
    # 🔤 TIPOGRAFÍA
    font_size  = Column(String(20), nullable=True)
    font_color = Column(String(50), nullable=True)
    # 🔥 CORREGIDO (NOMBRE DE CLASE, NO TABLA)
    company = relationship("Company", backref="theme")
    

