"""
Periodos de consulta (Día / Mes / Año) y su control por rol (Roles → Control de Acceso):

  · ver_periodos          → consultar un mes o un año completo (sin él: solo un día)
  · consultar_anteriores  → consultar fechas anteriores a hoy  (sin él: solo hoy, o el mes/año
                            en curso si tiene ver_periodos; y siempre la fecha del propio Id_Caja)
Se usa en Cuadre de Caja, Consulta de Ventas, Venta x Producto / Insumo y vistas de movimientos.
"""
import calendar
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_model import User
from app.services.permisos import permisos_usuario

_BOG = timezone(timedelta(hours=-5))
PERIODOS = ("dia", "mes", "anio")


def hoy() -> date:
    return datetime.now(_BOG).date()


def _fecha(txt: str) -> date:
    try:
        return datetime.strptime(str(txt)[:10], "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=422, detail="Fecha no válida")


def rango(periodo: str, fecha: str) -> tuple[str, str]:
    """(desde, hasta) del periodo que contiene `fecha`."""
    f = _fecha(fecha)
    if periodo == "mes":
        return f.replace(day=1).isoformat(), f.replace(day=calendar.monthrange(f.year, f.month)[1]).isoformat()
    if periodo == "anio":
        return date(f.year, 1, 1).isoformat(), date(f.year, 12, 31).isoformat()
    return f.isoformat(), f.isoformat()


async def validar_rango(db: AsyncSession, user: User, desde: str, hasta: str,
                        fecha_propia: Optional[str] = None) -> tuple[str, str]:
    """Valida el rango según los permisos del rol. Devuelve (desde, hasta) normalizados o lanza 403/422."""
    d, h = _fecha(desde), _fecha(hasta)
    if d > h:
        raise HTTPException(status_code=422, detail="La fecha inicial es mayor que la final")
    if (h - d).days > 366:
        raise HTTPException(status_code=422, detail="El rango máximo es de un año")
    permisos = await permisos_usuario(db, user)
    hoy_ = hoy()
    if d != h and "ver_periodos" not in permisos:
        raise HTTPException(status_code=403, detail="No tiene permiso para consultar por mes o año")
    if d < hoy_ and "consultar_anteriores" not in permisos:
        propio = fecha_propia and d == h == _fecha(fecha_propia)
        mes_actual = (d, h) == tuple(_fecha(x) for x in rango("mes", hoy_.isoformat()))
        anio_actual = (d, h) == tuple(_fecha(x) for x in rango("anio", hoy_.isoformat()))
        if not (propio or mes_actual or anio_actual):
            raise HTTPException(status_code=403, detail="No tiene permiso para consultar fechas anteriores")
    return d.isoformat(), h.isoformat()


async def permisos_periodo(db: AsyncSession, user: User) -> dict:
    p = await permisos_usuario(db, user)
    return {"anteriores": "consultar_anteriores" in p, "periodos": "ver_periodos" in p, "hoy": hoy().isoformat()}
