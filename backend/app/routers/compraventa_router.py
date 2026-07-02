import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.database import get_db, get_ext_session
from app.models.company_model import Company
from app.models.compraventa_foto_model import CompraventaFoto
from app.utils.storage import upload_file, delete_file
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/compraventa", tags=["compraventa"])


# ── Helper: obtener sesión BD externa ────────────────────────────────────────

async def _get_ext(company_id: int, db: AsyncSession):
    result = await db.execute(select(Company).where(Company.id_company == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    if not company.ext_db_host:
        raise HTTPException(status_code=400, detail="Esta empresa no tiene base de datos externa configurada")
    return get_ext_session(
        company_id,
        company.ext_db_host,
        company.ext_db_port or 3306,
        company.ext_db_name,
        company.ext_db_user,
        company.ext_db_password or "",
    )


# ── Movimientos diarios ───────────────────────────────────────────────────────

@router.get("/movimientos")
async def get_movimientos(
    company_id: int = Query(...),
    fecha: str      = Query(...),
    db: AsyncSession = Depends(get_db),
):
    ext = await _get_ext(company_id, db)
    async with ext as session:
        rows = await session.execute(text("""
            SELECT nro_movimiento, fecha_movimiento, nro_transaccion,
                   valor_movimiento, descripcion
            FROM movimientos_diarios
            WHERE DATE(fecha_movimiento) = :fecha
            ORDER BY descripcion, nro_movimiento DESC
        """), {"fecha": fecha})
        records = [dict(r) for r in rows.mappings()]
    return {"fecha": fecha, "total": len(records), "movimientos": records}


# ── Contratos por cédula (para selector) ─────────────────────────────────────

@router.get("/contratos-por-cedula")
async def contratos_por_cedula(
    company_id: int = Query(...),
    cedula: str     = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    ext = await _get_ext(company_id, db)
    async with ext as session:
        rows = await session.execute(text("""
            SELECT c.nro_contrato, c.cedula, c.fecha_inicio, c.fecha_final,
                   c.valor_contrato, c.estado,
                   COALESCE(ec.descripcion, c.estado) AS estado_descripcion,
                   CONCAT(COALESCE(cl.nombres,''), ' ', COALESCE(cl.apellidos,'')) AS cliente_nombre
            FROM contratos c
            LEFT JOIN clientes cl ON cl.cedula = c.cedula
            LEFT JOIN estado_contratos ec ON ec.estado = c.estado
            WHERE c.cedula = :cedula
            ORDER BY c.fecha_inicio DESC
        """), {"cedula": cedula.strip()})
        contratos = [dict(r) for r in rows.mappings()]
    if not contratos:
        raise HTTPException(status_code=404, detail="No se encontraron contratos para esa cédula")
    return {"total": len(contratos), "contratos": contratos}


# ── Detalle completo de un contrato ──────────────────────────────────────────

@router.get("/contrato")
async def get_contrato(
    company_id: int    = Query(...),
    nro_contrato: str  = Query(...),
    db: AsyncSession   = Depends(get_db),
    _=Depends(get_current_user),
):
    ext = await _get_ext(company_id, db)
    nro = nro_contrato.strip()

    async with ext as session:
        # Contrato + cliente + estado
        row = await session.execute(text("""
            SELECT c.*,
                   COALESCE(ec.descripcion, c.estado) AS estado_descripcion,
                   cl.nombres, cl.apellidos, cl.direccion, cl.telefono
            FROM contratos c
            LEFT JOIN clientes cl ON cl.cedula = c.cedula
            LEFT JOIN estado_contratos ec ON ec.estado = c.estado
            WHERE c.nro_contrato = :nro
            LIMIT 1
        """), {"nro": nro})
        contrato_row = row.mappings().first()

    if not contrato_row:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")

    contrato = dict(contrato_row)

    async with ext as session:
        # Artículos
        arts = await session.execute(text("""
            SELECT cod_categoria, Item_articulo, detalle, kilate,
                   ROUND(peso, 1) AS peso, Cantidad
            FROM articulos WHERE nro_cont_comp = :nro ORDER BY Item_articulo
        """), {"nro": nro})
        articulos = [dict(r) for r in arts.mappings()]

        # Prorrogas
        prorr = await session.execute(text("""
            SELECT nro_prorroga, fecha_prorroga, valor_prorroga,
                   meses_prorrogados, cod_tipo, nro_movimiento, Cod_Empleado
            FROM prorrogas WHERE nro_contrato = :nro ORDER BY fecha_prorroga ASC
        """), {"nro": nro})
        prorrogas = [dict(r) for r in prorr.mappings()]

        # Retiro
        ret = await session.execute(text("""
            SELECT nro_retiro, fecha_retiro, valor_retiro, sobre_costo,
                   descuento, cod_tipo, nro_movimiento, Cod_Empleado, Autorizado
            FROM retiros WHERE nro_contrato = :nro LIMIT 1
        """), {"nro": nro})
        retiro_row = ret.mappings().first()
        retiro = dict(retiro_row) if retiro_row else None

        # Remate
        rem = await session.execute(text("""
            SELECT nro_remate, fecha_remate, valor_contrato, Cod_Empleado
            FROM remates WHERE nro_contrato = :nro LIMIT 1
        """), {"nro": nro})
        remate_row = rem.mappings().first()
        remate = dict(remate_row) if remate_row else None

    return {
        "contrato":  contrato,
        "articulos": articulos,
        "prorrogas": prorrogas,
        "retiro":    retiro,
        "remate":    remate,
    }


# ── Fotos del contrato ────────────────────────────────────────────────────────

@router.get("/contrato/fotos")
async def list_fotos(
    company_id: int   = Query(...),
    nro_contrato: str = Query(...),
    db: AsyncSession  = Depends(get_db),
):
    rows = await db.execute(
        select(CompraventaFoto).where(
            CompraventaFoto.company_id   == company_id,
            CompraventaFoto.nro_contrato == nro_contrato,
        ).order_by(CompraventaFoto.created_at)
    )
    fotos = rows.scalars().all()
    return [{"id": f.id, "url": f.file_url, "name": f.file_name} for f in fotos]


@router.post("/contrato/foto")
async def upload_foto(
    company_id: int   = Query(...),
    nro_contrato: str = Query(...),
    file: UploadFile  = File(...),
    db: AsyncSession  = Depends(get_db),
    _=Depends(get_current_user),
):
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Solo se permiten imágenes")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Imagen demasiado grande (máx 10 MB)")
    ext  = (file.filename or "foto.jpg").rsplit(".", 1)[-1].lower()
    path = f"compraventa/{company_id}/{nro_contrato}/{uuid.uuid4().hex}.{ext}"
    url  = await upload_file(content, path)
    foto = CompraventaFoto(company_id=company_id, nro_contrato=nro_contrato,
                           file_url=url, file_name=file.filename)
    db.add(foto)
    await db.commit()
    await db.refresh(foto)
    return {"id": foto.id, "url": foto.file_url, "name": foto.file_name}


@router.delete("/contrato/foto/{foto_id}")
async def delete_foto(
    foto_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    foto = await db.get(CompraventaFoto, foto_id)
    if not foto:
        raise HTTPException(status_code=404, detail="Foto no encontrada")
    await delete_file(foto.file_url)
    await db.delete(foto)
    await db.commit()
    return {"ok": True}
