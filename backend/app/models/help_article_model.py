from sqlalchemy import Column, Integer, String, Text, SmallInteger, DateTime
from sqlalchemy.sql import func
from app.database import Base


class HelpArticle(Base):
    __tablename__ = "help_articles"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    profile_id  = Column(Integer, nullable=True)
    category    = Column(String(100), nullable=False, default="General")
    title       = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    gif_url     = Column(String(500), nullable=True)
    keywords    = Column(String(500), nullable=True)
    order_index = Column(Integer, default=0)
    is_active   = Column(SmallInteger, default=1)
    created_at  = Column(DateTime, server_default=func.now())
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())
