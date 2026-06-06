from fastapi import APIRouter, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select

from app.database import get_db, get_datatemppos_db
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.user_model import User

router = APIRouter(prefix="/api/pos/utilitarios", tags=["POS Utilitarios"])

# Tablas temp_ involucradas en la limpieza (orden: detalles primero, cabecera al final)
TEMP_TABLES = [
    {"name": "temp_detalle_comanda_parcial", "col": "Nro_pedido",  "label": "Detalle ítems"},
    {"name": "temp_plato_producto_parcial",  "col": "Nro_Pedido",  "label": "Platos / Productos"},
    {"name": "temp_novedades_plato_pedido",  "col": "Nro_Pedido",  "label": "Novedades de plato"},
    {"name": "temp_comanda",                 "col": "Nro_Pedido",  "label": "Cabeceras de pedido"},
]

ORPHAN_SUBQUERY = """
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
# GET /api/pos/utilitarios/temp-status
# Retorna el conteo actual de registros por tabla temp_ para la empresa.
# ═══════════════════════════════════════════════════════════════
@router.get("/temp-status")
async def temp_status(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    user = await _get_admin_user(authorization, db)
    cid = user.company_id

    tables = []
    for t in TEMP_TABLES:
        row = (await db_temp.execute(
            text(f"SELECT COUNT(*) AS cnt FROM {t['name']} WHERE company_id = :cid"),
            {"cid": cid}
        )).mappings().first()
        tables.append({
            "name":    t["name"],
            "label":   t["label"],
            "records": int(row["cnt"] or 0),
        })
    return {"tables": tables}


# ═══════════════════════════════════════════════════════════════
# POST /api/pos/utilitarios/cleanup-temp
# Elimina pedidos huérfanos de todas las tablas temp_.
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

    result_tables = []
    for t in TEMP_TABLES:
        if t["name"] == "temp_comanda":
            r = await db_temp.execute(text(f"""
                DELETE FROM temp_comanda
                WHERE company_id = :cid
                  AND Nro_Pedido IN ({ORPHAN_SUBQUERY})
            """), {"cid": cid})
        else:
            r = await db_temp.execute(text(f"""
                DELETE FROM {t['name']}
                WHERE company_id = :cid
                  AND {t['col']} IN ({ORPHAN_SUBQUERY})
            """), {"cid": cid})
        result_tables.append({
            "name":    t["name"],
            "label":   t["label"],
            "deleted": r.rowcount,
        })

    await db_temp.commit()

    total_headers = next((x["deleted"] for x in result_tables if x["name"] == "temp_comanda"), 0)
    total_details = sum(x["deleted"] for x in result_tables if x["name"] != "temp_comanda")

    return {
        "deleted_headers": total_headers,
        "deleted_details": total_details,
        "tables": result_tables,
    }
