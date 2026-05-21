from sqlalchemy import Column, Integer, String, Text, SmallInteger, DateTime, Enum
from sqlalchemy.sql import func
from app.database import Base


class CompanyAssetContent(Base):
    __tablename__ = "company_asset_content"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    company_id  = Column(Integer, nullable=False)
    type        = Column(Enum("requisito", "observacion"), nullable=False, default="requisito")
    content     = Column(Text, nullable=False)
    order_index = Column(Integer, default=0)
    is_active   = Column(SmallInteger, default=1)
    created_at  = Column(DateTime, server_default=func.now())
