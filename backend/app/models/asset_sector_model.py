from sqlalchemy import Column, Integer, String, SmallInteger, DateTime
from sqlalchemy.sql import func
from app.database import Base


class AssetSector(Base):
    __tablename__ = "asset_sectors"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    company_id  = Column(Integer, nullable=False)
    name        = Column(String(150), nullable=False)
    description = Column(String(255), nullable=True)
    order_index = Column(Integer, default=0)
    is_active   = Column(SmallInteger, default=1)
    created_at  = Column(DateTime, server_default=func.now())
