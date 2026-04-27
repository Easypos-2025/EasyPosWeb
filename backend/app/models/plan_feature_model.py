from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base


class PlanFeature(Base):
    __tablename__ = "plan_features"

    id           = Column(Integer, primary_key=True, index=True)
    category     = Column(String(100), nullable=False)
    feature_name = Column(String(200), nullable=False)
    val_free     = Column(String(50), nullable=True)
    val_basic    = Column(String(50), nullable=True)
    val_standard = Column(String(50), nullable=True)
    val_premium  = Column(String(50), nullable=True)
    order_index  = Column(Integer, default=0)
    is_active    = Column(Boolean, default=True)
