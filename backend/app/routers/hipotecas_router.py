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
                ROUND(c.Valor_Actual * (c.Interes + c.Interes_Socio), 0) AS cuota_mes,
                TIMESTAMPDIFF(MONTH, c.Pago_Hasta, CURDATE()) AS meses_deuda,
                ROUND(
                    c.Valor_Actual * (c.Interes + c.Interes_Socio)
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
