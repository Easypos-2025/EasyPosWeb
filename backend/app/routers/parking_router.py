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

    r_ocup = await db.execute(text("""
        SELECT COUNT(*) FROM parking_orders
        WHERE company_id = :cid
          AND estado IN ('ingresado', 'registrado')
          AND DATE(hora_ingreso) = :fecha
    """), {"cid": company_id, "fecha": fecha_sql})
    ocupadas = r_ocup.scalar() or 0

    r_cfg = await db.execute(text(
        "SELECT total_plazas FROM parking_config WHERE company_id = :cid"
    ), {"cid": company_id})
    cfg_row = r_cfg.mappings().first()
    total_plazas = cfg_row["total_plazas"] if cfg_row else 0

    disponibles = max(0, total_plazas - ocupadas)
    pct = round((ocupadas / total_plazas * 100) if total_plazas > 0 else 0, 1)

    return {
        "total_plazas":  total_plazas,
        "ocupadas":      ocupadas,
        "disponibles":   disponibles,
        "pct_ocupacion": pct,
    }


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
            vt.nombre AS tipo_vehiculo,
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
        LEFT JOIN users ur         ON ur.id  = po.registrado_por
        LEFT JOIN users uc         ON uc.id  = po.confirmado_por
        LEFT JOIN users up         ON up.id  = po.pagado_por
        WHERE {where_sql}
        ORDER BY po.hora_ingreso DESC
    """), filtros)

    return [dict(r) for r in rows.mappings()]


# ── Crear orden (portero) ─────────────────────────────────────────────────────

class NuevaOrdenBody(BaseModel):
    company_id:      int
    placa:           str
    vehicle_type_id: Optional[int] = None
    adultos:         int
    ninos:           int = 0
    mascotas:        int = 0
    hora_ingreso:    str
    foto_url:        Optional[str] = None
    obs_portero:     Optional[str] = None


@router.post("/orders")
async def crear_orden(
    body: NuevaOrdenBody,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if body.adultos < 1:
        raise HTTPException(400, detail="Se requiere al menos 1 adulto")

    placa_up = body.placa.strip().upper()

    r_count = await db.execute(text("""
        SELECT COUNT(*) FROM parking_orders
        WHERE company_id = :cid AND DATE(created_at) = CURDATE()
    """), {"cid": body.company_id})
    seq = (r_count.scalar() or 0) + 1
    numero_orden = f"PS-{datetime.now().strftime('%Y%m%d')}-{seq:03d}"

    await db.execute(text("""
        INSERT INTO parking_orders
            (company_id, numero_orden, placa, vehicle_type_id, adultos, ninos, mascotas,
             hora_ingreso, foto_url, obs_portero, estado, registrado_por)
        VALUES
            (:cid, :num, :placa, :vtid, :adu, :nin, :mas,
             :hi, :foto, :obs, 'ingresado', :uid)
    """), {
        "cid": body.company_id, "num": numero_orden, "placa": placa_up,
        "vtid": body.vehicle_type_id, "adu": body.adultos,
        "nin": body.ninos, "mas": body.mascotas,
        "hi": body.hora_ingreso, "foto": body.foto_url,
        "obs": body.obs_portero, "uid": current_user.id,
    })
    await db.commit()

    row = await db.execute(text("""
        SELECT po.*, vt.nombre AS tipo_vehiculo,
               ur.nombre AS portero_nombre
        FROM parking_orders po
        LEFT JOIN vehicle_types vt ON vt.id = po.vehicle_type_id
        LEFT JOIN users ur         ON ur.id = po.registrado_por
        WHERE po.numero_orden = :num AND po.company_id = :cid
    """), {"num": numero_orden, "cid": body.company_id})
    nueva = row.mappings().first()
    return dict(nueva)


# ── Registrar (mesero confirma personas) ─────────────────────────────────────

class RegistrarBody(BaseModel):
    adultos:    int
    ninos:      int = 0
    mascotas:   int = 0
    obs_mesero: Optional[str] = None


@router.put("/orders/{order_id}/registrar")
async def registrar_orden(
    order_id: int,
    body: RegistrarBody,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if body.adultos < 1:
        raise HTTPException(400, detail="Se requiere al menos 1 adulto")

    row = await db.execute(text(
        "SELECT id, estado FROM parking_orders WHERE id = :id"
    ), {"id": order_id})
    orden = row.mappings().first()
    if not orden:
        raise HTTPException(404, detail="Orden no encontrada")
    if orden["estado"] != "ingresado":
        raise HTTPException(400, detail=f"Estado actual '{orden['estado']}' no permite esta acción")

    await db.execute(text("""
        UPDATE parking_orders
        SET adultos        = :adu,
            ninos          = :nin,
            mascotas       = :mas,
            obs_mesero     = :obs,
            estado         = 'registrado',
            confirmado_por = :uid,
            updated_at     = NOW()
        WHERE id = :id
    """), {
        "adu": body.adultos, "nin": body.ninos, "mas": body.mascotas,
        "obs": body.obs_mesero, "uid": current_user.id, "id": order_id,
    })
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

    # Guardar ítems del cobro
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
