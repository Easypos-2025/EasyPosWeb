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

from fastapi import APIRouter, Depends, HTTPException, Request
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


# ═══════════════════════════════════════════════════════════════════════════
# Id_Caja (cajas_cierres): la llave de caja es `id_registro`, la misma del escritorio.
#   · Empresa CON escritorio (tiene Id_Caja subidos por la sincronización, synced=1):
#     la caja se abre/cierra solo en el escritorio; la web usa el Id_Caja abierto.
#   · Empresa solo web: la web abre su Id_Caja (positivo, siguiente número libre).
#   Abiertos válidos: de los Cierre=0, solo el mayor Id_Caja de cada cajero (Venta_Clientes);
#   los demás Cierre=0 son registros viejos que no se cerraron en la sincronización.
#   `customer_sales` (Venta_Clientes) = código/cédula del cajero (pos_employees.id); en la
#   web, el id del usuario (se le crea su registro en pos_employees al abrir caja).
# ═══════════════════════════════════════════════════════════════════════════
_VIGENTE = """c.closed = 0 AND c.id_registro = (
    SELECT MAX(c2.id_registro) FROM pos_cash_register_closings c2
    WHERE c2.company_id = c.company_id AND c2.customer_sales = c.customer_sales AND c2.closed = 0)"""

_SELECT_CAJA = """
    SELECT c.id_registro AS id, c.id AS row_id, c.register_number, c.base_amount, c.opening_datetime, c.date,
           CAST(c.customer_sales AS SIGNED) AS cajero_id, c.synced,
           COALESCE(r.name, CONCAT('Caja ', c.register_number)) AS caja_nombre,
           COALESCE(e.name, u.nombre, '') AS cajero
    FROM pos_cash_register_closings c
    LEFT JOIN pos_cash_registers r ON r.company_id = c.company_id AND r.id = c.register_number
    LEFT JOIN pos_employees e ON e.company_id = c.company_id AND e.id = CAST(c.customer_sales AS SIGNED)
    LEFT JOIN users u ON u.id = CAST(c.customer_sales AS SIGNED) AND u.company_id = c.company_id
"""


def _caja_dict(row) -> dict:
    t = dict(row)
    t["fecha"] = _fecha_turno(t)
    t["es_de_hoy"] = t["fecha"] == _hoy()
    t["opening_datetime"] = str(t["opening_datetime"] or "")
    t["date"] = str(t["date"] or "")
    t["origen"] = "escritorio" if int(t.pop("synced") or 0) else "web"
    return t


async def exigir_usuario_caja(db: AsyncSession, user: User) -> None:
    """Control de Acceso: solo los roles con "Es Usuario Caja" abren o usan un Id_Caja."""
    from app.services import permisos
    permisos.exigir(await permisos.permisos_usuario(db, user), "usuario_caja",
                    "Su rol no tiene permiso de usuario de caja")


async def _es_escritorio(db: AsyncSession, company_id: int) -> bool:
    """La empresa maneja la caja desde el escritorio si tiene Id_Caja subidos por la sincronización."""
    return bool((await db.execute(text(
        "SELECT 1 FROM pos_cash_register_closings WHERE company_id = :cid AND synced = 1 LIMIT 1"
    ), {"cid": company_id})).scalar())


async def _cajas_abiertas(db: AsyncSession, company_id: int) -> list[dict]:
    rows = (await db.execute(text(_SELECT_CAJA + f" WHERE c.company_id = :cid AND {_VIGENTE} ORDER BY c.id_registro DESC"),
                             {"cid": company_id})).mappings().all()
    return [_caja_dict(r) for r in rows]


async def _turno_abierto(db: AsyncSession, company_id: int, user_id: int,
                         id_caja: Optional[int] = None) -> dict | None:
    """Id_Caja con el que trabaja el usuario.
    Escritorio: el Id_Caja abierto elegido (header X-Id-Caja); si no eligió (o el elegido ya se
    cerró), el último creado de los abiertos (mayor Id_Caja).
    Solo web: el Id_Caja abierto de ese usuario."""
    abiertas = await _cajas_abiertas(db, company_id)      # ordenadas por Id_Caja descendente
    if await _es_escritorio(db, company_id):
        if id_caja:
            elegida = next((a for a in abiertas if int(a["id"]) == int(id_caja)), None)
            if elegida:
                return elegida
        return abiertas[0] if abiertas else None
    return next((a for a in abiertas if int(a["cajero_id"] or 0) == int(user_id)), None)


def _id_caja_header(request: Request) -> Optional[int]:
    v = (request.headers.get("x-id-caja") or "").strip()
    return int(v) if v.isdigit() else None


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
    return {"abierto": bool(await _cajas_abiertas(db, auth["company_id"]))}


@router.get("/actual")
async def turno_actual(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _turno_abierto(db, current_user.company_id, current_user.id, _id_caja_header(request)) or {}


@router.get("/estado")
async def estado_caja(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Para la ventana de caja: si la empresa abre caja en el escritorio y sus Id_Caja abiertos."""
    cid = current_user.company_id
    escritorio = await _es_escritorio(db, cid)
    return {
        "escritorio": escritorio,
        "abiertas": await _cajas_abiertas(db, cid) if escritorio else [],
        "actual": await _turno_abierto(db, cid, current_user.id, _id_caja_header(request)),
    }


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
    if not cajas and not await _tiene_cajas(db, cid):
        cajas = [CAJA_PROVISIONAL]
    ocupada_por = {int(a["register_number"]): int(a["cajero_id"] or 0) for a in await _cajas_abiertas(db, cid)}
    result = []
    for c in cajas:
        ocupante = ocupada_por.get(c["id"])
        result.append({
            **dict(c),
            "ocupada": ocupante is not None,
            "ocupada_por_mi": ocupante == current_user.id,
        })
    return result


# Empresa sin ninguna caja creada (Configuración → Cajas): se usa la Caja 1 mientras la crean
CAJA_PROVISIONAL = {"id": 1, "name": "Caja 1", "type": 0}


async def _tiene_cajas(db: AsyncSession, cid: int) -> bool:
    return bool((await db.execute(text(
        "SELECT 1 FROM pos_cash_registers WHERE company_id = :cid LIMIT 1"), {"cid": cid})).scalar())


async def _siguiente_id_caja(db: AsyncSession, cid: int) -> int:
    """Siguiente Id_Caja libre: mayor que cualquier Id_Caja usado (también en recibos, facturas,
    gastos y compras que referencien Id_Caja que no estén en cajas_cierres)."""
    return int((await db.execute(text("""
        SELECT GREATEST(
            COALESCE((SELECT MAX(id_registro) FROM pos_cash_register_closings WHERE company_id = :cid), 0),
            COALESCE((SELECT MAX(closing_id) FROM pos_cash_register_receipts WHERE company_id = :cid), 0),
            COALESCE((SELECT MAX(closing_id) FROM pos_cash_register_invoices WHERE company_id = :cid), 0),
            COALESCE((SELECT MAX(register_id) FROM pos_expenses WHERE company_id = :cid), 0),
            COALESCE((SELECT MAX(register_id) FROM pos_purchases WHERE company_id = :cid), 0),
            COALESCE((SELECT MAX(register_id) FROM pos_other_incomes WHERE company_id = :cid), 0),
            COALESCE((SELECT MAX(register_id) FROM pos_other_expenses WHERE company_id = :cid), 0),
            COALESCE((SELECT MAX(register_id) FROM pos_cash_advances WHERE company_id = :cid), 0)) + 1
    """), {"cid": cid})).scalar())


async def _asegurar_empleado(db: AsyncSession, cid: int, user: User) -> None:
    """El cajero web queda en pos_employees (empleados) con id = id del usuario."""
    await db.execute(text("""
        INSERT INTO pos_employees (id, company_id, name, login, password, status, employee_type, personal_skin, synced)
        SELECT :uid, :cid, :name, :login, '', 1, 0, 0, 0 FROM DUAL
        WHERE NOT EXISTS (SELECT 1 FROM pos_employees WHERE company_id = :cid AND id = :uid)
    """), {"uid": user.id, "cid": cid, "name": (user.nombre or f"Usuario {user.id}")[:50],
           "login": (user.email or str(user.id))[:25]})


@router.post("/abrir")
async def abrir_turno(
    body: dict,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cid, uid = current_user.company_id, current_user.id
    await exigir_usuario_caja(db, current_user)

    if await _es_escritorio(db, cid):
        raise HTTPException(status_code=409, detail="Esta empresa abre la caja desde el programa de escritorio")

    # Si el usuario ya tiene un Id_Caja abierto se sigue con ese hasta que se cierre
    existente = await _turno_abierto(db, cid, uid, _id_caja_header(request))
    if existente:
        return existente

    register_number = body.get("register_number")
    try:
        base_amount = float(body.get("base_amount") or 0)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Base inicial no válida")
    if base_amount < 0 or base_amount > 1e12:
        raise HTTPException(status_code=422, detail="Base inicial no válida")
    pc = (body.get("pc") or "")[:50]
    if register_number is None or not str(register_number).isdigit():
        raise HTTPException(status_code=422, detail="register_number es requerido")
    register_number = int(register_number)

    caja = (await db.execute(text(
        "SELECT id FROM pos_cash_registers WHERE id = :id AND company_id = :cid AND is_active = 1"
    ), {"id": register_number, "cid": cid})).mappings().first()
    if not caja and not (int(register_number) == CAJA_PROVISIONAL["id"] and not await _tiene_cajas(db, cid)):
        raise HTTPException(status_code=404, detail="Caja no encontrada")
    if any(int(a["register_number"]) == int(register_number) for a in await _cajas_abiertas(db, cid)):
        raise HTTPException(status_code=409, detail="Esta caja ya está abierta por otro usuario")

    await _asegurar_empleado(db, cid, current_user)
    for _ in range(5):
        id_caja = await _siguiente_id_caja(db, cid)
        try:
            await db.execute(text("""
                INSERT INTO pos_cash_register_closings
                    (id_registro, register_number, date, base_amount, customer_sales, closed,
                     opened_pc, opening_datetime, company_id, synced)
                VALUES
                    (:idreg, :rn, :hoy, :base, :uid, 0, :pc, :now, :cid, 0)
            """), {
                "idreg": id_caja, "rn": register_number, "base": base_amount, "uid": uid, "pc": pc,
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
        raise HTTPException(status_code=409, detail="No se pudo abrir la caja, intente nuevamente")

    return await _turno_abierto(db, cid, uid)


@router.post("/cerrar")
async def cerrar_turno(
    request: Request,
    body: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cierra un Id_Caja web: el propio (sin closing_id) o, si es Admin, el de otro usuario.
    Los Id_Caja del escritorio se cierran en el escritorio."""
    from app.services.permisos import permisos_usuario
    cid = current_user.company_id
    if "hacer_cierre" not in await permisos_usuario(db, current_user):
        raise HTTPException(status_code=403, detail="No tiene permiso para hacer el cierre de caja")
    closing_id = (body or {}).get("closing_id")
    if closing_id:
        turno = (await db.execute(text("""
            SELECT id_registro AS id, register_number, CAST(customer_sales AS SIGNED) AS cajero_id, synced
            FROM pos_cash_register_closings WHERE id_registro = :id AND company_id = :cid AND closed = 0
        """), {"id": int(closing_id), "cid": cid})).mappings().first()
        if not turno:
            raise HTTPException(status_code=404, detail="Id_Caja no encontrado o ya cerrado")
        if int(turno["synced"] or 0):
            raise HTTPException(status_code=409, detail="Este Id_Caja se cierra desde el programa de escritorio")
        if int(turno["cajero_id"] or 0) != current_user.id and not await _es_admin(db, current_user):
            raise HTTPException(status_code=403, detail="Solo el usuario que abrió la caja o un administrador pueden cerrarla")
    else:
        turno = await _turno_abierto(db, cid, current_user.id, _id_caja_header(request))
        if not turno:
            raise HTTPException(status_code=404, detail="No tiene una caja abierta")
        if turno["origen"] == "escritorio":
            raise HTTPException(status_code=409, detail="Este Id_Caja se cierra desde el programa de escritorio")

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
        WHERE id_registro = :id AND company_id = :cid AND closed = 0
    """), {"now": _ahora().strftime("%Y-%m-%d %H:%M:%S"), "id": turno_id, "cid": cid, **campos})
    # cajas.Abierta = 0 si ya no queda otro turno abierto en esa caja
    await db.execute(text(f"""
        UPDATE pos_cash_registers SET is_open = 0, employee_id = 0
        WHERE company_id = :cid AND id = :rn
          AND NOT EXISTS (SELECT 1 FROM pos_cash_register_closings c
                          WHERE c.company_id = :cid AND c.register_number = :rn AND {_VIGENTE})
    """), {"cid": cid, "rn": register_number})


async def require_open_shift(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Dependency reutilizable: exige Id_Caja abierto (y rol "Es Usuario Caja") antes de operar con dinero."""
    await exigir_usuario_caja(db, current_user)
    turno = await _turno_abierto(db, current_user.company_id, current_user.id, _id_caja_header(request))
    if not turno:
        raise HTTPException(status_code=409, detail="Debe abrir la caja antes de continuar")
    # Un Id_Caja puede pasar de medianoche (negocios 24 h): los recibos se registran con la
    # fecha de APERTURA (turno["fecha"]); la factura electrónica, solo con la de hoy.
    return turno
