from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, SmallInteger, ForeignKey, TIMESTAMP, DECIMAL, Date, DateTime, func
# unit_id, unit_uso_id, tipo_und_minima → FK lógica a pos_measure_forms (PK compuesta, no se declara como FK de SQLAlchemy)
from app.database import Base


class SupplyItem(Base):
    __tablename__ = "supply_items"

    id:                 Mapped[int]           = mapped_column(Integer, primary_key=True)
    company_id:         Mapped[int]           = mapped_column(ForeignKey("companies.id_company"), nullable=False, index=True)
    id_grupo:           Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    id_item:            Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    id_insumo:          Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    code:               Mapped[Optional[str]] = mapped_column(String(50),  nullable=True, index=True)
    description:        Mapped[Optional[str]] = mapped_column(Text,        nullable=True)
    marca_referencia:   Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    unit_id:            Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    unit_uso_id:        Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    valor_und_compra:   Mapped[object]        = mapped_column(DECIMAL(14, 4), default=0)
    und_min_utilizadas: Mapped[object]        = mapped_column(DECIMAL(14, 4), default=0)
    cost_price:         Mapped[object]        = mapped_column(DECIMAL(14, 4), default=0)
    stock_qty:          Mapped[object]        = mapped_column(DECIMAL(14, 4), default=0)
    min_stock:          Mapped[object]        = mapped_column(DECIMAL(14, 4), default=0)
    waste_pct:          Mapped[object]        = mapped_column(DECIMAL(5, 2),  default=0)
    fecha_vence:        Mapped[Optional[object]] = mapped_column(Date, nullable=True)
    posicion:           Mapped[int]           = mapped_column(Integer,      default=0)
    agrupar:            Mapped[int]           = mapped_column(Integer,      default=0)
    control_stock:      Mapped[int]           = mapped_column(SmallInteger, default=0)
    compras:            Mapped[int]           = mapped_column(SmallInteger, default=0)
    opcion_cambios:     Mapped[int]           = mapped_column(SmallInteger, default=0)
    centro_produccion:  Mapped[int]           = mapped_column(SmallInteger, default=0)
    tipo_und_minima:    Mapped[int]           = mapped_column(SmallInteger, default=0)
    cant_und_minimas:   Mapped[int]           = mapped_column(SmallInteger, default=0)
    bodega:             Mapped[int]           = mapped_column(SmallInteger, default=0)
    producto_preparado: Mapped[int]           = mapped_column(SmallInteger, default=0)
    id_preparacion:     Mapped[int]           = mapped_column(Integer,      default=0)
    preparado_en_sede:  Mapped[int]           = mapped_column(SmallInteger, default=0)
    descargar_en_venta: Mapped[int]           = mapped_column(SmallInteger, default=1)
    armar_plato:        Mapped[int]           = mapped_column(SmallInteger, default=0)
    cantidad_armar:     Mapped[object]        = mapped_column(DECIMAL(14, 4), default=0)
    insumo_cp:          Mapped[int]           = mapped_column(SmallInteger, default=0)
    is_active:          Mapped[int]           = mapped_column(SmallInteger, default=1)
    synced:             Mapped[int]           = mapped_column(SmallInteger, default=0)
    created_at:         Mapped[object]        = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at:         Mapped[Optional[object]] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
