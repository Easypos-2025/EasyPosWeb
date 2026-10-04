"""
Vales y Abono de Vales (menú Transaccional).

  GET  /api/caja/vales/opciones                         empleados, formas de pago, permisos, Id_Caja abierto
  GET  /api/caja/vales?periodo=&fecha=&estado=          vales del periodo (todos | pendientes | pagados)
  GET  /api/caja/vales/pendientes?empleado=             vales sin pagar de cualquier fecha (para abonar)
  POST /api/caja/vales                                  registrar vale en el Id_Caja abierto
  POST /api/caja/vales/{id}/anular                      anular vale (solo si no está pagado)
  GET  /api/caja/vales/abonos?periodo=&fecha=           abonos del periodo
  POST /api/caja/vales/abonos                           abonar (paga el vale completo)
  POST /api/caja/vales/abonos/{id}/anular               anular abono (el vale vuelve a pendiente)
  POST /api/caja/vales/imprimir · /abonos/imprimir      tirilla del listado

Vales = vales del escritorio (pos_cash_advances): salen de la caja; Estado 0 = pendiente, 1 = pagado.
Forma de pago en pos_cash_movement_payments con type_id 5 (vale) y 6 (abono), EFECTIVO por defecto.
El abono paga el vale completo (el valor lo toma el servidor del vale), entra a la caja del Id_Caja
abierto y deja el vale en Estado 1. Nada se elimina: se anula con motivo (permiso
"Anular Movimientos de Caja"), solo lo registrado en la web y mientras su Id_Caja siga abierto.
"""
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
from app.routers.caja_movimientos_router import (
    LIMITE, AnularIn, Money, PagoIn, Texto, _ahora, _formas_pago, _siguiente, armar_tirilla,
    caja_vigente, guardar_pagos, validar_pagos, vigentes,
)
from app.routers.pos_shift_router import _id_caja_header, _turno_abierto, exigir_usuario_caja
from app.services import periodos as per
from app.services.permisos import permisos_usuario

router = APIRouter(prefix="/api/caja/vales", tags=["Caja Vales"], dependencies=[Depends(tenant_guard)])

TIPO_VALE, TIPO_ABONO = 5, 6
Periodo = Literal["dia", "mes", "anio"]


class ValeIn(BaseModel):
    employee_id: int
    amount: Money
    description: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]] = None
    payments: List[PagoIn] = Field(default_factory=list, max_length=10)
    company_id: Optional[int] = None


class AbonoIn(BaseModel):
    advance_id: int
    detail: Optional[Texto] = None
    payments: List[PagoIn] = Field(default_factory=list, max_length=10)
    company_id: Optional[int] = None


class ImprimirIn(BaseModel):
    periodo: Periodo = "dia"
    fecha: str
    estado: Literal["todos", "pendientes", "pagados"] = "todos"
    printer_id: int
    raw: bool = False
    company_id: Optional[int] = None


_EMPLEADO = """LEFT JOIN pos_employees e ON e.company_id = {a}.company_id AND e.id = CAST({a}.employee_code AS SIGNED)"""


async def _caja(db: AsyncSession, user: User, request: Request) -> Optional[dict]:
    return await _turno_abierto(db, user.company_id, user.id, _id_caja_header(request))


async def _puede_anular(db: AsyncSession, user: User) -> None:
    if "anular_movimientos" not in await permisos_usuario(db, user):
        raise HTTPException(status_code=403, detail="Su rol no tiene permiso para anular movimientos de caja")


async def _rango(db: AsyncSession, user: User, request: Request, periodo: str, fecha: Optional[str]) -> tuple[str, str]:
    desde, hasta = per.rango(periodo, fecha or per.hoy().isoformat())
    caja = await _caja(db, user, request)
    return await per.validar_rango(db, user, desde, hasta, fecha_propia=caja["fecha"] if caja else None)


def _fp_sql(tipo: int, alias: str) -> str:
    return f"""(SELECT GROUP_CONCAT(CONCAT(COALESCE(pt.name, 'Forma pago'), ': ', ROUND(mp.amount)) ORDER BY mp.item SEPARATOR ' · ')
                FROM pos_cash_movement_payments mp
                LEFT JOIN pos_payment_types pt ON pt.id = mp.payment_method_id AND pt.company_id = mp.company_id
                WHERE mp.company_id = {alias}.company_id AND mp.type_id = {tipo} AND mp.movement_id = {alias}.id_registro)"""


def _vale_dict(r, abiertos: set) -> dict:
    return {"id": int(r["id_registro"]), "id_caja": int(r["register_id"] or 0), "fecha": str(r["date"] or ""),
            "empleado": r["empleado"] or "", "empleado_id": r["employee_code"] or "",
            "descripcion": r["description"] or "", "valor": int(round(float(r["amount"] or 0))),
            "pagado": bool(r["status"]), "formas": r.get("formas") or "",
            "origen": "web" if r["created_by"] else "escritorio",
            "anulado": bool(r["voided"]), "motivo": r["void_reason"] or "",
            "caja_abierta": int(r["register_id"] or 0) in abiertos}


# ─── Opciones ────────────────────────────────────────────────────────────────

@router.get("/opciones")
async def opciones(request: Request, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    cid = current_user.company_id
    empleados = (await db.execute(text(
        "SELECT id, name FROM pos_employees WHERE company_id = :cid AND status = 1 ORDER BY name"
    ), {"cid": cid})).mappings().all()
    caja = await _caja(db, current_user, request)
    p = await permisos_usuario(db, current_user)
    return {
        "empleados": [{"id": int(e["id"]), "nombre": e["name"]} for e in empleados],
        "formas_pago": await _formas_pago(db, cid),
        "caja": {"id": caja["id"], "caja": caja["caja_nombre"], "cajero": caja["cajero"], "fecha": caja["fecha"]} if caja else None,
        "permisos": {"anteriores": "consultar_anteriores" in p, "periodos": "ver_periodos" in p,
                     "anular": "anular_movimientos" in p},
        "hoy": per.hoy().isoformat(),
    }


# ─── Vales ───────────────────────────────────────────────────────────────────

async def _listar_vales(db, user, request, periodo, fecha, estado) -> dict:
    cid = user.company_id
    desde, hasta = await _rango(db, user, request, periodo, fecha)
    filtro = {"pendientes": " AND v.status = 0 AND v.voided = 0", "pagados": " AND v.status = 1"}.get(estado, "")
    p = {"cid": cid, "d": desde, "h": hasta}
    rows = (await db.execute(text(f"""
        SELECT v.id_registro, v.register_id, v.date, v.amount, v.employee_code, v.status, v.description,
               v.voided, v.void_reason, v.created_by, COALESCE(e.name, v.employee_code, '') AS empleado,
               {_fp_sql(TIPO_VALE, 'v')} AS formas
        FROM pos_cash_advances v {_EMPLEADO.format(a='v')}
        WHERE v.company_id = :cid AND v.date BETWEEN :d AND :h{filtro}
        ORDER BY v.date DESC, v.id_registro DESC LIMIT {LIMITE}
    """), p)).mappings().all()
    tot = (await db.execute(text(f"""
        SELECT COUNT(*) n, COALESCE(SUM(CASE WHEN v.voided = 0 THEN v.amount END), 0) total,
               COALESCE(SUM(v.voided), 0) anulados,
               COALESCE(SUM(CASE WHEN v.voided = 0 AND v.status = 0 THEN v.amount END), 0) pendiente
        FROM pos_cash_advances v WHERE v.company_id = :cid AND v.date BETWEEN :d AND :h{filtro}
    """), p)).mappings().first()
    abiertos = await vigentes(db, cid) if rows else set()
    return {"titulo": "Vales", "desde": desde, "hasta": hasta, "registros": int(tot["n"] or 0),
            "total": int(round(float(tot["total"] or 0))), "anulados": int(tot["anulados"] or 0),
            "pendiente": int(round(float(tot["pendiente"] or 0))),
            "rows": [_vale_dict(r, abiertos) for r in rows]}


@router.get("")
async def listar_vales(
    request: Request,
    periodo: Periodo = Query("dia"),
    fecha: Optional[str] = Query(None),
    estado: Literal["todos", "pendientes", "pagados"] = Query("todos"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _listar_vales(db, current_user, request, periodo, fecha, estado)


@router.get("/pendientes")
async def pendientes(
    empleado: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Vales sin pagar (de cualquier fecha) para el Abono de Vales."""
    cid = current_user.company_id
    where, p = "v.company_id = :cid AND v.status = 0 AND v.voided = 0", {"cid": cid}
    if empleado:
        where += " AND v.employee_code = :emp"
        p["emp"] = str(empleado)
    rows = (await db.execute(text(f"""
        SELECT v.id_registro, v.register_id, v.date, v.amount, v.employee_code, v.status, v.description,
               v.voided, v.void_reason, v.created_by, COALESCE(e.name, v.employee_code, '') AS empleado
        FROM pos_cash_advances v {_EMPLEADO.format(a='v')}
        WHERE {where} ORDER BY v.date, v.id_registro LIMIT {LIMITE}
    """), p)).mappings().all()
    return [_vale_dict(r, set()) for r in rows]


@router.post("")
async def registrar_vale(
    body: ValeIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cid = current_user.company_id
    await exigir_usuario_caja(db, current_user)
    caja = await _caja(db, current_user, request)
    if not caja:
        raise HTTPException(status_code=409, detail="Debe abrir la caja antes de registrar vales")
    if not (await db.execute(text(
        "SELECT 1 FROM pos_employees WHERE company_id = :cid AND id = :id AND status = 1"
    ), {"cid": cid, "id": body.employee_id})).scalar():
        raise HTTPException(status_code=422, detail="Empleado no válido o inactivo")
    total = int(round(body.amount))
    pagos = await validar_pagos(db, cid, total, body.payments)
    fecha = caja["fecha"] or per.hoy().isoformat()
    for intento in range(3):
        try:
            idr = await _siguiente(db, "pos_cash_advances", cid)
            await db.execute(text("""
                INSERT INTO pos_cash_advances (id_registro, company_id, register_id, date, amount, employee_code,
                                               status, description, shift, synced, created_by, created_at)
                VALUES (:idr, :cid, :caja, :f, :amt, :emp, 0, :desc, 0, 0, :uid, :now)
            """), {"idr": idr, "cid": cid, "caja": caja["id"], "f": fecha, "amt": total,
                   "emp": str(body.employee_id), "desc": (body.description or "").strip() or None,
                   "uid": current_user.id, "now": _ahora()})
            await guardar_pagos(db, cid, caja["id"], fecha, TIPO_VALE, idr, pagos)
            await db.commit()
            return {"ok": True, "id": idr, "id_caja": caja["id"], "fecha": fecha}
        except IntegrityError:
            await db.rollback()
            if intento == 2:
                raise HTTPException(status_code=409, detail="No se pudo asignar el número, intente de nuevo")


@router.post("/{vale_id}/anular")
async def anular_vale(
    body: AnularIn,
    vale_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cid = current_user.company_id
    await _puede_anular(db, current_user)
    v = (await db.execute(text(
        "SELECT register_id, status, voided, created_by FROM pos_cash_advances WHERE company_id = :cid AND id_registro = :id"
    ), {"cid": cid, "id": vale_id})).mappings().first()
    if not v:
        raise HTTPException(status_code=404, detail="Vale no encontrado")
    if v["voided"]:
        raise HTTPException(status_code=409, detail="El vale ya está anulado")
    if v["status"]:
        raise HTTPException(status_code=409, detail="El vale ya está pagado: anule primero el abono")
    if not v["created_by"]:
        raise HTTPException(status_code=409, detail="Este vale se registró en el escritorio: se anula allá")
    if not await caja_vigente(db, cid, v["register_id"]):
        raise HTTPException(status_code=409, detail="El Id_Caja de este vale ya está cerrado")
    await db.execute(text("""
        UPDATE pos_cash_advances SET voided = 1, void_reason = :r, voided_by = :uid, voided_at = :now
        WHERE company_id = :cid AND id_registro = :id AND voided = 0 AND status = 0
    """), {"r": body.reason, "uid": current_user.id, "now": _ahora(), "cid": cid, "id": vale_id})
    await db.commit()
    return {"ok": True}


# ─── Abonos ──────────────────────────────────────────────────────────────────

async def _listar_abonos(db, user, request, periodo, fecha) -> dict:
    cid = user.company_id
    desde, hasta = await _rango(db, user, request, periodo, fecha)
    p = {"cid": cid, "d": desde, "h": hasta}
    rows = (await db.execute(text(f"""
        SELECT a.id_registro, a.register_id, a.advance_id, a.date, a.amount, a.detail, a.voided, a.void_reason,
               a.created_by, COALESCE(e.name, a.employee_code, '') AS empleado, v.date AS fecha_vale,
               v.description AS desc_vale, {_fp_sql(TIPO_ABONO, 'a')} AS formas
        FROM pos_cash_advance_payments a {_EMPLEADO.format(a='a')}
        LEFT JOIN pos_cash_advances v ON v.company_id = a.company_id AND v.id_registro = a.advance_id
        WHERE a.company_id = :cid AND a.date BETWEEN :d AND :h
        ORDER BY a.date DESC, a.id_registro DESC LIMIT {LIMITE}
    """), p)).mappings().all()
    tot = (await db.execute(text("""
        SELECT COUNT(*) n, COALESCE(SUM(CASE WHEN voided = 0 THEN amount END), 0) total, COALESCE(SUM(voided), 0) anulados
        FROM pos_cash_advance_payments WHERE company_id = :cid AND date BETWEEN :d AND :h
    """), p)).mappings().first()
    abiertos = await vigentes(db, cid) if rows else set()
    return {"titulo": "Abono Vales", "desde": desde, "hasta": hasta, "registros": int(tot["n"] or 0),
            "total": int(round(float(tot["total"] or 0))), "anulados": int(tot["anulados"] or 0),
            "rows": [{"id": int(r["id_registro"]), "id_caja": int(r["register_id"] or 0), "vale": int(r["advance_id"]),
                      "fecha": str(r["date"] or ""), "fecha_vale": str(r["fecha_vale"] or ""),
                      "empleado": r["empleado"] or "", "descripcion": r["desc_vale"] or "", "detalle": r["detail"] or "",
                      "valor": int(round(float(r["amount"] or 0))), "formas": r["formas"] or "",
                      "origen": "web" if r["created_by"] else "escritorio",
                      "anulado": bool(r["voided"]), "motivo": r["void_reason"] or "",
                      "caja_abierta": int(r["register_id"] or 0) in abiertos} for r in rows]}


@router.get("/abonos")
async def listar_abonos(
    request: Request,
    periodo: Periodo = Query("dia"),
    fecha: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _listar_abonos(db, current_user, request, periodo, fecha)


@router.post("/abonos")
async def abonar(
    body: AbonoIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cid = current_user.company_id
    await exigir_usuario_caja(db, current_user)
    caja = await _caja(db, current_user, request)
    if not caja:
        raise HTTPException(status_code=409, detail="Debe abrir la caja antes de registrar abonos")
    fecha = caja["fecha"] or per.hoy().isoformat()
    for intento in range(3):
        try:
            # Bloquea el vale: dos abonos simultáneos al mismo vale no pueden pasar
            v = (await db.execute(text("""
                SELECT amount, employee_code, status, voided FROM pos_cash_advances
                WHERE company_id = :cid AND id_registro = :id FOR UPDATE
            """), {"cid": cid, "id": body.advance_id})).mappings().first()
            if not v:
                raise HTTPException(status_code=404, detail="Vale no encontrado")
            if v["voided"]:
                raise HTTPException(status_code=409, detail="El vale está anulado")
            if v["status"]:
                raise HTTPException(status_code=409, detail="El vale ya está pagado")
            total = int(round(float(v["amount"] or 0)))      # el abono paga el vale completo
            pagos = await validar_pagos(db, cid, total, body.payments)
            idr = await _siguiente(db, "pos_cash_advance_payments", cid)
            await db.execute(text("""
                INSERT INTO pos_cash_advance_payments (id_registro, company_id, register_id, advance_id, date, amount,
                                                       employee_code, detail, shift, synced, created_by, created_at)
                VALUES (:idr, :cid, :caja, :vale, :f, :amt, :emp, :det, 0, 0, :uid, :now)
            """), {"idr": idr, "cid": cid, "caja": caja["id"], "vale": body.advance_id, "f": fecha, "amt": total,
                   "emp": v["employee_code"], "det": (body.detail or "").strip() or None,
                   "uid": current_user.id, "now": _ahora()})
            await guardar_pagos(db, cid, caja["id"], fecha, TIPO_ABONO, idr, pagos)
            await db.execute(text(
                "UPDATE pos_cash_advances SET status = 1 WHERE company_id = :cid AND id_registro = :id"
            ), {"cid": cid, "id": body.advance_id})
            await db.commit()
            return {"ok": True, "id": idr, "id_caja": caja["id"], "valor": total, "fecha": fecha}
        except IntegrityError:
            await db.rollback()
            if intento == 2:
                raise HTTPException(status_code=409, detail="No se pudo asignar el número, intente de nuevo")
        except HTTPException:
            await db.rollback()
            raise


@router.post("/abonos/{abono_id}/anular")
async def anular_abono(
    body: AnularIn,
    abono_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cid = current_user.company_id
    await _puede_anular(db, current_user)
    a = (await db.execute(text("""
        SELECT register_id, advance_id, voided, created_by FROM pos_cash_advance_payments
        WHERE company_id = :cid AND id_registro = :id
    """), {"cid": cid, "id": abono_id})).mappings().first()
    if not a:
        raise HTTPException(status_code=404, detail="Abono no encontrado")
    if a["voided"]:
        raise HTTPException(status_code=409, detail="El abono ya está anulado")
    if not await caja_vigente(db, cid, a["register_id"]):
        raise HTTPException(status_code=409, detail="El Id_Caja de este abono ya está cerrado")
    await db.execute(text("""
        UPDATE pos_cash_advance_payments SET voided = 1, void_reason = :r, voided_by = :uid, voided_at = :now
        WHERE company_id = :cid AND id_registro = :id AND voided = 0
    """), {"r": body.reason, "uid": current_user.id, "now": _ahora(), "cid": cid, "id": abono_id})
    # El vale vuelve a pendiente (si no le queda otro abono vigente)
    await db.execute(text("""
        UPDATE pos_cash_advances SET status = 0
        WHERE company_id = :cid AND id_registro = :vale
          AND NOT EXISTS (SELECT 1 FROM pos_cash_advance_payments p
                          WHERE p.company_id = :cid AND p.advance_id = :vale AND p.voided = 0)
    """), {"cid": cid, "vale": a["advance_id"]})
    await db.commit()
    return {"ok": True}


# ─── Imprimir ────────────────────────────────────────────────────────────────

async def _empresa(db: AsyncSession, cid: int) -> str:
    return (await db.execute(text("SELECT name FROM companies WHERE id_company = :c"), {"c": cid})).scalar() or ""


@router.post("/imprimir")
async def imprimir_vales(body: ImprimirIn, request: Request, db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    from app.routers.pos_recibo_impresion_router import enviar_tirilla, _money
    cid = current_user.company_id
    lst = await _listar_vales(db, current_user, request, body.periodo, body.fecha, body.estado)

    async def datos():
        return {"empresa": await _empresa(db, cid), **lst}

    def armar(d):
        return armar_tirilla(d, [(f"#{r['id']} {r['fecha'][5:10]} {r['empleado']}",
                                  "ANULADO" if r["anulado"] else _money(r["valor"]),
                                  ("PAGADO " if r["pagado"] else "PENDIENTE ") + r["descripcion"]) for r in d["rows"]])

    return await enviar_tirilla(db, cid, body.printer_id, body.raw, datos, armar=armar)


@router.post("/abonos/imprimir")
async def imprimir_abonos(body: ImprimirIn, request: Request, db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    from app.routers.pos_recibo_impresion_router import enviar_tirilla, _money
    cid = current_user.company_id
    lst = await _listar_abonos(db, current_user, request, body.periodo, body.fecha)

    async def datos():
        return {"empresa": await _empresa(db, cid), **lst}

    def armar(d):
        return armar_tirilla(d, [(f"#{r['id']} {r['fecha'][5:10]} {r['empleado']}",
                                  "ANULADO" if r["anulado"] else _money(r["valor"]),
                                  f"Vale #{r['vale']} {r['descripcion']}".strip()) for r in d["rows"]])

    return await enviar_tirilla(db, cid, body.printer_id, body.raw, datos, armar=armar)
