from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.auth.dependencies import get_current_user
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/api/parking", tags=["parking"])


# ── Config ────────────────────────────────────────────────────────────────────

@router.get("/config")
async def get_config(
    company_id: int       = Query(...),
    db: AsyncSession      = Depends(get_db),
    _=Depends(get_current_user),
):
    row = await db.execute(text(
        "SELECT * FROM parking_config WHERE company_id = :cid"
    ), {"cid": company_id})
    cfg = row.mappings().first()
    if not cfg:
        return {
            "total_plazas": 20, "modo_cobro": "tarifa_unica",
            "tarifa_adulto": 0, "tarifa_nino": 0,
            "tarifa_minuto": 0, "tarifa_hora": 0,
        }
    return dict(cfg)


class ConfigUpdate(BaseModel):
    total_plazas:  int
    modo_cobro:    str = "tarifa_unica"
    tarifa_adulto: float = 0
    tarifa_nino:   float = 0
    tarifa_minuto: float = 0
    tarifa_hora:   float = 0


@router.put("/config")
async def update_config(
    company_id: int       = Query(...),
    body: ConfigUpdate    = ...,
    db: AsyncSession      = Depends(get_db),
    _=Depends(get_current_user),
):
    await db.execute(text("""
        INSERT INTO parking_config
            (company_id, total_plazas, modo_cobro, tarifa_adulto, tarifa_nino, tarifa_minuto, tarifa_hora)
        VALUES (:cid, :tp, :mc, :ta, :tn, :tm, :th)
        ON DUPLICATE KEY UPDATE
            total_plazas  = :tp,
            modo_cobro    = :mc,
            tarifa_adulto = :ta,
            tarifa_nino   = :tn,
            tarifa_minuto = :tm,
            tarifa_hora   = :th
    """), {
        "cid": company_id, "tp": body.total_plazas, "mc": body.modo_cobro,
        "ta": body.tarifa_adulto, "tn": body.tarifa_nino,
        "tm": body.tarifa_minuto, "th": body.tarifa_hora,
    })
    await db.commit()
    return {"ok": True}


# ── Stats / KPIs ──────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats(
    company_id: int  = Query(...),
    fecha: str       = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    fecha_sql = fecha or datetime.now().strftime("%Y-%m-%d")

    # Conteo por estado para el día
    r_cnt = await db.execute(text("""
        SELECT estado, COUNT(*) AS cnt
        FROM parking_orders
        WHERE company_id = :cid AND DATE(hora_ingreso) = :fecha
        GROUP BY estado
    """), {"cid": company_id, "fecha": fecha_sql})
    conteos = {row["estado"]: row["cnt"] for row in r_cnt.mappings()}

    cnt_ingresado  = conteos.get("ingresado",  0)
    cnt_registrado = conteos.get("registrado", 0)
    cnt_pagado     = conteos.get("pagado",     0)
    cnt_salido     = conteos.get("salido",     0)
    cnt_cancelado  = conteos.get("cancelado",  0)

    # Ocupadas = vehículos con presencia física (todos excepto salido y cancelado)
    ocupadas = cnt_ingresado + cnt_registrado + cnt_pagado

    r_cfg = await db.execute(text(
        "SELECT total_plazas FROM parking_config WHERE company_id = :cid"
    ), {"cid": company_id})
    cfg_row = r_cfg.mappings().first()
    total_plazas = cfg_row["total_plazas"] if cfg_row else 0

    disponibles = max(0, total_plazas - ocupadas)
    pct = round((ocupadas / total_plazas * 100) if total_plazas > 0 else 0, 1)

    # Recaudo del día (suma de subtotales de ítems de órdenes pagadas)
    r_rec = await db.execute(text("""
        SELECT COALESCE(SUM(poi.subtotal), 0) AS recaudo
        FROM parking_order_items poi
        JOIN parking_orders po ON po.id = poi.parking_order_id
        WHERE po.company_id = :cid
          AND po.estado IN ('pagado', 'salido')
          AND DATE(po.hora_ingreso) = :fecha
    """), {"cid": company_id, "fecha": fecha_sql})
    recaudo = float(r_rec.scalar() or 0)

    return {
        "total_plazas":   total_plazas,
        "ocupadas":       ocupadas,
        "disponibles":    disponibles,
        "pct_ocupacion":  pct,
        "cnt_ingresado":  cnt_ingresado,
        "cnt_registrado": cnt_registrado,
        "cnt_pagado":     cnt_pagado,
        "cnt_salido":     cnt_salido,
        "cnt_cancelado":  cnt_cancelado,
        "recaudo_hoy":    recaudo,
    }


# ── Búsqueda de vehículo por placa ───────────────────────────────────────────

@router.get("/vehicle")
async def get_vehicle(
    placa: str       = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    row = await db.execute(text(
        "SELECT placa, vehicle_type_name, foto_url FROM vehicles WHERE placa = :p"
    ), {"p": placa.strip().upper()})
    v = row.mappings().first()
    return dict(v) if v else {}


# ── Listar órdenes ────────────────────────────────────────────────────────────

@router.get("/orders")
async def listar_orders(
    company_id: int  = Query(...),
    fecha: str       = Query(None),
    estado: str      = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    fecha_sql = fecha or datetime.now().strftime("%Y-%m-%d")
    filtros = {"cid": company_id, "fecha": fecha_sql}
    where   = ["po.company_id = :cid", "DATE(po.hora_ingreso) = :fecha"]

    if estado:
        VALIDOS = {"ingresado", "registrado", "pagado", "cancelado"}
        estados = [e.strip() for e in estado.split(",") if e.strip() in VALIDOS]
        if len(estados) == 1:
            where.append("po.estado = :estado")
            filtros["estado"] = estados[0]
        elif len(estados) > 1:
            placeholders = ", ".join(f":est{i}" for i in range(len(estados)))
            where.append(f"po.estado IN ({placeholders})")
            for i, e in enumerate(estados):
                filtros[f"est{i}"] = e

    where_sql = " AND ".join(where)

    rows = await db.execute(text(f"""
        SELECT
            po.id, po.numero_orden, po.placa, po.vehicle_type_id,
            COALESCE(vt.nombre, v.vehicle_type_name) AS tipo_vehiculo,
            po.adultos, po.ninos, po.mascotas,
            po.hora_ingreso, po.hora_salida,
            po.foto_url, po.obs_portero, po.obs_mesero,
            po.estado,
            po.registrado_por, ur.nombre AS portero_nombre,
            po.confirmado_por, uc.nombre AS mesero_nombre,
            po.pagado_por,     up.nombre AS cajero_nombre,
            po.created_at
        FROM parking_orders po
        LEFT JOIN vehicle_types vt ON vt.id  = po.vehicle_type_id
        LEFT JOIN vehicles v       ON v.placa = po.placa
        LEFT JOIN users ur         ON ur.id  = po.registrado_por
        LEFT JOIN users uc         ON uc.id  = po.confirmado_por
        LEFT JOIN users up         ON up.id  = po.pagado_por
        WHERE {where_sql}
        ORDER BY po.hora_ingreso DESC
    """), filtros)

    orders = [dict(r) for r in rows.mappings()]

    # Carga los ítems de todas las órdenes en una sola query (evita N+1)
    if orders:
        ids = [o["id"] for o in orders]
        ph  = ", ".join(f":oid{i}" for i in range(len(ids)))
        items_rows = await db.execute(text(f"""
            SELECT parking_order_id, nombre, cantidad
            FROM parking_order_items
            WHERE parking_order_id IN ({ph})
            ORDER BY id
        """), {f"oid{i}": v for i, v in enumerate(ids)})
        items_map: dict = {}
        for ir in items_rows.mappings():
            oid = ir["parking_order_id"]
            items_map.setdefault(oid, []).append({"nombre": ir["nombre"], "cantidad": ir["cantidad"]})
        for o in orders:
            o["items"] = items_map.get(o["id"], [])

    return orders


# ── Crear orden (portero) ─────────────────────────────────────────────────────

class ItemIngreso(BaseModel):
    product_id: Optional[int] = None
    nombre:     str
    cantidad:   int = 1

class NuevaOrdenBody(BaseModel):
    company_id:        int
    placa:             str
    vehicle_type_name: Optional[str] = None
    foto_url:          Optional[str] = None
    items:             List[ItemIngreso] = []
    obs_portero:       Optional[str] = None


@router.post("/orders")
async def crear_orden(
    body: NuevaOrdenBody,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not body.items:
        raise HTTPException(400, detail="Selecciona al menos un servicio")

    placa_up  = body.placa.strip().upper()
    total_qty = sum(i.cantidad for i in body.items)

    # UPSERT vehicle (1 foto por placa, global)
    await db.execute(text("""
        INSERT INTO vehicles (placa, vehicle_type_name, foto_url)
        VALUES (:p, :vtn, :foto)
        ON DUPLICATE KEY UPDATE
            vehicle_type_name = COALESCE(:vtn, vehicle_type_name),
            foto_url          = COALESCE(:foto, foto_url),
            updated_at        = NOW()
    """), {"p": placa_up, "vtn": body.vehicle_type_name, "foto": body.foto_url})

    r_count = await db.execute(text("""
        SELECT COUNT(*) FROM parking_orders
        WHERE company_id = :cid AND DATE(created_at) = CURDATE()
    """), {"cid": body.company_id})
    seq = (r_count.scalar() or 0) + 1
    numero_orden = f"PS-{datetime.now().strftime('%Y%m%d')}-{seq:03d}"

    result = await db.execute(text("""
        INSERT INTO parking_orders
            (company_id, numero_orden, placa, vehicle_type_id, adultos, ninos, mascotas,
             hora_ingreso, foto_url, obs_portero, estado, registrado_por)
        VALUES
            (:cid, :num, :placa, NULL, :adu, 0, 0,
             NOW(), :foto, :obs, 'ingresado', :uid)
    """), {
        "cid": body.company_id, "num": numero_orden, "placa": placa_up,
        "adu": total_qty, "foto": body.foto_url,
        "obs": body.obs_portero, "uid": current_user.id,
    })
    new_id = result.lastrowid

    for item in body.items:
        await db.execute(text("""
            INSERT INTO parking_order_items
                (parking_order_id, product_id, nombre, precio_unitario, impuesto_pct, cantidad, subtotal)
            VALUES (:oid, :pid, :nom, 0, 0, :qty, 0)
        """), {
            "oid": new_id, "pid": item.product_id, "nom": item.nombre, "qty": item.cantidad,
        })

    await db.commit()

    row = await db.execute(text("""
        SELECT po.*, COALESCE(vt.nombre, v.vehicle_type_name) AS tipo_vehiculo,
               ur.nombre AS portero_nombre
        FROM parking_orders po
        LEFT JOIN vehicle_types vt ON vt.id  = po.vehicle_type_id
        LEFT JOIN vehicles v       ON v.placa = po.placa
        LEFT JOIN users ur         ON ur.id   = po.registrado_por
        WHERE po.id = :id
    """), {"id": new_id})
    nueva = row.mappings().first()
    return dict(nueva)


# ── Registrar (mesero confirma ingreso) ──────────────────────────────────────

class RegistrarBody(BaseModel):
    obs_mesero: Optional[str] = None
    items:      Optional[List[ItemIngreso]] = None


@router.put("/orders/{order_id}/registrar")
async def registrar_orden(
    order_id: int,
    body: RegistrarBody,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = await db.execute(text(
        "SELECT id, estado FROM parking_orders WHERE id = :id"
    ), {"id": order_id})
    orden = row.mappings().first()
    if not orden:
        raise HTTPException(404, detail="Orden no encontrada")
    if orden["estado"] not in ("ingresado", "registrado"):
        raise HTTPException(400, detail=f"Estado '{orden['estado']}' no permite esta acción")

    if orden["estado"] == "ingresado":
        await db.execute(text("""
            UPDATE parking_orders
            SET obs_mesero     = :obs,
                estado         = 'registrado',
                confirmado_por = :uid,
                updated_at     = NOW()
            WHERE id = :id
        """), {"obs": body.obs_mesero, "uid": current_user.id, "id": order_id})
    else:
        # Ya está confirmado: solo actualiza obs sin cambiar estado
        await db.execute(text("""
            UPDATE parking_orders
            SET obs_mesero = :obs, updated_at = NOW()
            WHERE id = :id
        """), {"obs": body.obs_mesero, "id": order_id})

    if body.items is not None:
        await db.execute(text(
            "DELETE FROM parking_order_items WHERE parking_order_id = :oid"
        ), {"oid": order_id})
        total_qty = sum(i.cantidad for i in body.items)
        for item in body.items:
            await db.execute(text("""
                INSERT INTO parking_order_items
                    (parking_order_id, product_id, nombre, precio_unitario, impuesto_pct, cantidad, subtotal)
                VALUES (:oid, :pid, :nom, 0, 0, :qty, 0)
            """), {"oid": order_id, "pid": item.product_id, "nom": item.nombre, "qty": item.cantidad})
        await db.execute(text(
            "UPDATE parking_orders SET adultos = :qty WHERE id = :id"
        ), {"qty": total_qty, "id": order_id})

    await db.commit()
    return {"ok": True, "estado": "registrado"}


# ── Pagar (cajero cierra la orden con detalle de ítems) ──────────────────────

class ItemCobro(BaseModel):
    product_id:      Optional[int] = None
    nombre:          str
    precio_unitario: float
    impuesto_pct:    float = 0
    cantidad:        int   = 1
    subtotal:        float

class PagarBody(BaseModel):
    items: List[ItemCobro] = []


@router.put("/orders/{order_id}/pagar")
async def pagar_orden(
    order_id: int,
    body: PagarBody,
    db: AsyncSession      = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = await db.execute(text(
        "SELECT id, estado FROM parking_orders WHERE id = :id"
    ), {"id": order_id})
    orden = row.mappings().first()
    if not orden:
        raise HTTPException(404, detail="Orden no encontrada")
    if orden["estado"] != "registrado":
        raise HTTPException(
            400,
            detail=f"Solo se pueden pagar órdenes en estado 'registrado'. Estado actual: '{orden['estado']}'"
        )

    # Reemplaza ítems existentes (los del portero/mesero con precio=0) con los del cobro
    await db.execute(text(
        "DELETE FROM parking_order_items WHERE parking_order_id = :oid"
    ), {"oid": order_id})

    for item in body.items:
        await db.execute(text("""
            INSERT INTO parking_order_items
                (parking_order_id, product_id, nombre, precio_unitario, impuesto_pct, cantidad, subtotal)
            VALUES (:oid, :pid, :nom, :pu, :imp, :qty, :sub)
        """), {
            "oid": order_id,
            "pid": item.product_id,
            "nom": item.nombre,
            "pu":  item.precio_unitario,
            "imp": item.impuesto_pct,
            "qty": item.cantidad,
            "sub": item.subtotal,
        })

    await db.execute(text("""
        UPDATE parking_orders
        SET estado      = 'pagado',
            hora_salida = NOW(),
            pagado_por  = :uid,
            updated_at  = NOW()
        WHERE id = :id
    """), {"uid": current_user.id, "id": order_id})
    await db.commit()
    return {"ok": True, "estado": "pagado"}


# ── Marcar salida física (portero confirma que el vehículo salió) ────────────

@router.put("/orders/{order_id}/salida")
async def marcar_salida(
    order_id: int,
    db: AsyncSession      = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = await db.execute(text(
        "SELECT id, estado FROM parking_orders WHERE id = :id"
    ), {"id": order_id})
    orden = row.mappings().first()
    if not orden:
        raise HTTPException(404, detail="Orden no encontrada")
    if orden["estado"] != "pagado":
        raise HTTPException(400, detail=f"Solo se puede marcar salida de órdenes pagadas. Estado actual: '{orden['estado']}'")

    await db.execute(text("""
        UPDATE parking_orders
        SET estado     = 'salido',
            updated_at = NOW()
        WHERE id = :id
    """), {"id": order_id})
    await db.commit()
    return {"ok": True, "estado": "salido"}


# ── Ítems de una orden (detalle del cobro) ────────────────────────────────────

@router.get("/orders/{order_id}/items")
async def get_order_items(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    rows = await db.execute(text("""
        SELECT poi.id, poi.product_id, poi.nombre, poi.precio_unitario,
               poi.impuesto_pct, poi.cantidad, poi.subtotal
        FROM parking_order_items poi
        WHERE poi.parking_order_id = :oid
        ORDER BY poi.id
    """), {"oid": order_id})
    return [dict(r) for r in rows.mappings()]


# ── Productos activos de la empresa (catálogo para cobrar) ────────────────────

@router.get("/products")
async def listar_productos(
    company_id: int  = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    rows = await db.execute(text("""
        SELECT id, name, base_price, tax_rate
        FROM products
        WHERE company_id = :cid AND is_active = 1
        ORDER BY name
    """), {"cid": company_id})
    return [dict(r) for r in rows.mappings()]


# ── Tipos de vehículo (reutiliza vehicle_types) ───────────────────────────────

@router.get("/vehicle-types")
async def get_vehicle_types(
    company_id: int  = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    rows = await db.execute(text("""
        SELECT id, nombre, icono FROM vehicle_types
        WHERE company_id = :cid AND activo = 1
        ORDER BY orden, nombre
    """), {"cid": company_id})
    return [dict(r) for r in rows.mappings()]
