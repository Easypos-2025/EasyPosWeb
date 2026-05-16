from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class BusinessProfileModule(Base):
    __tablename__ = "business_profile_modules"

    id = Column(Integer, primary_key=True, index=True)

    business_profile_id = Column(Integer, ForeignKey("business_profiles.id"))
    module_id = Column(Integer, ForeignKey("system_modules.id"))

    parent_id = Column(Integer, ForeignKey("business_profile_modules.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    display_name = Column(String(100), nullable=True)

    business_profile = relationship("BusinessProfile", lazy="selectin")
    module = relationship("SystemModule", lazy="selectin")