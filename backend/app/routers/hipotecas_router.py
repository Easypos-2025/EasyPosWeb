import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.database import get_db, get_ext_session
from app.models.company_model import Company
from app.models.credit_attachment_model import CreditAttachment
from app.auth.dependencies import get_current_user
from app.utils.storage import upload_file, delete_file

router = APIRouter(prefix="/api/hipotecas", tags=["hipotecas"])


# ── Helper: sesión BD externa ────────────────────────────────────────────────

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


# ── KPI: conteos de los 3 indicadores ────────────────────────────────────────

@router.get("/kpi")
async def get_kpi(
    company_id: int      = Query(...),
    meses: int           = Query(5, ge=1),
    db: AsyncSession     = Depends(get_db),
    _=Depends(get_current_user),
):
    ext = await _get_ext(company_id, db)
    async with ext as session:
        r1 = await session.execute(text("""
            SELECT COUNT(*) AS total FROM arriendos
            WHERE Activo = 1
              AND MONTH(Avisar) = MONTH(CURDATE())
              AND YEAR(Avisar)  = YEAR(CURDATE())
        """))
        avisar = r1.scalar() or 0

        r2 = await session.execute(text("""
            SELECT COUNT(*) AS total FROM arriendos
            WHERE Activo = 1
              AND MONTH(Vence) = MONTH(CURDATE())
              AND YEAR(Vence)  = YEAR(CURDATE())
        """))
        vencer = r2.scalar() or 0

        r3 = await session.execute(text("""
            SELECT COUNT(*) AS total FROM creditos
            WHERE Anulado   = 0
              AND Inactivo  = 0
              AND Cancelado = 0
              AND (TIMESTAMPDIFF(MONTH, Pago_Hasta, CURDATE()) + IF(DAY(CURDATE()) < DAY(Pago_Hasta), 1, 0)) >= :meses
        """), {"meses": meses})
        creditos_atr = r3.scalar() or 0

    return {
        "arriendos_avisar": avisar,
        "arriendos_vencer": vencer,
        "creditos_atrasados": creditos_atr,
        "meses_filtro": meses,
    }


# ── Detalle: Arriendos x Avisar (mes actual) ─────────────────────────────────

@router.get("/kpi/arriendos-avisar")
async def detalle_arriendos_avisar(
    company_id: int  = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    ext = await _get_ext(company_id, db)
    async with ext as session:
        rows = await session.execute(text("""
            SELECT
                a.Id_Arriendo,
                a.Cliente AS cedula,
                COALESCE(ca.nombres, a.Cliente) AS cliente_nombre,
                COALESCE(p.NombreCorto, p.Direccion, '') AS propiedad,
                p.Direccion AS propiedad_direccion,
                COALESCE(s.Descripcion, '') AS sector,
                a.Valor AS canon,
                a.Avisar,
                a.Vence,
                a.Pago_Hasta,
                a.Plazo_Meses
            FROM arriendos a
            LEFT JOIN clientes_arriendos ca ON ca.cedula = a.Cliente
            LEFT JOIN propiedades p ON p.Id_Propiedad = a.Id_Propiedad
            LEFT JOIN sectores s ON s.Id_Sector = p.Id_Sector
            WHERE a.Activo = 1
              AND MONTH(a.Avisar) = MONTH(CURDATE())
              AND YEAR(a.Avisar)  = YEAR(CURDATE())
            ORDER BY a.Avisar ASC
        """))
        data = [dict(r) for r in rows.mappings()]
    return {"total": len(data), "items": data}


# ── Detalle: Arriendos x Vencer (mes actual) ─────────────────────────────────

@router.get("/kpi/arriendos-vencer")
async def detalle_arriendos_vencer(
    company_id: int  = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    ext = await _get_ext(company_id, db)
    async with ext as session:
        rows = await session.execute(text("""
            SELECT
                a.Id_Arriendo,
                a.Cliente AS cedula,
                COALESCE(ca.nombres, a.Cliente) AS cliente_nombre,
                COALESCE(p.NombreCorto, p.Direccion, '') AS propiedad,
                p.Direccion AS propiedad_direccion,
                COALESCE(s.Descripcion, '') AS sector,
                a.Valor AS canon,
                a.Avisar,
                a.Vence,
                a.Pago_Hasta,
                a.Plazo_Meses
            FROM arriendos a
            LEFT JOIN clientes_arriendos ca ON ca.cedula = a.Cliente
            LEFT JOIN propiedades p ON p.Id_Propiedad = a.Id_Propiedad
            LEFT JOIN sectores s ON s.Id_Sector = p.Id_Sector
            WHERE a.Activo = 1
              AND MONTH(a.Vence) = MONTH(CURDATE())
              AND YEAR(a.Vence)  = YEAR(CURDATE())
            ORDER BY a.Vence ASC
        """))
        data = [dict(r) for r in rows.mappings()]
    return {"total": len(data), "items": data}


# ── Detalle: Créditos Atrasados ───────────────────────────────────────────────

@router.get("/kpi/creditos-atrasados")
async def detalle_creditos_atrasados(
    company_id: int  = Query(...),
    meses: int       = Query(5, ge=1),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    ext = await _get_ext(company_id, db)
    async with ext as session:
        rows = await session.execute(text("""
            SELECT
                c.Nro_Credito,
                c.Cliente AS cedula,
                COALESCE(cl.nombres, c.Cliente) AS cliente_nombre,
                c.Valor_Actual,
                ROUND(c.Valor_Actual * (c.Interes + c.Interes_Socio) / 100, 0) AS cuota_mes,
                (TIMESTAMPDIFF(MONTH, c.Pago_Hasta, CURDATE()) + IF(DAY(CURDATE()) < DAY(c.Pago_Hasta), 1, 0)) AS meses_deuda,
                ROUND(
                    c.Valor_Actual * (c.Interes + c.Interes_Socio) / 100
                    * (TIMESTAMPDIFF(MONTH, c.Pago_Hasta, CURDATE()) + IF(DAY(CURDATE()) < DAY(c.Pago_Hasta), 1, 0)),
                0) AS total_deuda,
                c.Pago_Hasta,
                c.Interes,
                c.Interes_Socio,
                COALESCE(e.nombres, '') AS acreedor_nombre,
                COALESCE(ca.Nro_Juridico, '') AS nro_juridico,
                COALESCE(ca.Ref_Adicional, '') AS ref_adicional
            FROM creditos c
            LEFT JOIN clientes cl ON cl.cedula = c.Cliente
            LEFT JOIN empleados e ON e.cod_empleado = c.Acreedor
            LEFT JOIN creditos_adicional ca ON ca.Nro_Credito = c.Nro_Credito
            WHERE c.Anulado   = 0
              AND c.Inactivo  = 0
              AND c.Cancelado = 0
              AND (TIMESTAMPDIFF(MONTH, c.Pago_Hasta, CURDATE()) + IF(DAY(CURDATE()) < DAY(c.Pago_Hasta), 1, 0)) >= :meses
            ORDER BY meses_deuda DESC
        """), {"meses": meses})
        data = [dict(r) for r in rows.mappings()]
    return {"total": len(data), "meses_filtro": meses, "items": data}


# ── Consulta Crédito: buscar ──────────────────────────────────────────────────

@router.get("/creditos/buscar")
async def buscar_creditos(
    company_id: int  = Query(...),
    nombre: str      = Query("", description="Búsqueda por nombre cliente"),
    nro: str         = Query("", description="Búsqueda por Nro_Credito"),
    ref: str         = Query("", description="Búsqueda por Ref_Adicional"),
    juridico: str    = Query("", description="Búsqueda por Nro_Juridico"),
    vigentes: bool   = Query(True),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    ext = await _get_ext(company_id, db)
    filtro_vigente = "AND c.Cancelado=0 AND c.Anulado=0 AND c.Inactivo=0" if vigentes else ""

    async with ext as session:
        base_select = """
            SELECT c.Nro_Credito, c.Cliente AS cedula,
                   COALESCE(cl.nombres, c.Cliente) AS cliente_nombre,
                   c.Valor_Actual, c.Pago_Hasta,
                   (TIMESTAMPDIFF(MONTH, c.Pago_Hasta, CURDATE()) + IF(DAY(CURDATE()) < DAY(c.Pago_Hasta), 1, 0)) AS meses_mora,
                   c.Cancelado, c.Anulado, c.Inactivo,
                   COALESCE(ca.Ref_Adicional, '') AS ref_adicional,
                   COALESCE(ca.Nro_Juridico, '')  AS nro_juridico
            FROM creditos c
            LEFT JOIN clientes cl ON cl.cedula = c.Cliente
            LEFT JOIN creditos_adicional ca ON ca.Nro_Credito = c.Nro_Credito
        """
        # Búsquedas por identificador específico: ignoran siempre el filtro de estado
        if nro.strip():
            sql = f"{base_select} WHERE c.Nro_Credito LIKE :q ORDER BY c.Nro_Credito LIMIT 50"
            params = {"q": f"%{nro.strip()}%"}
        elif ref.strip():
            sql = f"{base_select} WHERE ca.Ref_Adicional LIKE :q ORDER BY c.Nro_Credito LIMIT 50"
            params = {"q": f"%{ref.strip()}%"}
        elif juridico.strip():
            sql = f"{base_select} WHERE ca.Nro_Juridico LIKE :q ORDER BY c.Nro_Credito LIMIT 50"
            params = {"q": f"%{juridico.strip()}%"}
        else:
            # Búsqueda por nombre: respeta el filtro vigentes
            sql = f"{base_select} WHERE cl.nombres LIKE :q {filtro_vigente} ORDER BY cl.nombres LIMIT 80"
            params = {"q": f"%{nombre.strip()}%"}

        rows = await session.execute(text(sql), params)
        data = [dict(r) for r in rows.mappings()]
    return {"total": len(data), "creditos": data}


# ── Consulta Crédito: detalle completo ───────────────────────────────────────

@router.get("/credito/{nro_credito}")
async def detalle_credito(
    nro_credito: str,
    company_id: int  = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    nro = nro_credito.strip()
    ext = await _get_ext(company_id, db)

    async with ext as session:

        # ── General + cliente + acreedor + adicional ──────────────────────────
        row = await session.execute(text("""
            SELECT
                c.*,
                COALESCE(cl.nombres,   c.Cliente) AS cliente_nombre,
                cl.direccion  AS cliente_dir,
                cl.Telefono   AS cliente_tel,
                cl.Mail       AS cliente_mail,
                COALESCE(e.nombres, '') AS acreedor_nombre,
                ca.Ref_Adicional,
                ca.Nro_Juridico,
                ca.Nota_Tipo_Pago,
                ca.Id_Propiedad AS ca_id_propiedad,
                ca.Observaciones_Juridico,
                ca.Ubicacion,
                ca.Area_Predio,
                ca.Dificil_Cobro,
                ca.Fecha_Cancelado,
                ROUND(c.Valor_Actual * (c.Interes + c.Interes_Socio) / 100, 0) AS cuota_mes,
                (TIMESTAMPDIFF(MONTH, c.Pago_Hasta, CURDATE()) + IF(DAY(CURDATE()) < DAY(c.Pago_Hasta), 1, 0)) AS meses_mora,
                ROUND(
                    c.Valor_Actual * (c.Interes + c.Interes_Socio) / 100
                    * (TIMESTAMPDIFF(MONTH, c.Pago_Hasta, CURDATE()) + IF(DAY(CURDATE()) < DAY(c.Pago_Hasta), 1, 0)),
                0) AS valor_deuda
            FROM creditos c
            LEFT JOIN clientes cl ON cl.cedula = c.Cliente
            LEFT JOIN empleados e  ON e.cod_empleado = c.Acreedor
            LEFT JOIN creditos_adicional ca ON ca.Nro_Credito = c.Nro_Credito
            WHERE c.Nro_Credito = :nro
            LIMIT 1
        """), {"nro": nro})
        credito_row = row.mappings().first()
        if not credito_row:
            raise HTTPException(status_code=404, detail="Crédito no encontrado")
        credito = dict(credito_row)

        # ── Pagos realizados ──────────────────────────────────────────────────
        pagos_rows = await session.execute(text("""
            SELECT p.Nro_Pago, p.Fecha, p.Meses_Pagos, p.Valor_pago,
                   p.Descuento, p.Mes_Pago_Hasta,
                   COALESCE(p.Descripcion_Forma, '') AS descripcion_forma,
                   COALESCE(f.Descripcion_Forma, '') AS forma_pago_desc,
                   COALESCE(e.nombres, '') AS empleado_nombre
            FROM pagos_creditos p
            LEFT JOIN forma_pago f ON f.Forma_Pago = p.Forma_pago
            LEFT JOIN empleados  e ON e.cod_empleado = p.Cod_Empleado
            WHERE p.Nro_Credito = :nro
            ORDER BY p.Fecha DESC
        """), {"nro": nro})
        pagos = [dict(r) for r in pagos_rows.mappings()]

        # ── Abonos a capital ──────────────────────────────────────────────────
        abonos_cap = await session.execute(text("""
            SELECT ac.Nro_Abono, ac.Fecha, ac.Valor_Abono,
                   COALESCE(ac.Descripcion_Forma, '') AS descripcion_forma,
                   COALESCE(f.Descripcion_Forma, '') AS forma_pago_desc,
                   COALESCE(e.nombres, '') AS empleado_nombre
            FROM abonos_capital ac
            LEFT JOIN forma_pago f ON f.Forma_Pago = ac.Forma_pago
            LEFT JOIN empleados  e ON e.cod_empleado = ac.Cod_Empleado
            WHERE ac.Nro_Credito = :nro
            ORDER BY ac.Fecha DESC
        """), {"nro": nro})
        abonos_capital = [dict(r) for r in abonos_cap.mappings()]

        # ── Abonos parciales ──────────────────────────────────────────────────
        abonos_par = await session.execute(text("""
            SELECT ap.Nro_Abono, ap.Fecha, ap.Valor_Abono, ap.Pendiente,
                   ap.Fecha_Cruce, ap.Observacion,
                   COALESCE(ap.Descripcion_Forma, '') AS descripcion_forma,
                   COALESCE(f.Descripcion_Forma, '') AS forma_pago_desc
            FROM abonos_parciales_creditos ap
            LEFT JOIN forma_pago f ON f.Forma_Pago = ap.Forma_pago
            WHERE ap.Nro_Credito = :nro
            ORDER BY ap.Fecha DESC
        """), {"nro": nro})
        abonos_parciales = [dict(r) for r in abonos_par.mappings()]

        # ── Aumento de capital ────────────────────────────────────────────────
        aumentos_r = await session.execute(text("""
            SELECT au.Nro_Abono, au.Fecha, au.Valor_Abono, au.Nro_Pagare,
                   au.Unifica_En, au.Observaciones,
                   COALESCE(f.Descripcion_Forma, '') AS forma_pago_desc,
                   COALESCE(e.nombres, '') AS empleado_nombre
            FROM aumento_capital au
            LEFT JOIN forma_pago f ON f.Forma_Pago = au.Forma_pago
            LEFT JOIN empleados  e ON e.cod_empleado = au.Cod_Empleado
            WHERE au.Nro_Credito = :nro
            ORDER BY au.Fecha DESC
        """), {"nro": nro})
        aumentos = [dict(r) for r in aumentos_r.mappings()]

        # ── Novedades / observaciones ─────────────────────────────────────────
        novedades_r = await session.execute(text("""
            SELECT cn.Nro_Novedad, cn.Fecha, cn.Hora, cn.Observacion, cn.Anulada,
                   COALESCE(e.nombres, '') AS empleado_nombre
            FROM creditos_novedades cn
            LEFT JOIN empleados e ON e.cod_empleado = cn.Cod_Empleado
            WHERE cn.Nro_Credito = :nro AND cn.Anulada = 0
            ORDER BY cn.Fecha DESC, cn.Hora DESC
        """), {"nro": nro})
        novedades = [dict(r) for r in novedades_r.mappings()]

        # ── Otros deudores (codeudores) ───────────────────────────────────────
        deudores_r = await session.execute(text("""
            SELECT od.Cedula,
                   COALESCE(cl.nombres, od.Cedula) AS nombres,
                   cl.Telefono, cl.Mail, cl.direccion
            FROM otrosdeudorescreditos od
            LEFT JOIN clientes cl ON cl.cedula = od.Cedula
            WHERE od.Nro_Credito = :nro
        """), {"nro": nro})
        otros_deudores = [dict(r) for r in deudores_r.mappings()]

        # ── Todos los campos del cliente ──────────────────────────────────────
        cli_r = await session.execute(text("""
            SELECT cl.* FROM clientes cl WHERE cl.cedula = :ced LIMIT 1
        """), {"ced": credito["Cliente"]})
        cli_row = cli_r.mappings().first()
        cliente_detalle = dict(cli_row) if cli_row else {}

    return {
        "credito":          credito,
        "cliente_detalle":  cliente_detalle,
        "pagos":            pagos,
        "abonos_capital":   abonos_capital,
        "abonos_parciales": abonos_parciales,
        "aumentos_capital": aumentos,
        "novedades":        novedades,
        "otros_deudores":   otros_deudores,
    }


# ── Consulta Arriendo: buscar ─────────────────────────────────────────────────

@router.get("/arriendos/buscar")
async def buscar_arriendos(
    company_id: int  = Query(...),
    codigo: str      = Query("", description="Código lista propiedad"),
    id_arr: str      = Query("", description="Id_Arriendo exacto"),
    propietario: str = Query("", description="Nombre propietario"),
    cliente: str     = Query("", description="Nombre cliente arrendatario"),
    solo_activos: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    ext = await _get_ext(company_id, db)
    filtro_activo = "AND a.Activo = 1" if solo_activos else ""

    async with ext as session:
        def make_base(apply_filter: bool) -> str:
            f = filtro_activo if apply_filter else ""
            return f"""
                SELECT
                    a.Id_Arriendo,
                    a.Cliente AS cedula_cliente,
                    COALESCE(ca.nombres, a.Cliente) AS cliente_nombre,
                    COALESCE(p.NombreCorto, p.Direccion, '') AS propiedad_nombre,
                    p.Direccion AS propiedad_dir,
                    COALESCE(p.Codigo_Lista, '') AS codigo_lista,
                    p.NombrePropietario,
                    COALESCE(s.Descripcion, '') AS sector,
                    a.Valor AS canon,
                    a.Pago_Hasta,
                    a.Vence,
                    a.Avisar,
                    a.Fecha_Inicio,
                    a.Plazo_Meses,
                    a.Activo,
                    a.Deposito
                FROM arriendos a
                LEFT JOIN clientes_arriendos ca ON ca.cedula = a.Cliente
                LEFT JOIN propiedades p ON p.Id_Propiedad = a.Id_Propiedad
                LEFT JOIN sectores s ON s.Id_Sector = p.Id_Sector
                WHERE 1=1 {f}
            """

        # Búsquedas por identificador específico: ignoran siempre el filtro de estado
        if id_arr.strip():
            sql = make_base(False) + " AND a.Id_Arriendo = :q ORDER BY a.Id_Arriendo LIMIT 1"
            params = {"q": id_arr.strip()}
        elif codigo.strip():
            sql = make_base(False) + " AND p.Codigo_Lista LIKE :q ORDER BY a.Id_Arriendo LIMIT 50"
            params = {"q": f"%{codigo.strip()}%"}
        elif propietario.strip():
            sql = make_base(False) + " AND p.NombreCorto LIKE :q ORDER BY p.NombreCorto LIMIT 50"
            params = {"q": f"%{propietario.strip()}%"}
        else:
            sql = make_base(False) + " AND ca.nombres LIKE :q ORDER BY ca.nombres LIMIT 80"
            params = {"q": f"%{cliente.strip()}%"}

        rows = await session.execute(text(sql), params)
        data = [dict(r) for r in rows.mappings()]
    return {"total": len(data), "arriendos": data}


# ── Consulta Arriendo: detalle completo ───────────────────────────────────────

@router.get("/arriendo/{id_arriendo}")
async def detalle_arriendo(
    id_arriendo: int,
    company_id: int  = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    ext = await _get_ext(company_id, db)

    async with ext as session:

        # ── Contrato + propiedad + cliente ────────────────────────────────────
        row = await session.execute(text("""
            SELECT
                a.*,
                COALESCE(ca.nombres,  a.Cliente) AS cliente_nombre,
                ca.Telefono AS cliente_tel,
                COALESCE(p.NombreCorto, p.Direccion, '') AS propiedad_nombre,
                p.Direccion  AS propiedad_dir,
                p.NombrePropietario,
                COALESCE(p.Codigo_Lista, '') AS codigo_lista,
                COALESCE(s.Descripcion, '') AS sector,
                p.Valor_Canon  AS valor_canon_propietad,
                COALESCE(e.nombres, '') AS asesor_nombre,
                TIMESTAMPDIFF(MONTH, a.Pago_Hasta, CURDATE()) AS meses_mora
            FROM arriendos a
            LEFT JOIN clientes_arriendos ca ON ca.cedula = a.Cliente
            LEFT JOIN propiedades p ON p.Id_Propiedad = a.Id_Propiedad
            LEFT JOIN sectores s ON s.Id_Sector = p.Id_Sector
            LEFT JOIN empleados e ON e.cod_empleado = a.Cod_Empleado
            WHERE a.Id_Arriendo = :id
            LIMIT 1
        """), {"id": id_arriendo})
        arriendo_row = row.mappings().first()
        if not arriendo_row:
            raise HTTPException(status_code=404, detail="Arriendo no encontrado")
        arriendo = dict(arriendo_row)

        # ── Pagos realizados ──────────────────────────────────────────────────
        pagos_r = await session.execute(text("""
            SELECT pa.Nro_Pago, pa.Fecha_Pago, pa.Valor_Pago,
                   pa.Meses_Pagados, pa.Anulado,
                   COALESCE(f.Descripcion_Forma, '') AS forma_pago_desc
            FROM pago_arriendos pa
            LEFT JOIN forma_pago f ON f.Forma_Pago = pa.Forma_Pago
            WHERE pa.Id_Arriendo = :id AND pa.Anulado = 0
            ORDER BY pa.Fecha_Pago DESC
        """), {"id": id_arriendo})
        pagos = [dict(r) for r in pagos_r.mappings()]

    return {
        "arriendo": arriendo,
        "pagos":    pagos,
    }


# ── Adjuntos de crédito (fotos / documentos) ─────────────────────────────────

@router.get("/credito/{nro}/adjuntos")
async def listar_adjuntos(
    nro:        str          = None,
    company_id: int          = Query(...),
    tipo:       str          = Query("foto"),
    db:         AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    q = await db.execute(
        select(CreditAttachment)
        .where(CreditAttachment.company_id  == company_id)
        .where(CreditAttachment.nro_credito == nro)
        .where(CreditAttachment.tipo        == tipo)
        .order_by(CreditAttachment.created_at.asc())
    )
    items = q.scalars().all()
    return [
        {
            "id":         a.id,
            "filename":   a.filename,
            "url":        a.url,
            "file_size":  a.file_size,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in items
    ]


@router.post("/credito/{nro}/adjuntos")
async def subir_adjunto(
    nro:        str          = None,
    company_id: int          = Form(...),
    tipo:       str          = Form("foto"),
    file:       UploadFile   = File(...),
    db:         AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    content = await file.read()
    size    = len(content)
    ext     = os.path.splitext(file.filename or "")[-1].lower() or ".jpg"
    path    = f"creditos/{company_id}/{nro}/{tipo}/{uuid.uuid4().hex}{ext}"
    url     = await upload_file(content, path)

    adj = CreditAttachment(
        company_id  = company_id,
        nro_credito = nro,
        tipo        = tipo,
        filename    = file.filename or "archivo",
        url         = url,
        file_size   = size,
    )
    db.add(adj)
    await db.commit()
    await db.refresh(adj)
    return {
        "id":        adj.id,
        "filename":  adj.filename,
        "url":       adj.url,
        "file_size": adj.file_size,
    }


@router.delete("/credito/adjunto/{adj_id}")
async def eliminar_adjunto(
    adj_id:     int,
    company_id: int          = Query(...),
    db:         AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    q   = await db.execute(
        select(CreditAttachment)
        .where(CreditAttachment.id         == adj_id)
        .where(CreditAttachment.company_id == company_id)
    )
    adj = q.scalar_one_or_none()
    if not adj:
        raise HTTPException(status_code=404, detail="Adjunto no encontrado")

    url = adj.url
    await db.delete(adj)
    await db.commit()
    await delete_file(url)
    return {"ok": True}
