from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.auth.dependencies import get_current_user
from datetime import datetime, timezone, timedelta, date
from pydantic import BaseModel
from typing import Optional, List
import os, uuid, shutil
from pathlib import Path

router = APIRouter(prefix="/api/parqueadero", tags=["parqueadero"])

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads" / "parqueadero"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def bogota_now() -> datetime:
    return datetime.now(timezone(timedelta(hours=-5))).replace(tzinfo=None)


def bogota_today() -> str:
    return bogota_now().strftime('%Y-%m-%d')


# ── Utilidad: calcular valor a cobrar ─────────────────────────────────────────

def calcular_valor(servicio: dict, hora_ingreso: datetime) -> dict:
    """Retorna valor_cobrado y minutos_transcurridos según tipo_cobro del servicio."""
    ahora = bogota_now()
    minutos = max(0, int((ahora - hora_ingreso).total_seconds() / 60))

    tipo = servicio["tipo_cobro"]
    if tipo == "tarifa_plana":
        periodo = servicio.get("periodo_horas") or 12
        tarifa_base = float(servicio.get("tarifa_base") or 0)
        tarifa_adicional = float(servicio.get("tarifa_adicional") or 0)
        horas = minutos / 60
        if horas <= periodo:
            valor = tarifa_base
        else:
            periodos_extra = int((horas - periodo) / periodo) + 1
            valor = tarifa_base + periodos_extra * tarifa_adicional
    elif tipo == "por_minuto":
        tarifa_min = float(servicio.get("tarifa_minuto") or 0)
        valor = minutos * tarifa_min
    else:
        valor = 0.0

    return {"valor_cobrado": round(valor, 2), "minutos_transcurridos": minutos}


# ══════════════════════════════════════════════════════════════
# CATEGORÍAS
# ══════════════════════════════════════════════════════════════

class CategoriaBody(BaseModel):
    nombre: str
    icono: str = "bi-car-front-fill"
    color: str = "#3b82f6"
    orden: int = 0
    is_active: int = 1


@router.get("/categorias")
async def list_categorias(
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    rows = await db.execute(text(
        "SELECT * FROM parqueadero_categorias WHERE company_id = :cid ORDER BY orden, nombre"
    ), {"cid": company_id})
    return [dict(r) for r in rows.mappings()]


@router.post("/categorias")
async def create_categoria(
    company_id: int = Query(...),
    body: CategoriaBody = ...,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    r = await db.execute(text("""
        INSERT INTO parqueadero_categorias (company_id, nombre, icono, color, orden, is_active)
        VALUES (:cid, :n, :ic, :co, :or_, :a)
    """), {"cid": company_id, "n": body.nombre, "ic": body.icono, "co": body.color,
           "or_": body.orden, "a": body.is_active})
    await db.commit()
    return {"id": r.lastrowid, **body.dict()}


@router.put("/categorias/{cat_id}")
async def update_categoria(
    cat_id: int,
    company_id: int = Query(...),
    body: CategoriaBody = ...,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    await db.execute(text("""
        UPDATE parqueadero_categorias
        SET nombre=:n, icono=:ic, color=:co, orden=:or_, is_active=:a
        WHERE id=:id AND company_id=:cid
    """), {"n": body.nombre, "ic": body.icono, "co": body.color,
           "or_": body.orden, "a": body.is_active, "id": cat_id, "cid": company_id})
    await db.commit()
    return {"ok": True}


@router.delete("/categorias/{cat_id}")
async def delete_categoria(
    cat_id: int,
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    await db.execute(text(
        "DELETE FROM parqueadero_categorias WHERE id=:id AND company_id=:cid"
    ), {"id": cat_id, "cid": company_id})
    await db.commit()
    return {"ok": True}


# ══════════════════════════════════════════════════════════════
# SERVICIOS
# ══════════════════════════════════════════════════════════════

class ServicioBody(BaseModel):
    categoria_id: Optional[int] = None
    nombre: str
    tipo_cobro: str = "tarifa_plana"  # tarifa_plana | por_minuto | mensualidad
    tarifa_base: float = 0
    periodo_horas: Optional[int] = None
    tarifa_adicional: float = 0
    tarifa_minuto: float = 0
    plazas_total: int = 0
    is_active: int = 1


@router.get("/servicios")
async def list_servicios(
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    rows = await db.execute(text("""
        SELECT s.*, c.nombre AS categoria_nombre, c.color AS categoria_color
        FROM parqueadero_servicios s
        LEFT JOIN parqueadero_categorias c ON c.id = s.categoria_id
        WHERE s.company_id = :cid
        ORDER BY s.nombre
    """), {"cid": company_id})
    return [dict(r) for r in rows.mappings()]


@router.post("/servicios")
async def create_servicio(
    company_id: int = Query(...),
    body: ServicioBody = ...,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    r = await db.execute(text("""
        INSERT INTO parqueadero_servicios
            (company_id, categoria_id, nombre, tipo_cobro, tarifa_base,
             periodo_horas, tarifa_adicional, tarifa_minuto, plazas_total, is_active)
        VALUES (:cid, :cat, :n, :tc, :tb, :ph, :ta, :tm, :pt, :a)
    """), {
        "cid": company_id, "cat": body.categoria_id, "n": body.nombre,
        "tc": body.tipo_cobro, "tb": body.tarifa_base, "ph": body.periodo_horas,
        "ta": body.tarifa_adicional, "tm": body.tarifa_minuto,
        "pt": body.plazas_total, "a": body.is_active,
    })
    await db.commit()
    return {"id": r.lastrowid, **body.dict()}


@router.put("/servicios/{svc_id}")
async def update_servicio(
    svc_id: int,
    company_id: int = Query(...),
    body: ServicioBody = ...,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    await db.execute(text("""
        UPDATE parqueadero_servicios
        SET categoria_id=:cat, nombre=:n, tipo_cobro=:tc, tarifa_base=:tb,
            periodo_horas=:ph, tarifa_adicional=:ta, tarifa_minuto=:tm,
            plazas_total=:pt, is_active=:a
        WHERE id=:id AND company_id=:cid
    """), {
        "cat": body.categoria_id, "n": body.nombre, "tc": body.tipo_cobro,
        "tb": body.tarifa_base, "ph": body.periodo_horas, "ta": body.tarifa_adicional,
        "tm": body.tarifa_minuto, "pt": body.plazas_total, "a": body.is_active,
        "id": svc_id, "cid": company_id,
    })
    await db.commit()
    return {"ok": True}


@router.delete("/servicios/{svc_id}")
async def delete_servicio(
    svc_id: int,
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    await db.execute(text(
        "DELETE FROM parqueadero_servicios WHERE id=:id AND company_id=:cid"
    ), {"id": svc_id, "cid": company_id})
    await db.commit()
    return {"ok": True}


# ══════════════════════════════════════════════════════════════
# INGRESOS (entrada de vehículos)
# ══════════════════════════════════════════════════════════════

class IngresoBody(BaseModel):
    placa: str
    servicio_id: int
    foto_url: Optional[str] = None


@router.get("/ingresos")
async def list_ingresos(
    company_id: int = Query(...),
    estado: str = Query("activo"),
    fecha: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    fecha_filtro = fecha or bogota_today()
    rows = await db.execute(text("""
        SELECT i.*, s.nombre AS servicio_nombre, s.tipo_cobro, s.tarifa_base,
               s.periodo_horas, s.tarifa_adicional, s.tarifa_minuto,
               c.nombre AS categoria_nombre, c.color AS categoria_color,
               u.name AS registrado_por_nombre
        FROM parqueadero_ingresos i
        JOIN parqueadero_servicios s ON s.id = i.servicio_id
        LEFT JOIN parqueadero_categorias c ON c.id = s.categoria_id
        LEFT JOIN users u ON u.id = i.registrado_por
        WHERE i.company_id = :cid
          AND i.estado = :est
          AND DATE(i.hora_ingreso) = :fecha
        ORDER BY i.hora_ingreso DESC
    """), {"cid": company_id, "est": estado, "fecha": fecha_filtro})
    items = [dict(r) for r in rows.mappings()]
    # Calcular valor en tiempo real para activos
    for item in items:
        if item["estado"] == "activo":
            svc = {k: item[k] for k in ("tipo_cobro", "tarifa_base", "periodo_horas", "tarifa_adicional", "tarifa_minuto")}
            calc = calcular_valor(svc, item["hora_ingreso"])
            item["valor_actual"] = calc["valor_cobrado"]
            item["minutos_transcurridos"] = calc["minutos_transcurridos"]
        else:
            item["valor_actual"] = None
            item["minutos_transcurridos"] = None
    return items


@router.post("/ingresos")
async def create_ingreso(
    company_id: int = Query(...),
    body: IngresoBody = ...,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    qr_token = str(uuid.uuid4()).replace("-", "")[:20].upper()
    r = await db.execute(text("""
        INSERT INTO parqueadero_ingresos
            (company_id, placa, servicio_id, hora_ingreso, foto_url, qr_token, estado, registrado_por)
        VALUES (:cid, :pl, :svc, :hi, :fu, :qr, 'activo', :usr)
    """), {
        "cid": company_id, "pl": body.placa.upper().strip(), "svc": body.servicio_id,
        "hi": bogota_now(), "fu": body.foto_url, "qr": qr_token,
        "usr": current_user["id"],
    })
    await db.commit()
    ingreso_id = r.lastrowid
    return {"id": ingreso_id, "qr_token": qr_token, "placa": body.placa.upper().strip()}


@router.get("/ingresos/{ingreso_id}")
async def get_ingreso(
    ingreso_id: int,
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    row = await db.execute(text("""
        SELECT i.*, s.nombre AS servicio_nombre, s.tipo_cobro, s.tarifa_base,
               s.periodo_horas, s.tarifa_adicional, s.tarifa_minuto,
               u.name AS registrado_por_nombre
        FROM parqueadero_ingresos i
        JOIN parqueadero_servicios s ON s.id = i.servicio_id
        LEFT JOIN users u ON u.id = i.registrado_por
        WHERE i.id = :id AND i.company_id = :cid
    """), {"id": ingreso_id, "cid": company_id})
    item = row.mappings().first()
    if not item:
        raise HTTPException(404, "Ingreso no encontrado")
    item = dict(item)
    if item["estado"] == "activo":
        svc = {k: item[k] for k in ("tipo_cobro", "tarifa_base", "periodo_horas", "tarifa_adicional", "tarifa_minuto")}
        calc = calcular_valor(svc, item["hora_ingreso"])
        item["valor_actual"] = calc["valor_cobrado"]
        item["minutos_transcurridos"] = calc["minutos_transcurridos"]
    return item


@router.get("/ingresos/by-qr/{qr_token}")
async def get_ingreso_by_qr(
    qr_token: str,
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    row = await db.execute(text("""
        SELECT i.*, s.nombre AS servicio_nombre, s.tipo_cobro, s.tarifa_base,
               s.periodo_horas, s.tarifa_adicional, s.tarifa_minuto,
               u.name AS registrado_por_nombre
        FROM parqueadero_ingresos i
        JOIN parqueadero_servicios s ON s.id = i.servicio_id
        LEFT JOIN users u ON u.id = i.registrado_por
        WHERE i.qr_token = :qr AND i.company_id = :cid AND i.estado = 'activo'
    """), {"qr": qr_token.upper(), "cid": company_id})
    item = row.mappings().first()
    if not item:
        raise HTTPException(404, "Token no encontrado o vehículo ya salió")
    item = dict(item)
    svc = {k: item[k] for k in ("tipo_cobro", "tarifa_base", "periodo_horas", "tarifa_adicional", "tarifa_minuto")}
    calc = calcular_valor(svc, item["hora_ingreso"])
    item["valor_actual"] = calc["valor_cobrado"]
    item["minutos_transcurridos"] = calc["minutos_transcurridos"]
    return item


class PagoBody(BaseModel):
    valor_cobrado: float
    forma_pago: str = "efectivo"


@router.post("/ingresos/{ingreso_id}/pagar")
async def pagar_ingreso(
    ingreso_id: int,
    company_id: int = Query(...),
    body: PagoBody = ...,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Verificar que el ingreso existe y está activo
    chk = await db.execute(text(
        "SELECT id, hora_ingreso, servicio_id FROM parqueadero_ingresos "
        "WHERE id=:id AND company_id=:cid AND estado='activo'"
    ), {"id": ingreso_id, "cid": company_id})
    row = chk.mappings().first()
    if not row:
        raise HTTPException(404, "Ingreso no encontrado o ya procesado")

    hora_salida = bogota_now()
    minutos = max(0, int((hora_salida - row["hora_ingreso"]).total_seconds() / 60))

    # Registrar pago
    await db.execute(text("""
        INSERT INTO parqueadero_pagos
            (ingreso_id, company_id, hora_salida, minutos_transcurridos, valor_cobrado, forma_pago, registrado_por)
        VALUES (:iid, :cid, :hs, :min, :val, :fp, :usr)
    """), {
        "iid": ingreso_id, "cid": company_id, "hs": hora_salida,
        "min": minutos, "val": body.valor_cobrado, "fp": body.forma_pago,
        "usr": current_user["id"],
    })
    # Marcar ingreso como pagado
    await db.execute(text(
        "UPDATE parqueadero_ingresos SET estado='pagado' WHERE id=:id"
    ), {"id": ingreso_id})
    await db.commit()
    return {"ok": True, "hora_salida": hora_salida.isoformat(), "valor_cobrado": body.valor_cobrado}


@router.put("/ingresos/{ingreso_id}/cancelar")
async def cancelar_ingreso(
    ingreso_id: int,
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    await db.execute(text(
        "UPDATE parqueadero_ingresos SET estado='cancelado' WHERE id=:id AND company_id=:cid"
    ), {"id": ingreso_id, "cid": company_id})
    await db.commit()
    return {"ok": True}


# ── Upload foto de ingreso ─────────────────────────────────────────────────────

@router.post("/ingresos/foto")
async def upload_foto_ingreso(
    company_id: int = Query(...),
    file: UploadFile = File(...),
    _=Depends(get_current_user),
):
    ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    if ext not in (".jpg", ".jpeg", ".png", ".webp"):
        raise HTTPException(400, "Formato no permitido")
    fname = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOADS_DIR / fname
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"url": f"/uploads/parqueadero/{fname}"}


# ══════════════════════════════════════════════════════════════
# STATS / DASHBOARD KPIs
# ══════════════════════════════════════════════════════════════

@router.get("/stats")
async def get_stats(
    company_id: int = Query(...),
    fecha: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    fecha_filtro = fecha or bogota_today()

    # Vehículos activos en este momento
    activos_r = await db.execute(text("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN s.tipo_cobro = 'mensualidad' THEN 1 ELSE 0 END) AS mensualidades_activas
        FROM parqueadero_ingresos i
        JOIN parqueadero_servicios s ON s.id = i.servicio_id
        WHERE i.company_id = :cid AND i.estado = 'activo'
    """), {"cid": company_id})
    activos = dict(activos_r.mappings().first() or {})

    # Ingresos del día (pagados)
    ingresos_r = await db.execute(text("""
        SELECT COUNT(*) AS total_salidas, COALESCE(SUM(valor_cobrado), 0) AS recaudo_dia
        FROM parqueadero_pagos
        WHERE company_id = :cid AND DATE(hora_salida) = :fecha
    """), {"cid": company_id, "fecha": fecha_filtro})
    ingresos = dict(ingresos_r.mappings().first() or {})

    # Entradas del día
    entradas_r = await db.execute(text("""
        SELECT COUNT(*) AS entradas_dia
        FROM parqueadero_ingresos
        WHERE company_id = :cid AND DATE(hora_ingreso) = :fecha
    """), {"cid": company_id, "fecha": fecha_filtro})
    entradas = dict(entradas_r.mappings().first() or {})

    # Plazas totales por servicio
    plazas_r = await db.execute(text("""
        SELECT COALESCE(SUM(plazas_total), 0) AS plazas_totales
        FROM parqueadero_servicios
        WHERE company_id = :cid AND is_active = 1 AND tipo_cobro != 'mensualidad'
    """), {"cid": company_id})
    plazas = dict(plazas_r.mappings().first() or {})

    # Mensualidades morosas
    morosos_r = await db.execute(text("""
        SELECT COUNT(*) AS morosos
        FROM parqueadero_mensualidades
        WHERE company_id = :cid AND estado = 'moroso'
    """), {"cid": company_id})
    morosos = dict(morosos_r.mappings().first() or {})

    return {
        "vehiculos_activos": int(activos.get("total") or 0),
        "mensualidades_activas_entrada": int(activos.get("mensualidades_activas") or 0),
        "plazas_totales": int(plazas.get("plazas_totales") or 0),
        "plazas_disponibles": max(0, int(plazas.get("plazas_totales") or 0) - int(activos.get("total") or 0)),
        "entradas_dia": int(entradas.get("entradas_dia") or 0),
        "salidas_dia": int(ingresos.get("total_salidas") or 0),
        "recaudo_dia": float(ingresos.get("recaudo_dia") or 0),
        "morosos": int(morosos.get("morosos") or 0),
    }


# ══════════════════════════════════════════════════════════════
# MENSUALIDADES
# ══════════════════════════════════════════════════════════════

class MensualidadBody(BaseModel):
    client_id: Optional[int] = None
    placa: str
    tipo_vehiculo: str = "auto"
    nombre_titular: str
    documento: Optional[str] = None
    telefono: Optional[str] = None
    fecha_inicio: str
    fecha_fin: str
    valor_mensualidad: float = 0
    observaciones: Optional[str] = None


@router.get("/mensualidades")
async def list_mensualidades(
    company_id: int = Query(...),
    estado: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    where = "WHERE m.company_id = :cid"
    params: dict = {"cid": company_id}
    if estado:
        where += " AND m.estado = :est"
        params["est"] = estado
    if q:
        where += " AND (m.placa LIKE :q OR m.nombre_titular LIKE :q OR m.documento LIKE :q)"
        params["q"] = f"%{q}%"

    rows = await db.execute(text(f"""
        SELECT m.*,
               DATEDIFF(m.fecha_fin, CURDATE()) AS dias_restantes,
               (SELECT MAX(fecha_pago) FROM parqueadero_mensualidad_pagos p2
                WHERE p2.mensualidad_id = m.id) AS ultimo_pago
        FROM parqueadero_mensualidades m
        {where}
        ORDER BY m.estado, m.fecha_fin
    """), params)
    return [dict(r) for r in rows.mappings()]


@router.post("/mensualidades")
async def create_mensualidad(
    company_id: int = Query(...),
    body: MensualidadBody = ...,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    r = await db.execute(text("""
        INSERT INTO parqueadero_mensualidades
            (company_id, client_id, placa, tipo_vehiculo, nombre_titular,
             documento, telefono, fecha_inicio, fecha_fin, valor_mensualidad,
             estado, observaciones)
        VALUES (:cid, :cli, :pl, :tv, :nt, :doc, :tel, :fi, :ff, :val, 'activo', :obs)
    """), {
        "cid": company_id, "cli": body.client_id,
        "pl": body.placa.upper().strip(), "tv": body.tipo_vehiculo,
        "nt": body.nombre_titular, "doc": body.documento,
        "tel": body.telefono, "fi": body.fecha_inicio,
        "ff": body.fecha_fin, "val": body.valor_mensualidad,
        "obs": body.observaciones,
    })
    await db.commit()
    return {"id": r.lastrowid}


@router.get("/mensualidades/{men_id}")
async def get_mensualidad(
    men_id: int,
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    row = await db.execute(text("""
        SELECT m.*, DATEDIFF(m.fecha_fin, CURDATE()) AS dias_restantes
        FROM parqueadero_mensualidades m
        WHERE m.id = :id AND m.company_id = :cid
    """), {"id": men_id, "cid": company_id})
    item = row.mappings().first()
    if not item:
        raise HTTPException(404, "Mensualidad no encontrada")
    data = dict(item)

    # Fotos
    fotos_r = await db.execute(text(
        "SELECT * FROM parqueadero_mensualidad_fotos WHERE mensualidad_id = :id ORDER BY created_at"
    ), {"id": men_id})
    data["fotos"] = [dict(f) for f in fotos_r.mappings()]

    # Pagos
    pagos_r = await db.execute(text("""
        SELECT p.*, u.name AS registrado_por_nombre
        FROM parqueadero_mensualidad_pagos p
        LEFT JOIN users u ON u.id = p.registrado_por
        WHERE p.mensualidad_id = :id
        ORDER BY p.fecha_pago DESC
    """), {"id": men_id})
    data["pagos"] = [dict(p) for p in pagos_r.mappings()]

    return data


@router.put("/mensualidades/{men_id}")
async def update_mensualidad(
    men_id: int,
    company_id: int = Query(...),
    body: MensualidadBody = ...,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    await db.execute(text("""
        UPDATE parqueadero_mensualidades
        SET client_id=:cli, placa=:pl, tipo_vehiculo=:tv, nombre_titular=:nt,
            documento=:doc, telefono=:tel, fecha_inicio=:fi, fecha_fin=:ff,
            valor_mensualidad=:val, observaciones=:obs
        WHERE id=:id AND company_id=:cid
    """), {
        "cli": body.client_id, "pl": body.placa.upper().strip(),
        "tv": body.tipo_vehiculo, "nt": body.nombre_titular,
        "doc": body.documento, "tel": body.telefono,
        "fi": body.fecha_inicio, "ff": body.fecha_fin,
        "val": body.valor_mensualidad, "obs": body.observaciones,
        "id": men_id, "cid": company_id,
    })
    await db.commit()
    return {"ok": True}


@router.patch("/mensualidades/{men_id}/estado")
async def cambiar_estado_mensualidad(
    men_id: int,
    company_id: int = Query(...),
    estado: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    if estado not in ("activo", "moroso", "retirado"):
        raise HTTPException(400, "Estado inválido")
    await db.execute(text(
        "UPDATE parqueadero_mensualidades SET estado=:est WHERE id=:id AND company_id=:cid"
    ), {"est": estado, "id": men_id, "cid": company_id})
    await db.commit()
    return {"ok": True}


# ── Pagos de mensualidades ─────────────────────────────────────────────────────

class MensualidadPagoBody(BaseModel):
    fecha_pago: str
    periodo_desde: str
    periodo_hasta: str
    valor_pagado: float
    forma_pago: str = "efectivo"
    observacion: Optional[str] = None


@router.post("/mensualidades/{men_id}/pagos")
async def registrar_pago_mensualidad(
    men_id: int,
    company_id: int = Query(...),
    body: MensualidadPagoBody = ...,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    r = await db.execute(text("""
        INSERT INTO parqueadero_mensualidad_pagos
            (mensualidad_id, company_id, fecha_pago, periodo_desde, periodo_hasta,
             valor_pagado, forma_pago, registrado_por, observacion)
        VALUES (:mid, :cid, :fp, :pd, :ph, :val, :fpa, :usr, :obs)
    """), {
        "mid": men_id, "cid": company_id, "fp": body.fecha_pago,
        "pd": body.periodo_desde, "ph": body.periodo_hasta,
        "val": body.valor_pagado, "fpa": body.forma_pago,
        "usr": current_user["id"], "obs": body.observacion,
    })
    # Si pagó, mover a activo automáticamente
    await db.execute(text(
        "UPDATE parqueadero_mensualidades SET estado='activo', fecha_fin=:ff "
        "WHERE id=:id AND company_id=:cid"
    ), {"ff": body.periodo_hasta, "id": men_id, "cid": company_id})
    await db.commit()
    return {"id": r.lastrowid, "ok": True}


@router.delete("/mensualidades/pagos/{pago_id}")
async def delete_pago_mensualidad(
    pago_id: int,
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    await db.execute(text(
        "DELETE FROM parqueadero_mensualidad_pagos WHERE id=:id AND company_id=:cid"
    ), {"id": pago_id, "cid": company_id})
    await db.commit()
    return {"ok": True}


# ── Fotos de mensualidades ─────────────────────────────────────────────────────

@router.post("/mensualidades/{men_id}/fotos")
async def upload_foto_mensualidad(
    men_id: int,
    company_id: int = Query(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    if ext not in (".jpg", ".jpeg", ".png", ".webp"):
        raise HTTPException(400, "Formato no permitido")
    subdir = UPLOADS_DIR / "mensualidades"
    subdir.mkdir(parents=True, exist_ok=True)
    fname = f"{uuid.uuid4().hex}{ext}"
    with open(subdir / fname, "wb") as f:
        shutil.copyfileobj(file.file, f)
    url = f"/uploads/parqueadero/mensualidades/{fname}"
    await db.execute(text(
        "INSERT INTO parqueadero_mensualidad_fotos (mensualidad_id, url, tipo) VALUES (:mid, :url, 'evidencia')"
    ), {"mid": men_id, "url": url})
    await db.commit()
    return {"url": url}


@router.delete("/mensualidades/fotos/{foto_id}")
async def delete_foto_mensualidad(
    foto_id: int,
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    row = await db.execute(text(
        "SELECT url FROM parqueadero_mensualidad_fotos WHERE id=:id"
    ), {"id": foto_id})
    foto = row.mappings().first()
    if foto:
        path = Path(__file__).resolve().parent.parent.parent.parent / foto["url"].lstrip("/")
        if path.exists():
            path.unlink(missing_ok=True)
        await db.execute(text(
            "DELETE FROM parqueadero_mensualidad_fotos WHERE id=:id"
        ), {"id": foto_id})
        await db.commit()
    return {"ok": True}


# ── Morosos ────────────────────────────────────────────────────────────────────

@router.get("/morosos")
async def list_morosos(
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    rows = await db.execute(text("""
        SELECT m.*,
               DATEDIFF(CURDATE(), m.fecha_fin) AS dias_mora,
               (SELECT MAX(fecha_pago) FROM parqueadero_mensualidad_pagos p2
                WHERE p2.mensualidad_id = m.id) AS ultimo_pago
        FROM parqueadero_mensualidades m
        WHERE m.company_id = :cid
          AND (m.estado = 'moroso' OR (m.estado = 'activo' AND m.fecha_fin < CURDATE()))
        ORDER BY dias_mora DESC
    """), {"cid": company_id})
    return [dict(r) for r in rows.mappings()]
