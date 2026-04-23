from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime, timedelta
from app.database import Base

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String(255), unique=True, index=True)
    expires_at = Column(DateTime)