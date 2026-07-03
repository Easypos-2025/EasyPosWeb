from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.database import get_db, get_ext_session
from app.models.company_model import Company
from app.auth.dependencies import get_current_user

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
              AND TIMESTAMPDIFF(MONTH, Pago_Hasta, CURDATE()) >= :meses
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
                TIMESTAMPDIFF(MONTH, c.Pago_Hasta, CURDATE()) AS meses_deuda,
                ROUND(
                    c.Valor_Actual * (c.Interes + c.Interes_Socio) / 100
                    * TIMESTAMPDIFF(MONTH, c.Pago_Hasta, CURDATE()),
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
              AND TIMESTAMPDIFF(MONTH, c.Pago_Hasta, CURDATE()) >= :meses
            ORDER BY meses_deuda DESC
        """), {"meses": meses})
        data = [dict(r) for r in rows.mappings()]
    return {"total": len(data), "meses_filtro": meses, "items": data}


# ── Consulta Crédito: buscar por nombre ──────────────────────────────────────

@router.get("/creditos/buscar")
async def buscar_creditos(
    company_id: int  = Query(...),
    nombre: str      = Query("", description="Búsqueda por nombre cliente"),
    nro: str         = Query("", description="Búsqueda por Nro_Credito"),
    vigentes: bool   = Query(True),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    ext = await _get_ext(company_id, db)
    filtro_vigente = "AND c.Cancelado=0 AND c.Anulado=0 AND c.Inactivo=0" if vigentes else ""

    async with ext as session:
        if nro.strip():
            rows = await session.execute(text(f"""
                SELECT c.Nro_Credito, c.Cliente AS cedula,
                       COALESCE(cl.nombres, c.Cliente) AS cliente_nombre,
                       c.Valor_Actual, c.Pago_Hasta,
                       TIMESTAMPDIFF(MONTH, c.Pago_Hasta, CURDATE()) AS meses_mora,
                       c.Cancelado, c.Anulado, c.Inactivo
                FROM creditos c
                LEFT JOIN clientes cl ON cl.cedula = c.Cliente
                WHERE c.Nro_Credito LIKE :nro {filtro_vigente}
                ORDER BY c.Nro_Credito
                LIMIT 50
            """), {"nro": f"%{nro.strip()}%"})
        else:
            rows = await session.execute(text(f"""
                SELECT c.Nro_Credito, c.Cliente AS cedula,
                       COALESCE(cl.nombres, c.Cliente) AS cliente_nombre,
                       c.Valor_Actual, c.Pago_Hasta,
                       TIMESTAMPDIFF(MONTH, c.Pago_Hasta, CURDATE()) AS meses_mora,
                       c.Cancelado, c.Anulado, c.Inactivo
                FROM creditos c
                LEFT JOIN clientes cl ON cl.cedula = c.Cliente
                WHERE cl.nombres LIKE :nombre {filtro_vigente}
                ORDER BY cl.nombres
                LIMIT 80
            """), {"nombre": f"%{nombre.strip()}%"})
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
                TIMESTAMPDIFF(MONTH, c.Pago_Hasta, CURDATE()) AS meses_mora,
                ROUND(
                    c.Valor_Actual * (c.Interes + c.Interes_Socio) / 100
                    * TIMESTAMPDIFF(MONTH, c.Pago_Hasta, CURDATE()),
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

    return {
        "credito":          credito,
        "pagos":            pagos,
        "abonos_capital":   abonos_capital,
        "abonos_parciales": abonos_parciales,
        "aumentos_capital": aumentos,
        "novedades":        novedades,
        "otros_deudores":   otros_deudores,
    }
