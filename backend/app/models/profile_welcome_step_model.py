from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from app.database import Base


class ProfileWelcomeStep(Base):
    __tablename__ = "profile_welcome_steps"

    id                  = Column(Integer, primary_key=True, index=True)
    business_profile_id = Column(Integer, ForeignKey("business_profiles.id"), nullable=False, index=True)
    step_number         = Column(Integer, nullable=False, default=0)
    icon                = Column(String(60),  nullable=False, default="bi-star")
    title               = Column(String(120), nullable=False)
    description         = Column(Text,        nullable=False)
    route_hint          = Column(String(150), nullable=True)
    is_active           = Column(Boolean,     default=True)
