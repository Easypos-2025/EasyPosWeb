from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, SmallInteger, ForeignKey, TIMESTAMP, func
from app.database import Base


class Client(Base):
    __tablename__ = "clients"

    id:              Mapped[int]  = mapped_column(Integer, primary_key=True)
    company_id:      Mapped[int]  = mapped_column(ForeignKey("companies.id_company"), nullable=False, index=True)
    name:            Mapped[str]  = mapped_column(String(200), nullable=False)
    document_type:   Mapped[str]  = mapped_column(String(20),  nullable=True)   # NIT, CC, CE, Pasaporte
    document_number: Mapped[str]  = mapped_column(String(50),  nullable=True)
    email:           Mapped[str]  = mapped_column(String(150), nullable=True)
    phone:           Mapped[str]  = mapped_column(String(20),  nullable=True)
    address:         Mapped[str]  = mapped_column(Text,        nullable=True)
    is_active:       Mapped[int]  = mapped_column(SmallInteger, default=1)
    created_at:      Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now())
