"""
Listas de precios por cliente.
  Cabecera: pos_customer_price_list_header  (= lista_precios_cliente_cabecera del escritorio)
  Detalle:  pos_customer_price_list          (= lista_precios_cliente), relacionadas por id_lista.
Reglas:
  - id_lista es consecutivo por empresa y lo genera la web (0 = lista general, reservada).
  - Un cliente tiene UNA sola lista activa: al crear o activar una, las demás se desactivan.
  - Nueva lista: carga todos los platos activos con su Valor (o copia la lista anterior).
  - Sin lista activa → la comanda cobra platos.Valor.
"""
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import tenant
from app.auth.dependencies import get_current_user
from app.auth.tenant import tenant_guard
from app.database import get_db
from app.models.user_model import User
from app.services import clientes as clientes_svc

# Aislamiento multi-tenant: valida todo company_id que envíe el navegador (CLAUDE.md §6)
router = APIRouter(prefix="/api/pos-catalogo/listas-cliente", tags=["POS Listas de precios por cliente"],
                   dependencies=[Depends(tenant_guard)])

_BOG = timezone(timedelta(hours=-5))
Money = Annotated[float, Field(ge=0, le=2_000_000_000)]
Text100 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


def _today() -> str:
    return datetime.now(_BOG).date().isoformat()


class ListaIn(BaseModel):
    id_cliente: Annotated[int, Field(ge=1)]
    nombre: Text100
    observacion: Optional[Annotated[str, StringConstraints(max_length=255)]] = None
    origen: Literal["platos", "anterior"] = "platos"


class ListaUpdate(BaseModel):
    nombre: Text100
    observacion: Optional[Annotated[str, StringConstraints(max_length=255)]] = None


class PrecioIn(BaseModel):
    precio: Money


class ItemIn(BaseModel):
    id_producto: Annotated[int, Field(ge=1)]
    precio: Money


class ClienteIn(BaseModel):
    nombres: str
    cedula: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    mail: Optional[str] = None


async def _ctx(db: AsyncSession, user: User, company_id: Optional[int]) -> int:
    return await tenant.resolve_company(db, user, company_id)


async def _header(db: AsyncSession, cid: int, id_lista: int):
    h = (await db.execute(text("""
        SELECT id_lista, id_cliente, nombre, fecha, activa, usuario, observacion
        FROM pos_customer_price_list_header WHERE company_id = :cid AND id_lista = :l
    """), {"cid": cid, "l": id_lista})).mappings().first()
    if not h:
        raise HTTPException(status_code=404, detail="Lista no encontrada")
    return h


async def _check_dish(db: AsyncSession, cid: int, id_producto: int):
    d = (await db.execute(text(
        "SELECT id, price, wholesale_price FROM pos_dishes WHERE id = :id AND company_id = :cid"
    ), {"id": id_producto, "cid": cid})).mappings().first()
    if not d:
        raise HTTPException(status_code=400, detail="Producto no válido para esta empresa")
    return d


async def _set_activa(db: AsyncSession, cid: int, id_cliente: int, id_lista: Optional[int]) -> None:
    """Deja activa solo id_lista (o ninguna si es None) para el cliente; cabecera y detalle."""
    await db.execute(text("""
        UPDATE pos_customer_price_list_header SET activa = IF(id_lista = :l, 1, 0), synced = 0
        WHERE company_id = :cid AND id_cliente = :cli
    """), {"cid": cid, "cli": id_cliente, "l": id_lista or -1})
    await db.execute(text("""
        UPDATE pos_customer_price_list SET activa = IF(id_lista = :l, 1, 0), synced = 0
        WHERE company_id = :cid AND id_cliente = :cli AND id_lista <> 0
    """), {"cid": cid, "cli": id_cliente, "l": id_lista or -1})


# ─── Clientes ─────────────────────────────────────────────────────────────────

@router.get("/clientes")
async def buscar_clientes(q: Optional[str] = Query(None, max_length=60), company_id: Optional[int] = Query(None),
                          user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _ctx(db, user, company_id)
    rows = await clientes_svc.buscar(db, cid, q, limit=50)
    await db.commit()
    activas = {int(r["id_cliente"]): r["nombre"] for r in (await db.execute(text(
        "SELECT id_cliente, nombre FROM pos_customer_price_list_header WHERE company_id = :cid AND activa = 1"
    ), {"cid": cid})).mappings().all()}
    for r in rows:
        r["lista_activa"] = activas.get(r["id_cliente"])
    return rows


@router.post("/clientes", status_code=201)
async def crear_cliente(data: ClienteIn, company_id: Optional[int] = Query(None),
                        user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _ctx(db, user, company_id)
    row = await clientes_svc.crear(db, cid, data.nombres, data.cedula, data.telefono, data.direccion, data.mail)
    await db.commit()
    return row


@router.get("/cliente/{id_cliente}")
async def listas_de_cliente(id_cliente: int, company_id: Optional[int] = Query(None),
                            user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _ctx(db, user, company_id)
    cliente = await clientes_svc.get_cliente(db, cid, id_cliente)
    await db.commit()
    listas = (await db.execute(text("""
        SELECT h.id_lista, h.nombre, h.fecha, h.activa, h.usuario, h.observacion,
               (SELECT COUNT(*) FROM pos_customer_price_list d
                WHERE d.company_id = h.company_id AND d.id_lista = h.id_lista) AS productos
        FROM pos_customer_price_list_header h
        WHERE h.company_id = :cid AND h.id_cliente = :cli
        ORDER BY h.activa DESC, h.id_lista DESC
    """), {"cid": cid, "cli": id_cliente})).mappings().all()
    return {"cliente": cliente, "listas": [dict(l) for l in listas]}


# ─── Listas ───────────────────────────────────────────────────────────────────

@router.get("/lista/{id_lista}")
async def get_lista(id_lista: int, company_id: Optional[int] = Query(None),
                    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _ctx(db, user, company_id)
    h = await _header(db, cid, id_lista)
    rows = (await db.execute(text("""
        SELECT d.id_producto, d.precio_producto AS precio, p.name, p.price AS precio_base,
               COALESCE(p.wholesale_price, 0) AS precio_minimo, COALESCE(p.active, 0) AS desactivado,
               c.name AS categoria
        FROM pos_customer_price_list d
        JOIN pos_dishes p ON p.id = d.id_producto AND p.company_id = d.company_id
        LEFT JOIN pos_dish_categories c ON c.id = p.category_id AND c.company_id = p.company_id
        WHERE d.company_id = :cid AND d.id_lista = :l AND d.id_presentacion = 0
        ORDER BY c.name, p.name
    """), {"cid": cid, "l": id_lista})).mappings().all()
    items = []
    for r in rows:
        it = dict(r)
        it["precio"] = float(it["precio"] or 0)
        it["bajo_minimo"] = bool(it["precio_minimo"]) and it["precio"] < float(it["precio_minimo"])
        items.append(it)
    return {"lista": dict(h), "items": items}


@router.post("/lista", status_code=201)
async def crear_lista(data: ListaIn, company_id: Optional[int] = Query(None),
                      user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _ctx(db, user, company_id)
    if data.id_cliente == clientes_svc.CONSUMIDOR_FINAL_ID:
        raise HTTPException(status_code=400, detail="Consumidor Final usa los precios de la carta; no se le asigna lista")
    await clientes_svc.get_cliente(db, cid, data.id_cliente)

    anterior = (await db.execute(text("""
        SELECT id_lista FROM pos_customer_price_list_header
        WHERE company_id = :cid AND id_cliente = :cli ORDER BY activa DESC, id_lista DESC LIMIT 1
    """), {"cid": cid, "cli": data.id_cliente})).scalar()
    if data.origen == "anterior" and not anterior:
        raise HTTPException(status_code=400, detail="El cliente no tiene una lista anterior para copiar")

    nid = int((await db.execute(text(
        "SELECT COALESCE(MAX(id_lista), 0) + 1 FROM pos_customer_price_list_header WHERE company_id = :cid FOR UPDATE"
    ), {"cid": cid})).scalar())
    fecha = _today()
    await db.execute(text("""
        INSERT INTO pos_customer_price_list_header
            (company_id, id_lista, id_cliente, nombre, fecha, activa, usuario, observacion, synced)
        VALUES (:cid, :l, :cli, :n, :f, 1, :u, :o, 0)
    """), {"cid": cid, "l": nid, "cli": data.id_cliente, "n": data.nombre, "f": fecha,
           "u": (getattr(user, "email", None) or "")[:50], "o": (data.observacion or "").strip() or None})

    if data.origen == "anterior":
        await db.execute(text("""
            INSERT INTO pos_customer_price_list
                (id_lista, id_cliente, id_producto, id_presentacion, precio_producto, fecha, activa, company_id, synced)
            SELECT :l, :cli, d.id_producto, 0, d.precio_producto, :f, 1, :cid, 0
            FROM pos_customer_price_list d
            JOIN pos_dishes p ON p.id = d.id_producto AND p.company_id = d.company_id AND COALESCE(p.active,0) = 0
            WHERE d.company_id = :cid AND d.id_lista = :ant AND d.id_presentacion = 0
        """), {"cid": cid, "l": nid, "cli": data.id_cliente, "f": fecha, "ant": anterior})
    else:   # todos los platos activos con su precio de carta
        await db.execute(text("""
            INSERT INTO pos_customer_price_list
                (id_lista, id_cliente, id_producto, id_presentacion, precio_producto, fecha, activa, company_id, synced)
            SELECT :l, :cli, p.id, 0, p.price, :f, 1, :cid, 0
            FROM pos_dishes p WHERE p.company_id = :cid AND COALESCE(p.active, 0) = 0
        """), {"cid": cid, "l": nid, "cli": data.id_cliente, "f": fecha})

    await _set_activa(db, cid, data.id_cliente, nid)
    await db.commit()
    return {"ok": True, "id_lista": nid}


@router.put("/lista/{id_lista}")
async def editar_lista(id_lista: int, data: ListaUpdate, company_id: Optional[int] = Query(None),
                       user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _ctx(db, user, company_id)
    await _header(db, cid, id_lista)
    await db.execute(text("""
        UPDATE pos_customer_price_list_header SET nombre = :n, observacion = :o, synced = 0
        WHERE company_id = :cid AND id_lista = :l
    """), {"n": data.nombre, "o": (data.observacion or "").strip() or None, "cid": cid, "l": id_lista})
    await db.commit()
    return {"ok": True}


@router.post("/lista/{id_lista}/activar")
async def activar_lista(id_lista: int, company_id: Optional[int] = Query(None),
                        user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _ctx(db, user, company_id)
    h = await _header(db, cid, id_lista)
    await _set_activa(db, cid, int(h["id_cliente"]), id_lista)
    await db.commit()
    return {"ok": True}


@router.post("/lista/{id_lista}/desactivar")
async def desactivar_lista(id_lista: int, company_id: Optional[int] = Query(None),
                           user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _ctx(db, user, company_id)
    h = await _header(db, cid, id_lista)
    if h["activa"]:
        await _set_activa(db, cid, int(h["id_cliente"]), None)
    await db.commit()
    return {"ok": True}


# ─── Ítems de la lista ────────────────────────────────────────────────────────

@router.get("/productos")
async def productos(q: Optional[str] = Query(None, max_length=60), company_id: Optional[int] = Query(None),
                    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _ctx(db, user, company_id)
    sql = """SELECT p.id, p.name, p.price, COALESCE(p.wholesale_price,0) AS precio_minimo, c.name AS categoria
             FROM pos_dishes p
             LEFT JOIN pos_dish_categories c ON c.id = p.category_id AND c.company_id = p.company_id
             WHERE p.company_id = :cid AND COALESCE(p.active,0) = 0"""
    params: dict = {"cid": cid}
    term = (q or "").strip()
    if term:
        term = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        sql += " AND p.name LIKE :q"
        params["q"] = f"%{term}%"
    sql += " ORDER BY c.name, p.name LIMIT 300"
    return [dict(r) for r in (await db.execute(text(sql), params)).mappings().all()]


@router.post("/lista/{id_lista}/item", status_code=201)
async def agregar_item(id_lista: int, data: ItemIn, company_id: Optional[int] = Query(None),
                       user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _ctx(db, user, company_id)
    h = await _header(db, cid, id_lista)
    d = await _check_dish(db, cid, data.id_producto)
    await db.execute(text("""
        INSERT INTO pos_customer_price_list
            (id_lista, id_cliente, id_producto, id_presentacion, precio_producto, fecha, activa, company_id, synced)
        VALUES (:l, :cli, :p, 0, :pr, :f, :a, :cid, 0)
        ON DUPLICATE KEY UPDATE precio_producto = VALUES(precio_producto), fecha = VALUES(fecha), synced = 0
    """), {"l": id_lista, "cli": h["id_cliente"], "p": data.id_producto, "pr": data.precio,
           "f": _today(), "a": 1 if h["activa"] else 0, "cid": cid})
    await db.commit()
    return {"ok": True, "bajo_minimo": bool(d["wholesale_price"]) and data.precio < float(d["wholesale_price"])}


@router.put("/lista/{id_lista}/item/{id_producto}")
async def editar_precio(id_lista: int, id_producto: int, data: PrecioIn, company_id: Optional[int] = Query(None),
                        user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _ctx(db, user, company_id)
    await _header(db, cid, id_lista)
    d = await _check_dish(db, cid, id_producto)
    res = await db.execute(text("""
        UPDATE pos_customer_price_list SET precio_producto = :pr, fecha = :f, synced = 0
        WHERE company_id = :cid AND id_lista = :l AND id_producto = :p AND id_presentacion = 0
    """), {"pr": data.precio, "f": _today(), "cid": cid, "l": id_lista, "p": id_producto})
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="El producto no está en la lista")
    await db.commit()
    return {"ok": True, "bajo_minimo": bool(d["wholesale_price"]) and data.precio < float(d["wholesale_price"])}


@router.delete("/lista/{id_lista}/item/{id_producto}")
async def quitar_item(id_lista: int, id_producto: int, company_id: Optional[int] = Query(None),
                      user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _ctx(db, user, company_id)
    await _header(db, cid, id_lista)
    await db.execute(text("""
        DELETE FROM pos_customer_price_list
        WHERE company_id = :cid AND id_lista = :l AND id_producto = :p AND id_presentacion = 0
    """), {"cid": cid, "l": id_lista, "p": id_producto})
    await db.commit()
    return {"ok": True}
