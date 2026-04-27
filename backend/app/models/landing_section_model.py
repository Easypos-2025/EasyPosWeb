from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, func
from app.database import Base


class LandingSection(Base):
    __tablename__ = "landing_sections"

    id           = Column(Integer, primary_key=True, index=True)
    section_key  = Column(String(100), unique=True, nullable=False)
    title        = Column(String(300), nullable=True)
    subtitle     = Column(String(500), nullable=True)
    body_text    = Column(Text, nullable=True)
    cta_text     = Column(String(150), nullable=True)
    cta_url      = Column(String(300), nullable=True)
    image_url    = Column(String(500), nullable=True)
    is_active    = Column(Boolean, default=True)
    order_index  = Column(Integer, default=0)
    section_type = Column(String(50), default="general")
    created_at   = Column(TIMESTAMP, server_default=func.now())
    updated_at   = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
