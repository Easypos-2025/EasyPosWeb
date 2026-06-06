"""
pos_temp_router.py
Endpoints para sincronización con datatemppos (pedidos activos en curso).
Distintos de pos_sync_router que opera sobre tablas históricas (pos_orders, etc.).

Convención de rutas: /api/pos/sync/push/temp-* y /api/pos/sync/pull/temp-*
"""
import json
import os
from typing import List, Optional

from fastapi import APIRouter, Header, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi import Depends

from app.database import get_datatemppos_db, get_db

router = APIRouter(prefix="/api/pos", tags=["POS Temp Sync"])

POS_API_KEY = os.getenv("POS_API_KEY", "easypos-sync-key-2024")


def _verify(x_api_key: str = Header(...)):
    if x_api_key != POS_API_KEY:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="API Key inválida")


def _norm_date(d: str) -> str:
    """VB6 envía fechas como YYYY/MM/DD — normalizar a YYYY-MM-DD para queries."""
    return d.replace("/", "-") if d else d


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
    db_main: AsyncSession = Depends(get_db),
):
    _verify(x_api_key)
    saved, failed = [], []
    cancel_events = []  # (order, fecha) pairs that transitioned to Cancelado=1

    for o in orders:
        key = f"{o.order_number}|{o.date}"
        fecha = _norm_date(o.date)
        try:
            # Detect Cancelado 0→1 transition before upsert
            existing = (await db.execute(text("""
                SELECT Cancelado FROM temp_comanda
                WHERE Nro_Pedido = :np AND company_id = :cid AND Fecha = :fecha
                LIMIT 1
            """), {"np": o.order_number, "cid": o.company_id, "fecha": fecha})).mappings().first()

            was_cancelled = int(existing["Cancelado"] or 0) if existing else -1
            is_new_cancel = (o.cancelled == 1 and was_cancelled in (0, -1))

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
                "fecha":      fecha,
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
            if is_new_cancel:
                cancel_events.append((o, fecha))
        except Exception as e:
            failed.append({"key": key, "error": str(e)})

    await db.commit()

    # Create kitchen cancel events for orders that just got cancelled
    for o, fecha in cancel_events:
        try:
            items_rows = (await db.execute(text("""
                SELECT Id_Plato, Cantidad, Novedad FROM temp_detalle_comanda_parcial
                WHERE Nro_pedido = :np AND Fecha = :fecha AND company_id = :cid
                  AND Nro_Factura = '0' AND Mostrar = 1
            """), {"np": o.order_number, "cid": o.company_id, "fecha": fecha})).mappings().all()
            snap = json.dumps([
                {"dish_id": int(r["Id_Plato"] or 0),
                 "quantity": float(r["Cantidad"] or 1),
                 "dish_name": ""}
                for r in items_rows
            ])
            await db_main.execute(text("""
                INSERT INTO pos_kitchen_events
                    (company_id, event_type, order_number, table_name,
                     waiter_id, items_snapshot, event_date, created_at)
                SELECT :cid, 'cancelado', :on, :mesa,
                       :wid, :snap, :today, NOW()
                FROM DUAL WHERE NOT EXISTS (
                    SELECT 1 FROM pos_kitchen_events
                    WHERE company_id = :cid AND order_number = :on
                      AND event_type = 'cancelado' AND event_date = :today
                )
            """), {
                "cid":   o.company_id,
                "on":    o.order_number,
                "mesa":  o.table_name or "",
                "wid":   o.waiter_id or 0,
                "snap":  snap,
                "today": fecha,
            })
            await db_main.commit()
        except Exception:
            pass

    # Limpieza proactiva — el lote VB6 es la fuente de verdad para Movil=0.
    # Si un pedido ya no llega en el lote (facturado, eliminado, cancelado,
    # o cualquier otra razón), se borra del servidor automáticamente.
    # Movil=1 (pedidos web) nunca se toca.
    batch_by_company: dict = {}
    for o in orders:
        batch_by_company.setdefault(o.company_id, []).append(o.order_number)

    for cid, batch_orders in batch_by_company.items():
        if not batch_orders:
            continue
        try:
            ph = ",".join(f":np_{i}" for i in range(len(batch_orders)))
            params: dict = {"cid": cid}
            params.update({f"np_{i}": v for i, v in enumerate(batch_orders)})

            # Primero detalles (subquery sobre alias para evitar restricción MySQL)
            await db.execute(text(f"""
                DELETE FROM temp_detalle_comanda_parcial
                WHERE company_id = :cid
                  AND Nro_pedido IN (
                      SELECT Nro_Pedido FROM (
                          SELECT Nro_Pedido FROM temp_comanda
                          WHERE company_id = :cid
                            AND Movil = 0
                            AND (Nro_Pedido NOT IN ({ph}) OR Cancelado = 1)
                      ) AS _orphans
                  )
            """), params)

            # Luego cabeceras
            await db.execute(text(f"""
                DELETE FROM temp_comanda
                WHERE company_id = :cid
                  AND Movil = 0
                  AND (Nro_Pedido NOT IN ({ph}) OR Cancelado = 1)
            """), params)

        except Exception:
            pass
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
            """), {"cid": order.company_id, "np": order.order_number, "fecha": _norm_date(order.date)})
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
                    "fecha":    _norm_date(order.date),
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

    # Recalculate temp_comanda.Valor from actual item sums so KPI shows correct totals
    for order in orders:
        if order.order_number.startswith("WEB-"):
            continue
        try:
            await db.execute(text("""
                UPDATE temp_comanda
                SET Valor = (
                    SELECT COALESCE(SUM(Valor), 0)
                    FROM temp_detalle_comanda_parcial
                    WHERE Nro_pedido = :np AND Fecha = :fecha AND company_id = :cid
                      AND Nro_Factura = '0' AND Mostrar = 1
                )
                WHERE Nro_Pedido = :np AND Fecha = :fecha AND company_id = :cid
            """), {
                "np":    order.order_number,
                "fecha": _norm_date(order.date),
                "cid":   order.company_id,
            })
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
                    "fecha":    _norm_date(order.date),
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
# Estrategia: REPLACE completo por company (Variante D)
#   VB6 envía {company_id, tables:[...]} con el estado COMPLETO actual.
#   Si tables=[] significa que no hay mesas bloqueadas → limpiar todo.
# Destino: datatemppos.temp_mesa_abierta
# ═══════════════════════════════════════════════════════════════

class _TempTableItem(BaseModel):
    table_id:   int
    table_name: Optional[str] = ""
    is_open:    Optional[int] = 1


class TempTableStatusBatchIn(BaseModel):
    company_id: int
    tables:     List[_TempTableItem]


@router.post("/sync/push/temp-table-status")
async def push_temp_table_status(
    batch: TempTableStatusBatchIn,
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_datatemppos_db),
):
    _verify(x_api_key)
    await db.execute(
        text("DELETE FROM temp_mesa_abierta WHERE company_id = :cid"),
        {"cid": batch.company_id},
    )
    saved = 0
    for t in batch.tables:
        await db.execute(text("""
            INSERT INTO temp_mesa_abierta
                (company_id, Id_Mesa, Mesa, Abierta, Abierta_Desde, updated_at)
            VALUES
                (:cid, :id_mesa, :mesa, :abierta, NOW(), NOW())
        """), {
            "cid":     batch.company_id,
            "id_mesa": t.table_id,
            "mesa":    t.table_name,
            "abierta": t.is_open,
        })
        saved += 1
    await db.commit()
    return {"total_sent": len(batch.tables), "total_saved": saved}


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


# ═══════════════════════════════════════════════════════════════
# PUSH — historico_comandas_eliminadas (trazabilidad de cancelados)
# Fuente VB6: <BD_asociado>.historico_comandas_eliminadas
# Destino:    easyposweb.historico_comandas_eliminadas
# Al recibir registros nuevos:
#   1. Upsert en tabla histórica
#   2. Crea evento TV 'cancelado' (si aún no notificado)
#   3. Limpia el pedido de datatemppos (temp_comanda + temp_detalle)
# ═══════════════════════════════════════════════════════════════

class HistoricoComandaEliminadaIn(BaseModel):
    company_id:          int
    order_number:        str
    date:                str
    invoice_number:      Optional[str]   = "0"
    table_name:          Optional[str]   = ""
    time:                Optional[str]   = ""
    waiter_id:           Optional[int]   = 0
    cancelled:           Optional[int]   = 0
    amount:              Optional[int]   = 0
    salio:               Optional[int]   = 0
    notes:               Optional[str]   = ""
    complimentary:       Optional[int]   = 0
    printed_precuenta:   Optional[int]   = 0
    guests_count:        Optional[int]   = 0
    mostrar:             Optional[int]   = 0
    seats_count:         Optional[int]   = 0
    motivo_eliminacion:  Optional[str]   = ""
    quien_elimino:       Optional[str]   = ""
    enviada_mysql:       Optional[int]   = 0
    delivery:            Optional[int]   = 0
    customer_id:         Optional[int]   = 0


@router.post("/sync/push/historico-comanda-eliminada")
async def push_historico_comanda_eliminada(
    records: List[HistoricoComandaEliminadaIn],
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_datatemppos_db),
    db_main: AsyncSession = Depends(get_db),
):
    _verify(x_api_key)
    saved, tv_fired, failed = 0, 0, 0
    errors = []

    for r in records:
        fecha = _norm_date(r.date)
        try:
            # Check if already tv_notified to avoid duplicate TV events
            existing = (await db_main.execute(text("""
                SELECT tv_notified FROM historico_comandas_eliminadas
                WHERE company_id = :cid AND Nro_Pedido = :np AND Fecha = :fecha
                LIMIT 1
            """), {"cid": r.company_id, "np": r.order_number, "fecha": fecha})).mappings().first()

            already_notified = int(existing["tv_notified"] or 0) if existing else 0

            # Upsert into permanent history table
            await db_main.execute(text("""
                INSERT INTO historico_comandas_eliminadas
                    (company_id, Nro_Pedido, Fecha, Nro_Factura, Mesa, Hora,
                     Mesero, Cancelado, Valor, Salio, Novedad,
                     Cortesia, Imprimio_Precuenta, Nro_Comenzales, Mostrar, Nro_Puestos,
                     Motivo_Eliminacion, Quien_Elimino, Enviada_MySql, Domicilio, Id_Cliente,
                     updated_at)
                VALUES
                    (:cid, :np, :fecha, :nf, :mesa, :hora,
                     :mesero, :cancelado, :valor, :salio, :novedad,
                     :cortesia, :precuenta, :comenzales, :mostrar, :puestos,
                     :motivo, :quien, :enviada, :domicilio, :id_cliente,
                     NOW())
                ON DUPLICATE KEY UPDATE
                    Quien_Elimino      = VALUES(Quien_Elimino),
                    Motivo_Eliminacion = VALUES(Motivo_Eliminacion),
                    updated_at         = NOW()
            """), {
                "cid":        r.company_id,
                "np":         r.order_number,
                "fecha":      fecha,
                "nf":         r.invoice_number,
                "mesa":       r.table_name,
                "hora":       r.time,
                "mesero":     r.waiter_id,
                "cancelado":  r.cancelled,
                "valor":      r.amount,
                "salio":      r.salio,
                "novedad":    r.notes,
                "cortesia":   r.complimentary,
                "precuenta":  r.printed_precuenta,
                "comenzales": r.guests_count,
                "mostrar":    r.mostrar,
                "puestos":    r.seats_count,
                "motivo":     r.motivo_eliminacion,
                "quien":      r.quien_elimino,
                "enviada":    r.enviada_mysql,
                "domicilio":  r.delivery,
                "id_cliente": r.customer_id,
            })
            saved += 1

            if not already_notified:
                # Get item snapshot before cleanup (solo si aún no se notificó TV)
                items_rows = (await db.execute(text("""
                    SELECT Id_Plato, Cantidad FROM temp_detalle_comanda_parcial
                    WHERE Nro_pedido = :np AND company_id = :cid
                      AND Mostrar = 1
                    LIMIT 30
                """), {"np": r.order_number, "cid": r.company_id})).mappings().all()

                snap = json.dumps([
                    {"dish_id": int(row["Id_Plato"] or 0),
                     "quantity": float(row["Cantidad"] or 1),
                     "dish_name": ""}
                    for row in items_rows
                ])

                # Create TV cancellation event
                await db_main.execute(text("""
                    INSERT INTO pos_kitchen_events
                        (company_id, event_type, order_number, table_name,
                         waiter_id, items_snapshot, event_date, created_at)
                    SELECT :cid, 'cancelado', :on, :mesa,
                           :wid, :snap, :today, NOW()
                    FROM DUAL WHERE NOT EXISTS (
                        SELECT 1 FROM pos_kitchen_events
                        WHERE company_id = :cid AND order_number = :on
                          AND event_type = 'cancelado' AND event_date = :today
                    )
                """), {
                    "cid":   r.company_id,
                    "on":    r.order_number,
                    "mesa":  r.table_name or "",
                    "wid":   r.waiter_id or 0,
                    "snap":  snap,
                    "today": fecha,
                })
                tv_fired += 1

                # Mark as notified
                await db_main.execute(text("""
                    UPDATE historico_comandas_eliminadas
                    SET tv_notified = 1
                    WHERE company_id = :cid AND Nro_Pedido = :np AND Fecha = :fecha
                """), {"cid": r.company_id, "np": r.order_number, "fecha": fecha})

            # Cleanup SIEMPRE — idempotente, evita que queden pedidos fantasma en temp_
            await db.execute(text("""
                DELETE FROM temp_detalle_comanda_parcial
                WHERE company_id = :cid AND Nro_pedido = :np
            """), {"cid": r.company_id, "np": r.order_number})
            await db.execute(text("""
                DELETE FROM temp_comanda
                WHERE company_id = :cid AND Nro_Pedido = :np
            """), {"cid": r.company_id, "np": r.order_number})

        except Exception as e:
            failed += 1
            errors.append(f"{r.order_number}: {str(e)[:120]}")

    await db_main.commit()
    await db.commit()
    return {"total_saved": saved, "total_failed": failed, "tv_fired": tv_fired, "errors": errors}


# ═══════════════════════════════════════════════════════════════
# PUSH — historico_detalle_comanda_eliminadas (items de cancelados)
# Fuente VB6: <BD_asociado>.historico_detalle_comanda_eliminadas
# Destino:    easyposweb.historico_detalle_comanda_eliminadas
# ═══════════════════════════════════════════════════════════════

class HistoricoDetalleEliminadaIn(BaseModel):
    company_id:             int
    order_number:           str
    date:                   str
    invoice_number:         Optional[str]   = "0"
    dish_id:                Optional[int]   = 0
    item:                   Optional[int]   = 0
    description:            Optional[str]   = ""
    quantity:               Optional[int]   = 0
    amount:                 Optional[int]   = 0
    min_val:                Optional[int]   = 0
    min_s:                  Optional[int]   = 0
    hora:                   Optional[str]   = ""
    salio:                  Optional[int]   = 0
    notes:                  Optional[str]   = ""
    complimentary:          Optional[int]   = 0
    dish_discount_pct:      Optional[float] = 0
    general_discount_pct:   Optional[float] = 0
    printed:                Optional[int]   = 0
    changes:                Optional[str]   = ""
    mostrar:                Optional[int]   = 0
    printer:                Optional[str]   = ""
    depends_on:             Optional[str]   = ""
    enviada_mysql:          Optional[int]   = 0
    seat_number:            Optional[int]   = 0
    category_id:            Optional[int]   = 0
    dish_time:              Optional[str]   = ""
    pays_tax:               Optional[int]   = 0
    tax:                    Optional[float] = 0
    original_tax:           Optional[float] = 0
    pays_dish:              Optional[int]   = 0
    item_original:          Optional[int]   = 0
    custom_product:         Optional[str]   = ""


@router.post("/sync/push/historico-detalle-eliminada")
async def push_historico_detalle_eliminada(
    records: List[HistoricoDetalleEliminadaIn],
    x_api_key: str = Header(...),
    db_main: AsyncSession = Depends(get_db),
):
    _verify(x_api_key)
    saved = 0

    for r in records:
        fecha = _norm_date(r.date)
        try:
            await db_main.execute(text("""
                INSERT INTO historico_detalle_comanda_eliminadas
                    (company_id, Nro_pedido, Fecha, Nro_Factura,
                     Id_Plato, Item, Descripcion, Cantidad, Valor,
                     Min, Min_S, Hora, Salio, Novedad, Cortesia,
                     Porc_Descuento_Plato, Porc_Descuento_General,
                     Impreso, Cambios, Mostrar, Impresora, Depende, Enviada_MySql,
                     Nro_Puesto, Cod_Categoria_Plato, Hora_Plato,
                     Paga_Impuesto, Impuesto, Impuesto_Original, Paga_Plato,
                     Item_Original, Producto_Personalizado, updated_at)
                VALUES
                    (:cid, :np, :fecha, :nf,
                     :dish_id, :item, :desc, :qty, :amt,
                     :min_v, :min_s, :hora, :salio, :notes, :comp,
                     :dsc_d, :dsc_g,
                     :printed, :changes, :mostrar, :printer, :dep, :enviada,
                     :seat, :cat_id, :dish_time,
                     :ptax, :tax, :otax, :pdish,
                     :item_orig, :custom, NOW())
                ON DUPLICATE KEY UPDATE
                    Cantidad    = VALUES(Cantidad),
                    Valor       = VALUES(Valor),
                    updated_at  = NOW()
            """), {
                "cid":      r.company_id,
                "np":       r.order_number,
                "fecha":    fecha,
                "nf":       r.invoice_number,
                "dish_id":  r.dish_id,
                "item":     r.item,
                "desc":     r.description,
                "qty":      r.quantity,
                "amt":      r.amount,
                "min_v":    r.min_val,
                "min_s":    r.min_s,
                "hora":     r.hora,
                "salio":    r.salio,
                "notes":    r.notes,
                "comp":     r.complimentary,
                "dsc_d":    r.dish_discount_pct,
                "dsc_g":    r.general_discount_pct,
                "printed":  r.printed,
                "changes":  r.changes,
                "mostrar":  r.mostrar,
                "printer":  r.printer,
                "dep":      r.depends_on,
                "enviada":  r.enviada_mysql,
                "seat":     r.seat_number,
                "cat_id":   r.category_id,
                "dish_time": r.dish_time,
                "ptax":     r.pays_tax,
                "tax":      r.tax,
                "otax":     r.original_tax,
                "pdish":     r.pays_dish,
                "item_orig": r.item_original,
                "custom":    r.custom_product,
            })
            saved += 1
        except Exception:
            pass

    await db_main.commit()
    return {"total_saved": saved}


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
