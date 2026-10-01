"""
Listas de Precios (lista_precios_cliente del escritorio).
  Cabecera: pos_customer_price_list_header  (Id_Lista, Fecha, Id_Cliente, Nombre, Activa…)
  Detalle:  pos_customer_price_list          (Id_Producto, Id_Presentacion = variante, Precio)
Reglas:
  - Id_Lista es consecutivo por empresa.
  - Lista DEFAULT (predeterminada) = lista del cliente 1 (Consumidor Final). Puede haber varias
    (histórico de precios), solo una activa. Sus precios = precio de platos/variantes (ambos sentidos).
  - Un cliente tiene UNA sola lista activa: al crear o activar una, la anterior queda anulada.
  - El detalle son todos los platos activos y sus variantes; solo se edita el precio.
  - Se cobra con la Default si el cliente es el 1 o si no tiene lista propia activa.
"""
from datetime import datetime, timedelta, timezone
from typing import Annotated, List, Literal, Optional

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
from app.services import listas_precios as lp

# Aislamiento multi-tenant: valida todo company_id que envíe el navegador (CLAUDE.md §6)
router = APIRouter(prefix="/api/pos-catalogo/listas-cliente", tags=["Listas de Precios"],
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
    origen: Literal["default", "anterior"] = "default"


class ListaUpdate(BaseModel):
    nombre: Text100
    observacion: Optional[Annotated[str, StringConstraints(max_length=255)]] = None


class PrecioLinea(BaseModel):
    id_producto: Annotated[int, Field(ge=1)]
    id_presentacion: Annotated[int, Field(ge=0)] = 0
    precio: Money


class PreciosIn(BaseModel):
    items: Annotated[List[PrecioLinea], Field(min_length=1, max_length=5000)]


class ClienteIn(BaseModel):
    nombres: str
    cedula: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    mail: Optional[str] = None


class ImprimirIn(BaseModel):
    printer_id: Annotated[int, Field(ge=0)]
    raw: bool = False
    company_id: Optional[int] = None     # lo valida tenant_guard


async def _ctx(db: AsyncSession, user: User, company_id: Optional[int]) -> int:
    return await tenant.resolve_company(db, user, company_id)


async def _header(db: AsyncSession, cid: int, id_lista: int):
    h = (await db.execute(text("""
        SELECT h.id_lista, h.id_cliente, h.nombre, h.fecha, h.activa, h.usuario, h.observacion,
               (h.id_cliente = 1) AS predeterminada,
               TRIM(CONCAT(COALESCE(c.nombres,''),' ',COALESCE(c.apellidos,''))) AS cliente
        FROM pos_customer_price_list_header h
        LEFT JOIN clientes c ON c.company_id = h.company_id AND c.id_cliente = h.id_cliente
        WHERE h.company_id = :cid AND h.id_lista = :l
    """), {"cid": cid, "l": id_lista})).mappings().first()
    if not h:
        raise HTTPException(status_code=404, detail="Lista no encontrada")
    out = dict(h)
    out["predeterminada"] = bool(out["predeterminada"])
    out["fecha"] = str(out["fecha"] or "")
    if out["predeterminada"]:
        out["cliente"] = out["cliente"] or "Consumidor Final"
    return out


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


async def _items(db: AsyncSession, cid: int, id_lista: int) -> list:
    """Detalle: plato (id_presentacion 0) y variantes, de platos activos."""
    rows = (await db.execute(text("""
        SELECT d.id_producto, d.id_presentacion, d.precio_producto AS precio,
               CASE WHEN v.id IS NULL THEN p.name ELSE CONCAT(p.name, ' - ', v.name) END AS name,
               COALESCE(v.is_default, 0) AS var_default,
               COALESCE(p.wholesale_price, 0) AS precio_minimo, c.name AS categoria
        FROM pos_customer_price_list d
        JOIN pos_dishes p ON p.id = d.id_producto AND p.company_id = d.company_id AND COALESCE(p.active, 0) = 0
        LEFT JOIN pos_dish_variants v
               ON d.id_presentacion > 0 AND v.id = d.id_presentacion AND v.company_id = d.company_id
              AND v.dish_id = d.id_producto
        LEFT JOIN pos_dish_categories c ON c.id = p.category_id AND c.company_id = p.company_id
        WHERE d.company_id = :cid AND d.id_lista = :l
          AND (d.id_presentacion = 0 OR (v.id IS NOT NULL AND v.is_active = 1))
        ORDER BY c.name, p.name, d.id_presentacion
    """), {"cid": cid, "l": id_lista})).mappings().all()
    out = []
    for r in rows:
        it = dict(r)
        it["precio"] = float(it["precio"] or 0)
        it["var_default"] = bool(it["var_default"])
        it["precio_minimo"] = float(it["precio_minimo"] or 0)
        it["bajo_minimo"] = bool(it["precio_minimo"]) and it["precio"] < it["precio_minimo"]
        out.append(it)
    return out


# ─── Clientes (selector del encabezado) ──────────────────────────────────────

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


# ─── Listas (encabezados) ────────────────────────────────────────────────────

@router.get("/listas")
async def listar(estado: Literal["activas", "todas"] = "activas", q: Optional[str] = Query(None, max_length=60),
                 company_id: Optional[int] = Query(None),
                 user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _ctx(db, user, company_id)
    await clientes_svc.ensure_consumidor_final(db, cid)
    await lp.asegurar_default(db, cid, getattr(user, "email", "") or "")
    await db.commit()
    sql = """
        SELECT h.id_lista, h.id_cliente, h.nombre, h.fecha, h.activa, h.observacion,
               (h.id_cliente = 1) AS predeterminada,
               TRIM(CONCAT(COALESCE(c.nombres,''),' ',COALESCE(c.apellidos,''))) AS cliente,
               (SELECT COUNT(*) FROM pos_customer_price_list d
                 WHERE d.company_id = h.company_id AND d.id_lista = h.id_lista) AS productos
        FROM pos_customer_price_list_header h
        LEFT JOIN clientes c ON c.company_id = h.company_id AND c.id_cliente = h.id_cliente
        WHERE h.company_id = :cid
    """
    params: dict = {"cid": cid}
    if estado == "activas":
        sql += " AND h.activa = 1"
    term = (q or "").strip()
    if term:
        term = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        sql += " AND (h.nombre LIKE :q OR c.nombres LIKE :q OR c.apellidos LIKE :q)"
        params["q"] = f"%{term}%"
    sql += " ORDER BY (h.id_cliente = 1) DESC, h.activa DESC, h.id_lista DESC LIMIT 300"
    out = []
    for r in (await db.execute(text(sql), params)).mappings().all():
        x = dict(r)
        x["predeterminada"] = bool(x["predeterminada"])
        x["fecha"] = str(x["fecha"] or "")
        if x["predeterminada"]:
            x["cliente"] = x["cliente"] or "Consumidor Final"
        out.append(x)
    return out


@router.get("/lista/{id_lista}")
async def get_lista(id_lista: int, company_id: Optional[int] = Query(None),
                    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _ctx(db, user, company_id)
    h = await _header(db, cid, id_lista)
    await lp.completar_lista(db, cid, id_lista, int(h["id_cliente"]))   # productos nuevos
    await db.commit()
    return {"lista": h, "items": await _items(db, cid, id_lista)}


@router.post("/lista", status_code=201)
async def crear_lista(data: ListaIn, company_id: Optional[int] = Query(None),
                      user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Nueva lista para un cliente con todos los productos activos (precios de la Default
    activa o de la lista anterior del cliente). La lista activa anterior del cliente queda
    anulada. Para el cliente 1 es una nueva Default (la anterior queda como histórico)."""
    cid = await _ctx(db, user, company_id)
    await clientes_svc.get_cliente(db, cid, data.id_cliente)
    default = await lp.asegurar_default(db, cid, getattr(user, "email", "") or "")
    anterior = (await db.execute(text("""
        SELECT id_lista FROM pos_customer_price_list_header
        WHERE company_id = :cid AND id_cliente = :cli ORDER BY activa DESC, id_lista DESC LIMIT 1
    """), {"cid": cid, "cli": data.id_cliente})).scalar()
    if data.origen == "anterior" and not anterior:
        raise HTTPException(status_code=400, detail="El cliente no tiene una lista anterior para copiar")
    fuente = anterior if data.origen == "anterior" else default

    nid = int((await db.execute(text(
        "SELECT COALESCE(MAX(id_lista), 0) + 1 FROM pos_customer_price_list_header WHERE company_id = :cid FOR UPDATE"
    ), {"cid": cid})).scalar())
    fecha = _today()
    await db.execute(text("""
        INSERT INTO pos_customer_price_list_header
            (company_id, id_lista, id_cliente, nombre, fecha, activa, usuario, observacion, synced)
        VALUES (:cid, :l, :cli, :n, :f, 0, :u, :o, 0)
    """), {"cid": cid, "l": nid, "cli": data.id_cliente, "n": data.nombre, "f": fecha,
           "u": (getattr(user, "email", None) or "")[:50], "o": (data.observacion or "").strip() or None})
    await db.execute(text("""
        INSERT INTO pos_customer_price_list
            (id_lista, id_cliente, id_producto, id_presentacion, precio_producto, fecha, activa, company_id, synced)
        SELECT :l, :cli, d.id_producto, d.id_presentacion, d.precio_producto, :f, 0, :cid, 0
        FROM pos_customer_price_list d
        JOIN pos_dishes p ON p.id = d.id_producto AND p.company_id = d.company_id AND COALESCE(p.active, 0) = 0
        WHERE d.company_id = :cid AND d.id_lista = :src
    """), {"cid": cid, "l": nid, "cli": data.id_cliente, "f": fecha, "src": fuente})
    await _set_activa(db, cid, data.id_cliente, nid)            # anula la anterior del cliente
    await lp.completar_lista(db, cid, nid, data.id_cliente)
    if data.id_cliente == lp.CLIENTE_DEFAULT:
        await lp.default_a_platos(db, cid, nid)
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


@router.put("/lista/{id_lista}/precios")
async def guardar_precios(id_lista: int, data: PreciosIn, company_id: Optional[int] = Query(None),
                          user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Guarda los precios editados (botón Guardar cambios). Si es la Default activa, el precio
    de los platos y variantes queda igual al de la lista."""
    cid = await _ctx(db, user, company_id)
    h = await _header(db, cid, id_lista)
    actualizados = 0
    for ln in data.items:
        r = await db.execute(text("""
            UPDATE pos_customer_price_list SET precio_producto = :pr, fecha = :f, synced = 0
            WHERE company_id = :cid AND id_lista = :l AND id_producto = :p AND id_presentacion = :pres
        """), {"pr": round(ln.precio), "f": _today(), "cid": cid, "l": id_lista,
               "p": ln.id_producto, "pres": ln.id_presentacion})
        actualizados += r.rowcount
    if h["predeterminada"] and h["activa"]:
        # En la Default, el plato y su variante por defecto son el mismo precio: lo editado en
        # una de las dos filas se copia a la otra antes de pasar los precios a los platos.
        for ln in data.items:
            vdef = (await db.execute(text(
                "SELECT id FROM pos_dish_variants WHERE company_id=:cid AND dish_id=:p AND is_active=1 AND is_default=1 LIMIT 1"
            ), {"cid": cid, "p": ln.id_producto})).scalar()
            if not vdef:
                continue
            if ln.id_presentacion == 0:
                destino = int(vdef)
            elif ln.id_presentacion == int(vdef):
                destino = 0
            else:
                continue
            await db.execute(text("""
                UPDATE pos_customer_price_list SET precio_producto = :pr, fecha = :f, synced = 0
                WHERE company_id = :cid AND id_lista = :l AND id_producto = :p AND id_presentacion = :pres
            """), {"pr": round(ln.precio), "f": _today(), "cid": cid, "l": id_lista,
                   "p": ln.id_producto, "pres": destino})
        await lp.default_a_platos(db, cid, id_lista)
    await db.commit()
    return {"ok": True, "actualizados": actualizados}


@router.post("/lista/{id_lista}/activar")
async def activar_lista(id_lista: int, company_id: Optional[int] = Query(None),
                        user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Solo las listas Default (cliente 1) del histórico se pueden volver a activar (p. ej.
    terminar un evento y regresar a los precios normales). Sus precios pasan a los platos."""
    cid = await _ctx(db, user, company_id)
    h = await _header(db, cid, id_lista)
    if not h["predeterminada"]:
        raise HTTPException(status_code=400,
                            detail="Una lista de cliente anulada no se puede reactivar: cree una nueva para ese cliente")
    await _set_activa(db, cid, int(h["id_cliente"]), id_lista)
    await lp.completar_lista(db, cid, id_lista, int(h["id_cliente"]))
    await lp.default_a_platos(db, cid, id_lista)
    await db.commit()
    return {"ok": True}


@router.post("/lista/{id_lista}/desactivar")
async def desactivar_lista(id_lista: int, company_id: Optional[int] = Query(None),
                           user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = await _ctx(db, user, company_id)
    h = await _header(db, cid, id_lista)
    if h["predeterminada"]:
        raise HTTPException(status_code=400,
                            detail="La lista Default no se desactiva: cree una nueva o active otra del histórico")
    if h["activa"]:
        await _set_activa(db, cid, int(h["id_cliente"]), None)
    await db.commit()
    return {"ok": True}


# ─── Impresión (tirilla ESC/POS) ─────────────────────────────────────────────

def _tirilla_lista(d: dict, width: int = 32) -> bytes:
    from app.routers.pos_recibo_impresion_router import _ascii, _money
    ESC = b"\x1b"
    INIT, BOLD_ON, BOLD_OFF = ESC + b"@", ESC + b"E\x01", ESC + b"E\x00"
    CENTER, LEFT, CUT, LF = ESC + b"a\x01", ESC + b"a\x00", b"\x1dV\x42\x00", b"\n"
    buf = bytearray(INIT)

    def line(t="", bold=False, center=False):
        buf.extend((BOLD_ON if bold else b"") + (CENTER if center else LEFT) + _ascii(t) + LF + (BOLD_OFF if bold else b""))

    def dl(a, b):
        a = str(a)[: max(1, width - len(b) - 1)]
        line(a + " " * max(1, width - len(a) - len(b)) + b)

    line(d["empresa"], bold=True, center=True)
    line("LISTA DE PRECIOS", bold=True, center=True)
    line(d["lista"]["nombre"], center=True)
    line(f"Cliente: {d['lista']['cliente'] or ''}")
    line(f"Lista No. {d['lista']['id_lista']}  {d['lista']['fecha']}")
    line("-" * width)
    cat = None
    for it in d["items"]:
        if it["categoria"] != cat:
            cat = it["categoria"]
            line(cat or "SIN CATEGORIA", bold=True)
        dl(("  " if it["id_presentacion"] else "") + it["name"], _money(it["precio"]))
    buf.extend(LF * 3 + CUT)
    return bytes(buf)


@router.post("/lista/{id_lista}/imprimir")
async def imprimir_lista(id_lista: int, data: ImprimirIn,
                         user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.routers.pos_recibo_impresion_router import enviar_tirilla
    cid = await _ctx(db, user, data.company_id)

    async def datos():
        h = await _header(db, cid, id_lista)
        emp = (await db.execute(text("SELECT name FROM companies WHERE id_company = :cid"),
                                {"cid": cid})).scalar() or ""
        return {"empresa": emp, "lista": h, "items": await _items(db, cid, id_lista)}

    return await enviar_tirilla(db, cid, data.printer_id, data.raw, datos, armar=_tirilla_lista)


@router.delete("/lista/{id_lista}")
async def eliminar_lista(id_lista: int, company_id: Optional[int] = Query(None),
                         user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Elimina la lista (cabecera y detalle). No se puede eliminar la Default activa: siempre
    debe existir una. Si era la lista activa de un cliente, el cliente pasa a la Default."""
    cid = await _ctx(db, user, company_id)
    h = await _header(db, cid, id_lista)
    if h["predeterminada"] and h["activa"]:
        raise HTTPException(status_code=400,
                            detail="No se puede eliminar la Lista Default activa: active otra Default o cree una nueva primero")
    await db.execute(text("DELETE FROM pos_customer_price_list WHERE company_id = :cid AND id_lista = :l"),
                     {"cid": cid, "l": id_lista})
    await db.execute(text("DELETE FROM pos_customer_price_list_header WHERE company_id = :cid AND id_lista = :l"),
                     {"cid": cid, "l": id_lista})
    await db.commit()
    return {"ok": True}
