"""
Apertura / cierre de turno de caja (equivalente web de `cajas_cierres`
de escritorio, tabla `pos_cash_register_closings`).

Prerrequisito transversal: cualquier operación que mueva dinero (registrar
recibo, gasto, compra, vale, ingreso) debe exigir un turno de caja abierto
para poder anexar el id_caja (aquí: el id de la fila de cierre) al
movimiento. Ver `require_open_shift`.

Nota de campo: `pos_cash_register_closings.customer_sales` es, en el
propósito original de la columna, la venta a clientes para el cuadre de
caja (así la mapea el sync de escritorio). Por decisión explícita del
negocio, este mismo campo se reutiliza aquí para guardar el id del usuario
que abrió el turno — igual que hace el programa de escritorio con su
campo `Venta_Clientes`. No confundir con una métrica de ventas.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user_model import User
from app.routers.pos_comanda_router import _auth_comanda

router = APIRouter(prefix="/api/pos/turno", tags=["POS Turno de Caja"])

# Hora de Colombia (el servidor corre en UTC): la apertura/cierre y la regla "caja del día"
_BOG = timezone(timedelta(hours=-5))


def _ahora() -> datetime:
    return datetime.now(_BOG).replace(tzinfo=None)


def _hoy() -> str:
    return _ahora().date().isoformat()


def _fecha_turno(turno: dict) -> Optional[str]:
    """Fecha (AAAA-MM-DD) de apertura del turno, según opening_datetime o date."""
    for k in ("opening_datetime", "date"):
        v = turno.get(k)
        if v:
            txt = str(v)[:10]
            if len(txt) == 10 and txt[4] == "-":
                return txt
    return None


async def _es_admin(db: AsyncSession, user: User) -> bool:
    from app.models.role_model import Role
    role = await db.get(Role, user.role_id) if user.role_id else None
    return bool(role) and (bool(role.is_system) or "ADMIN" in (role.name or "").upper())


async def _turno_abierto(db: AsyncSession, company_id: int, user_id: int) -> dict | None:
    row = (await db.execute(text("""
        SELECT c.id, c.register_number, c.base_amount, c.opening_datetime, c.date,
               COALESCE(r.name, CONCAT('Caja ', c.register_number)) AS caja_nombre
        FROM pos_cash_register_closings c
        LEFT JOIN pos_cash_registers r ON r.company_id = c.company_id AND r.id = c.register_number
        WHERE c.company_id = :cid AND c.customer_sales = :uid AND c.closed = 0
        ORDER BY c.id DESC LIMIT 1
    """), {"cid": company_id, "uid": user_id})).mappings().first()
    if not row:
        return None
    t = dict(row)
    t["fecha"] = _fecha_turno(t)
    t["es_de_hoy"] = t["fecha"] == _hoy()
    t["opening_datetime"] = str(t["opening_datetime"] or "")
    t["date"] = str(t["date"] or "")
    return t


@router.get("/company-abierto")
async def turno_company_abierto(
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(_auth_comanda),
):
    """
    Chequeo liviano para la comanda (mesero/TPV, que no inician sesión como
    `users` admin): ¿hay algún turno de caja abierto en la empresa, sin
    importar qué usuario/cajero lo abrió? Gate de "tomar pedido".
    """
    row = (await db.execute(text(
        "SELECT id FROM pos_cash_register_closings WHERE company_id = :cid AND closed = 0 LIMIT 1"
    ), {"cid": auth["company_id"]})).mappings().first()
    return {"abierto": row is not None}


@router.get("/actual")
async def turno_actual(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _turno_abierto(db, current_user.company_id, current_user.id) or {}


@router.get("/cajas")
async def cajas_disponibles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cid = current_user.company_id
    cajas = (await db.execute(text("""
        SELECT id, name, type FROM pos_cash_registers
        WHERE company_id = :cid AND is_active = 1
        ORDER BY type DESC, name
    """), {"cid": cid})).mappings().all()

    ocupadas = (await db.execute(text("""
        SELECT register_number, customer_sales AS user_id
        FROM pos_cash_register_closings
        WHERE company_id = :cid AND closed = 0
    """), {"cid": cid})).mappings().all()
    ocupada_por = {int(o["register_number"]): int(o["user_id"]) for o in ocupadas}

    result = []
    for c in cajas:
        ocupante = ocupada_por.get(c["id"])
        result.append({
            **dict(c),
            "ocupada": ocupante is not None,
            "ocupada_por_mi": ocupante == current_user.id,
        })
    return result


@router.post("/abrir")
async def abrir_turno(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cid, uid = current_user.company_id, current_user.id

    # Si el usuario ya tiene un turno abierto (en cualquier caja), se continúa
    # con ese mismo turno hasta que se cierre — no se abre uno nuevo.
    existente = await _turno_abierto(db, cid, uid)
    if existente:
        return existente      # se sigue con el mismo turno (puede pasar de medianoche) hasta cerrarlo

    register_number = body.get("register_number")
    try:
        base_amount = float(body.get("base_amount") or 0)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Base inicial no válida")
    if base_amount < 0 or base_amount > 1e12:
        raise HTTPException(status_code=422, detail="Base inicial no válida")
    pc = (body.get("pc") or "")[:50]
    if register_number is None:
        raise HTTPException(status_code=422, detail="register_number es requerido")

    caja = (await db.execute(text(
        "SELECT id FROM pos_cash_registers WHERE id = :id AND company_id = :cid AND is_active = 1"
    ), {"id": register_number, "cid": cid})).mappings().first()
    if not caja:
        raise HTTPException(status_code=404, detail="Caja no encontrada")

    ocupada = (await db.execute(text("""
        SELECT id FROM pos_cash_register_closings
        WHERE company_id = :cid AND register_number = :rn AND closed = 0
    """), {"cid": cid, "rn": register_number})).mappings().first()
    if ocupada:
        raise HTTPException(status_code=409, detail="Esta caja ya está abierta por otro usuario")

    # `id_registro` participa en la UNIQUE KEY (id_registro, company_id) que
    # el escritorio usa para no duplicar cierres sincronizados. El escritorio
    # siempre manda valores positivos (su propio autoincremental); las
    # aperturas nativas de la web usan una secuencia negativa propia para no
    # chocar nunca con eso ni entre sí.
    for _ in range(5):
        next_id_registro = (await db.execute(text(
            "SELECT COALESCE(MIN(id_registro), 0) - 1 AS next FROM pos_cash_register_closings WHERE company_id = :cid"
        ), {"cid": cid})).mappings().first()["next"]
        try:
            await db.execute(text("""
                INSERT INTO pos_cash_register_closings
                    (id_registro, register_number, date, base_amount, customer_sales, closed,
                     opened_pc, opening_datetime, company_id, synced)
                VALUES
                    (:idreg, :rn, :hoy, :base, :uid, 0, :pc, :now, :cid, 1)
            """), {
                "idreg": next_id_registro, "rn": register_number, "base": base_amount, "uid": uid, "pc": pc,
                "now": _ahora().strftime("%Y-%m-%d %H:%M:%S"), "hoy": _hoy(), "cid": cid,
            })
            # cajas.Abierta: la caja queda bloqueada para otros usuarios
            await db.execute(text(
                "UPDATE pos_cash_registers SET is_open = 1, employee_id = :uid WHERE company_id = :cid AND id = :rn"
            ), {"uid": uid, "cid": cid, "rn": register_number})
            await db.commit()
            break
        except IntegrityError:
            await db.rollback()
            continue
    else:
        raise HTTPException(status_code=409, detail="No se pudo abrir el turno, intente nuevamente")

    return await _turno_abierto(db, cid, uid)


@router.post("/cerrar")
async def cerrar_turno(
    body: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cierra un turno: el propio (sin closing_id) o, si es Admin, el de otro usuario.
    El cuadre de caja se hará en la vista Cuadre de Caja; aquí solo se cierra y se libera la caja."""
    cid = current_user.company_id
    closing_id = (body or {}).get("closing_id")
    if closing_id:
        turno = (await db.execute(text("""
            SELECT id, register_number, customer_sales AS user_id FROM pos_cash_register_closings
            WHERE id = :id AND company_id = :cid AND closed = 0
        """), {"id": int(closing_id), "cid": cid})).mappings().first()
        if not turno:
            raise HTTPException(status_code=404, detail="Turno no encontrado o ya cerrado")
        if int(turno["user_id"] or 0) != current_user.id and not await _es_admin(db, current_user):
            raise HTTPException(status_code=403, detail="Solo el usuario que abrió la caja o un administrador pueden cerrarla")
    else:
        turno = await _turno_abierto(db, cid, current_user.id)
        if not turno:
            raise HTTPException(status_code=404, detail="No tiene un turno de caja abierto")

    await cerrar_y_liberar(db, cid, int(turno["id"]), int(turno["register_number"]))
    await db.commit()
    return {"ok": True}


# Columnas del cuadre que se guardan al cerrar (cuadre_caja del escritorio)
_CAMPOS_CUADRE = ("base_amount", "final_base", "total_sales", "cash_sales", "voucher_sales", "tips",
                  "expenses", "purchases", "vouchers", "total_invoices", "voucher_invoices",
                  "voided_invoices", "invoice_start", "invoice_end", "delivery_income", "delivery_expense")


async def cerrar_y_liberar(db: AsyncSession, cid: int, turno_id: int, register_number: int,
                           cuadre: Optional[dict] = None) -> None:
    """Marca el turno cerrado (con la foto del cuadre si se envía) y libera la caja.
    No hace commit: lo hace quien llama."""
    campos = {k: v for k, v in (cuadre or {}).items() if k in _CAMPOS_CUADRE}
    sets = "".join(f", {k} = :{k}" for k in campos)
    await db.execute(text(f"""
        UPDATE pos_cash_register_closings
        SET closed = 1, closing_datetime = :now{sets}
        WHERE id = :id AND company_id = :cid AND closed = 0
    """), {"now": _ahora().strftime("%Y-%m-%d %H:%M:%S"), "id": turno_id, "cid": cid, **campos})
    # cajas.Abierta = 0 si ya no queda otro turno abierto en esa caja
    await db.execute(text("""
        UPDATE pos_cash_registers SET is_open = 0, employee_id = 0
        WHERE company_id = :cid AND id = :rn
          AND NOT EXISTS (SELECT 1 FROM pos_cash_register_closings
                          WHERE company_id = :cid AND register_number = :rn AND closed = 0)
    """), {"cid": cid, "rn": register_number})


async def require_open_shift(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Dependency reutilizable: exige turno de caja abierto antes de operar con dinero."""
    turno = await _turno_abierto(db, current_user.company_id, current_user.id)
    if not turno:
        raise HTTPException(status_code=409, detail="Debe abrir un turno de caja antes de continuar")
    # Un turno puede pasar de medianoche (negocios 24 h): los recibos se registran con la
    # fecha de APERTURA del turno (turno["fecha"]); la factura electrónica, solo con la de hoy.
    return turno
