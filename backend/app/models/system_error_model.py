"""
Monitor de Errores (solo SYSADMIN).

- system_error_groups    → encabezado: un registro por error distinto (huella).
- system_error_details   → detalle completo SOLO de la primera ocurrencia y de cada regresión.
- system_error_companies → una fila por empresa afectada (contador), sin detalle.
"""
from sqlalchemy import (
    BigInteger, Integer, SmallInteger, String, Text, JSON, Enum, DateTime, Boolean,
    ForeignKey, UniqueConstraint, Index, func,
)
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from app.database import Base

ERROR_TYPES = (
    "SERVIDOR", "BASE_DATOS", "VISTA", "RED", "SINCRONIZACION",
    "IMPRESION", "INTEGRACION", "SEGURIDAD", "VERSION_DESACTUALIZADA",
)
ERROR_LEVELS = ("CRITICO", "ERROR", "ADVERTENCIA")
ERROR_STATES = ("NUEVO", "EN_REVISION", "RESUELTO", "IGNORADO")


class SystemErrorGroup(Base):
    __tablename__ = "system_error_groups"
    __table_args__ = (
        Index("ix_seg_estado_last", "estado", "last_seen"),
        Index("ix_seg_tipo", "tipo_error"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    ref_code: Mapped[str] = mapped_column(String(12), nullable=False, index=True)   # ERR-XXXXXXXX
    tipo_error: Mapped[str] = mapped_column(Enum(*ERROR_TYPES), nullable=False)
    nivel: Mapped[str] = mapped_column(Enum(*ERROR_LEVELS), nullable=False, default="ERROR")
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    clase_error: Mapped[Optional[str]] = mapped_column(String(150))
    endpoint: Mapped[Optional[str]] = mapped_column(String(255))
    vista: Mapped[Optional[str]] = mapped_column(String(255))
    modulo: Mapped[Optional[str]] = mapped_column(String(150))

    first_seen: Mapped[object] = mapped_column(DateTime, nullable=False, server_default=func.now())
    first_company_id: Mapped[Optional[int]] = mapped_column(Integer)
    first_user_id: Mapped[Optional[int]] = mapped_column(Integer)
    last_seen: Mapped[object] = mapped_column(DateTime, nullable=False, server_default=func.now())
    last_company_id: Mapped[Optional[int]] = mapped_column(Integer)

    total_ocurrencias: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    total_empresas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    estado: Mapped[str] = mapped_column(Enum(*ERROR_STATES), nullable=False, default="NUEVO")
    regresiones: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    resuelto_por: Mapped[Optional[int]] = mapped_column(Integer)
    resuelto_en: Mapped[Optional[object]] = mapped_column(DateTime)
    nota_solucion: Mapped[Optional[str]] = mapped_column(Text)
    version_solucion: Mapped[Optional[str]] = mapped_column(String(40))

    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class SystemErrorDetail(Base):
    __tablename__ = "system_error_details"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("system_error_groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    es_regresion: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fecha_hora: Mapped[object] = mapped_column(DateTime, nullable=False, server_default=func.now())

    company_id: Mapped[Optional[int]] = mapped_column(Integer)
    business_profile_id: Mapped[Optional[int]] = mapped_column(Integer)
    user_id: Mapped[Optional[int]] = mapped_column(Integer)
    username: Mapped[Optional[str]] = mapped_column(String(150))
    rol: Mapped[Optional[str]] = mapped_column(String(100))
    id_caja: Mapped[Optional[str]] = mapped_column(String(30))

    http_method: Mapped[Optional[str]] = mapped_column(String(10))
    path_real: Mapped[Optional[str]] = mapped_column(String(500))
    http_status: Mapped[Optional[int]] = mapped_column(SmallInteger)
    codigo_error: Mapped[Optional[str]] = mapped_column(String(60))

    mensaje: Mapped[Optional[str]] = mapped_column(Text)
    stack_trace: Mapped[Optional[str]] = mapped_column(Text)
    payload: Mapped[Optional[dict]] = mapped_column(JSON)
    query_params: Mapped[Optional[dict]] = mapped_column(JSON)

    vista_real: Mapped[Optional[str]] = mapped_column(String(500))
    componente: Mapped[Optional[str]] = mapped_column(String(200))
    toast_mostrado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    toast_mensaje: Mapped[Optional[str]] = mapped_column(String(500))

    version_cliente: Mapped[Optional[str]] = mapped_column(String(40))
    version_servidor: Mapped[Optional[str]] = mapped_column(String(40))
    dispositivo: Mapped[Optional[str]] = mapped_column(String(20))
    user_agent: Mapped[Optional[str]] = mapped_column(String(400))
    ip: Mapped[Optional[str]] = mapped_column(String(64))

    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())


class SystemErrorCompany(Base):
    __tablename__ = "system_error_companies"
    __table_args__ = (UniqueConstraint("group_id", "company_id", name="uq_sec_group_company"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("system_error_groups.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    ocurrencias: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    first_seen: Mapped[object] = mapped_column(DateTime, nullable=False, server_default=func.now())
    last_seen: Mapped[object] = mapped_column(DateTime, nullable=False, server_default=func.now())
