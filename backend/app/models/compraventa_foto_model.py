from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, func
from app.database import Base


class CompraventaFoto(Base):
    __tablename__ = "compraventa_fotos"

    id:           Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id:   Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    nro_contrato: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    file_url:     Mapped[str] = mapped_column(String(500), nullable=False)
    file_name:    Mapped[str] = mapped_column(String(200), nullable=True)
    created_at:   Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
