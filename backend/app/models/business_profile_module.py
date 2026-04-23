from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
 
class BusinessProfileModule(Base):
    __tablename__ = "business_profile_modules"

    id = Column(Integer, primary_key=True, index=True)

    business_profile_id = Column(Integer, ForeignKey("business_profiles.id"))
    module_id = Column(Integer, ForeignKey("system_modules.id"))

    parent_id = Column(Integer, ForeignKey("business_profile_modules.id"), nullable=True)
    
    sort_order = Column(Integer, default=0)

    business_profile = relationship("BusinessProfile")
    module = relationship("SystemModule")