from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select

from app.database import get_db, get_datatemppos_db
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.user_model import User

router = APIRouter(prefix="/api/pos/utilitarios", tags=["POS Utilitarios"])


async def _get_admin_user(authorization: str, db: AsyncSession) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido")
    result = await db.execute(
        select(UserSession).where(UserSession.token == token, UserSession.is_active == True)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=401, detail="Sesión inválida")
    uid = payload.get("user_id")
    user = await db.get(User, int(uid)) if uid else None
    if not user:
        result = await db.execute(select(User).where(User.email == payload.get("sub")))
        user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not user.company_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asignada")
    if user.role and not user.role.is_system:
        if "ADMIN" not in (user.role.name or "").upper():
            raise HTTPException(status_code=403, detail="Requiere rol ADMIN")
    return user


# ═══════════════════════════════════════════════════════════════
# POST /api/pos/utilitarios/cleanup-temp
# Elimina de temp_comanda y temp_detalle_comanda_parcial todos los
# pedidos huérfanos: cancelados, eliminados en escritorio o facturados.
# Requiere sesión activa con rol ADMIN o SYSADMIN.
# ═══════════════════════════════════════════════════════════════
@router.post("/cleanup-temp")
async def cleanup_temp(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    user = await _get_admin_user(authorization, db)
    cid = user.company_id

    orphan_subquery = """
        SELECT Nro_Pedido FROM temp_comanda
         WHERE company_id = :cid AND Cancelado = 1
        UNION
        SELECT Nro_Pedido FROM easyposweb.historico_comandas_eliminadas
         WHERE company_id = :cid
        UNION
        SELECT order_number FROM easyposweb.pos_orders
         WHERE company_id = :cid
        UNION
        SELECT order_number FROM easyposweb.pos_receipt_orders
         WHERE company_id = :cid
    """

    r_det = await db_temp.execute(text(f"""
        DELETE FROM temp_detalle_comanda_parcial
        WHERE company_id = :cid
          AND Nro_pedido IN ({orphan_subquery})
    """), {"cid": cid})

    r_cab = await db_temp.execute(text(f"""
        DELETE FROM temp_comanda
        WHERE company_id = :cid
          AND Nro_Pedido IN ({orphan_subquery})
    """), {"cid": cid})

    await db_temp.commit()

    return {
        "deleted_headers": r_cab.rowcount,
        "deleted_details": r_det.rowcount,
    }
