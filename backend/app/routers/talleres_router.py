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
            (SELECT COUNT(*) FROM service_participants sp
             WHERE sp.product_id = p.id AND sp.company_id = p.company_id) AS num_participantes
        FROM products p
        LEFT JOIN product_categories cat ON cat.id = p.category_id
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
