from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.database import get_db, get_ext_session
from app.models.company_model import Company

router = APIRouter(prefix="/api/compraventa", tags=["compraventa"])


@router.get("/movimientos")
async def get_movimientos(
    company_id: int = Query(...),
    fecha: str   = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Company).where(Company.id_company == company_id))
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    if not company.ext_db_host:
        raise HTTPException(status_code=400, detail="Esta empresa no tiene base de datos externa configurada")

    ext = get_ext_session(
        company_id,
        company.ext_db_host,
        company.ext_db_port or 3306,
        company.ext_db_name,
        company.ext_db_user,
        company.ext_db_password or "",
    )

    async with ext as session:
        rows = await session.execute(text("""
            SELECT
                nro_movimiento,
                fecha_movimiento,
                nro_transaccion,
                valor_movimiento,
                descripcion
            FROM movimientos_diarios
            WHERE DATE(fecha_movimiento) = :fecha
            ORDER BY descripcion, nro_movimiento DESC
        """), {"fecha": fecha})
        records = [dict(r) for r in rows.mappings()]

    return {"fecha": fecha, "total": len(records), "movimientos": records}
