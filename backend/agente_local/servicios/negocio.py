"""
Datos generales del negocio que usa la toma de pedidos.

Fecha de negocio (regla del usuario, 2026-10-07): variables_del_sistema.Fecha de la BD de la
empresa. Con ella se graban los pedidos y se arma el Nro_Pedido.

Caja (turno) abierta = variables_del_sistema.Cerrar_Dia = 0 Y variables_del_sistema.Fecha = hoy
(fecha del PC de caja donde corre el agente, no la del dispositivo). Si no, no se puede comandar:
se debe abrir el turno en el escritorio.
"""
from datetime import date, datetime

from fastapi import HTTPException
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


async def fecha_negocio(emp: AsyncSession) -> date:
    valor = (await emp.execute(text("SELECT Fecha FROM variables_del_sistema LIMIT 1"))).scalar()
    return _a_fecha(valor) or date.today()


async def fecha_turno_escritorio(tmp: AsyncSession) -> date | None:
    """Fecha que el escritorio copia a datatemppos al abrir turno: cuando cambia, se abrió un turno
    (la usa el actualizador para aplicar la versión nueva del agente)."""
    return _a_fecha((await tmp.execute(text("SELECT Fecha FROM temp_variables_del_sistema LIMIT 1"))).scalar())


async def estado_caja(emp: AsyncSession) -> dict:
    """{abierta, fecha, motivo}: motivo 'cerrada' (Cerrar_Dia = 1) o 'fecha' (Fecha distinta a hoy)."""
    fila = (await emp.execute(text("SELECT Fecha, Cerrar_Dia FROM variables_del_sistema LIMIT 1"))).mappings().first() or {}
    fecha = _a_fecha(fila.get("Fecha"))
    if int(fila.get("Cerrar_Dia") or 0) == 1:
        motivo = "cerrada"
    elif fecha != date.today():
        motivo = "fecha"
    else:
        motivo = None
    return {"abierta": motivo is None, "fecha": fecha.isoformat() if fecha else None, "motivo": motivo}


def mensaje_caja(estado: dict) -> str:
    if estado["motivo"] == "fecha":
        f = datetime.strptime(estado["fecha"], "%Y-%m-%d").strftime("%d/%m/%Y") if estado["fecha"] else "sin fecha"
        return (f"La fecha del sistema en caja ({f}) no es la de hoy. "
                "Abra el turno en el programa de escritorio para tomar pedidos.")
    return "La caja está cerrada. Abra el turno en el programa de escritorio para tomar pedidos."


async def exigir_caja_abierta(emp: AsyncSession) -> date:
    """Antes de comandar. Devuelve la fecha de negocio (la de hoy)."""
    estado = await estado_caja(emp)
    if not estado["abierta"]:
        raise HTTPException(status_code=409, detail=mensaje_caja(estado), headers={"X-Error-Code": "CAJA_CERRADA"})
    return date.fromisoformat(estado["fecha"])


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
