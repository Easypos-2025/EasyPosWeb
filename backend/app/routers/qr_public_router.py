from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.loan_model import Loan
from app.models.bodega_item_model import BodegaItem
from app.models.external_collaborator_model import ExternalCollaborator

router = APIRouter(prefix="/qr", tags=["QRPublic"])
ESTADOS_ACTIVOS = {"pendiente_confirmacion", "activo", "retorno_pendiente"}


async def _get_loan_by_token(token: str, db: AsyncSession) -> Loan:
    result = await db.execute(select(Loan).where(Loan.qr_token == token))
    loan = result.scalar_one_or_none()
    if not loan:
        raise HTTPException(status_code=404, detail="QR no válido o expirado")
    if loan.qr_expires_at and datetime.utcnow() > loan.qr_expires_at:
        raise HTTPException(status_code=410, detail="Este QR ha expirado. Solicita uno nuevo al encargado.")
    return loan


@router.get("/prestamo/{token}")
async def qr_info(token: str, db: AsyncSession = Depends(get_db)):
    loan = await _get_loan_by_token(token, db)
    item = await db.get(BodegaItem, loan.bodega_item_id)
    collab = await db.get(ExternalCollaborator, loan.external_collaborator_id)
    accion = None
    if loan.estado == "pendiente_confirmacion":
        accion = "confirmar_recepcion"
    elif loan.estado == "retorno_pendiente":
        accion = "confirmar_devolucion"
    return {"loan_id": loan.id, "estado": loan.estado, "accion_disponible": accion,
            "articulo": item.nombre if item else "—", "articulo_codigo": item.codigo if item else None,
            "cantidad": loan.cantidad, "colaborador_nombre": collab.nombre if collab else "—",
            "colaborador_empresa": collab.empresa if collab else None,
            "fecha_retorno_esperada": loan.fecha_retorno_esperada.isoformat() if loan.fecha_retorno_esperada else None}


@router.post("/prestamo/{token}/confirmar")
async def qr_confirmar(token: str, db: AsyncSession = Depends(get_db)):
    loan = await _get_loan_by_token(token, db)
    if loan.estado == "pendiente_confirmacion":
        item = await db.get(BodegaItem, loan.bodega_item_id)
        if item:
            item.cantidad_disponible = max(0, item.cantidad_disponible - loan.cantidad)
        loan.estado = "activo"
        loan.fecha_salida_confirmada = datetime.utcnow()
        loan.qr_expires_at = datetime.utcnow() + timedelta(days=365)
        await db.commit()
        return {"message": "Recepción confirmada", "nuevo_estado": "activo"}
    elif loan.estado == "retorno_pendiente":
        loan.estado = "devuelto"
        loan.fecha_retorno_confirmada = datetime.utcnow()
        item = await db.get(BodegaItem, loan.bodega_item_id)
        if item:
            item.cantidad_disponible = min(item.cantidad_total, item.cantidad_disponible + loan.cantidad)
        await db.commit()
        return {"message": "Devolución confirmada", "nuevo_estado": "devuelto"}
    else:
        raise HTTPException(status_code=409, detail=f"Este préstamo ya fue procesado (estado: {loan.estado})")
