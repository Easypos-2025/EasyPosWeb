"""
CRUD de Tipificaciones de Descuento (`datatemppos.temp_tipificaciones_descuentos`).

Catálogo transversal (todos los perfiles) usado para tipificar los
descuentos que se aplican a un ítem al montar el pedido (Fase 1) y que,
al registrarse el recibo, se guardan como histórico permanente en
`easyposweb.pos_receipt_discounts.typification_id` (Fase 2).

Vive en `datatemppos` (no en `easyposweb`) porque así lo usa hoy el
software de escritorio; aquí se le agregó `company_id` para aislar cada
empresa dentro de la base compartida.
"""
from fastapi import Depends
from app.auth.tenant import tenant_guard
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_datatemppos_db
from app.auth.dependencies import get_current_user

# Aislamiento multi-tenant: valida todo company_id que envíe el navegador (CLAUDE.md §6)
router = APIRouter(prefix="/api/pos/tipificaciones-descuento", tags=["POS Tipificaciones de Descuento"], dependencies=[Depends(tenant_guard)])
def _row_out(r: dict) -> dict:
    return {
        "id": r["Id_Tipificacion"],
        "company_id": r["company_id"],
        "name": r["Nombre"],
        "discount_pesos": float(r["Valor_Descuento_Pesos"] or 0),
        "discount_percentage": int(r["Valor_Descuento_Porcentaje"] or 0),
        "ask_customer_info": bool(r["Exigir_Info_Cliente"]),
        "is_active": not bool(r["Desactivada"]),
    }


@router.get("")
async def listar(
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_datatemppos_db),
    current_user=Depends(get_current_user),
):
    rows = (await db.execute(text("""
        SELECT Id_Tipificacion, company_id, Nombre, Valor_Descuento_Pesos,
               Valor_Descuento_Porcentaje, Exigir_Info_Cliente, Desactivada
        FROM temp_tipificaciones_descuentos
        WHERE company_id = :cid
        ORDER BY Nombre
    """), {"cid": company_id})).mappings().all()
    return [_row_out(dict(r)) for r in rows]


@router.post("")
async def crear(
    body: dict,
    db: AsyncSession = Depends(get_datatemppos_db),
    current_user=Depends(get_current_user),
):
    company_id = body.get("company_id")
    name = (body.get("name") or "").strip()
    if not company_id or not name:
        raise HTTPException(status_code=422, detail="company_id y name son requeridos")

    row = (await db.execute(text(
        "SELECT COALESCE(MAX(Id_Tipificacion), -1) + 1 AS next_id "
        "FROM temp_tipificaciones_descuentos WHERE company_id = :cid"
    ), {"cid": company_id})).mappings().first()
    next_id = int(row["next_id"])

    await db.execute(text("""
        INSERT INTO temp_tipificaciones_descuentos
            (Id_Tipificacion, company_id, Nombre, Valor_Descuento_Pesos,
             Valor_Descuento_Porcentaje, Exigir_Info_Cliente, Desactivada, Enviada_MySql)
        VALUES
            (:id, :cid, :name, :pesos, :pct, :ask_cust, :inactive, 0)
    """), {
        "id": next_id, "cid": company_id, "name": name,
        "pesos": body.get("discount_pesos", 0),
        "pct": body.get("discount_percentage", 0),
        "ask_cust": int(bool(body.get("ask_customer_info", 0))),
        "inactive": int(not bool(body.get("is_active", 1))),
    })
    await db.commit()
    return {"id": next_id, "company_id": company_id, "name": name}


@router.put("/{tip_id}")
async def actualizar(
    tip_id: int,
    body: dict,
    db: AsyncSession = Depends(get_datatemppos_db),
    current_user=Depends(get_current_user),
):
    company_id = body.get("company_id")
    name = (body.get("name") or "").strip()
    if not company_id or not name:
        raise HTTPException(status_code=422, detail="company_id y name son requeridos")

    exists = (await db.execute(text(
        "SELECT Id_Tipificacion FROM temp_tipificaciones_descuentos "
        "WHERE Id_Tipificacion = :id AND company_id = :cid"
    ), {"id": tip_id, "cid": company_id})).mappings().first()
    if not exists:
        raise HTTPException(status_code=404, detail="Tipificación no encontrada")

    await db.execute(text("""
        UPDATE temp_tipificaciones_descuentos SET
            Nombre = :name,
            Valor_Descuento_Pesos = :pesos,
            Valor_Descuento_Porcentaje = :pct,
            Exigir_Info_Cliente = :ask_cust,
            Desactivada = :inactive
        WHERE Id_Tipificacion = :id AND company_id = :cid
    """), {
        "name": name,
        "pesos": body.get("discount_pesos", 0),
        "pct": body.get("discount_percentage", 0),
        "ask_cust": int(bool(body.get("ask_customer_info", 0))),
        "inactive": int(not bool(body.get("is_active", 1))),
        "id": tip_id, "cid": company_id,
    })
    await db.commit()
    return {"ok": True}


@router.patch("/{tip_id}/toggle-active")
async def toggle_activo(
    tip_id: int,
    body: dict,
    db: AsyncSession = Depends(get_datatemppos_db),
    current_user=Depends(get_current_user),
):
    company_id = body.get("company_id")
    if not company_id:
        raise HTTPException(status_code=422, detail="company_id requerido")

    row = (await db.execute(text(
        "SELECT Desactivada FROM temp_tipificaciones_descuentos "
        "WHERE Id_Tipificacion = :id AND company_id = :cid"
    ), {"id": tip_id, "cid": company_id})).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Tipificación no encontrada")

    nuevo = 0 if row["Desactivada"] else 1
    await db.execute(text(
        "UPDATE temp_tipificaciones_descuentos SET Desactivada = :v "
        "WHERE Id_Tipificacion = :id AND company_id = :cid"
    ), {"v": nuevo, "id": tip_id, "cid": company_id})
    await db.commit()
    return {"is_active": not bool(nuevo)}


@router.delete("/{tip_id}")
async def eliminar(
    tip_id: int,
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_datatemppos_db),
    current_user=Depends(get_current_user),
):
    used = (await db.execute(text("""
        SELECT COUNT(*) AS cnt FROM easyposweb.pos_receipt_discounts
        WHERE typification_id = :id AND company_id = :cid
    """), {"id": tip_id, "cid": company_id})).mappings().first()
    if used and int(used["cnt"]) > 0:
        raise HTTPException(
            status_code=409,
            detail=f"No se puede eliminar: esta tipificación tiene {used['cnt']} descuento(s) aplicado(s)",
        )

    await db.execute(text(
        "DELETE FROM temp_tipificaciones_descuentos WHERE Id_Tipificacion = :id AND company_id = :cid"
    ), {"id": tip_id, "cid": company_id})
    await db.commit()
    return {"ok": True}
