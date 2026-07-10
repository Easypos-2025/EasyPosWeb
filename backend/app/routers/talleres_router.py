from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.auth.dependencies import get_current_user
from datetime import datetime, timezone, timedelta

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


# ── Sugerencias de placa (autocomplete) ──────────────────────────────────────

@router.get("/vehiculo/sugerencias")
async def sugerencias_placa(
    company_id: int  = Query(...),
    q: str           = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    q_up = q.strip().upper()
    rows = await db.execute(text("""
        SELECT v.placa, v.tipo, v.marca, v.modelo, v.anio,
               c.name AS cliente_nombre
        FROM talleres_vehiculo_ext v
        JOIN assets a ON a.id = v.asset_id
        LEFT JOIN clients c ON c.id = a.client_id
        WHERE v.company_id = :cid AND v.placa LIKE :q
        ORDER BY v.placa
        LIMIT 8
    """), {"cid": company_id, "q": f"%{q_up}%"})
    return [dict(r) for r in rows.mappings()]


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
                wj.name AS jefe_nombre,
                (SELECT SUM(d.subtotal) FROM service_order_details d
                 WHERE d.order_id = so.id) AS total_orden
            FROM service_orders so
            LEFT JOIN workers wj ON wj.id = so.jefe_responsable_id
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
        estados_lista = [e.strip() for e in estado.split(",") if e.strip()]
        ESTADOS_VALIDOS = {"abierta", "en_proceso", "terminada", "entregada", "cancelada"}
        estados_lista = [e for e in estados_lista if e in ESTADOS_VALIDOS]
        if len(estados_lista) == 1:
            where.append("so.estado = :estado")
            filtros["estado"] = estados_lista[0]
        elif len(estados_lista) > 1:
            placeholders = ", ".join(f":est{i}" for i in range(len(estados_lista)))
            where.append(f"so.estado IN ({placeholders})")
            for i, e in enumerate(estados_lista):
                filtros[f"est{i}"] = e
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
            u.nombre AS jefe_nombre,
            uc.nombre AS creado_por,
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

    # Insertar detalles enviados en el mismo payload (todo en una transacción)
    _tipos_validos = {"mecanica", "lavado", "latoneria", "pintura", "repuesto"}
    for det in (payload.get("detalles") or []):
        cantidad  = float(det.get("cantidad", 1))
        precio    = float(det.get("precio_unitario", 0))
        descuento = float(det.get("descuento", 0))
        subtotal  = round((precio * cantidad) - descuento, 2)
        tipo_det  = det.get("tipo_item", "mecanica")
        if tipo_det not in _tipos_validos:
            tipo_det = "mecanica"
        await db.execute(text("""
            INSERT INTO service_order_details (
                order_id, tipo_item, product_id, nombre,
                worker_id, modified_by, cantidad,
                precio_unitario, descuento, subtotal,
                mano_obra_operario, profession_id
            ) VALUES (
                :oid, :tipo, :pid, :nom,
                :wid, :uid, :qty,
                :pu, :desc, :sub, 0, :prof
            )
        """), {
            "oid":  new_id,
            "tipo": tipo_det,
            "pid":  det.get("product_id"),
            "nom":  det.get("nombre", ""),
            "wid":  det.get("worker_id"),
            "uid":  current_user.id,
            "qty":  cantidad,
            "pu":   precio,
            "desc": descuento,
            "sub":  subtotal,
            "prof": det.get("profession_id"),
        })

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
            wj.name   AS jefe_nombre,
            uc.nombre AS creado_por_nombre,
            cv.nombre_empresa AS convenio_nombre,
            v.marca, v.modelo, v.anio, v.color, v.tipo AS tipo_vehiculo
        FROM service_orders so
        LEFT JOIN clients c            ON c.id  = so.client_id
        LEFT JOIN workers wj           ON wj.id = so.jefe_responsable_id
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
            mu.nombre AS modificado_por_nombre
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

    fotos = await db.execute(text("""
        SELECT id, file_url, file_type, file_name
        FROM asset_media
        WHERE asset_id = :aid
        ORDER BY sort_order ASC, id ASC
        LIMIT 20
    """), {"aid": dict(orden).get("vehicle_id")}) if dict(orden).get("vehicle_id") else None

    return {
        "orden":    dict(orden),
        "detalles": [dict(r) for r in det.mappings()],
        "workers":  [dict(r) for r in wks.mappings()],
        "fotos":    [dict(r) for r in fotos.mappings()] if fotos else [],
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

    _tipos_validos = {"mecanica", "lavado", "latoneria", "pintura", "repuesto"}
    tipo_item_raw  = payload.get("tipo_item", "mecanica")
    tipo_item      = tipo_item_raw if tipo_item_raw in _tipos_validos else "mecanica"

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
        "tipo":  tipo_item,
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
    r_id = await db.execute(text("SELECT LAST_INSERT_ID()"))
    new_det_id = r_id.scalar()
    return {"id": new_det_id, "ok": True, "subtotal": subtotal, "mano_obra_operario": mano_obra}


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


# ── Editar encabezado de la orden ────────────────────────────────────────────

@router.patch("/ordenes/{orden_id}/editar")
async def editar_orden(
    orden_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    chk = await db.execute(text(
        "SELECT id FROM service_orders WHERE id=:oid AND company_id=:cid"
    ), {"oid": orden_id, "cid": payload.get("company_id")})
    if not chk.scalar():
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    sets, vals = [], {"oid": orden_id}
    campos = {
        "km_ingreso":          "km_ingreso",
        "km_salida":           "km_salida",
        "diagnostico":         "diagnostico",
        "trabajo_realizado":   "trabajo_realizado",
        "promesa_entrega":     "promesa_entrega",
        "jefe_responsable_id": "jefe_responsable_id",
        "convenio_id":         "convenio_id",
        "client_id":           "client_id",
    }
    for campo, col in campos.items():
        if campo in payload:
            sets.append(f"{col} = :{campo}")
            vals[campo] = payload[campo] or None

    if not sets:
        return {"ok": True, "msg": "Sin cambios"}

    await db.execute(text(
        f"UPDATE service_orders SET {', '.join(sets)}, updated_at=NOW() WHERE id=:oid"
    ), vals)
    await db.commit()
    return {"ok": True}


# ── Historial por placa ───────────────────────────────────────────────────────

@router.get("/historial/placa")
async def historial_por_placa(
    placa: str       = Query(...),
    company_id: int  = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    rows = await db.execute(text("""
        SELECT
            so.id, so.numero_orden, so.fecha_ingreso, so.fecha_entrega_real,
            so.estado, so.estado_facturacion, so.km_ingreso, so.km_salida,
            so.diagnostico, so.trabajo_realizado,
            u.nombre   AS jefe_nombre,
            uc.nombre  AS creado_por,
            (SELECT SUM(d.subtotal) FROM service_order_details d WHERE d.order_id=so.id) AS total_orden,
            (SELECT COUNT(*) FROM service_order_details d WHERE d.order_id=so.id) AS cant_items
        FROM service_orders so
        LEFT JOIN users u  ON u.id  = so.jefe_responsable_id
        LEFT JOIN users uc ON uc.id = so.created_by
        WHERE so.company_id = :cid AND so.placa_vehiculo = :placa
        ORDER BY so.fecha_ingreso DESC
        LIMIT 100
    """), {"cid": company_id, "placa": placa.strip().upper()})
    return [dict(r._mapping) for r in rows]


# ── Historial por cliente ─────────────────────────────────────────────────────

@router.get("/historial/cliente")
async def historial_por_cliente(
    client_id: int   = Query(...),
    company_id: int  = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    rows = await db.execute(text("""
        SELECT
            so.id, so.numero_orden, so.placa_vehiculo,
            so.fecha_ingreso, so.fecha_entrega_real,
            so.estado, so.estado_facturacion,
            so.diagnostico, so.trabajo_realizado,
            u.nombre  AS jefe_nombre,
            (SELECT SUM(d.subtotal) FROM service_order_details d WHERE d.order_id=so.id) AS total_orden,
            (SELECT COUNT(*) FROM service_order_details d WHERE d.order_id=so.id) AS cant_items
        FROM service_orders so
        LEFT JOIN users u ON u.id = so.jefe_responsable_id
        WHERE so.company_id = :cid AND so.client_id = :clt
        ORDER BY so.fecha_ingreso DESC
        LIMIT 150
    """), {"cid": company_id, "clt": client_id})
    return [dict(r._mapping) for r in rows]


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


# ── Tipos de Vehículo ─────────────────────────────────────────────────────────

_VEHICLE_TYPES_DEFAULT = [
    ("Automóvil / Carro",    "bi-car-front",      1),
    ("Camioneta / SUV",      "bi-truck",           2),
    ("Motocicleta",          "bi-bicycle",         3),
    ("Cuadrimoto / ATV",     "bi-car-front-fill",  4),
    ("Camión / Furgón",      "bi-truck",           5),
    ("Bus / Buseta / Van",   "bi-bus-front-fill",  6),
    ("Tractomula / Volqueta","bi-truck",           7),
    ("Otro",                 "bi-tools",           8),
]

@router.get("/tipos-vehiculo")
async def get_tipos_vehiculo(
    company_id: int  = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    rows = await db.execute(text("""
        SELECT * FROM vehicle_types WHERE company_id = :cid ORDER BY orden, nombre
    """), {"cid": company_id})
    tipos = [dict(r) for r in rows.mappings()]
    if not tipos:
        # Lazy seed: primeros tipos por defecto
        for nombre, icono, orden in _VEHICLE_TYPES_DEFAULT:
            await db.execute(text("""
                INSERT INTO vehicle_types (company_id, nombre, icono, activo, orden)
                VALUES (:cid, :nom, :ico, 1, :ord)
            """), {"cid": company_id, "nom": nombre, "ico": icono, "ord": orden})
        await db.commit()
        rows2 = await db.execute(text("""
            SELECT * FROM vehicle_types WHERE company_id = :cid ORDER BY orden
        """), {"cid": company_id})
        tipos = [dict(r) for r in rows2.mappings()]
    return tipos


@router.post("/tipos-vehiculo")
async def crear_tipo_vehiculo(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    company_id = payload.get("company_id")
    nombre = (payload.get("nombre") or "").strip()
    if not company_id or not nombre:
        raise HTTPException(status_code=400, detail="company_id y nombre son requeridos")
    r_ord = await db.execute(text(
        "SELECT COALESCE(MAX(orden),0)+1 FROM vehicle_types WHERE company_id=:cid"
    ), {"cid": company_id})
    nuevo_orden = r_ord.scalar() or 1
    await db.execute(text("""
        INSERT INTO vehicle_types (company_id, nombre, icono, activo, orden)
        VALUES (:cid, :nom, :ico, 1, :ord)
    """), {"cid": company_id, "nom": nombre, "ico": payload.get("icono","bi-car-front"), "ord": nuevo_orden})
    await db.commit()
    r_id = await db.execute(text("SELECT LAST_INSERT_ID()"))
    return {"id": r_id.scalar(), "ok": True}


@router.put("/tipos-vehiculo/{tipo_id}")
async def actualizar_tipo_vehiculo(
    tipo_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    await db.execute(text("""
        UPDATE vehicle_types SET nombre=:nom, icono=:ico, activo=:act
        WHERE id=:id AND company_id=:cid
    """), {
        "id": tipo_id, "cid": payload.get("company_id"),
        "nom": (payload.get("nombre") or "").strip(),
        "ico": payload.get("icono", "bi-car-front"),
        "act": payload.get("activo", 1),
    })
    await db.commit()
    return {"ok": True}


@router.delete("/tipos-vehiculo/{tipo_id}")
async def eliminar_tipo_vehiculo(
    tipo_id: int,
    company_id: int  = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    await db.execute(text(
        "UPDATE vehicle_types SET activo=0 WHERE id=:id AND company_id=:cid"
    ), {"id": tipo_id, "cid": company_id})
    await db.commit()
    return {"ok": True}


# ── Participantes de Servicio ──────────────────────────────────────────────────

@router.get("/servicios/{product_id}/participantes")
async def get_participantes(
    product_id: int,
    company_id: int  = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    rows = await db.execute(text("""
        SELECT sp.*, p.name AS profession_nombre
        FROM service_participants sp
        JOIN professions p ON p.id = sp.profession_id
        WHERE sp.product_id = :pid AND sp.company_id = :cid
        ORDER BY sp.pct_pago DESC
    """), {"pid": product_id, "cid": company_id})
    participantes = [dict(r) for r in rows.mappings()]
    # Total asignado y % para el negocio
    total_asignado = sum(float(x["pct_pago"]) for x in participantes)
    negocio_pct    = round(100 - total_asignado, 2)
    return {"participantes": participantes, "total_asignado": total_asignado, "negocio_pct": negocio_pct}


@router.post("/servicios/{product_id}/participantes")
async def agregar_participante(
    product_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    company_id    = payload.get("company_id")
    profession_id = payload.get("profession_id")
    pct           = round(float(payload.get("pct_pago", 0)), 2)
    if not company_id or not profession_id:
        raise HTTPException(status_code=400, detail="company_id y profession_id son requeridos")
    if pct <= 0 or pct > 100:
        raise HTTPException(status_code=400, detail="pct_pago debe estar entre 0.01 y 100")

    # Validar que no supere 100% junto con los existentes
    r_total = await db.execute(text("""
        SELECT COALESCE(SUM(pct_pago),0) FROM service_participants
        WHERE product_id=:pid AND company_id=:cid AND profession_id != :prof
    """), {"pid": product_id, "cid": company_id, "prof": profession_id})
    total_otros = float(r_total.scalar() or 0)
    if total_otros + pct > 100:
        raise HTTPException(status_code=400,
            detail=f"La suma de participantes superaría 100%. Disponible: {round(100-total_otros,2)}%")

    await db.execute(text("""
        INSERT INTO service_participants (company_id, product_id, profession_id, rol_display, pct_pago)
        VALUES (:cid, :pid, :prof, :rol, :pct)
        ON DUPLICATE KEY UPDATE rol_display=:rol, pct_pago=:pct
    """), {
        "cid": company_id, "pid": product_id, "prof": profession_id,
        "rol": payload.get("rol_display"), "pct": pct,
    })
    await db.commit()
    return {"ok": True}


@router.delete("/servicios/participantes/{participante_id}")
async def eliminar_participante(
    participante_id: int,
    company_id: int  = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    await db.execute(text("""
        DELETE FROM service_participants WHERE id=:id AND company_id=:cid
    """), {"id": participante_id, "cid": company_id})
    await db.commit()
    return {"ok": True}


# ── CRUD Convenios Empresariales ─────────────────────────────────────────────

@router.post("/convenios")
async def crear_convenio(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = payload.get("company_id")
    if not company_id:
        raise HTTPException(status_code=400, detail="company_id requerido")
    nombre = (payload.get("nombre_empresa") or "").strip()
    if not nombre:
        raise HTTPException(status_code=400, detail="El nombre de la empresa es requerido")

    await db.execute(text("""
        INSERT INTO service_convenios (
            company_id, nombre_empresa, nit_empresa,
            contacto_nombre, contacto_telefono, contacto_email,
            periodicidad_facturacion, condicion_pago, dias_credito,
            observaciones, activo
        ) VALUES (
            :cid, :nombre, :nit,
            :contacto, :tel, :email,
            :periodi, :cond, :dias,
            :obs, 1
        )
    """), {
        "cid":     company_id,
        "nombre":  nombre,
        "nit":     payload.get("nit_empresa"),
        "contacto":payload.get("contacto_nombre"),
        "tel":     payload.get("contacto_telefono"),
        "email":   payload.get("contacto_email"),
        "periodi": payload.get("periodicidad_facturacion", "mensual"),
        "cond":    payload.get("condicion_pago", "credito"),
        "dias":    payload.get("dias_credito", 30),
        "obs":     payload.get("observaciones"),
    })
    await db.commit()
    r = await db.execute(text("SELECT LAST_INSERT_ID()"))
    return {"id": r.scalar(), "ok": True}


@router.put("/convenios/{convenio_id}")
async def actualizar_convenio(
    convenio_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    company_id = payload.get("company_id")
    nombre = (payload.get("nombre_empresa") or "").strip()
    if not nombre:
        raise HTTPException(status_code=400, detail="El nombre de la empresa es requerido")

    await db.execute(text("""
        UPDATE service_convenios SET
            nombre_empresa           = :nombre,
            nit_empresa              = :nit,
            contacto_nombre          = :contacto,
            contacto_telefono        = :tel,
            contacto_email           = :email,
            periodicidad_facturacion = :periodi,
            condicion_pago           = :cond,
            dias_credito             = :dias,
            observaciones            = :obs
        WHERE id = :id AND company_id = :cid
    """), {
        "id":      convenio_id,
        "cid":     company_id,
        "nombre":  nombre,
        "nit":     payload.get("nit_empresa"),
        "contacto":payload.get("contacto_nombre"),
        "tel":     payload.get("contacto_telefono"),
        "email":   payload.get("contacto_email"),
        "periodi": payload.get("periodicidad_facturacion", "mensual"),
        "cond":    payload.get("condicion_pago", "credito"),
        "dias":    payload.get("dias_credito", 30),
        "obs":     payload.get("observaciones"),
    })
    await db.commit()
    return {"ok": True}


@router.patch("/convenios/{convenio_id}/activo")
async def toggle_convenio(
    convenio_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    await db.execute(text("""
        UPDATE service_convenios SET activo = :activo
        WHERE id = :id AND company_id = :cid
    """), {"id": convenio_id, "activo": payload.get("activo", 1), "cid": payload.get("company_id")})
    await db.commit()
    return {"ok": True}


# ── Sprint 3: Configuración de porcentajes por profesión ─────────────────

@router.get("/profession-config")
async def get_profession_config(
    company_id: int  = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Lista todas las profesiones de la empresa con su configuración de pagos."""
    rows = await db.execute(text("""
        SELECT
            p.id, p.name, p.description,
            COALESCE(pc.id, 0)            AS config_id,
            COALESCE(pc.pct_operario, 0)  AS pct_operario,
            COALESCE(pc.pct_jefe,     0)  AS pct_jefe,
            COALESCE(pc.pct_negocio, 100) AS pct_negocio,
            (SELECT COUNT(*) FROM workers w
             WHERE w.profession_id = p.id AND w.company_id = :cid) AS total_workers
        FROM professions p
        LEFT JOIN profession_payment_config pc
               ON pc.profession_id = p.id AND pc.company_id = :cid
        WHERE p.company_id = :cid
        ORDER BY p.name
    """), {"cid": company_id})
    return [dict(r) for r in rows.mappings()]


@router.put("/profession-config/{profession_id}")
async def upsert_profession_config(
    profession_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    company_id   = payload.get("company_id")
    pct_operario = round(float(payload.get("pct_operario", 0)), 2)
    pct_jefe     = round(float(payload.get("pct_jefe",     0)), 2)
    pct_negocio  = round(float(payload.get("pct_negocio", 100)), 2)

    if abs(pct_operario + pct_jefe + pct_negocio - 100) > 0.05:
        raise HTTPException(
            status_code=400,
            detail=f"Los porcentajes deben sumar 100%. Suma actual: {pct_operario + pct_jefe + pct_negocio}"
        )

    await db.execute(text("""
        INSERT INTO profession_payment_config
            (profession_id, company_id, pct_operario, pct_jefe, pct_negocio)
        VALUES (:pid, :cid, :po, :pj, :pn)
        ON DUPLICATE KEY UPDATE
            pct_operario = :po,
            pct_jefe     = :pj,
            pct_negocio  = :pn
    """), {
        "pid": profession_id, "cid": company_id,
        "po": pct_operario, "pj": pct_jefe, "pn": pct_negocio,
    })
    await db.commit()
    return {"ok": True}


@router.get("/workers-con-config")
async def get_workers_con_config(
    company_id: int  = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Directorio del equipo: workers con profesión, saldo pendiente y actividad del mes."""
    rows = await db.execute(text("""
        SELECT
            w.id, w.name, w.phone,
            COALESCE(w.is_active, 1)  AS is_active,
            p.id   AS profession_id,
            p.name AS profession_nombre,
            (SELECT COUNT(DISTINCT d.order_id)
             FROM service_order_details d
             WHERE d.worker_id = w.id
               AND d.liq_estado = 'pendiente') AS items_pendientes,
            (SELECT COALESCE(SUM(d.mano_obra_operario), 0)
             FROM service_order_details d
             WHERE d.worker_id = w.id
               AND d.liq_estado = 'pendiente') AS monto_pendiente,
            (SELECT COUNT(DISTINCT d.order_id)
             FROM service_order_details d
             JOIN service_orders so ON so.id = d.order_id
             WHERE d.worker_id = w.id
               AND so.company_id = :cid
               AND MONTH(so.fecha_ingreso) = MONTH(CURDATE())
               AND YEAR(so.fecha_ingreso)  = YEAR(CURDATE())) AS ordenes_mes
        FROM workers w
        LEFT JOIN professions p ON p.id = w.profession_id
        WHERE w.company_id = :cid
        ORDER BY p.name, w.name
    """), {"cid": company_id})
    return [dict(r) for r in rows.mappings()]


# ── Sprint 4: Búsqueda de productos para el detalle de la orden ───────────

@router.get("/productos-buscar")
async def buscar_productos(
    company_id: int  = Query(...),
    q: str           = Query("", max_length=100),
    item_type: str   = Query(None),  # 'servicio' | 'producto' | None (ambos)
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Busca productos y servicios del catálogo por nombre o código."""
    like = f"%{q}%"
    tipo_filter = ""
    params: dict = {"cid": company_id, "q": like}
    if item_type in ("servicio", "producto"):
        tipo_filter = "AND p.item_type = :itype"
        params["itype"] = item_type

    rows = await db.execute(text(f"""
        SELECT
            p.id, p.code, p.name, p.base_price, p.cost_price,
            p.item_type, p.inventory_behavior,
            cat.name AS categoria,
            COALESCE(pse.service_type, 'mecanica') AS service_type,
            (SELECT COUNT(*) FROM service_participants sp
             WHERE sp.product_id = p.id AND sp.company_id = p.company_id) AS num_participantes
        FROM products p
        LEFT JOIN product_categories cat ON cat.id = p.category_id
        LEFT JOIN product_service_ext pse ON pse.product_id = p.id
        WHERE p.company_id = :cid AND p.is_active = 1
          AND (p.name LIKE :q OR p.code LIKE :q)
          {tipo_filter}
        ORDER BY p.item_type, p.name
        LIMIT 40
    """), params)
    return [dict(r) for r in rows.mappings()]


@router.delete("/ordenes/{orden_id}/detalle/{detalle_id}")
async def eliminar_detalle(
    orden_id: int,
    detalle_id: int,
    company_id: int  = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    # Verificar que el ítem existe, pertenece a la empresa y está pendiente
    chk = await db.execute(text("""
        SELECT d.id, d.liq_estado FROM service_order_details d
        JOIN service_orders so ON so.id = d.order_id
        WHERE d.id = :did AND d.order_id = :oid AND so.company_id = :cid
    """), {"did": detalle_id, "oid": orden_id, "cid": company_id})
    row = chk.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    if row["liq_estado"] and row["liq_estado"] != "pendiente":
        raise HTTPException(status_code=409, detail="El ítem ya fue liquidado y no puede eliminarse")

    await db.execute(text("""
        DELETE FROM service_order_details WHERE id = :did
    """), {"did": detalle_id})
    await db.commit()
    return {"ok": True}


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
            (asset_id, company_id, placa, tipo, marca, modelo, anio, color, km_actual,
             cliente_nombre, cliente_documento, cliente_telefono)
        VALUES
            (:aid, :cid, :placa, :tipo, :marca, :modelo, :anio, :color, :km,
             :cli_nom, :cli_doc, :cli_tel)
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
        "cli_nom": payload.get("cliente_nombre"),
        "cli_doc": payload.get("cliente_documento"),
        "cli_tel": payload.get("cliente_telefono"),
    })
    await db.commit()
    return {"asset_id": asset_id, "placa": placa}


# ═══════════════════════════════════════════════════════════════════════════════
# EDITAR VEHÍCULO
# ═══════════════════════════════════════════════════════════════════════════════

@router.put("/vehiculo/{asset_id}")
async def editar_vehiculo(
    asset_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Actualiza datos del vehículo y su propietario. Solo admin."""
    company_id = payload.get("company_id") or current_user.company_id

    chk = await db.execute(text(
        "SELECT id FROM talleres_vehiculo_ext WHERE asset_id=:aid AND company_id=:cid"
    ), {"aid": asset_id, "cid": company_id})
    if not chk.scalar():
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")

    sets, params = [], {"aid": asset_id}
    for col in ("tipo", "marca", "modelo", "color", "cliente_nombre", "cliente_documento", "cliente_telefono"):
        if col in payload:
            sets.append(f"{col} = :{col}")
            params[col] = payload[col]
    if "anio" in payload:
        sets.append("anio = :anio")
        params["anio"] = payload["anio"] or None
    if "km_actual" in payload:
        sets.append("km_actual = :km_actual")
        params["km_actual"] = payload["km_actual"] or 0

    if sets:
        await db.execute(text(
            f"UPDATE talleres_vehiculo_ext SET {', '.join(sets)} WHERE asset_id = :aid"
        ), params)
        await db.commit()
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════════
# FOTOS DEL VEHÍCULO
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/vehiculo/{asset_id}/fotos")
async def listar_fotos(
    asset_id: int,
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    rows = await db.execute(text("""
        SELECT id, photo_url, tipo, created_at
        FROM vehicle_photos
        WHERE asset_id = :aid AND company_id = :cid
        ORDER BY created_at DESC
    """), {"aid": asset_id, "cid": company_id})
    return [dict(r) for r in rows.mappings()]


@router.post("/vehiculo/{asset_id}/fotos")
async def agregar_foto(
    asset_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    company_id = payload.get("company_id")
    photo_url  = (payload.get("photo_url") or "").strip()
    tipo       = payload.get("tipo", "ingreso")
    if not company_id or not photo_url:
        raise HTTPException(status_code=400, detail="company_id y photo_url son requeridos")
    if tipo not in ("ingreso", "proceso", "salida", "general"):
        tipo = "ingreso"

    await db.execute(text("""
        INSERT INTO vehicle_photos (company_id, asset_id, photo_url, tipo)
        VALUES (:cid, :aid, :url, :tipo)
    """), {"cid": company_id, "aid": asset_id, "url": photo_url, "tipo": tipo})
    await db.commit()
    r = await db.execute(text("SELECT LAST_INSERT_ID()"))
    return {"id": r.scalar(), "ok": True, "photo_url": photo_url, "tipo": tipo}


@router.delete("/vehiculo/fotos/{foto_id}")
async def eliminar_foto(
    foto_id: int,
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    chk = await db.execute(text(
        "SELECT id FROM vehicle_photos WHERE id=:fid AND company_id=:cid"
    ), {"fid": foto_id, "cid": company_id})
    if not chk.scalar():
        raise HTTPException(status_code=404, detail="Foto no encontrada")
    await db.execute(text("DELETE FROM vehicle_photos WHERE id=:fid"), {"fid": foto_id})
    await db.commit()
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════════
# BÚSQUEDA AVANZADA DE ÓRDENES
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/ordenes/buscar")
async def buscar_ordenes_avanzado(
    company_id: int  = Query(...),
    q: str           = Query("", max_length=100),
    estado: str      = Query(None),
    mes: int         = Query(None),
    anio: int        = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Búsqueda avanzada: por placa, cliente, número de orden, estado, mes/año."""
    where = ["so.company_id = :cid"]
    params: dict = {"cid": company_id}

    if q:
        where.append("(so.placa_vehiculo LIKE :q OR so.numero_orden LIKE :q OR c.name LIKE :q)")
        params["q"] = f"%{q}%"
    if estado:
        where.append("so.estado = :estado")
        params["estado"] = estado
    if mes:
        where.append("MONTH(so.fecha_ingreso) = :mes")
        params["mes"] = mes
    if anio:
        where.append("YEAR(so.fecha_ingreso) = :anio")
        params["anio"] = anio

    sql = f"""
        SELECT
            so.id, so.numero_orden, so.placa_vehiculo, so.fecha_ingreso,
            so.estado, so.estado_facturacion,
            c.name AS cliente_nombre,
            u.nombre AS jefe_nombre,
            (SELECT COALESCE(SUM(d.subtotal),0) FROM service_order_details d
             WHERE d.order_id = so.id) AS total_orden,
            (SELECT COUNT(*) FROM service_order_details d
             WHERE d.order_id = so.id) AS cant_items,
            cv.nombre_empresa AS convenio_nombre
        FROM service_orders so
        LEFT JOIN clients c    ON c.id  = so.client_id
        LEFT JOIN users u      ON u.id  = so.jefe_responsable_id
        LEFT JOIN service_convenios cv ON cv.id = so.convenio_id
        WHERE {' AND '.join(where)}
        ORDER BY so.fecha_ingreso DESC
        LIMIT 60
    """
    rows = await db.execute(text(sql), params)
    return [dict(r) for r in rows.mappings()]


# ═══════════════════════════════════════════════════════════════════════════════
# CIERRE DE CAJA DIARIO
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/caja/resumen")
async def resumen_caja(
    company_id: int = Query(...),
    fecha: str      = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Resumen financiero del día: ingresos facturados (pos_receipts), mano de obra, egresos."""
    fecha_q = fecha or datetime.now(_BOG).date().isoformat()

    # ── Ingresos facturados del día (pos_receipts) ────────────────────────────
    # Agrupado por forma de pago para separar efectivo de otros medios
    ing = await db.execute(text("""
        SELECT
            COALESCE(SUM(r.amount_without_tip), 0)                          AS ingresos_subtotal,
            COALESCE(SUM(r.tip), 0)                                         AS ingresos_propina,
            COALESCE(SUM(r.cash_amount), 0)                                 AS ingresos_total,
            COUNT(*)                                                         AS num_recibos,
            -- Efectivo: pagos con forma adds_to_cash=1
            COALESCE(SUM(
                CASE WHEN EXISTS(
                    SELECT 1 FROM pos_receipt_payment_methods pm
                    JOIN pos_payment_types pt ON pt.id = pm.payment_method_id AND pt.company_id = pm.company_id
                    WHERE pm.invoice_number = r.receipt_number AND pm.company_id = r.company_id
                      AND pt.adds_to_cash = 1
                ) THEN r.cash_amount ELSE 0 END
            ), 0)                                                            AS ingresos_efectivo,
            -- Convenio / crédito: el resto
            COALESCE(SUM(
                CASE WHEN NOT EXISTS(
                    SELECT 1 FROM pos_receipt_payment_methods pm
                    JOIN pos_payment_types pt ON pt.id = pm.payment_method_id AND pt.company_id = pm.company_id
                    WHERE pm.invoice_number = r.receipt_number AND pm.company_id = r.company_id
                      AND pt.adds_to_cash = 1
                ) THEN r.cash_amount ELSE 0 END
            ), 0)                                                            AS ingresos_convenio
        FROM pos_receipts r
        WHERE r.company_id = :cid AND r.date = :fecha AND r.voided = 0
    """), {"cid": company_id, "fecha": fecha_q})
    ingresos = dict(ing.mappings().first() or {})

    # ── Detalle de recibos del día ────────────────────────────────────────────
    det = await db.execute(text("""
        SELECT
            r.receipt_number,
            r.time,
            r.cash_amount          AS total_orden,
            r.amount_without_tip   AS subtotal,
            r.tip,
            so.numero_orden,
            so.placa_vehiculo,
            so.estado_facturacion,
            c.name                 AS cliente_nombre,
            cv.nombre_empresa      AS convenio_nombre,
            -- Formas de pago concatenadas
            GROUP_CONCAT(pt.name ORDER BY pm.item SEPARATOR ' / ') AS formas_pago
        FROM pos_receipts r
        LEFT JOIN pos_receipt_payment_methods pm
               ON pm.invoice_number = r.receipt_number AND pm.company_id = r.company_id
        LEFT JOIN pos_payment_types pt
               ON pt.id = pm.payment_method_id AND pt.company_id = r.company_id
        LEFT JOIN service_orders so
               ON so.id = CAST(pm.order_number AS UNSIGNED) AND so.company_id = r.company_id
        LEFT JOIN clients c ON c.id = so.client_id
        LEFT JOIN service_convenios cv ON cv.id = so.convenio_id
        WHERE r.company_id = :cid AND r.date = :fecha AND r.voided = 0
        GROUP BY r.receipt_number, r.company_id, r.time, r.cash_amount, r.amount_without_tip, r.tip,
                 so.numero_orden, so.placa_vehiculo, so.estado_facturacion, c.name, cv.nombre_empresa
        ORDER BY r.time
    """), {"cid": company_id, "fecha": fecha_q})
    ordenes_dia = [dict(r) for r in det.mappings()]

    # ── Mano de obra liquidada (pagos a workers del día) ──────────────────────
    liq = await db.execute(text("""
        SELECT
            COALESCE(SUM(wl.monto_operario), 0) AS total_mano_obra,
            COUNT(*)                             AS num_liquidaciones
        FROM worker_liquidaciones wl
        WHERE wl.company_id = :cid AND wl.fecha_pago = :fecha AND wl.estado = 'pagado'
    """), {"cid": company_id, "fecha": fecha_q})
    liquidaciones = dict(liq.mappings().first() or {})

    # Detalle liquidaciones
    liq_det = await db.execute(text("""
        SELECT
            wl.id, wl.monto_operario, wl.forma_pago, wl.fecha_pago,
            w.name AS worker_nombre,
            p.name AS profession_nombre
        FROM worker_liquidaciones wl
        JOIN workers w    ON w.id = wl.worker_id
        LEFT JOIN professions p ON p.id = w.profession_id
        WHERE wl.company_id = :cid AND wl.fecha_pago = :fecha AND wl.estado = 'pagado'
        ORDER BY wl.created_at
    """), {"cid": company_id, "fecha": fecha_q})
    liquidaciones_det = [dict(r) for r in liq_det.mappings()]

    # ── Egresos manuales del día ──────────────────────────────────────────────
    eg = await db.execute(text("""
        SELECT COALESCE(SUM(monto), 0) AS total_egresos, COUNT(*) AS num_egresos
        FROM caja_egresos WHERE company_id = :cid AND fecha = :fecha
    """), {"cid": company_id, "fecha": fecha_q})
    egresos_sum = dict(eg.mappings().first() or {})

    eg_det = await db.execute(text("""
        SELECT id, concepto, categoria, monto, forma_pago, created_at
        FROM caja_egresos WHERE company_id = :cid AND fecha = :fecha ORDER BY created_at
    """), {"cid": company_id, "fecha": fecha_q})
    egresos_det = [dict(r) for r in eg_det.mappings()]

    total_egresos = float(liquidaciones.get("total_mano_obra") or 0) + float(egresos_sum.get("total_egresos") or 0)
    saldo_neto    = float(ingresos.get("ingresos_efectivo") or 0) - total_egresos

    return {
        "fecha":             fecha_q,
        "ingresos":          {k: float(v or 0) for k, v in ingresos.items()},
        "ordenes_dia":       ordenes_dia,
        "liquidaciones":     {k: float(v or 0) if isinstance(v, (int, float)) else v
                              for k, v in liquidaciones.items()},
        "liquidaciones_det": liquidaciones_det,
        "egresos":           {k: float(v or 0) if isinstance(v, (int, float)) else v
                              for k, v in egresos_sum.items()},
        "egresos_det":       egresos_det,
        "saldo_neto":        saldo_neto,
        "total_egresos":     total_egresos,
    }


@router.post("/caja/egresos")
async def crear_egreso_caja(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from datetime import date as ddate
    company_id = payload.get("company_id") or current_user.company_id
    concepto   = (payload.get("concepto") or "").strip()
    if not concepto:
        raise HTTPException(status_code=400, detail="El concepto es requerido")
    monto = float(payload.get("monto") or 0)
    if monto <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser mayor a 0")
    categoria  = payload.get("categoria", "gasto")
    if categoria not in ("gasto", "compra", "nomina", "otro"):
        categoria = "gasto"
    forma_pago = payload.get("forma_pago", "efectivo")
    fecha      = payload.get("fecha") or str(ddate.today())

    await db.execute(text("""
        INSERT INTO caja_egresos (company_id, fecha, concepto, categoria, monto, forma_pago, registrado_por)
        VALUES (:cid, :fecha, :concepto, :cat, :monto, :fp, :usr)
    """), {
        "cid": company_id, "fecha": fecha, "concepto": concepto,
        "cat": categoria, "monto": monto, "fp": forma_pago,
        "usr": current_user.id,
    })
    await db.commit()
    r = await db.execute(text("SELECT LAST_INSERT_ID()"))
    return {"id": r.scalar(), "ok": True}


@router.delete("/caja/egresos/{egreso_id}")
async def eliminar_egreso_caja(
    egreso_id: int,
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    chk = await db.execute(text(
        "SELECT id FROM caja_egresos WHERE id=:eid AND company_id=:cid"
    ), {"eid": egreso_id, "cid": company_id})
    if not chk.scalar():
        raise HTTPException(status_code=404, detail="Egreso no encontrado")
    await db.execute(text("DELETE FROM caja_egresos WHERE id=:eid"), {"eid": egreso_id})
    await db.commit()
    return {"ok": True}


# ── Liquidación de Operarios ───────────────────────────────────────────────────

@router.get("/liquidacion/dia")
async def liquidacion_dia(
    company_id: int = Query(...),
    fecha: str      = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    fecha_sel = fecha or datetime.now(_BOG).date().isoformat()

    # Filtra por fecha del RECIBO (pos_receipts.date), no fecha_ingreso
    # Muestra lo que se facturó hoy y aún está pendiente de pago al operario
    res_workers = await db.execute(text("""
        SELECT
            w.id                  AS worker_id,
            w.name                AS worker_nombre,
            pr.name               AS profesion,
            COUNT(DISTINCT so.id) AS num_ordenes,
            COUNT(sod.id)         AS num_items,
            SUM(COALESCE(
                NULLIF(sod.mano_obra_operario, 0),
                sod.subtotal * COALESCE(
                    (SELECT sp.pct_pago / 100
                     FROM service_participants sp
                     WHERE sp.product_id    = sod.product_id
                       AND sp.profession_id = w.profession_id
                     LIMIT 1), 0)
            ))                    AS total_pendiente
        FROM service_order_details sod
        JOIN service_orders so ON sod.order_id = so.id
        JOIN workers w         ON sod.worker_id = w.id
        LEFT JOIN professions pr ON w.profession_id = pr.id
        JOIN pos_receipt_order_details rod
             ON rod.order_number = CAST(so.id AS CHAR) AND rod.company_id = so.company_id
        JOIN pos_receipts r
             ON r.receipt_number = rod.receipt_number AND r.company_id = rod.company_id
        WHERE so.company_id    = :cid
          AND r.date           = :fecha
          AND r.voided         = 0
          AND sod.liq_estado   = 'pendiente'
          AND sod.worker_id IS NOT NULL
        GROUP BY w.id, w.name, pr.name
        ORDER BY total_pendiente DESC
    """), {"cid": company_id, "fecha": fecha_sel})
    workers_rows = [dict(r._mapping) for r in res_workers]

    res_det = await db.execute(text("""
        SELECT
            sod.id                    AS detail_id,
            sod.nombre                AS servicio,
            sod.tipo_item,
            sod.subtotal,
            COALESCE(
                NULLIF(sod.mano_obra_operario, 0),
                sod.subtotal * COALESCE(
                    (SELECT sp.pct_pago / 100
                     FROM service_participants sp
                     WHERE sp.product_id    = sod.product_id
                       AND sp.profession_id = w2.profession_id
                     LIMIT 1), 0)
            )                         AS monto_operario,
            so.numero_orden,
            so.placa_vehiculo,
            so.fecha_ingreso,
            sod.worker_id
        FROM service_order_details sod
        JOIN service_orders so ON sod.order_id  = so.id
        JOIN workers w2        ON w2.id          = sod.worker_id
        JOIN pos_receipt_order_details rod
             ON rod.order_number = CAST(so.id AS CHAR) AND rod.company_id = so.company_id
        JOIN pos_receipts r
             ON r.receipt_number = rod.receipt_number AND r.company_id = rod.company_id
        WHERE so.company_id    = :cid
          AND r.date           = :fecha
          AND r.voided         = 0
          AND sod.liq_estado   = 'pendiente'
          AND sod.worker_id IS NOT NULL
        ORDER BY so.fecha_ingreso, sod.worker_id
    """), {"cid": company_id, "fecha": fecha_sel})

    det_map: dict = {}
    for d in res_det:
        dm    = dict(d._mapping)
        wid   = dm["worker_id"]
        if wid not in det_map:
            det_map[wid] = []
        det_map[wid].append({
            "detail_id":    dm["detail_id"],
            "servicio":     dm["servicio"],
            "tipo_item":    dm["tipo_item"],
            "subtotal":     float(dm["subtotal"]       or 0),
            "monto_operario": float(dm["monto_operario"] or 0),
            "numero_orden": dm["numero_orden"],
            "placa":        dm["placa_vehiculo"],
            "fecha_ingreso": str(dm["fecha_ingreso"]) if dm["fecha_ingreso"] else None,
        })

    workers = []
    for w in workers_rows:
        wid = w["worker_id"]
        workers.append({
            "worker_id":       wid,
            "worker_nombre":   w["worker_nombre"],
            "profesion":       w["profesion"] or "",
            "num_ordenes":     int(w["num_ordenes"] or 0),
            "num_items":       int(w["num_items"]   or 0),
            "total_pendiente": float(w["total_pendiente"] or 0),
            "detalles":        det_map.get(wid, []),
        })

    return {
        "fecha":           fecha_sel,
        "workers":         workers,
        "total_workers":   len(workers),
        "total_mano_obra": sum(r["total_pendiente"] for r in workers),
    }


@router.post("/liquidacion/registrar")
async def registrar_liquidacion(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id    = int(payload.get("company_id") or current_user.company_id)
    worker_id     = int(payload.get("worker_id")  or 0)
    fecha         = payload.get("fecha", "")
    monto         = float(payload.get("monto_operario") or 0)
    total_bruto   = float(payload.get("total_bruto")    or monto)
    forma_pago    = payload.get("forma_pago", "efectivo")
    if forma_pago not in ("efectivo", "transferencia", "otro"):
        forma_pago = "efectivo"
    observaciones = (payload.get("observaciones") or "").strip()
    detail_ids    = [int(d) for d in (payload.get("detail_ids") or []) if str(d).isdigit()]

    if not worker_id or monto <= 0:
        raise HTTPException(status_code=400, detail="Datos incompletos")

    await db.execute(text("""
        INSERT INTO worker_liquidaciones
            (company_id, worker_id, fecha_inicio, fecha_fin, total_bruto, pct_aplicado,
             monto_operario, estado, fecha_pago, forma_pago, observaciones, registrado_por)
        VALUES (:cid, :wid, :fi, :ff, :tb, 0, :mo, 'pagado', :fpd, :fp, :obs, :usr)
    """), {
        "cid": company_id, "wid": worker_id,
        "fi": fecha, "ff": fecha,
        "tb": total_bruto, "mo": monto,
        "fpd": fecha, "fp": forma_pago,
        "obs": observaciones, "usr": current_user.id,
    })
    await db.commit()
    r     = await db.execute(text("SELECT LAST_INSERT_ID()"))
    liq_id = r.scalar()

    for did in detail_ids:
        try:
            await db.execute(text("""
                INSERT INTO worker_liquidacion_details (liq_id, detail_id, subtotal, monto_pagado)
                SELECT :lid, sod.id, sod.subtotal, sod.mano_obra_operario
                FROM service_order_details sod WHERE sod.id = :did
            """), {"lid": liq_id, "did": did})
            await db.execute(text("""
                UPDATE service_order_details
                SET liq_estado = 'liquidado', liq_id = :lid
                WHERE id = :did
            """), {"lid": liq_id, "did": did})
        except Exception:
            pass
    if detail_ids:
        await db.commit()

    return {"ok": True, "liq_id": liq_id}


@router.get("/liquidacion/historial")
async def liquidacion_historial(
    company_id: int  = Query(...),
    fecha_ini: str   = Query(...),
    fecha_fin: str   = Query(...),
    worker_id: int   = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    params: dict = {"cid": company_id, "fi": fecha_ini, "ff": fecha_fin}
    w_filter = ""
    if worker_id:
        w_filter = " AND wl.worker_id = :wid"
        params["wid"] = worker_id

    res = await db.execute(text(f"""
        SELECT
            wl.id, wl.worker_id,
            wl.fecha_inicio, wl.fecha_fin,
            wl.total_bruto, wl.monto_operario,
            wl.estado, wl.fecha_pago, wl.forma_pago,
            wl.observaciones, wl.created_at,
            w.name       AS worker_nombre,
            pr.name      AS profesion,
            u.nombre     AS registrado_por_nombre,
            COUNT(wld.id) AS num_items
        FROM worker_liquidaciones wl
        JOIN workers w       ON wl.worker_id     = w.id
        LEFT JOIN professions pr ON w.profession_id = pr.id
        LEFT JOIN users u    ON wl.registrado_por = u.id
        LEFT JOIN worker_liquidacion_details wld ON wld.liq_id = wl.id
        WHERE wl.company_id   = :cid
          AND wl.fecha_inicio >= :fi
          AND wl.fecha_fin   <= :ff
          {w_filter}
        GROUP BY wl.id, wl.worker_id, wl.fecha_inicio, wl.fecha_fin,
                 wl.total_bruto, wl.monto_operario, wl.estado,
                 wl.fecha_pago, wl.forma_pago, wl.observaciones, wl.created_at,
                 w.name, pr.name, u.nombre
        ORDER BY wl.created_at DESC
        LIMIT 500
    """), params)

    result = []
    for row in res:
        rm = dict(row._mapping)
        result.append({
            "id":              rm["id"],
            "worker_id":       rm["worker_id"],
            "worker_nombre":   rm["worker_nombre"],
            "profesion":       rm["profesion"] or "",
            "fecha_inicio":    str(rm["fecha_inicio"]) if rm["fecha_inicio"] else None,
            "fecha_fin":       str(rm["fecha_fin"])    if rm["fecha_fin"]    else None,
            "total_bruto":     float(rm["total_bruto"]    or 0),
            "monto_operario":  float(rm["monto_operario"] or 0),
            "estado":          rm["estado"],
            "fecha_pago":      str(rm["fecha_pago"]) if rm["fecha_pago"] else None,
            "forma_pago":      rm["forma_pago"],
            "observaciones":   rm["observaciones"],
            "registrado_por":  rm["registrado_por_nombre"],
            "num_items":       int(rm["num_items"] or 0),
            "created_at":      str(rm["created_at"]) if rm["created_at"] else None,
        })

    return {
        "liquidaciones": result,
        "total":         sum(r["monto_operario"] for r in result),
        "count":         len(result),
    }


@router.get("/ventas/resumen")
async def ventas_resumen(
    company_id: int  = Query(...),
    fecha_ini: str   = Query(...),
    fecha_fin: str   = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    params: dict = {"cid": company_id, "fi": fecha_ini, "ff": fecha_fin}

    res_svc = await db.execute(text("""
        SELECT
            sod.tipo_item,
            sod.nombre,
            COUNT(*)                      AS cantidad,
            SUM(sod.subtotal)             AS total,
            SUM(sod.mano_obra_operario)   AS total_mano_obra
        FROM service_order_details sod
        JOIN service_orders so ON sod.order_id = so.id
        WHERE so.company_id          = :cid
          AND DATE(so.fecha_ingreso) BETWEEN :fi AND :ff
          AND sod.tipo_item         != 'repuesto'
        GROUP BY sod.tipo_item, sod.nombre
        ORDER BY sod.tipo_item, total DESC
    """), params)

    res_prod = await db.execute(text("""
        SELECT
            sod.nombre,
            SUM(sod.cantidad)  AS cantidad,
            SUM(sod.subtotal)  AS total
        FROM service_order_details sod
        JOIN service_orders so ON sod.order_id = so.id
        WHERE so.company_id          = :cid
          AND DATE(so.fecha_ingreso) BETWEEN :fi AND :ff
          AND sod.tipo_item          = 'repuesto'
        GROUP BY sod.product_id, sod.nombre
        ORDER BY total DESC
    """), params)

    res_tot = await db.execute(text("""
        SELECT
            COUNT(DISTINCT so.id) AS num_ordenes,
            SUM(sod.subtotal)     AS total_venta
        FROM service_orders so
        JOIN service_order_details sod ON sod.order_id = so.id
        WHERE so.company_id          = :cid
          AND DATE(so.fecha_ingreso) BETWEEN :fi AND :ff
    """), params)
    tot = dict(res_tot.first()._mapping)

    servicios = []
    for row in res_svc:
        rm = dict(row._mapping)
        servicios.append({
            "tipo_item":      rm["tipo_item"],
            "nombre":         rm["nombre"],
            "cantidad":       int(rm["cantidad"] or 0),
            "total":          float(rm["total"]          or 0),
            "total_mano_obra": float(rm["total_mano_obra"] or 0),
        })

    productos = []
    for row in res_prod:
        rm = dict(row._mapping)
        productos.append({
            "nombre":   rm["nombre"],
            "cantidad": float(rm["cantidad"] or 0),
            "total":    float(rm["total"]    or 0),
        })

    return {
        "servicios":        servicios,
        "productos":        productos,
        "num_ordenes":      int(tot["num_ordenes"]  or 0),
        "total_venta":      float(tot["total_venta"] or 0),
        "total_servicios":  sum(s["total"] for s in servicios),
        "total_productos":  sum(p["total"] for p in productos),
    }


# ─── Billing config pública (formas de pago + propina) ───────────────────────

_BOG = timezone(timedelta(hours=-5))


@router.get("/billing-config")
async def get_billing_config(
    company_id: int  = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    row = (await db.execute(text("""
        SELECT has_pos_electronico,
               COALESCE(has_tip, 0)          AS has_tip,
               COALESCE(tip_percentage, 0)   AS tip_percentage,
               COALESCE(tip_label, 'Propina') AS tip_label
        FROM company_configs
        WHERE company_id = :cid
    """), {"cid": company_id})).mappings().first()

    if not row:
        return {"has_pos_electronico": 0, "has_tip": 0, "tip_percentage": 0.0, "tip_label": "Propina"}
    return dict(row)


# ─── Formas de pago activas ───────────────────────────────────────────────────

@router.get("/payment-types")
async def get_payment_types(
    company_id: int  = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    rows = (await db.execute(text("""
        SELECT id, name, adds_to_cash, is_default, ask_notes
        FROM pos_payment_types
        WHERE company_id = :cid AND is_active = 1
        ORDER BY is_default DESC, name
    """), {"cid": company_id})).mappings().all()
    return [dict(r) for r in rows]


# ─── Impresoras POS de la empresa ────────────────────────────────────────────

@router.get("/printers")
async def get_printers(
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rows = (await db.execute(text("""
        SELECT id, name, ip, port, connection_type, is_active
        FROM pos_printers
        WHERE company_id = :cid AND is_active = 1
        ORDER BY id
    """), {"cid": company_id})).mappings().all()
    return [dict(r) for r in rows]


# ─── Registrar Recibo ─────────────────────────────────────────────────────────

@router.post("/ordenes/{orden_id}/recibo")
async def registrar_recibo(
    orden_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = body.get("company_id")
    pagos      = body.get("pagos", [])   # [{payment_method_id, amount, notes?}]

    if not company_id or not pagos:
        raise HTTPException(status_code=422, detail="company_id y pagos son requeridos")

    # ── Verificar orden ───────────────────────────────────────────────────────
    orden = (await db.execute(text("""
        SELECT id, estado FROM service_orders
        WHERE id = :oid AND company_id = :cid
    """), {"oid": orden_id, "cid": company_id})).mappings().first()

    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if orden["estado"] == "entregada":
        raise HTTPException(status_code=400, detail="La orden ya fue entregada/facturada")

    # ── Ítems de la orden ─────────────────────────────────────────────────────
    items = (await db.execute(text("""
        SELECT id, nombre, cantidad, precio_unitario AS precio,
               COALESCE(product_id, 0) AS producto_id
        FROM service_order_details
        WHERE order_id = :oid
    """), {"oid": orden_id})).mappings().all()

    subtotal = sum(float(it["precio"]) * float(it["cantidad"]) for it in items)

    # ── Config propina ────────────────────────────────────────────────────────
    cfg = (await db.execute(text("""
        SELECT COALESCE(has_tip, 0) AS has_tip,
               COALESCE(tip_percentage, 0) AS tip_percentage
        FROM company_configs WHERE company_id = :cid
    """), {"cid": company_id})).mappings().first()

    tip_amount = 0.0
    if cfg and cfg["has_tip"]:
        # Recibo: propina sobre el total de la cuenta (sin impuesto)
        tip_amount = round(subtotal * float(cfg["tip_percentage"]) / 100, 0)

    grand_total = subtotal + tip_amount

    # ── Validar suma de pagos ─────────────────────────────────────────────────
    total_pagado = sum(float(p.get("amount", 0)) for p in pagos)
    if abs(total_pagado - grand_total) > 1:   # tolerancia $1 por redondeo
        raise HTTPException(
            status_code=422,
            detail=f"La suma de pagos ({total_pagado}) no coincide con el total ({grand_total})"
        )

    # ── Generar número de recibo ──────────────────────────────────────────────
    rn_row = (await db.execute(text("""
        SELECT COALESCE(MAX(CAST(receipt_number AS UNSIGNED)), 0) + 1 AS next_rn
        FROM pos_receipts WHERE company_id = :cid
    """), {"cid": company_id})).mappings().first()
    receipt_number = str(int(rn_row["next_rn"]))

    now_bog = datetime.now(_BOG)
    fecha   = now_bog.date().isoformat()
    hora    = now_bog.strftime("%H:%M:%S")

    # ── Insertar pos_receipts ─────────────────────────────────────────────────
    await db.execute(text("""
        INSERT INTO pos_receipts
            (receipt_number, date, company_id, cash_amount, tip,
             amount_without_tip, employee_id, shift, time, time_text, voided, synced)
        VALUES
            (:rn, :fecha, :cid, :total, :tip,
             :subtotal, :uid, 1, :hora, :hora, 0, 0)
    """), {
        "rn": receipt_number, "fecha": fecha, "cid": company_id,
        "total": int(grand_total), "tip": int(tip_amount),
        "subtotal": int(subtotal),
        "uid": current_user.id if hasattr(current_user, "id") else 0,
        "hora": hora,
    })

    # ── Insertar pos_receipt_order_details ────────────────────────────────────
    for idx, it in enumerate(items, start=1):
        await db.execute(text("""
            INSERT INTO pos_receipt_order_details
                (order_number, date, receipt_number, dish_id, item,
                 quantity, amount, notes, complimentary, depends_on, synced, company_id)
            VALUES
                (:orden, :fecha, :rn, :dish_id, :item,
                 :qty, :amount, :notes, 0, 0, 0, :cid)
        """), {
            "orden": str(orden_id), "fecha": fecha, "rn": receipt_number,
            "dish_id": int(it["producto_id"] or 0), "item": idx,
            "qty": float(it["cantidad"]), "amount": int(it["precio"]),
            "notes": it["nombre"], "cid": company_id,
        })

    # ── Insertar pos_receipt_payment_methods ──────────────────────────────────
    for idx, pago in enumerate(pagos, start=1):
        await db.execute(text("""
            INSERT INTO pos_receipt_payment_methods
                (item, payment_method_id, card_id, invoice_number,
                 amount, date, order_number, notes, synced, company_id)
            VALUES
                (:item, :pm_id, 0, :rn,
                 :amount, :fecha, :orden, :notes, 0, :cid)
        """), {
            "item": idx,
            "pm_id": int(pago["payment_method_id"]),
            "rn": receipt_number,
            "amount": float(pago["amount"]),
            "fecha": fecha,
            "orden": str(orden_id),
            "notes": pago.get("notes", "") or "",
            "cid": company_id,
        })

    # ── Marcar orden como entregada ───────────────────────────────────────────
    await db.execute(text("""
        UPDATE service_orders
        SET estado = 'entregada'
        WHERE id = :oid AND company_id = :cid
    """), {"oid": orden_id, "cid": company_id})

    await db.commit()
    return {
        "receipt_number": receipt_number,
        "fecha": fecha,
        "hora": hora,
        "subtotal": subtotal,
        "tip": tip_amount,
        "total": grand_total,
        "items": [{"nombre": it["nombre"], "cantidad": float(it["cantidad"]), "precio": float(it["precio"])} for it in items],
    }


# ─── Imprimir recibo en impresora POS (socket TCP ESC/POS) ───────────────────

@router.post("/imprimir-pos")
async def imprimir_pos(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    import socket as _socket

    company_id     = body.get("company_id")
    printer_id     = body.get("printer_id")
    receipt_number = str(body.get("receipt_number", ""))

    if not company_id or not printer_id:
        raise HTTPException(status_code=422, detail="company_id y printer_id requeridos")

    # Datos de la impresora
    printer = (await db.execute(text("""
        SELECT name, ip, port FROM pos_printers
        WHERE id = :pid AND company_id = :cid AND is_active = 1
    """), {"pid": printer_id, "cid": company_id})).mappings().first()

    if not printer or not printer["ip"]:
        raise HTTPException(status_code=404, detail="Impresora no encontrada o sin IP configurada")

    # Datos del recibo
    receipt = (await db.execute(text("""
        SELECT r.receipt_number, r.date, r.cash_amount, r.tip, r.amount_without_tip
        FROM pos_receipts r
        WHERE r.receipt_number = :rn AND r.company_id = :cid
    """), {"rn": receipt_number, "cid": company_id})).mappings().first()

    items_r = (await db.execute(text("""
        SELECT notes AS nombre, quantity AS cantidad, amount AS precio
        FROM pos_receipt_order_details
        WHERE receipt_number = :rn AND company_id = :cid
    """), {"rn": receipt_number, "cid": company_id})).mappings().all()

    pagos_r = (await db.execute(text("""
        SELECT pt.name, prm.amount
        FROM pos_receipt_payment_methods prm
        LEFT JOIN pos_payment_types pt ON pt.id = prm.payment_method_id AND pt.company_id = prm.company_id
        WHERE prm.invoice_number = :rn AND prm.company_id = :cid
    """), {"rn": receipt_number, "cid": company_id})).mappings().all()

    company_name = (await db.execute(text(
        "SELECT name FROM companies WHERE id_company = :cid"
    ), {"cid": company_id})).scalar() or "EasyPos"

    # ── Construir texto ESC/POS ───────────────────────────────────────────────
    ESC = b'\x1b'
    INIT        = ESC + b'@'
    BOLD_ON     = ESC + b'\x45\x01'
    BOLD_OFF    = ESC + b'\x45\x00'
    CENTER      = ESC + b'\x61\x01'
    LEFT        = ESC + b'\x61\x00'
    LF          = b'\n'
    CUT         = ESC + b'\x69'          # cut parcial

    def line(txt="", bold=False, center=False):
        enc = (BOLD_ON if bold else b'') + (CENTER if center else LEFT)
        return enc + txt.encode('utf-8', errors='replace') + LF + (BOLD_OFF if bold else b'')

    def dline(left_txt, right_txt, width=32):
        spaces = max(1, width - len(left_txt) - len(right_txt))
        return LEFT + (left_txt + ' ' * spaces + right_txt).encode('utf-8', errors='replace') + LF

    buf = bytearray()
    buf += INIT
    buf += line(company_name, bold=True, center=True)
    buf += line("RECIBO DE VENTA", bold=True, center=True)
    buf += line(f"Recibo N°: {receipt_number}", center=True)
    if receipt:
        buf += line(f"Fecha: {receipt['date']}", center=True)
    buf += line("--------------------------------")
    for it in items_r:
        nombre = str(it["nombre"])[:24]
        total  = float(it["precio"]) * float(it["cantidad"])
        buf += dline(nombre, f"${int(total):,}")
    buf += line("--------------------------------")
    if receipt:
        buf += dline("Subtotal", f"${int(receipt['amount_without_tip']):,}")
        if receipt["tip"]:
            buf += dline("Propina", f"${int(receipt['tip']):,}")
    buf += line("", bold=True)
    total_val = receipt["cash_amount"] if receipt else 0
    buf += dline("TOTAL", f"${int(total_val):,}", width=32)
    buf += line("--------------------------------")
    for p in pagos_r:
        buf += dline(str(p["name"] or "Pago"), f"${int(p['amount']):,}")
    buf += line("--------------------------------")
    buf += line("Gracias por su preferencia!", center=True)
    buf += LF + LF + LF
    buf += CUT

    # ── Enviar via socket TCP ─────────────────────────────────────────────────
    try:
        with _socket.create_connection(
            (printer["ip"], int(printer["port"] or 9100)),
            timeout=5,
        ) as sock:
            sock.sendall(bytes(buf))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error al conectar con la impresora: {e}")

    return {"ok": True, "printer": printer["name"]}
