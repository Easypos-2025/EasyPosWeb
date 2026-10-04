"""
Movimientos de Caja: Registro Gastos · Registro Compras · Otros Ingresos · Otros Egresos.

  GET  /api/caja/movimientos/{tipo}/opciones                 conceptos, formas de pago, permisos, Id_Caja abierto
  GET  /api/caja/movimientos/{tipo}?periodo=&fecha=          listado del periodo (Día / Mes / Año según el rol)
  POST /api/caja/movimientos/{tipo}                          registrar en el Id_Caja abierto
  POST /api/caja/movimientos/{tipo}/{id_registro}/anular     anular (nunca se elimina)
  POST /api/caja/movimientos/{tipo}/imprimir                 tirilla del listado

Tablas espejo del escritorio (gastos, compras, otros_ingresos, otros_egresos) y su forma de pago en
pos_cash_movement_payments (ingresos_egresos_forma_pago, type_id = tipo_concepto).
  · id_registro: consecutivo por empresa (MAX + 1). Nro_Movimiento = 1.
  · Fecha = fecha de apertura del Id_Caja (igual que los recibos); Cod_Empleado = cajero del Id_Caja.
  · Anular: permiso "Anular Movimientos de Caja", con motivo, solo movimientos hechos en la web y
    mientras su Id_Caja siga abierto. Los anulados no suman en el Cuadre de Caja.
La empresa sale siempre de la sesión (tenant); los conceptos y formas de pago se validan contra ella.
"""
from datetime import datetime
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Annotated

from app.auth.dependencies import get_current_user
from app.auth.tenant import tenant_guard
from app.database import get_db
from app.models.user_model import User
from app.routers.pos_shift_router import _BOG, _VIGENTE, _id_caja_header, _turno_abierto
from app.services import periodos as per
from app.services.formas_pago import es_efectivo_sql
from app.services.permisos import permisos_usuario

router = APIRouter(prefix="/api/caja/movimientos", tags=["Caja Movimientos"], dependencies=[Depends(tenant_guard)])

# tipo (ruta) → (tabla, tipo_concepto = type_id de la forma de pago, título)
TIPOS = {
    "gastos": ("pos_expenses", 1, "Gastos"),
    "compras": ("pos_purchases", 2, "Compras"),
    "otros-egresos": ("pos_other_expenses", 3, "Otros Egresos"),
    "otros-ingresos": ("pos_other_incomes", 4, "Otros Ingresos"),
}
Tipo = Literal["gastos", "compras", "otros-egresos", "otros-ingresos"]
Money = Annotated[float, Field(gt=0, le=2_000_000_000)]
Texto = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]
LIMITE = 1000


class PagoIn(BaseModel):
    payment_method_id: int
    amount: Annotated[float, Field(ge=0, le=2_000_000_000)]
    notes: Optional[Texto] = None


class MovimientoIn(BaseModel):
    concept_id: int
    sub_concept_id: int = 0
    amount: Money
    detail: Optional[Texto] = None
    payments: List[PagoIn] = Field(default_factory=list, max_length=10)
    company_id: Optional[int] = None      # lo valida tenant_guard; no se usa


class AnularIn(BaseModel):
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=255)]
    company_id: Optional[int] = None


class ImprimirIn(BaseModel):
    periodo: Literal["dia", "mes", "anio"] = "dia"
    fecha: str
    printer_id: int
    raw: bool = False
    company_id: Optional[int] = None


def _ahora() -> datetime:
    return datetime.now(_BOG).replace(tzinfo=None)


def _tipo(tipo: str) -> tuple[str, int, str]:
    if tipo not in TIPOS:
        raise HTTPException(status_code=404, detail="Tipo de movimiento no válido")
    return TIPOS[tipo]


async def _formas_pago(db: AsyncSession, cid: int) -> list[dict]:
    rows = (await db.execute(text(
        f"SELECT id, name, is_default, {es_efectivo_sql('pos_payment_types')} AS es_efectivo, ask_notes "
        "FROM pos_payment_types WHERE company_id = :cid AND is_active = 1 ORDER BY is_default DESC, id"
    ), {"cid": cid})).mappings().all()
    return [{"id": int(r["id"]), "name": r["name"], "es_efectivo": bool(r["es_efectivo"]),
             "is_default": bool(r["is_default"]), "ask_notes": bool(r["ask_notes"])} for r in rows]


async def validar_pagos(db: AsyncSession, cid: int, total: int, payments: List[PagoIn]) -> List[PagoIn]:
    """Formas de pago de la empresa y activas, que sumen exactamente `total`.
    Sin formas → todo en EFECTIVO (o la forma por defecto)."""
    fps = {f["id"]: f for f in await _formas_pago(db, cid)}
    pagos = [p for p in payments if p.amount > 0]
    if not pagos:
        fp = next((f for f in fps.values() if f["es_efectivo"]), None) or next((f for f in fps.values() if f["is_default"]), None)
        if not fp:
            raise HTTPException(status_code=422, detail="La empresa no tiene la forma de pago EFECTIVO activa")
        pagos = [PagoIn(payment_method_id=fp["id"], amount=total)]
    for p in pagos:
        fp = fps.get(p.payment_method_id)
        if not fp:
            raise HTTPException(status_code=422, detail="Forma de pago no válida o inactiva")
        if fp["ask_notes"] and not (p.notes or "").strip():
            raise HTTPException(status_code=422, detail=f"La forma de pago {fp['name']} exige una observación")
    pagado = sum(int(round(p.amount)) for p in pagos)
    if pagado != total:
        raise HTTPException(status_code=422, detail=f"Las formas de pago suman ${pagado:,} y el valor es ${total:,}".replace(",", "."))
    return pagos


async def guardar_pagos(db: AsyncSession, cid: int, id_caja: int, fecha: str, tipo_id: int, mov_id: int,
                        pagos: List[PagoIn]) -> None:
    """ingresos_egresos_forma_pago: una fila por forma de pago (type_id = tipo de movimiento)."""
    sig = await _siguiente(db, "pos_cash_movement_payments", cid)
    for i, p in enumerate(pagos):
        await db.execute(text("""
            INSERT INTO pos_cash_movement_payments
                (id_registro, company_id, register_id, item, payment_method_id, card_id, invoice_number,
                 type_id, shift, amount, date, authorization, notes, movement_id, synced)
            VALUES (:idr, :cid, :caja, :item, :pm, 0, :num, :t, 0, :amt, :f, 0, :notes, :mov, 0)
        """), {"idr": sig + i, "cid": cid, "caja": id_caja, "item": i + 1, "pm": p.payment_method_id,
               "num": str(mov_id), "t": tipo_id, "amt": int(round(p.amount)), "f": fecha,
               "notes": (p.notes or "").strip() or None, "mov": mov_id})


async def caja_vigente(db: AsyncSession, cid: int, id_caja) -> bool:
    return bool((await db.execute(text(
        f"SELECT 1 FROM pos_cash_register_closings c WHERE c.company_id = :cid AND c.id_registro = :caja AND {_VIGENTE}"
    ), {"cid": cid, "caja": int(id_caja or 0)})).scalar())


async def vigentes(db: AsyncSession, cid: int) -> set:
    return {int(x) for x in (await db.execute(text(
        f"SELECT c.id_registro FROM pos_cash_register_closings c WHERE c.company_id = :cid AND {_VIGENTE}"
    ), {"cid": cid})).scalars().all()}


def armar_tirilla(d: dict, filas, width: int = 32) -> bytes:
    """Tirilla de un listado: encabezado, filas (izquierda, derecha, subtexto) y totales."""
    from app.routers.pos_recibo_impresion_router import _ascii, _money
    ESC = b"\x1b"
    buf = bytearray(ESC + b"@")

    def line(t="", bold=False, center=False):
        buf.extend((ESC + b"E\x01" if bold else b"") + (ESC + b"a\x01" if center else ESC + b"a\x00")
                   + _ascii(t) + b"\n" + (ESC + b"E\x00" if bold else b""))

    def dl(a, b, bold=False):
        a = str(a)[: max(1, width - len(b) - 1)]
        line(a + " " * max(1, width - len(a) - len(b)) + b, bold=bold)

    f = lambda x: f"{x[8:10]}/{x[5:7]}/{x[:4]}"
    line(d["empresa"], bold=True, center=True)
    line(d["titulo"].upper(), bold=True, center=True)
    line(f(d["desde"]) if d["desde"] == d["hasta"] else f"{f(d['desde'])} al {f(d['hasta'])}", center=True)
    line("-" * width)
    for izq, der, sub in filas:
        dl(izq, der)
        if sub:
            line("  " + sub[: width - 2])
    line("-" * width)
    dl("Registros", str(d["registros"]))
    if d.get("anulados"):
        dl("Anulados", str(d["anulados"]))
    dl("TOTAL", _money(d["total"]), True)
    if d["registros"] > len(d["rows"]):
        line(f"(se listan {len(d['rows'])} de {d['registros']})", center=True)
    buf.extend(b"\n" * 4 + b"\x1dV\x42\x00")
    return bytes(buf)


# ─── Opciones de la vista ────────────────────────────────────────────────────

@router.get("/{tipo}/opciones")
async def opciones(
    request: Request,
    tipo: Tipo = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _tabla, tc, titulo = _tipo(tipo)
    cid = current_user.company_id
    conceptos = (await db.execute(text("""
        SELECT concept_id, description FROM pos_cash_concepts
        WHERE company_id = :cid AND concept_type = :t AND is_active = 1 ORDER BY description
    """), {"cid": cid, "t": tc})).mappings().all()
    subs = (await db.execute(text("""
        SELECT s.concept_id, s.subconcept_id, s.description FROM pos_cash_subconcepts s
        JOIN pos_cash_concepts c ON c.company_id = s.company_id AND c.concept_id = s.concept_id
        WHERE s.company_id = :cid AND c.concept_type = :t AND s.is_active = 1 ORDER BY s.description
    """), {"cid": cid, "t": tc})).mappings().all()
    caja = await _turno_abierto(db, cid, current_user.id, _id_caja_header(request))
    p = await permisos_usuario(db, current_user)
    return {
        "titulo": titulo,
        "conceptos": [{"id": int(c["concept_id"]), "nombre": c["description"],
                       "subconceptos": [{"id": int(s["subconcept_id"]), "nombre": s["description"]}
                                        for s in subs if int(s["concept_id"]) == int(c["concept_id"])]}
                      for c in conceptos],
        "formas_pago": await _formas_pago(db, cid),
        "caja": {"id": caja["id"], "caja": caja["caja_nombre"], "cajero": caja["cajero"], "fecha": caja["fecha"]} if caja else None,
        "permisos": {"anteriores": "consultar_anteriores" in p, "periodos": "ver_periodos" in p,
                     "anular": "anular_movimientos" in p},
        "hoy": per.hoy().isoformat(),
    }


# ─── Listado por periodo ─────────────────────────────────────────────────────

async def _listado(db: AsyncSession, user: User, request: Request, tipo: str, periodo: str, fecha: str) -> dict:
    tabla, tc, titulo = _tipo(tipo)
    cid = user.company_id
    desde, hasta = per.rango(periodo, fecha)
    caja = await _turno_abierto(db, cid, user.id, _id_caja_header(request))
    desde, hasta = await per.validar_rango(db, user, desde, hasta, fecha_propia=caja["fecha"] if caja else None)
    p = {"cid": cid, "d": desde, "h": hasta, "t": tc}
    rows = (await db.execute(text(f"""
        SELECT m.id_registro, m.register_id, m.date, m.amount, m.detail, m.voided, m.void_reason,
               m.created_by, m.created_at,
               COALESCE(c.description, '') AS concepto, COALESCE(s.description, '') AS subconcepto,
               COALESCE(e.name, u.nombre, m.employee_code, '') AS cajero,
               (SELECT GROUP_CONCAT(CONCAT(COALESCE(pt.name, 'Forma pago'), ': ', ROUND(mp.amount)) ORDER BY mp.item SEPARATOR ' · ')
                FROM pos_cash_movement_payments mp
                LEFT JOIN pos_payment_types pt ON pt.id = mp.payment_method_id AND pt.company_id = mp.company_id
                WHERE mp.company_id = m.company_id AND mp.type_id = :t AND mp.movement_id = m.id_registro) AS formas
        FROM {tabla} m
        LEFT JOIN pos_cash_concepts c ON c.company_id = m.company_id AND c.concept_id = m.concept_id
        LEFT JOIN pos_cash_subconcepts s ON s.company_id = m.company_id AND s.concept_id = m.concept_id
                                        AND s.subconcept_id = m.sub_concept_id
        LEFT JOIN pos_employees e ON e.company_id = m.company_id AND e.id = CAST(m.employee_code AS SIGNED)
        LEFT JOIN users u ON u.id = m.created_by AND u.company_id = m.company_id
        WHERE m.company_id = :cid AND m.date BETWEEN :d AND :h
        ORDER BY m.date DESC, m.id_registro DESC
        LIMIT {LIMITE}
    """), p)).mappings().all()
    tot = (await db.execute(text(f"""
        SELECT COUNT(*) n, COALESCE(SUM(CASE WHEN voided = 0 THEN amount END), 0) total,
               COALESCE(SUM(voided), 0) anulados
        FROM {tabla} WHERE company_id = :cid AND date BETWEEN :d AND :h
    """), p)).mappings().first()
    abiertos = await vigentes(db, cid) if rows else set()
    return {
        "titulo": titulo, "desde": desde, "hasta": hasta,
        "registros": int(tot["n"] or 0), "total": int(round(float(tot["total"] or 0))),
        "anulados": int(tot["anulados"] or 0),
        "rows": [{
            "id": int(r["id_registro"]), "id_caja": int(r["register_id"] or 0), "fecha": str(r["date"] or ""),
            "concepto": r["concepto"], "subconcepto": r["subconcepto"], "detalle": r["detail"] or "",
            "valor": int(round(float(r["amount"] or 0))), "cajero": r["cajero"] or "",
            "formas": r["formas"] or "", "origen": "web" if r["created_by"] else "escritorio",
            "anulado": bool(r["voided"]), "motivo": r["void_reason"] or "",
            "caja_abierta": int(r["register_id"] or 0) in abiertos,
        } for r in rows],
    }


@router.get("/{tipo}")
async def listar(
    request: Request,
    tipo: Tipo = Path(...),
    periodo: Literal["dia", "mes", "anio"] = Query("dia"),
    fecha: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _listado(db, current_user, request, tipo, periodo, fecha or per.hoy().isoformat())


# ─── Registrar ───────────────────────────────────────────────────────────────

async def _siguiente(db: AsyncSession, tabla: str, cid: int) -> int:
    return int((await db.execute(text(
        f"SELECT COALESCE(MAX(id_registro), 0) + 1 FROM {tabla} WHERE company_id = :cid FOR UPDATE"
    ), {"cid": cid})).scalar())


@router.post("/{tipo}")
async def registrar(
    body: MovimientoIn,
    request: Request,
    tipo: Tipo = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tabla, tc, titulo = _tipo(tipo)
    cid = current_user.company_id
    caja = await _turno_abierto(db, cid, current_user.id, _id_caja_header(request))
    if not caja:
        raise HTTPException(status_code=409, detail="Debe abrir la caja antes de registrar movimientos")

    # Concepto y subconcepto: de la empresa, del tipo y activos
    if not (await db.execute(text("""
        SELECT 1 FROM pos_cash_concepts WHERE company_id = :cid AND concept_id = :c AND concept_type = :t AND is_active = 1
    """), {"cid": cid, "c": body.concept_id, "t": tc})).scalar():
        raise HTTPException(status_code=422, detail="Concepto no válido o inactivo")
    if body.sub_concept_id and not (await db.execute(text("""
        SELECT 1 FROM pos_cash_subconcepts WHERE company_id = :cid AND concept_id = :c AND subconcept_id = :s AND is_active = 1
    """), {"cid": cid, "c": body.concept_id, "s": body.sub_concept_id})).scalar():
        raise HTTPException(status_code=422, detail="Subconcepto no válido o inactivo")

    total = int(round(body.amount))
    pagos = await validar_pagos(db, cid, total, body.payments)
    fecha = caja["fecha"] or per.hoy().isoformat()
    for intento in range(3):
        try:
            idr = await _siguiente(db, tabla, cid)
            await db.execute(text(f"""
                INSERT INTO {tabla} (id_registro, company_id, register_id, date, amount, employee_code, concept_id,
                                     sub_concept_id, shift, movement_number, detail, synced, created_by, created_at)
                VALUES (:idr, :cid, :caja, :f, :amt, :emp, :c, :s, 0, 1, :det, 0, :uid, :now)
            """), {"idr": idr, "cid": cid, "caja": caja["id"], "f": fecha, "amt": total,
                   "emp": str(caja["cajero_id"] or current_user.id)[:15], "c": body.concept_id,
                   "s": body.sub_concept_id or 0, "det": (body.detail or "").strip() or None,
                   "uid": current_user.id, "now": _ahora()})
            await guardar_pagos(db, cid, caja["id"], fecha, tc, idr, pagos)
            await db.commit()
            return {"ok": True, "id": idr, "id_caja": caja["id"], "fecha": fecha}
        except IntegrityError:
            await db.rollback()
            if intento == 2:
                raise HTTPException(status_code=409, detail="No se pudo asignar el número, intente de nuevo")


# ─── Anular ──────────────────────────────────────────────────────────────────

@router.post("/{tipo}/{id_registro}/anular")
async def anular(
    body: AnularIn,
    tipo: Tipo = Path(...),
    id_registro: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tabla, _tc, _titulo = _tipo(tipo)
    cid = current_user.company_id
    if "anular_movimientos" not in await permisos_usuario(db, current_user):
        raise HTTPException(status_code=403, detail="Su rol no tiene permiso para anular movimientos de caja")
    m = (await db.execute(text(f"""
        SELECT register_id, voided, created_by FROM {tabla} WHERE company_id = :cid AND id_registro = :id
    """), {"cid": cid, "id": id_registro})).mappings().first()
    if not m:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")
    if m["voided"]:
        raise HTTPException(status_code=409, detail="El movimiento ya está anulado")
    if not m["created_by"]:
        raise HTTPException(status_code=409, detail="Este movimiento se registró en el escritorio: se anula allá")
    if not await caja_vigente(db, cid, m["register_id"]):
        raise HTTPException(status_code=409, detail="El Id_Caja de este movimiento ya está cerrado")
    await db.execute(text(f"""
        UPDATE {tabla} SET voided = 1, void_reason = :r, voided_by = :uid, voided_at = :now
        WHERE company_id = :cid AND id_registro = :id AND voided = 0
    """), {"r": body.reason, "uid": current_user.id, "now": _ahora(), "cid": cid, "id": id_registro})
    await db.commit()
    return {"ok": True}


# ─── Imprimir (tirilla del listado) ──────────────────────────────────────────

@router.post("/{tipo}/imprimir")
async def imprimir(
    body: ImprimirIn,
    request: Request,
    tipo: Tipo = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.routers.pos_recibo_impresion_router import enviar_tirilla, _money
    cid = current_user.company_id
    # Valida permisos del periodo antes de tocar la impresora
    lst = await _listado(db, current_user, request, tipo, body.periodo, body.fecha)

    async def datos():
        empresa = (await db.execute(text("SELECT name FROM companies WHERE id_company = :c"), {"c": cid})).scalar() or ""
        return {"empresa": empresa, **lst}

    def armar(d: dict) -> bytes:
        return armar_tirilla(d, [(f"#{r['id']} {r['fecha'][5:10]} {r['concepto']}",
                                  "ANULADO" if r["anulado"] else _money(r["valor"]),
                                  " - ".join(x for x in (r["subconcepto"], r["detalle"]) if x)) for r in d["rows"]])

    return await enviar_tirilla(db, cid, body.printer_id, body.raw, datos, armar=armar)
