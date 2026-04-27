from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP, func
from app.database import Base


class LandingContact(Base):
    __tablename__ = "landing_contacts"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(200), nullable=False)
    email      = Column(String(200), nullable=False)
    phone      = Column(String(50),  nullable=True)
    company    = Column(String(200), nullable=True)
    message    = Column(Text, nullable=False)
    is_read    = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
