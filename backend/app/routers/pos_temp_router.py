"""
pos_temp_router.py
Endpoints para sincronización con datatemppos (pedidos activos en curso).
Distintos de pos_sync_router que opera sobre tablas históricas (pos_orders, etc.).

Convención de rutas: /api/pos/sync/push/temp-* y /api/pos/sync/pull/temp-*
"""
import os
from typing import List, Optional

from fastapi import APIRouter, Header, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi import Depends

from app.database import get_datatemppos_db

router = APIRouter(prefix="/api/pos", tags=["POS Temp Sync"])

POS_API_KEY = os.getenv("POS_API_KEY", "easypos-sync-key-2024")


def _verify(x_api_key: str = Header(...)):
    if x_api_key != POS_API_KEY:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="API Key inválida")


# ═══════════════════════════════════════════════════════════════
# PUSH — temp_comanda (cabeceras de pedidos activos)
# Destino: datatemppos.temp_comanda
# ═══════════════════════════════════════════════════════════════

class TempComandaIn(BaseModel):
    order_number:   str
    company_id:     int
    date:           str
    invoice_number: Optional[str]  = "0"
    table_name:     Optional[str]  = ""
    time:           Optional[str]  = None
    waiter_id:      Optional[int]  = 0
    cancelled:      Optional[int]  = 0
    amount:         Optional[int]  = 0
    notes:          Optional[str]  = ""
    complimentary:  Optional[int]  = 0
    guests_count:   Optional[int]  = 0
    delivery:       Optional[int]  = 0
    customer_id:    Optional[int]  = 0
    table_id:       Optional[int]  = 0


@router.post("/sync/push/temp-comanda")
async def push_temp_comanda(
    orders: List[TempComandaIn],
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_datatemppos_db),
):
    _verify(x_api_key)
    saved, failed = [], []
    for o in orders:
        key = f"{o.order_number}|{o.date}"
        try:
            await db.execute(text("""
                INSERT INTO temp_comanda
                    (company_id, Nro_Pedido, Fecha, Nro_Factura, Mesa, Hora,
                     Mesero, Cancelado, Valor, Novedad, Cortesia,
                     Nro_Comenzales, Domicilio, Id_Cliente, Movil, updated_at)
                VALUES
                    (:cid, :np, :fecha, :nf, :mesa, :hora,
                     :mesero, :cancelado, :valor, :novedad, :cortesia,
                     :comenzales, :domicilio, :id_cliente, 0, NOW())
                ON DUPLICATE KEY UPDATE
                    Nro_Factura  = VALUES(Nro_Factura),
                    Mesa         = VALUES(Mesa),
                    Cancelado    = VALUES(Cancelado),
                    Valor        = VALUES(Valor),
                    Novedad      = VALUES(Novedad),
                    Mesero       = VALUES(Mesero),
                    updated_at   = NOW()
            """), {
                "cid":        o.company_id,
                "np":         o.order_number,
                "fecha":      o.date,
                "nf":         o.invoice_number,
                "mesa":       o.table_name,
                "hora":       o.time,
                "mesero":     o.waiter_id,
                "cancelado":  o.cancelled,
                "valor":      o.amount,
                "novedad":    o.notes,
                "cortesia":   o.complimentary,
                "comenzales": o.guests_count,
                "domicilio":  o.delivery,
                "id_cliente": o.customer_id,
            })
            saved.append(key)
        except Exception as e:
            failed.append({"key": key, "error": str(e)})
    await db.commit()
    return {"saved": saved, "failed": failed,
            "total_sent": len(orders), "total_saved": len(saved), "total_failed": len(failed)}


# ═══════════════════════════════════════════════════════════════
# PUSH — temp_detalle_comanda_parcial (ítems activos por pedido)
# Estrategia: REPLACE por pedido (Variante C)
# Destino: datatemppos.temp_detalle_comanda_parcial
# ═══════════════════════════════════════════════════════════════

class _TempDetailItem(BaseModel):
    dish_id:              int
    item:                 int
    depends_on:           Optional[int]   = 0
    invoice_number:       Optional[str]   = "0"
    quantity:             Optional[float] = 0
    amount:               Optional[int]   = 0
    notes:                Optional[str]   = ""
    complimentary:        Optional[int]   = 0
    dish_discount_pct:    Optional[float] = 0
    general_discount_pct: Optional[float] = 0
    seat_number:          Optional[int]   = 0
    changes:              Optional[str]   = ""
    dish_time:            Optional[str]   = ""
    pays_tax:             Optional[int]   = 0
    tax:                  Optional[int]   = 0
    original_tax:         Optional[int]   = 0
    pays_dish:            Optional[int]   = 0
    custom_product:       Optional[str]   = ""


class TempDetailReplaceIn(BaseModel):
    company_id:   int
    order_number: str
    date:         str
    items:        List[_TempDetailItem]


@router.post("/sync/push/temp-details-replace")
async def push_temp_details_replace(
    orders: List[TempDetailReplaceIn],
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_datatemppos_db),
):
    _verify(x_api_key)
    saved, total_orders = 0, 0
    for order in orders:
        if order.order_number.startswith("WEB-"):
            continue
        try:
            await db.execute(text("""
                DELETE FROM temp_detalle_comanda_parcial
                WHERE company_id = :cid AND Nro_pedido = :np AND Fecha = :fecha
            """), {"cid": order.company_id, "np": order.order_number, "fecha": order.date})
            for it in order.items:
                await db.execute(text("""
                    INSERT INTO temp_detalle_comanda_parcial
                        (company_id, Nro_pedido, Fecha, Nro_Factura, Id_Plato, Item, Depende,
                         Cantidad, Valor, Novedad, Cortesia,
                         Porc_Descuento_Plato, Porc_Descuento_General,
                         Nro_Puesto, Cambios, Hora_Plato,
                         Paga_Impuesto, Impuesto, Impuesto_Original, Paga_Plato,
                         Producto_Personalizado, Mostrar, updated_at)
                    VALUES
                        (:cid, :np, :fecha, :nf, :dish_id, :item, :dep,
                         :qty, :amt, :notes, :comp,
                         :dsc_d, :dsc_g,
                         :seat, :changes, :dish_time,
                         :ptax, :tax, :otax, :pdish,
                         :custom, 1, NOW())
                """), {
                    "cid":      order.company_id,
                    "np":       order.order_number,
                    "fecha":    order.date,
                    "nf":       it.invoice_number,
                    "dish_id":  it.dish_id,
                    "item":     it.item,
                    "dep":      it.depends_on,
                    "qty":      it.quantity,
                    "amt":      it.amount,
                    "notes":    it.notes,
                    "comp":     it.complimentary,
                    "dsc_d":    it.dish_discount_pct,
                    "dsc_g":    it.general_discount_pct,
                    "seat":     it.seat_number,
                    "changes":  it.changes,
                    "dish_time": it.dish_time,
                    "ptax":     it.pays_tax,
                    "tax":      it.tax,
                    "otax":     it.original_tax,
                    "pdish":    it.pays_dish,
                    "custom":   it.custom_product,
                })
                saved += 1
            total_orders += 1
        except Exception:
            pass
    await db.commit()
    return {"total_orders": total_orders, "total_saved": saved}


# ═══════════════════════════════════════════════════════════════
# PUSH — temp_plato_producto_parcial (modificadores/armados)
# Estrategia: REPLACE por pedido (Variante C)
# Destino: datatemppos.temp_plato_producto_parcial
# ═══════════════════════════════════════════════════════════════

class _TempAssemblyItem(BaseModel):
    dish_id:        int
    item:           int
    group_id:       int
    item_id:        int
    invoice_number: Optional[str]   = "0"
    quantity:       Optional[float] = 0


class TempAssemblyReplaceIn(BaseModel):
    company_id:   int
    order_number: str
    date:         str
    items:        List[_TempAssemblyItem]


@router.post("/sync/push/temp-assembly-replace")
async def push_temp_assembly_replace(
    orders: List[TempAssemblyReplaceIn],
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_datatemppos_db),
):
    _verify(x_api_key)
    saved, total_orders = 0, 0
    for order in orders:
        if order.order_number.startswith("WEB-"):
            continue
        try:
            await db.execute(text("""
                DELETE FROM temp_plato_producto_parcial
                WHERE company_id = :cid AND Nro_Pedido = :np
            """), {"cid": order.company_id, "np": order.order_number})
            for it in order.items:
                await db.execute(text("""
                    INSERT INTO temp_plato_producto_parcial
                        (company_id, Nro_Pedido, Fecha, Nro_Factura,
                         Id_Plato, Item, Id_Grupo, Id_Item, Cantidad, updated_at)
                    VALUES
                        (:cid, :np, :fecha, :nf,
                         :dish_id, :item, :group_id, :item_id, :qty, NOW())
                """), {
                    "cid":      order.company_id,
                    "np":       order.order_number,
                    "fecha":    order.date,
                    "nf":       it.invoice_number,
                    "dish_id":  it.dish_id,
                    "item":     it.item,
                    "group_id": it.group_id,
                    "item_id":  it.item_id,
                    "qty":      it.quantity,
                })
                saved += 1
            total_orders += 1
        except Exception:
            pass
    await db.commit()
    return {"total_orders": total_orders, "total_saved": saved}


# ═══════════════════════════════════════════════════════════════
# PUSH — temp_novedades_plato_pedido (notas especiales por ítem)
# Estrategia: REPLACE por pedido (Variante C)
# Destino: datatemppos.temp_novedades_plato_pedido
# ═══════════════════════════════════════════════════════════════

class _TempNoteItem(BaseModel):
    consecutive_id: Optional[int] = 0
    item:           Optional[int] = 0
    depends_on:     Optional[int] = 0
    category_id:    Optional[int] = 0
    note_id:        Optional[int] = 0
    note:           Optional[str] = ""


class TempNotesReplaceIn(BaseModel):
    company_id:   int
    order_number: str
    items:        List[_TempNoteItem]


@router.post("/sync/push/temp-notes-replace")
async def push_temp_notes_replace(
    orders: List[TempNotesReplaceIn],
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_datatemppos_db),
):
    _verify(x_api_key)
    saved, total_orders = 0, 0
    for order in orders:
        if order.order_number.startswith("WEB-"):
            continue
        try:
            await db.execute(text("""
                DELETE FROM temp_novedades_plato_pedido
                WHERE company_id = :cid AND Nro_Pedido = :np
            """), {"cid": order.company_id, "np": order.order_number})
            for it in order.items:
                await db.execute(text("""
                    INSERT INTO temp_novedades_plato_pedido
                        (company_id, Id_Consecutivo, Nro_Pedido, Item,
                         Depende, Cod_Categoria, Id_Novedad, Novedad, updated_at)
                    VALUES
                        (:cid, :cons, :np, :item,
                         :dep, :cat, :note_id, :note, NOW())
                """), {
                    "cid":     order.company_id,
                    "cons":    it.consecutive_id,
                    "np":      order.order_number,
                    "item":    it.item,
                    "dep":     it.depends_on,
                    "cat":     it.category_id,
                    "note_id": it.note_id,
                    "note":    it.note,
                })
                saved += 1
            total_orders += 1
        except Exception:
            pass
    await db.commit()
    return {"total_orders": total_orders, "total_saved": saved}


# ═══════════════════════════════════════════════════════════════
# PUSH — temp_mesa_abierta (estado de mesas)
# Destino: datatemppos.temp_mesa_abierta
# ═══════════════════════════════════════════════════════════════

class TempTableStatusIn(BaseModel):
    company_id: int
    table_id:   int
    table_name: Optional[str] = ""
    is_open:    Optional[int] = 0


@router.post("/sync/push/temp-table-status")
async def push_temp_table_status(
    tables: List[TempTableStatusIn],
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_datatemppos_db),
):
    _verify(x_api_key)
    saved, failed = 0, 0
    for t in tables:
        try:
            await db.execute(text("""
                INSERT INTO temp_mesa_abierta
                    (company_id, Id_Mesa, Mesa, Abierta, Abierta_Desde, updated_at)
                VALUES
                    (:cid, :id_mesa, :mesa, :abierta,
                     CASE WHEN :abierta = 1 THEN NOW() ELSE NULL END, NOW())
                ON DUPLICATE KEY UPDATE
                    Mesa        = VALUES(Mesa),
                    Abierta     = VALUES(Abierta),
                    Abierta_Desde = CASE
                        WHEN VALUES(Abierta) = 1 AND Abierta = 0 THEN NOW()
                        WHEN VALUES(Abierta) = 0 THEN NULL
                        ELSE Abierta_Desde
                    END,
                    updated_at  = NOW()
            """), {
                "cid":     t.company_id,
                "id_mesa": t.table_id,
                "mesa":    t.table_name,
                "abierta": t.is_open,
            })
            saved += 1
        except Exception:
            failed += 1
    await db.commit()
    return {"total_sent": len(tables), "total_saved": saved, "total_failed": failed}


# ═══════════════════════════════════════════════════════════════
# PULL — lecturas desde datatemppos para web (cocina TV, dashboard)
# ═══════════════════════════════════════════════════════════════

@router.get("/sync/pull/temp-comanda")
async def pull_temp_comanda(
    company_id: int = Query(...),
    date: Optional[str] = Query(None),
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_datatemppos_db),
):
    _verify(x_api_key)
    sql = "SELECT * FROM temp_comanda WHERE company_id = :cid"
    params: dict = {"cid": company_id}
    if date:
        sql += " AND Fecha = :date"
        params["date"] = date
    sql += " ORDER BY updated_at DESC LIMIT 500"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "orders": [dict(r) for r in rows]}


@router.get("/sync/pull/temp-details")
async def pull_temp_details(
    company_id: int = Query(...),
    order_number: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_datatemppos_db),
):
    _verify(x_api_key)
    sql = "SELECT * FROM temp_detalle_comanda_parcial WHERE company_id = :cid AND Mostrar = 1"
    params: dict = {"cid": company_id}
    if order_number:
        sql += " AND Nro_pedido = :np"
        params["np"] = order_number
    if date:
        sql += " AND Fecha = :date"
        params["date"] = date
    sql += " ORDER BY Item ASC LIMIT 2000"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "details": [dict(r) for r in rows]}


@router.get("/sync/pull/temp-assembly")
async def pull_temp_assembly(
    company_id: int = Query(...),
    order_number: Optional[str] = Query(None),
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_datatemppos_db),
):
    _verify(x_api_key)
    sql = "SELECT * FROM temp_plato_producto_parcial WHERE company_id = :cid"
    params: dict = {"cid": company_id}
    if order_number:
        sql += " AND Nro_Pedido = :np"
        params["np"] = order_number
    sql += " ORDER BY Item ASC LIMIT 2000"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "assembly": [dict(r) for r in rows]}


@router.get("/sync/pull/temp-notes")
async def pull_temp_notes(
    company_id: int = Query(...),
    order_number: Optional[str] = Query(None),
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_datatemppos_db),
):
    _verify(x_api_key)
    sql = "SELECT * FROM temp_novedades_plato_pedido WHERE company_id = :cid"
    params: dict = {"cid": company_id}
    if order_number:
        sql += " AND Nro_Pedido = :np"
        params["np"] = order_number
    sql += " LIMIT 2000"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return {"total": len(rows), "notes": [dict(r) for r in rows]}


@router.get("/sync/pull/temp-table-status")
async def pull_temp_table_status(
    company_id: int = Query(...),
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_datatemppos_db),
):
    _verify(x_api_key)
    rows = (await db.execute(text("""
        SELECT Id_Mesa AS table_id, Mesa AS table_name,
               Abierta AS is_open, Abierta_Desde AS opened_since, updated_at
        FROM temp_mesa_abierta
        WHERE company_id = :cid
        ORDER BY Id_Mesa
    """), {"cid": company_id})).mappings().all()
    return {"total": len(rows), "tables": [dict(r) for r in rows]}
