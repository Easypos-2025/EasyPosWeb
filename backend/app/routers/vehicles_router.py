from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


# ══════════════════════════════════════════════════════════════════════════════
# PROPIETARIOS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/propietarios")
async def listar_propietarios(
    company_id: int = Query(...),
    q: str          = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    filtros = {"cid": company_id}
    where   = ["company_id = :cid"]
    if q:
        where.append("(nombre LIKE :q OR documento LIKE :q OR telefono LIKE :q)")
        filtros["q"] = f"%{q}%"
    rows = await db.execute(text(f"""
        SELECT id, company_id, nombre, documento, telefono, email,
               (SELECT COUNT(*) FROM vehicles v WHERE v.propietario_id = propietarios.id) AS total_vehiculos
        FROM propietarios
        WHERE {" AND ".join(where)}
        ORDER BY nombre
        LIMIT 100
    """), filtros)
    return [dict(r) for r in rows.mappings()]


@router.post("/propietarios")
async def crear_propietario(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    company_id = payload.get("company_id")
    nombre     = (payload.get("nombre") or "").strip()
    if not company_id or not nombre:
        raise HTTPException(400, detail="company_id y nombre son requeridos")

    r = await db.execute(text("""
        INSERT INTO propietarios (company_id, nombre, documento, telefono, email)
        VALUES (:cid, :nom, :doc, :tel, :email)
    """), {
        "cid":   company_id,
        "nom":   nombre,
        "doc":   payload.get("documento"),
        "tel":   payload.get("telefono"),
        "email": payload.get("email"),
    })
    await db.commit()
    return {"id": r.lastrowid, "nombre": nombre}


@router.put("/propietarios/{pid}")
async def actualizar_propietario(
    pid: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    company_id = payload.get("company_id")
    chk = await db.execute(text(
        "SELECT id FROM propietarios WHERE id=:pid AND company_id=:cid"
    ), {"pid": pid, "cid": company_id})
    if not chk.scalar():
        raise HTTPException(404, detail="Propietario no encontrado")

    await db.execute(text("""
        UPDATE propietarios
        SET nombre=:nom, documento=:doc, telefono=:tel, email=:email
        WHERE id=:pid
    """), {
        "pid":   pid,
        "nom":   payload.get("nombre"),
        "doc":   payload.get("documento"),
        "tel":   payload.get("telefono"),
        "email": payload.get("email"),
    })
    await db.commit()
    return {"ok": True}


# ══════════════════════════════════════════════════════════════════════════════
# VEHÍCULOS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/")
async def listar_vehiculos(
    company_id:    int  = Query(...),
    q:             str  = Query(None),
    propietario_id: int = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Lista vehículos de la empresa. Busca por placa o nombre/documento del propietario."""
    filtros = {"cid": company_id}
    where   = ["v.company_id = :cid", "v.is_active = 1"]

    if q:
        where.append("(v.placa LIKE :q OR v.marca LIKE :q OR v.modelo LIKE :q OR p.nombre LIKE :q OR p.documento LIKE :q)")
        filtros["q"] = f"%{q.upper()}%"
    if propietario_id:
        where.append("v.propietario_id = :pid")
        filtros["pid"] = propietario_id

    rows = await db.execute(text(f"""
        SELECT
            v.id, v.company_id, v.placa, v.marca, v.modelo, v.anio, v.color,
            v.km_actual, v.vehicle_type_id, v.foto_url, v.is_active,
            vt.nombre  AS tipo_nombre,
            v.propietario_id,
            p.nombre   AS propietario_nombre,
            p.documento AS propietario_documento,
            p.telefono  AS propietario_telefono,
            p.email     AS propietario_email,
            (SELECT COUNT(*) FROM service_orders so
             WHERE so.vehicle_ref_id = v.id) AS total_ordenes_taller,
            (SELECT COUNT(*) FROM parking_orders po
             WHERE po.vehicle_id = v.id)     AS total_ordenes_parking,
            v.created_at
        FROM  vehicles v
        LEFT JOIN vehicle_types vt ON vt.id = v.vehicle_type_id
        LEFT JOIN propietarios  p  ON p.id  = v.propietario_id
        WHERE {" AND ".join(where)}
        ORDER BY v.placa
        LIMIT 200
    """), filtros)
    return [dict(r) for r in rows.mappings()]


@router.get("/{vid}")
async def obtener_vehiculo(
    vid: int,
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    row = await db.execute(text("""
        SELECT
            v.id, v.company_id, v.placa, v.marca, v.modelo, v.anio, v.color,
            v.km_actual, v.vehicle_type_id, v.foto_url, v.is_active,
            vt.nombre  AS tipo_nombre,
            v.propietario_id,
            p.nombre   AS propietario_nombre,
            p.documento AS propietario_documento,
            p.telefono  AS propietario_telefono,
            p.email     AS propietario_email
        FROM  vehicles v
        LEFT JOIN vehicle_types vt ON vt.id = v.vehicle_type_id
        LEFT JOIN propietarios  p  ON p.id  = v.propietario_id
        WHERE v.id = :vid AND v.company_id = :cid
    """), {"vid": vid, "cid": company_id})
    v = row.mappings().first()
    if not v:
        raise HTTPException(404, detail="Vehículo no encontrado")
    return dict(v)


@router.get("/{vid}/historial")
async def historial_vehiculo(
    vid: int,
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Historial completo del vehículo: órdenes de taller + parking ordenadas por fecha."""
    ordenes_taller = await db.execute(text("""
        SELECT
            so.id, 'taller' AS origen,
            so.numero_orden, so.fecha_ingreso AS fecha,
            so.estado, so.diagnostico, so.trabajo_realizado,
            so.km_ingreso, so.km_salida,
            u.nombre AS responsable,
            (SELECT SUM(d.subtotal) FROM service_order_details d WHERE d.order_id = so.id) AS total
        FROM service_orders so
        LEFT JOIN users u ON u.id = so.jefe_responsable_id
        WHERE so.vehicle_ref_id = :vid AND so.company_id = :cid
        ORDER BY so.fecha_ingreso DESC
        LIMIT 50
    """), {"vid": vid, "cid": company_id})

    ordenes_parking = await db.execute(text("""
        SELECT
            po.id, 'parking' AS origen,
            po.numero_orden, po.hora_ingreso AS fecha,
            po.estado, NULL AS diagnostico, NULL AS trabajo_realizado,
            NULL AS km_ingreso, NULL AS km_salida,
            u.nombre AS responsable,
            NULL AS total
        FROM parking_orders po
        LEFT JOIN users u ON u.id = po.registrado_por
        WHERE po.vehicle_id = :vid AND po.company_id = :cid
        ORDER BY po.hora_ingreso DESC
        LIMIT 50
    """), {"vid": vid, "cid": company_id})

    historial = (
        [dict(r) for r in ordenes_taller.mappings()] +
        [dict(r) for r in ordenes_parking.mappings()]
    )
    historial.sort(key=lambda x: x["fecha"] or "", reverse=True)

    fotos = await db.execute(text("""
        SELECT id, photo_url, tipo, created_at
        FROM vehicle_photos
        WHERE company_id = :cid AND asset_id IN (
            SELECT asset_id FROM talleres_vehiculo_ext
            WHERE company_id = :cid AND placa = (
                SELECT placa FROM vehicles WHERE id = :vid
            )
        )
        ORDER BY created_at DESC
        LIMIT 30
    """), {"vid": vid, "cid": company_id})

    return {
        "historial": historial,
        "fotos":     [dict(r) for r in fotos.mappings()],
    }


@router.post("/")
async def crear_vehiculo(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    company_id = payload.get("company_id")
    placa      = (payload.get("placa") or "").strip().upper()
    if not company_id or not placa:
        raise HTTPException(400, detail="company_id y placa son requeridos")

    existe = await db.execute(text(
        "SELECT id FROM vehicles WHERE company_id=:cid AND placa=:p"
    ), {"cid": company_id, "p": placa})
    if existe.scalar():
        raise HTTPException(409, detail="Ya existe un vehículo con esa placa en esta empresa")

    # Crear o reutilizar propietario
    propietario_id = payload.get("propietario_id")
    if not propietario_id and payload.get("propietario_nombre"):
        r_p = await db.execute(text("""
            INSERT INTO propietarios (company_id, nombre, documento, telefono, email)
            VALUES (:cid, :nom, :doc, :tel, :email)
        """), {
            "cid":   company_id,
            "nom":   payload["propietario_nombre"].strip(),
            "doc":   payload.get("propietario_documento"),
            "tel":   payload.get("propietario_telefono"),
            "email": payload.get("propietario_email"),
        })
        propietario_id = r_p.lastrowid

    r = await db.execute(text("""
        INSERT INTO vehicles
            (company_id, placa, propietario_id, vehicle_type_id,
             marca, modelo, anio, color, km_actual, foto_url)
        VALUES
            (:cid, :placa, :pid, :vtid,
             :marca, :modelo, :anio, :color, :km, :foto)
    """), {
        "cid":   company_id,
        "placa": placa,
        "pid":   propietario_id,
        "vtid":  payload.get("vehicle_type_id"),
        "marca": payload.get("marca"),
        "modelo": payload.get("modelo"),
        "anio":  payload.get("anio"),
        "color": payload.get("color"),
        "km":    payload.get("km_actual", 0),
        "foto":  payload.get("foto_url"),
    })
    await db.commit()
    return {"id": r.lastrowid, "placa": placa}


@router.put("/{vid}")
async def actualizar_vehiculo(
    vid: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    company_id = payload.get("company_id")
    chk = await db.execute(text(
        "SELECT id FROM vehicles WHERE id=:vid AND company_id=:cid"
    ), {"vid": vid, "cid": company_id})
    if not chk.scalar():
        raise HTTPException(404, detail="Vehículo no encontrado")

    # Si vienen datos de propietario nuevo, crearlo
    propietario_id = payload.get("propietario_id")
    if not propietario_id and payload.get("propietario_nombre"):
        r_p = await db.execute(text("""
            INSERT INTO propietarios (company_id, nombre, documento, telefono, email)
            VALUES (:cid, :nom, :doc, :tel, :email)
        """), {
            "cid":   company_id,
            "nom":   payload["propietario_nombre"].strip(),
            "doc":   payload.get("propietario_documento"),
            "tel":   payload.get("propietario_telefono"),
            "email": payload.get("propietario_email"),
        })
        propietario_id = r_p.lastrowid

    await db.execute(text("""
        UPDATE vehicles SET
            propietario_id  = :pid,
            vehicle_type_id = :vtid,
            marca           = :marca,
            modelo          = :modelo,
            anio            = :anio,
            color           = :color,
            km_actual       = :km,
            foto_url        = :foto,
            is_active       = :active
        WHERE id = :vid
    """), {
        "vid":   vid,
        "pid":   propietario_id,
        "vtid":  payload.get("vehicle_type_id"),
        "marca": payload.get("marca"),
        "modelo": payload.get("modelo"),
        "anio":  payload.get("anio"),
        "color": payload.get("color"),
        "km":    payload.get("km_actual", 0),
        "foto":  payload.get("foto_url"),
        "active": payload.get("is_active", 1),
    })
    await db.commit()
    return {"ok": True}


@router.get("/placa/{placa}")
async def buscar_por_placa(
    placa: str,
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Búsqueda rápida por placa (para autocompletar en órdenes)."""
    placa_up = placa.strip().upper()
    rows = await db.execute(text("""
        SELECT
            v.id, v.placa, v.marca, v.modelo, v.anio, v.color,
            v.km_actual, v.foto_url,
            vt.nombre AS tipo_nombre,
            p.nombre  AS propietario_nombre,
            p.telefono AS propietario_telefono,
            p.documento AS propietario_documento
        FROM  vehicles v
        LEFT JOIN vehicle_types vt ON vt.id = v.vehicle_type_id
        LEFT JOIN propietarios  p  ON p.id  = v.propietario_id
        WHERE v.company_id = :cid AND v.placa LIKE :q AND v.is_active = 1
        ORDER BY v.placa
        LIMIT 10
    """), {"cid": company_id, "q": f"%{placa_up}%"})
    return [dict(r) for r in rows.mappings()]
