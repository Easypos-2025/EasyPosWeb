import calendar
from math import ceil
from collections import defaultdict
from typing import Optional, List

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
import io
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.database import get_db
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.user_model import User
from app.utils.excel_ventas import build_ventas_excel

router = APIRouter(prefix="/api/metricas", tags=["Métricas"])

_MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

_DIAS_ES = {
    0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
    4: "Viernes", 5: "Sábado", 6: "Domingo",
}

_TOTAL_EXPR = (
    "COALESCE(SUM(cash_amount + credit_card_amount + debit_card_amount"
    " - discount - tip - extra_tip), 0)"
)


async def _get_user(authorization: str, db: AsyncSession) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido")
    result = await db.execute(
        select(UserSession).where(UserSession.token == token, UserSession.is_active == True)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=401, detail="Sesión inválida")
    uid = payload.get("user_id")
    user = await db.get(User, int(uid)) if uid else None
    if not user:
        r2 = await db.execute(select(User).where(User.email == payload.get("sub")))
        user = r2.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not user.company_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asignada")
    return user


def _resolve_cid(user: User, override: Optional[int]) -> int:
    if override and user.role and user.role.is_system:
        return override
    return user.company_id


def _sql_anual_por_tabla(tabla: str) -> str:
    return f"""
        SELECT MONTH(date) AS mes, {_TOTAL_EXPR} AS total, COUNT(*) AS cnt
        FROM {tabla}
        WHERE company_id = :cid AND YEAR(date) = :year AND voided = 0
        GROUP BY MONTH(date)
    """


def _sql_mensual_por_tabla(tabla: str) -> str:
    return f"""
        SELECT date AS fecha, {_TOTAL_EXPR} AS total, COUNT(*) AS cnt
        FROM {tabla}
        WHERE company_id = :cid AND YEAR(date) = :year AND MONTH(date) = :month AND voided = 0
        GROUP BY date
    """


@router.get("/ventas/anual")
async def ventas_anual(
    year: int = Query(..., ge=2000, le=2100),
    tipo: str = Query("ambos", pattern="^(facturas|recibos|ambos)$"),
    company_id: Optional[int] = Query(None),
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid = _resolve_cid(user, company_id)

    if tipo == "facturas":
        sql = _sql_anual_por_tabla("pos_invoices")
    elif tipo == "recibos":
        sql = _sql_anual_por_tabla("pos_receipts")
    else:
        sql = f"""
            SELECT mes, SUM(total) AS total, SUM(cnt) AS cnt FROM (
                {_sql_anual_por_tabla("pos_invoices")}
                UNION ALL
                {_sql_anual_por_tabla("pos_receipts")}
            ) t GROUP BY mes
        """

    rows = (await db.execute(text(sql), {"cid": cid, "year": year})).mappings().all()
    por_mes = {int(r["mes"]): {"total": float(r["total"]), "count": int(r["cnt"])} for r in rows}

    meses = []
    total_general = 0.0
    count_general = 0
    for m in range(1, 13):
        v = por_mes.get(m, {"total": 0.0, "count": 0})
        total_general += v["total"]
        count_general += v["count"]
        meses.append({
            "mes": m,
            "nombre_mes": _MESES_ES[m],
            "total": v["total"],
            "count": v["count"],
        })

    return {
        "year": year,
        "tipo": tipo,
        "meses": meses,
        "total_general": total_general,
        "count_general": count_general,
    }


@router.get("/ventas/mensual")
async def ventas_mensual(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    tipo: str = Query("ambos", pattern="^(facturas|recibos|ambos)$"),
    company_id: Optional[int] = Query(None),
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid = _resolve_cid(user, company_id)

    if tipo == "facturas":
        sql = f"{_sql_mensual_por_tabla('pos_invoices')} ORDER BY fecha"
    elif tipo == "recibos":
        sql = f"{_sql_mensual_por_tabla('pos_receipts')} ORDER BY fecha"
    else:
        sql = f"""
            SELECT fecha, SUM(total) AS total, SUM(cnt) AS cnt FROM (
                {_sql_mensual_por_tabla("pos_invoices")}
                UNION ALL
                {_sql_mensual_por_tabla("pos_receipts")}
            ) t GROUP BY fecha ORDER BY fecha
        """

    rows = (await db.execute(text(sql), {"cid": cid, "year": year, "month": month})).mappings().all()

    dias = []
    for r in rows:
        fecha = r["fecha"]
        dia_num = fecha.day
        semana_del_mes = ceil(dia_num / 7)
        dias.append({
            "fecha": fecha.isoformat(),
            "dia": dia_num,
            "dia_nombre": _DIAS_ES[fecha.weekday()],
            "dia_abrev": _DIAS_ES[fecha.weekday()][:3],
            "semana_del_mes": semana_del_mes,
            "total": float(r["total"]),
            "count": int(r["cnt"]),
        })

    total_mes = sum(d["total"] for d in dias)
    count_mes = sum(d["count"] for d in dias)

    return {
        "year": year,
        "month": month,
        "nombre_mes": _MESES_ES[month],
        "tipo": tipo,
        "dias": dias,
        "total_mes": total_mes,
        "count_mes": count_mes,
    }


# ═══════════════════════════════════════════════════════════════════
# FORMA DE PAGO
# ═══════════════════════════════════════════════════════════════════

_FP_EXPR = """
    SELECT {date_col} AS fecha,
           COALESCE(pt.name, CONCAT('Método ', pm.payment_method_id)) AS forma_pago,
           SUM(pm.amount) AS total
    FROM {tabla} pm
    LEFT JOIN pos_payment_types pt
           ON pt.id = pm.payment_method_id AND pt.company_id = pm.company_id
    WHERE pm.company_id = :cid {extra}
    GROUP BY {date_col}, forma_pago
"""


def _fp_sql(tipo: str, date_group: str, year_filter: str) -> str:
    fact_date = "DATE(pm.date)" if date_group == "dia" else "MONTH(pm.date)"
    extra_f = f"AND YEAR(pm.date) = :year {year_filter}"
    extra_r = f"AND YEAR(pm.date) = :year {year_filter}"

    q_fact = _FP_EXPR.format(
        date_col=fact_date, tabla="pos_invoice_payment_methods",
        extra=extra_f)
    q_rec = _FP_EXPR.format(
        date_col=fact_date, tabla="pos_receipt_payment_methods",
        extra=extra_r)

    if tipo == "facturas":
        return q_fact
    elif tipo == "recibos":
        return q_rec
    else:
        return f"""
        SELECT fecha, forma_pago, SUM(total) AS total FROM (
            {q_fact} UNION ALL {q_rec}
        ) t GROUP BY fecha, forma_pago
        """


@router.get("/forma-pago/anual")
async def forma_pago_anual(
    year: int = Query(..., ge=2000, le=2100),
    tipo: str = Query("ambos", pattern="^(facturas|recibos|ambos)$"),
    company_id: Optional[int] = Query(None),
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid = _resolve_cid(user, company_id)

    sql = _fp_sql(tipo, "mes", "")
    rows = (await db.execute(text(sql), {"cid": cid, "year": year})).mappings().all()

    # Pivot: {mes: {forma_pago: total}}
    pivot: dict[int, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    formas_set: set[str] = set()
    for r in rows:
        m = int(r["fecha"])
        fp = str(r["forma_pago"])
        pivot[m][fp] += float(r["total"])
        formas_set.add(fp)

    formas_pago = sorted(formas_set)
    meses = []
    totales_por_forma: dict[str, float] = defaultdict(float)
    total_general = 0.0

    for m in range(1, 13):
        por_forma = {fp: pivot[m].get(fp, 0.0) for fp in formas_pago}
        total_mes = sum(por_forma.values())
        total_general += total_mes
        for fp, v in por_forma.items():
            totales_por_forma[fp] += v
        meses.append({
            "mes": m,
            "nombre_mes": _MESES_ES[m],
            "total": total_mes,
            "por_forma": por_forma,
        })

    return {
        "year": year,
        "tipo": tipo,
        "formas_pago": formas_pago,
        "meses": meses,
        "totales_por_forma": dict(totales_por_forma),
        "total_general": total_general,
    }


@router.get("/forma-pago/mensual")
async def forma_pago_mensual(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    tipo: str = Query("ambos", pattern="^(facturas|recibos|ambos)$"),
    company_id: Optional[int] = Query(None),
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid = _resolve_cid(user, company_id)

    sql = _fp_sql(tipo, "dia", "AND MONTH(pm.date) = :month")
    rows = (await db.execute(text(sql), {"cid": cid, "year": year, "month": month})).mappings().all()

    pivot: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    formas_set: set[str] = set()
    for r in rows:
        fecha_key = r["fecha"].isoformat() if hasattr(r["fecha"], "isoformat") else str(r["fecha"])
        fp = str(r["forma_pago"])
        pivot[fecha_key][fp] += float(r["total"])
        formas_set.add(fp)

    formas_pago = sorted(formas_set)
    dias = []
    totales_por_forma: dict[str, float] = defaultdict(float)
    total_mes = 0.0

    for fecha_key in sorted(pivot.keys()):
        from datetime import date as _date
        fecha_obj = _date.fromisoformat(fecha_key)
        por_forma = {fp: pivot[fecha_key].get(fp, 0.0) for fp in formas_pago}
        total_dia = sum(por_forma.values())
        total_mes += total_dia
        for fp, v in por_forma.items():
            totales_por_forma[fp] += v
        dias.append({
            "fecha": fecha_key,
            "dia": fecha_obj.day,
            "dia_nombre": _DIAS_ES[fecha_obj.weekday()],
            "dia_abrev": _DIAS_ES[fecha_obj.weekday()][:3],
            "semana_del_mes": ceil(fecha_obj.day / 7),
            "total": total_dia,
            "por_forma": por_forma,
        })

    return {
        "year": year,
        "month": month,
        "nombre_mes": _MESES_ES[month],
        "tipo": tipo,
        "formas_pago": formas_pago,
        "dias": dias,
        "totales_por_forma": dict(totales_por_forma),
        "total_mes": total_mes,
    }


# ═══════════════════════════════════════════════════════════════════
# ABC DE PRODUCTOS
# ═══════════════════════════════════════════════════════════════════

def _abc_sql_tabla(fact_tabla: str, num_col: str) -> str:
    return f"""
        SELECT
            COALESCE(d.name, CONCAT('Prod.', pid.dish_id)) AS producto,
            SUM(pid.quantity) AS cantidad,
            SUM(pid.dish_amount) AS total
        FROM {fact_tabla} pid
        LEFT JOIN pos_dishes d ON d.id = pid.dish_id AND d.company_id = pid.company_id
        WHERE pid.company_id = :cid
          AND YEAR(pid.date) = :year
          {num_col}
          AND COALESCE(pid.complimentary, 0) = 0
        GROUP BY pid.dish_id, producto
    """


def _abc_sql(tipo: str, extra: str = "") -> str:
    q_fact = _abc_sql_tabla("pos_invoice_details", extra)
    q_rec  = _abc_sql_tabla("pos_receipt_invoice_details", extra)
    if tipo == "facturas":
        return q_fact
    elif tipo == "recibos":
        return q_rec
    else:
        return f"""
        SELECT producto, SUM(cantidad) AS cantidad, SUM(total) AS total FROM (
            {q_fact} UNION ALL {q_rec}
        ) t GROUP BY producto
        """


def _clasificar_abc(productos: list) -> tuple[list, dict]:
    total_gral = sum(p["total"] for p in productos)
    if not total_gral:
        return productos, {"A": {"count": 0, "total": 0, "pct": 0},
                           "B": {"count": 0, "total": 0, "pct": 0},
                           "C": {"count": 0, "total": 0, "pct": 0}}
    acum = 0.0
    for i, p in enumerate(productos):
        acum += p["total"]
        pct_acum = (acum / total_gral) * 100
        if pct_acum <= 80:
            clase = "A"
        elif pct_acum <= 95:
            clase = "B"
        else:
            clase = "C"
        p["rank"] = i + 1
        p["pct"] = round((p["total"] / total_gral) * 100, 2)
        p["pct_acum"] = round(pct_acum, 2)
        p["clase"] = clase

    resumen: dict[str, dict] = {"A": defaultdict(float), "B": defaultdict(float), "C": defaultdict(float)}
    for p in productos:
        resumen[p["clase"]]["count"] += 1
        resumen[p["clase"]]["total"] += p["total"]
    result_resumen = {}
    for cls, vals in resumen.items():
        cnt = int(vals["count"])
        tot = float(vals["total"])
        result_resumen[cls] = {
            "count": cnt,
            "total": tot,
            "pct": round((tot / total_gral) * 100, 1) if total_gral else 0,
        }
    return productos, result_resumen


@router.get("/productos-abc/anual")
async def productos_abc_anual(
    year: int = Query(..., ge=2000, le=2100),
    tipo: str = Query("ambos", pattern="^(facturas|recibos|ambos)$"),
    company_id: Optional[int] = Query(None),
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid = _resolve_cid(user, company_id)

    sql = _abc_sql(tipo)
    rows = (await db.execute(text(sql), {"cid": cid, "year": year})).mappings().all()

    productos = [
        {"producto": r["producto"], "cantidad": float(r["cantidad"] or 0), "total": float(r["total"] or 0)}
        for r in rows
    ]
    productos.sort(key=lambda x: x["total"], reverse=True)
    total_general = sum(p["total"] for p in productos)
    productos, resumen_abc = _clasificar_abc(productos)

    return {
        "year": year,
        "tipo": tipo,
        "productos": productos,
        "total_general": total_general,
        "resumen_abc": resumen_abc,
    }


@router.get("/productos-abc/mensual")
async def productos_abc_mensual(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    tipo: str = Query("ambos", pattern="^(facturas|recibos|ambos)$"),
    company_id: Optional[int] = Query(None),
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid = _resolve_cid(user, company_id)

    sql = _abc_sql(tipo, "AND MONTH(pid.date) = :month")
    rows = (await db.execute(text(sql), {"cid": cid, "year": year, "month": month})).mappings().all()

    productos = [
        {"producto": r["producto"], "cantidad": float(r["cantidad"] or 0), "total": float(r["total"] or 0)}
        for r in rows
    ]
    productos.sort(key=lambda x: x["total"], reverse=True)
    total_mes = sum(p["total"] for p in productos)
    productos, resumen_abc = _clasificar_abc(productos)

    return {
        "year": year,
        "month": month,
        "nombre_mes": _MESES_ES[month],
        "tipo": tipo,
        "productos": productos,
        "total_mes": total_mes,
        "resumen_abc": resumen_abc,
    }


# ── Helpers de consulta para export ──────────────────────────────────────────

def _sql_enc_facturas():
    return """
        SELECT 'Factura' AS Tipo,
            i.invoice_number AS Numero,
            NULL            AS Cedula,
            i.date          AS Fecha,
            i.time          AS Hora,
            i.employee_id   AS Cod_Empleado,
            w.name          AS Empleado,
            i.cash_amount   AS Total_Efectivo,
            i.credit_card_amount AS T_Credito,
            i.tip           AS Propina,
            i.voided        AS Anulada,
            i.resolution_id AS Id_Resolucion,
            i.customer_id   AS Id_Cliente
        FROM pos_invoices i
        LEFT JOIN pos_waiters w ON w.id = i.employee_id AND w.company_id = i.company_id
        WHERE i.company_id = :cid AND i.date BETWEEN :desde AND :hasta
        ORDER BY i.date, i.invoice_number
    """

def _sql_enc_recibos():
    return """
        SELECT 'Recibo' AS Tipo,
            r.receipt_number AS Numero,
            r.id_number     AS Cedula,
            r.date          AS Fecha,
            r.time          AS Hora,
            r.employee_id   AS Cod_Empleado,
            w.name          AS Empleado,
            r.cash_amount   AS Total_Efectivo,
            r.credit_card_amount AS T_Credito,
            r.tip           AS Propina,
            r.voided        AS Anulada,
            r.resolution_id AS Id_Resolucion,
            r.customer_id   AS Id_Cliente
        FROM pos_receipts r
        LEFT JOIN pos_waiters w ON w.id = r.employee_id AND w.company_id = r.company_id
        WHERE r.company_id = :cid AND r.date BETWEEN :desde AND :hasta
        ORDER BY r.date, r.receipt_number
    """

def _sql_det_facturas():
    return """
        SELECT 'Factura' AS Tipo,
            d.order_number   AS Nro_Pedido,
            d.date           AS Fecha,
            d.invoice_number AS Nro_Factura,
            d.dish_id        AS Id_Plato,
            d.item           AS Item,
            d.quantity       AS Cantidad,
            d.dish_amount    AS Valor,
            d.notes          AS Novedad,
            d.discount_pct   AS Porc_Descuento_Plato,
            NULL             AS Porc_Descuento_General,
            NULL             AS Cambios,
            NULL             AS Hora_Plato,
            pl.tax           AS Impuesto,
            d.complimentary  AS Producto_Personalizado,
            d.depends_on     AS Depende,
            pl.name          AS Plato_Nombre,
            pl.product_code  AS Codigo_Producto,
            pl.price         AS Plato_Valor,
            pl.active        AS Plato_Activo,
            pl.category_id   AS Cod_Categoria,
            pl.product_cost  AS Costo_Producto,
            pl.minimum_stock AS Stock_Minimo
        FROM pos_invoice_details d
        LEFT JOIN pos_dishes pl ON pl.id = d.dish_id AND pl.company_id = d.company_id
        WHERE d.company_id = :cid AND d.date BETWEEN :desde AND :hasta
        ORDER BY d.date, d.invoice_number, d.item
    """

def _sql_det_recibos():
    return """
        SELECT 'Recibo' AS Tipo,
            d.order_number   AS Nro_Pedido,
            d.date           AS Fecha,
            d.receipt_number AS Nro_Factura,
            d.dish_id        AS Id_Plato,
            d.item           AS Item,
            d.quantity       AS Cantidad,
            d.dish_amount    AS Valor,
            d.notes          AS Novedad,
            d.discount_pct   AS Porc_Descuento_Plato,
            NULL             AS Porc_Descuento_General,
            NULL             AS Cambios,
            NULL             AS Hora_Plato,
            pl.tax           AS Impuesto,
            d.complimentary  AS Producto_Personalizado,
            d.depends_on     AS Depende,
            pl.name          AS Plato_Nombre,
            pl.product_code  AS Codigo_Producto,
            pl.price         AS Plato_Valor,
            pl.active        AS Plato_Activo,
            pl.category_id   AS Cod_Categoria,
            pl.product_cost  AS Costo_Producto,
            pl.minimum_stock AS Stock_Minimo
        FROM pos_receipt_invoice_details d
        LEFT JOIN pos_dishes pl ON pl.id = d.dish_id AND pl.company_id = d.company_id
        WHERE d.company_id = :cid AND d.date BETWEEN :desde AND :hasta
        ORDER BY d.date, d.receipt_number, d.item
    """

def _sql_fp_facturas():
    return """
        SELECT 'Factura' AS Tipo,
            pm.item              AS Item,
            pm.payment_method_id AS Id_Forma_Pago,
            pm.card_id           AS Id_Tarjeta,
            pm.invoice_number    AS Nro_Factura,
            pm.amount            AS Valor,
            pm.date              AS Fecha,
            pm.delivery_amount   AS Valor_Domicilio,
            pm.order_number      AS Nro_Pedido,
            pt.name              AS FP_Descripcion,
            pt.value             AS FP_Valor,
            pt.is_active         AS FP_Activo
        FROM pos_invoice_payment_methods pm
        LEFT JOIN pos_payment_types pt ON pt.id = pm.payment_method_id AND pt.company_id = pm.company_id
        WHERE pm.company_id = :cid AND pm.date BETWEEN :desde AND :hasta
        ORDER BY pm.date, pm.invoice_number, pm.item
    """

def _sql_fp_recibos():
    return """
        SELECT 'Recibo' AS Tipo,
            pm.item              AS Item,
            pm.payment_method_id AS Id_Forma_Pago,
            pm.card_id           AS Id_Tarjeta,
            pm.invoice_number    AS Nro_Factura,
            pm.amount            AS Valor,
            pm.date              AS Fecha,
            pm.delivery_amount   AS Valor_Domicilio,
            pm.order_number      AS Nro_Pedido,
            pt.name              AS FP_Descripcion,
            pt.value             AS FP_Valor,
            pt.is_active         AS FP_Activo
        FROM pos_receipt_payment_methods pm
        LEFT JOIN pos_payment_types pt ON pt.id = pm.payment_method_id AND pt.company_id = pm.company_id
        WHERE pm.company_id = :cid AND pm.date BETWEEN :desde AND :hasta
        ORDER BY pm.date, pm.invoice_number, pm.item
    """


async def _query_export(db: AsyncSession, cid: int, tipo: str, desde: str, hasta: str):
    """Ejecuta las 3 consultas y retorna (rows_enc, rows_det, rows_fp) como listas de dicts."""
    params = {"cid": cid, "desde": desde, "hasta": hasta}

    async def run(sql):
        return [dict(r) for r in (await db.execute(text(sql), params)).mappings().all()]

    if tipo == "facturas":
        enc = await run(_sql_enc_facturas())
        det = await run(_sql_det_facturas())
        fp  = await run(_sql_fp_facturas())
    elif tipo == "recibos":
        enc = await run(_sql_enc_recibos())
        det = await run(_sql_det_recibos())
        fp  = await run(_sql_fp_recibos())
    else:  # ambos
        enc = (await run(_sql_enc_facturas())) + (await run(_sql_enc_recibos()))
        det = (await run(_sql_det_facturas())) + (await run(_sql_det_recibos()))
        fp  = (await run(_sql_fp_facturas()))  + (await run(_sql_fp_recibos()))

    return enc, det, fp


# ── Endpoint export Excel ─────────────────────────────────────────────────────

@router.get("/export-excel")
async def export_excel(
    year:       int            = Query(..., ge=2000, le=2100),
    month:      Optional[int]  = Query(None, ge=1, le=12),
    tipo:       str            = Query("ambos", pattern="^(facturas|recibos|ambos)$"),
    company_id: Optional[int]  = Query(None),
    authorization: str         = Header(None),
    db: AsyncSession           = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid  = _resolve_cid(user, company_id)

    if month:
        desde = f"{year}-{month:02d}-01"
        hasta = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}"
        label = f"{year}-{month:02d}"
    else:
        desde = f"{year}-01-01"
        hasta = f"{year}-12-31"
        label = str(year)

    enc, det, fp = await _query_export(db, cid, tipo, desde, hasta)
    xlsx_bytes   = build_ventas_excel(enc, det, fp)

    filename = f"ventas_{label}_{tipo}.xlsx"
    return StreamingResponse(
        io.BytesIO(xlsx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
