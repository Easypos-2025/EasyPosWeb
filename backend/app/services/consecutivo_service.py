"""
Servicio de generación de consecutivos para Recibos y Facturas.

Reutilizable por todos los perfiles de negocio: numera contra
`consecutivo_factura_manual` (Recibo) o `consecutivo_factura_sistema`
(Factura electrónica), replicando el mismo mecanismo que usa el software
de escritorio: se reserva el consecutivo insertando Nro_Pedido + Fecha,
y el Id_Consecutivo asignado (MAX + 1 por company_id) queda como número
de Recibo/Factura definitivo.
"""
from datetime import date as date_type

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

_TABLAS = {
    "recibo": "consecutivo_factura_manual",
    "factura": "consecutivo_factura_sistema",
}

_MAX_REINTENTOS = 5


def _tabla(tipo: str) -> str:
    tabla = _TABLAS.get(tipo)
    if not tabla:
        raise ValueError(f"Tipo de consecutivo inválido: {tipo!r} (use 'recibo' o 'factura')")
    return tabla


async def previsualizar_consecutivo(db: AsyncSession, company_id: int, tipo: str = "recibo") -> int:
    """Consulta informativa (no reserva nada) del consecutivo que le tocaría al próximo registro."""
    tabla = _tabla(tipo)
    row = (await db.execute(text(
        f"SELECT COALESCE(MAX(Id_Consecutivo), 0) + 1 AS next FROM {tabla} WHERE company_id = :cid"
    ), {"cid": company_id})).mappings().first()
    return int(row["next"])


async def generar_consecutivo(
    db: AsyncSession,
    company_id: int,
    nro_pedido: str,
    fecha: date_type,
    tipo: str = "recibo",
) -> int:
    """
    Reserva (INSERT) el siguiente consecutivo para company_id y devuelve el
    Id_Consecutivo asignado. Es el número definitivo de Recibo/Factura.

    - Si Nro_Pedido ya tiene un consecutivo asignado, lanza 409 (el pedido
      debe eliminarse y reenviarse para poder reintentar).
    - La reserva se confirma (commit) de inmediato, independiente de si el
      resto del registro del recibo llega a completarse, tal como se
      comporta en escritorio.
    """
    tabla = _tabla(tipo)

    existente = (await db.execute(text(
        f"SELECT Id_Consecutivo FROM {tabla} WHERE company_id = :cid AND Nro_Pedido = :np"
    ), {"cid": company_id, "np": nro_pedido})).mappings().first()
    if existente:
        raise HTTPException(
            status_code=409,
            detail=(
                f"El pedido {nro_pedido} ya tiene un consecutivo asignado "
                f"({existente['Id_Consecutivo']}). Elimine el registro actual antes de reintentar."
            ),
        )

    for _ in range(_MAX_REINTENTOS):
        siguiente = await previsualizar_consecutivo(db, company_id, tipo)
        try:
            await db.execute(text(f"""
                INSERT INTO {tabla} (company_id, Id_Consecutivo, Nro_Pedido, Fecha, Enviada_MySql, updated_at)
                VALUES (:cid, :idc, :np, :fecha, 1, NOW())
            """), {"cid": company_id, "idc": siguiente, "np": nro_pedido, "fecha": fecha})
            await db.commit()
            return siguiente
        except IntegrityError:
            await db.rollback()
            continue

    raise HTTPException(status_code=409, detail="No se pudo generar el consecutivo, intente nuevamente")
