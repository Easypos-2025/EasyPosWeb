from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/talleres", tags=["talleres"])


# ── KPI Dashboard ─────────────────────────────────────────────────────────────

@router.get("/kpi")
async def get_kpi(
    company_id: int  = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    try:
        r1 = await db.execute(text("""
            SELECT COUNT(*) FROM service_orders
            WHERE company_id = :cid AND estado = 'abierta'
              AND DATE(fecha_ingreso) = CURDATE()
        """), {"cid": company_id})
        ordenes_hoy = r1.scalar() or 0

        r2 = await db.execute(text("""
            SELECT COUNT(*) FROM service_orders
            WHERE company_id = :cid AND estado = 'en_proceso'
        """), {"cid": company_id})
        en_proceso = r2.scalar() or 0

        r3 = await db.execute(text("""
            SELECT COUNT(*) FROM service_orders
            WHERE company_id = :cid AND estado = 'terminada'
        """), {"cid": company_id})
        listos = r3.scalar() or 0

        r4 = await db.execute(text("""
            SELECT COUNT(*) FROM service_orders
            WHERE company_id = :cid AND estado_facturacion = 'convenio_pendiente'
        """), {"cid": company_id})
        convenios = r4.scalar() or 0

        r5 = await db.execute(text("""
            SELECT COUNT(*) FROM products
            WHERE company_id = :cid AND is_active = 1 AND min_stock > 0
              AND id NOT IN (
                SELECT DISTINCT id_item FROM inventory_entries
                WHERE company_id = :cid AND cantidad > 0
              )
        """), {"cid": company_id})
        bajo_stock = r5.scalar() or 0

    except Exception:
        ordenes_hoy = en_proceso = listos = convenios = bajo_stock = 0

    return {
        "ordenes_hoy":          ordenes_hoy,
        "en_proceso":           en_proceso,
        "listos_entrega":       listos,
        "convenios_pendientes": convenios,
        "bajo_stock":           bajo_stock,
    }


# ── Buscar vehículo por placa ─────────────────────────────────────────────────

@router.get("/vehiculo")
async def buscar_vehiculo(
    company_id: int  = Query(...),
    placa: str       = Query(..., min_length=3),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Busca un vehículo registrado por placa. Retorna datos + historial de órdenes."""
    placa_up = placa.strip().upper()

    row = await db.execute(text("""
        SELECT
            a.id            AS asset_id,
            a.name          AS nombre_vehiculo,
            a.client_id,
            c.name          AS cliente_nombre,
            c.phone         AS cliente_telefono,
            c.document_number AS cliente_documento,
            v.placa, v.tipo, v.marca, v.modelo, v.anio, v.color, v.km_actual
        FROM talleres_vehiculo_ext v
        JOIN assets a ON a.id = v.asset_id
        LEFT JOIN clients c ON c.id = a.client_id
        WHERE v.company_id = :cid AND v.placa = :placa
        LIMIT 1
    """), {"cid": company_id, "placa": placa_up})
    vehiculo = row.mappings().first()

    historial = []
    if vehiculo:
        hist = await db.execute(text("""
            SELECT
                so.id, so.numero_orden, so.fecha_ingreso,
                so.estado, so.estado_facturacion,
                so.km_ingreso, so.trabajo_realizado,
                so.diagnostico,
                u.full_name AS jefe_nombre,
                (SELECT SUM(d.subtotal) FROM service_order_details d
                 WHERE d.order_id = so.id) AS total_orden
            FROM service_orders so
            LEFT JOIN users u ON u.id = so.jefe_responsable_id
            WHERE so.company_id = :cid AND so.placa_vehiculo = :placa
            ORDER BY so.fecha_ingreso DESC
            LIMIT 30
        """), {"cid": company_id, "placa": placa_up})
        historial = [dict(r) for r in hist.mappings()]

    return {
        "encontrado": vehiculo is not None,
        "vehiculo":   dict(vehiculo) if vehiculo else None,
        "historial":  historial,
    }


# ── Listar órdenes de servicio ────────────────────────────────────────────────

@router.get("/ordenes")
async def listar_ordenes(
    company_id: int       = Query(...),
    estado: str           = Query(None),
    fecha_desde: str      = Query(None),
    fecha_hasta: str      = Query(None),
    placa: str            = Query(None),
    page: int             = Query(1, ge=1),
    page_size: int        = Query(20, ge=1, le=100),
    db: AsyncSession      = Depends(get_db),
    _=Depends(get_current_user),
):
    filtros = {"cid": company_id}
    where   = ["so.company_id = :cid"]

    if estado:
        where.append("so.estado = :estado")
        filtros["estado"] = estado
    if fecha_desde:
        where.append("DATE(so.fecha_ingreso) >= :fd")
        filtros["fd"] = fecha_desde
    if fecha_hasta:
        where.append("DATE(so.fecha_ingreso) <= :fh")
        filtros["fh"] = fecha_hasta
    if placa:
        where.append("so.placa_vehiculo LIKE :placa")
        filtros["placa"] = f"%{placa.upper()}%"

    where_sql = " AND ".join(where)
    offset    = (page - 1) * page_size

    total_r = await db.execute(text(f"""
        SELECT COUNT(*) FROM service_orders so WHERE {where_sql}
    """), filtros)
    total = total_r.scalar() or 0

    rows = await db.execute(text(f"""
        SELECT
            so.id, so.numero_orden, so.placa_vehiculo,
            so.fecha_ingreso, so.promesa_entrega, so.estado,
            so.estado_facturacion, so.km_ingreso,
            c.name  AS cliente_nombre,
            c.phone AS cliente_telefono,
            u.full_name AS jefe_nombre,
            uc.full_name AS creado_por,
            (SELECT SUM(d.subtotal) FROM service_order_details d
             WHERE d.order_id = so.id) AS total_orden,
            (SELECT COUNT(*) FROM service_order_details d
             WHERE d.order_id = so.id) AS cant_items,
            cv.nombre_empresa AS convenio_nombre
        FROM service_orders so
        LEFT JOIN clients c       ON c.id  = so.client_id
        LEFT JOIN users u         ON u.id  = so.jefe_responsable_id
        LEFT JOIN users uc        ON uc.id = so.created_by
        LEFT JOIN service_convenios cv ON cv.id = so.convenio_id
        WHERE {where_sql}
        ORDER BY so.fecha_ingreso DESC
        LIMIT :lim OFFSET :off
    """), {**filtros, "lim": page_size, "off": offset})

    return {
        "total": total,
        "page":  page,
        "items": [dict(r) for r in rows.mappings()],
    }


# ── Crear orden de servicio ───────────────────────────────────────────────────

@router.post("/ordenes")
async def crear_orden(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = payload.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="company_id requerido")

    placa = (payload.get("placa_vehiculo") or "").strip().upper()
    if not placa:
        raise HTTPException(status_code=400, detail="La placa del vehículo es requerida")

    # Generar número de orden correlativo por empresa
    r = await db.execute(text("""
        SELECT COUNT(*) FROM service_orders WHERE company_id = :cid
    """), {"cid": company_id})
    correlativo = (r.scalar() or 0) + 1
    numero_orden = f"OS-{company_id:04d}-{correlativo:05d}"

    await db.execute(text("""
        INSERT INTO service_orders (
            company_id, created_by, numero_orden,
            vehicle_id, placa_vehiculo, client_id, convenio_id,
            km_ingreso, fecha_ingreso, jefe_responsable_id,
            estado, estado_facturacion, diagnostico
        ) VALUES (
            :cid, :uid, :num,
            :vid, :placa, :clt, :conv,
            :km, COALESCE(:fi, NOW()), :jefe,
            'abierta',
            CASE WHEN :conv IS NOT NULL THEN 'convenio_pendiente' ELSE 'particular' END,
            :diag
        )
    """), {
        "cid":  company_id,
        "uid":  current_user.id,
        "num":  numero_orden,
        "vid":  payload.get("vehicle_id"),
        "placa": placa,
        "clt":  payload.get("client_id"),
        "conv": payload.get("convenio_id"),
        "km":   payload.get("km_ingreso"),
        "fi":   payload.get("fecha_ingreso"),
        "jefe": payload.get("jefe_responsable_id"),
        "diag": payload.get("diagnostico"),
    })
    await db.commit()

    r2 = await db.execute(text(
        "SELECT id FROM service_orders WHERE company_id=:cid AND numero_orden=:num"
    ), {"cid": company_id, "num": numero_orden})
    new_id = r2.scalar()

    # Registrar operarios asignados
    for w in (payload.get("workers") or []):
        await db.execute(text("""
            INSERT IGNORE INTO service_order_workers (order_id, worker_id, rol_en_orden)
            VALUES (:oid, :wid, :rol)
        """), {"oid": new_id, "wid": w["worker_id"], "rol": w.get("rol", "")})
    await db.commit()

    return {"id": new_id, "numero_orden": numero_orden}


# ── Detalle de una orden ──────────────────────────────────────────────────────

@router.get("/ordenes/{orden_id}")
async def get_orden(
    orden_id: int,
    company_id: int  = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    row = await db.execute(text("""
        SELECT
            so.*,
            c.name  AS cliente_nombre, c.phone AS cliente_telefono,
            c.document_number AS cliente_documento,
            u.full_name  AS jefe_nombre,
            uc.full_name AS creado_por_nombre,
            cv.nombre_empresa AS convenio_nombre,
            v.marca, v.modelo, v.anio, v.color, v.tipo AS tipo_vehiculo
        FROM service_orders so
        LEFT JOIN clients c            ON c.id  = so.client_id
        LEFT JOIN users u              ON u.id  = so.jefe_responsable_id
        LEFT JOIN users uc             ON uc.id = so.created_by
        LEFT JOIN service_convenios cv ON cv.id = so.convenio_id
        LEFT JOIN talleres_vehiculo_ext v ON v.asset_id = so.vehicle_id
        WHERE so.id = :oid AND so.company_id = :cid
    """), {"oid": orden_id, "cid": company_id})
    orden = row.mappings().first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    det = await db.execute(text("""
        SELECT
            d.*,
            w.name AS operario_nombre,
            p.name AS profession_nombre,
            mu.full_name AS modificado_por_nombre
        FROM service_order_details d
        LEFT JOIN workers w    ON w.id = d.worker_id
        LEFT JOIN professions p ON p.id = d.profession_id
        LEFT JOIN users mu     ON mu.id = d.modified_by
        WHERE d.order_id = :oid
        ORDER BY d.id
    """), {"oid": orden_id})

    wks = await db.execute(text("""
        SELECT sow.*, w.name AS worker_nombre, pr.name AS profession_nombre
        FROM service_order_workers sow
        JOIN workers w     ON w.id  = sow.worker_id
        LEFT JOIN professions pr ON pr.id = w.profession_id
        WHERE sow.order_id = :oid
    """), {"oid": orden_id})

    return {
        "orden":    dict(orden),
        "detalles": [dict(r) for r in det.mappings()],
        "workers":  [dict(r) for r in wks.mappings()],
    }


# ── Agregar línea de detalle a la orden ──────────────────────────────────────

@router.post("/ordenes/{orden_id}/detalle")
async def agregar_detalle(
    orden_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    cantidad  = float(payload.get("cantidad", 1))
    precio    = float(payload.get("precio_unitario", 0))
    descuento = float(payload.get("descuento", 0))
    subtotal  = round((precio * cantidad) - descuento, 2)

    # Calcular mano de obra del operario según % del rol
    mano_obra = 0.0
    profession_id = payload.get("profession_id")
    if profession_id:
        rp = await db.execute(text("""
            SELECT pct_operario FROM profession_payment_config
            WHERE profession_id = :pid
        """), {"pid": profession_id})
        cfg = rp.mappings().first()
        if cfg:
            mano_obra = round(subtotal * float(cfg["pct_operario"]) / 100, 2)

    await db.execute(text("""
        INSERT INTO service_order_details (
            order_id, tipo_item, product_id, nombre,
            worker_id, modified_by, cantidad,
            precio_unitario, descuento, subtotal,
            mano_obra_operario, profession_id, combo_id
        ) VALUES (
            :oid, :tipo, :pid, :nom,
            :wid, :uid, :qty,
            :pu, :desc, :sub,
            :mo, :prof, :combo
        )
    """), {
        "oid":   orden_id,
        "tipo":  payload.get("tipo_item", "mecanica"),
        "pid":   payload.get("product_id"),
        "nom":   payload.get("nombre", ""),
        "wid":   payload.get("worker_id"),
        "uid":   current_user.id,
        "qty":   cantidad,
        "pu":    precio,
        "desc":  descuento,
        "sub":   subtotal,
        "mo":    mano_obra,
        "prof":  profession_id,
        "combo": payload.get("combo_id"),
    })
    await db.commit()
    return {"ok": True, "subtotal": subtotal, "mano_obra_operario": mano_obra}


# ── Cambiar estado de la orden ────────────────────────────────────────────────

@router.patch("/ordenes/{orden_id}/estado")
async def cambiar_estado(
    orden_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    nuevo = payload.get("estado")
    estados_validos = ("abierta", "en_proceso", "terminada", "entregada", "cancelada")
    if nuevo not in estados_validos:
        raise HTTPException(status_code=400, detail="Estado inválido")

    extra_set = ""
    extra_vals: dict = {}
    if nuevo == "entregada":
        extra_set = ", fecha_entrega_real = NOW()"
    if payload.get("trabajo_realizado"):
        extra_set += ", trabajo_realizado = :tr"
        extra_vals["tr"] = payload["trabajo_realizado"]
    if payload.get("km_salida"):
        extra_set += ", km_salida = :km_s"
        extra_vals["km_s"] = payload["km_salida"]

    await db.execute(text(f"""
        UPDATE service_orders
        SET estado = :est, updated_at = NOW(){extra_set}
        WHERE id = :oid
    """), {"est": nuevo, "oid": orden_id, **extra_vals})
    await db.commit()
    return {"ok": True}


# ── Convenios de la empresa ───────────────────────────────────────────────────

@router.get("/convenios")
async def listar_convenios(
    company_id: int  = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    rows = await db.execute(text("""
        SELECT
            sc.*,
            (SELECT COUNT(*) FROM service_orders so
             WHERE so.convenio_id = sc.id
               AND so.estado_facturacion = 'convenio_pendiente') AS ordenes_pendientes,
            (SELECT COALESCE(SUM(
                (SELECT SUM(d.subtotal) FROM service_order_details d WHERE d.order_id = so2.id)
             ), 0)
             FROM service_orders so2
             WHERE so2.convenio_id = sc.id
               AND so2.estado_facturacion = 'convenio_pendiente') AS saldo_pendiente
        FROM service_convenios sc
        WHERE sc.company_id = :cid AND sc.activo = 1
        ORDER BY sc.nombre_empresa
    """), {"cid": company_id})
    return [dict(r) for r in rows.mappings()]


# ── Registrar / actualizar vehículo ──────────────────────────────────────────

@router.post("/vehiculo")
async def registrar_vehiculo(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Crea el asset y la extensión del vehículo."""
    company_id = payload.get("company_id")
    placa = (payload.get("placa") or "").strip().upper()
    if not company_id or not placa:
        raise HTTPException(status_code=400, detail="company_id y placa son requeridos")

    # Evitar duplicados
    existe = await db.execute(text(
        "SELECT id FROM talleres_vehiculo_ext WHERE company_id=:cid AND placa=:p"
    ), {"cid": company_id, "p": placa})
    if existe.scalar():
        raise HTTPException(status_code=409, detail="Ya existe un vehículo con esa placa")

    # Crear asset base
    await db.execute(text("""
        INSERT INTO assets (company_id, name, category_id, client_id, is_active)
        VALUES (:cid, :name, :cat, :cli, 1)
    """), {
        "cid":  company_id,
        "name": f"{payload.get('marca','')} {payload.get('modelo','')} {placa}".strip(),
        "cat":  payload.get("category_id", 1),
        "cli":  payload.get("client_id"),
    })
    r = await db.execute(text("SELECT LAST_INSERT_ID()"))
    asset_id = r.scalar()

    # Crear extensión vehículo
    await db.execute(text("""
        INSERT INTO talleres_vehiculo_ext
            (asset_id, company_id, placa, tipo, marca, modelo, anio, color, km_actual)
        VALUES
            (:aid, :cid, :placa, :tipo, :marca, :modelo, :anio, :color, :km)
    """), {
        "aid":    asset_id,
        "cid":    company_id,
        "placa":  placa,
        "tipo":   payload.get("tipo", "auto"),
        "marca":  payload.get("marca"),
        "modelo": payload.get("modelo"),
        "anio":   payload.get("anio"),
        "color":  payload.get("color"),
        "km":     payload.get("km_actual", 0),
    })
    await db.commit()
    return {"asset_id": asset_id, "placa": placa}
