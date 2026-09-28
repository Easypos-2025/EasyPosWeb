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
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user_model import User
from app.routers.pos_comanda_router import _auth_comanda

router = APIRouter(prefix="/api/pos/turno", tags=["POS Turno de Caja"])


async def _turno_abierto(db: AsyncSession, company_id: int, user_id: int) -> dict | None:
    row = (await db.execute(text("""
        SELECT id, register_number, base_amount, opening_datetime
        FROM pos_cash_register_closings
        WHERE company_id = :cid AND customer_sales = :uid AND closed = 0
        ORDER BY id DESC LIMIT 1
    """), {"cid": company_id, "uid": user_id})).mappings().first()
    return dict(row) if row else None


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
        return existente

    register_number = body.get("register_number")
    base_amount = body.get("base_amount", 0)
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
                    (:idreg, :rn, CURDATE(), :base, :uid, 0, :pc, :now, :cid, 1)
            """), {
                "idreg": next_id_registro, "rn": register_number, "base": base_amount, "uid": uid, "pc": pc,
                "now": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "cid": cid,
            })
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    turno = await _turno_abierto(db, current_user.company_id, current_user.id)
    if not turno:
        raise HTTPException(status_code=404, detail="No tiene un turno de caja abierto")

    # Cuadre de caja (ventas/gastos/etc.) queda pendiente para otra fase;
    # por ahora el cierre solo libera la caja.
    await db.execute(text("""
        UPDATE pos_cash_register_closings
        SET closed = 1, closing_datetime = :now
        WHERE id = :id
    """), {"now": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "id": turno["id"]})
    await db.commit()
    return {"ok": True}


async def require_open_shift(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Dependency reutilizable: exige turno de caja abierto antes de operar con dinero."""
    turno = await _turno_abierto(db, current_user.company_id, current_user.id)
    if not turno:
        raise HTTPException(status_code=409, detail="Debe abrir un turno de caja antes de continuar")
    return turno
