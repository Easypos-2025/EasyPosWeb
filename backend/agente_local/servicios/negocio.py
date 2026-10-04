"""
Datos generales del negocio que usa la toma de pedidos.

Fecha de negocio: la del turno abierto en el escritorio (datatemppos.temp_variables_del_sistema),
que es la que el VB6 graba en sus pedidos. Puede diferir de la fecha del calendario y de la
guardada en la BD de la empresa.
"""
from datetime import date, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def _a_fecha(valor) -> date | None:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    for formato in ("%Y/%m/%d", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(valor or "").strip()[:10], formato).date()
        except ValueError:
            continue
    return None


async def fecha_negocio(tmp: AsyncSession) -> date:
    valor = (await tmp.execute(text("SELECT Fecha FROM temp_variables_del_sistema LIMIT 1"))).scalar()
    return _a_fecha(valor) or date.today()


async def facturacion(emp: AsyncSession) -> dict:
    fila = (await emp.execute(text("""
        SELECT Paga_Impuesto, Precios_Incluyen_Impuesto FROM configuracion_facturacion LIMIT 1
    """))).mappings().first() or {}
    return {"paga_impuesto": int(fila.get("Paga_Impuesto") or 0),
            "precios_incluyen_impuesto": int(fila.get("Precios_Incluyen_Impuesto") or 0)}


async def opciones_toma(emp: AsyncSession) -> dict:
    fila = (await emp.execute(text("""
        SELECT Pedir_Cantidad_Mod_Mesas FROM variables_del_sistema LIMIT 1
    """))).mappings().first() or {}
    return {"pedir_cantidad": int(fila.get("Pedir_Cantidad_Mod_Mesas") or 0)}
