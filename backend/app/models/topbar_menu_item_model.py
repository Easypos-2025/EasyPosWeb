from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean, ForeignKey, TIMESTAMP, func
from app.database import Base


class TopbarMenuItem(Base):
    __tablename__ = "topbar_menu_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    icon: Mapped[str] = mapped_column(String(50), nullable=True, default="bi-grid")
    route: Mapped[str] = mapped_column(String(150), nullable=True)
    has_evidence: Mapped[bool] = mapped_column(Boolean, default=False)
    min_plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("plans.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
