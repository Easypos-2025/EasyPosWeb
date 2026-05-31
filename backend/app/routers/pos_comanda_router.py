"""
POS Comanda — Modalidad B: Servicio a Mesas
Endpoints para la app de comandera del mesero y la vista de cocina TV.
"""
from datetime import datetime, timezone, timedelta
import json

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_db
from app.auth.jwt_handler import create_access_token, decode_access_token

router = APIRouter(prefix="/api/pos/comanda", tags=["POS Comanda"])

_BOG = timezone(timedelta(hours=-5))


def _now_bog() -> datetime:
    return datetime.now(_BOG)


def _today() -> str:
    return _now_bog().date().isoformat()


def _time_str() -> str:
    return _now_bog().strftime("%H:%M:%S")


def _order_number(cid: int, table_id: int) -> str:
    ts = _now_bog().strftime("%Y%m%d%H%M%S")
    return f"WEB-{cid}-{table_id}-{ts}"


async def _auth_waiter(authorization: str) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload or payload.get("type") != "waiter":
        raise HTTPException(status_code=401, detail="Token de mesero inválido")
    return payload


# ── Schemas ───────────────────────────────────────────────────────────────────

class WaiterLoginIn(BaseModel):
    company_id: int
    waiter_id: int
    pin: str


class AbrirMesaIn(BaseModel):
    table_id: int
    guests_count: Optional[int] = 1


class AssemblySelection(BaseModel):
    category_code: int
    item_id: int
    item_name: str
    discount_qty: Optional[float] = 1.0


class AgregarItemIn(BaseModel):
    order_number: str
    date: str
    table_id: int
    dish_id: int
    quantity: float = 1
    amount: Optional[int] = 0
    notes: Optional[str] = None
    changes: Optional[str] = None
    assembly_selections: Optional[List[AssemblySelection]] = []
    customer_id: Optional[int] = 0


class ActualizarItemIn(BaseModel):
    order_number: str
    date: str
    dish_id: int
    item: int
    quantity: Optional[float] = None
    notes: Optional[str] = None
    changes: Optional[str] = None


class EliminarItemIn(BaseModel):
    order_number: str
    date: str
    dish_id: int
    item: int
    depends_on: Optional[int] = 0


class SolicitarCuentaIn(BaseModel):
    table_id: int


class CancelarOrdenIn(BaseModel):
    table_id: int


class EnviarCocinaIn(BaseModel):
    order_number: str
    date: str


# ── 1. AUTH MESERO ────────────────────────────────────────────────────────────

@router.get("/auth/waiters")
async def list_waiters(company_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(text(
        "SELECT id, name FROM pos_waiters "
        "WHERE company_id=:cid AND status=1 AND plan_blocked=0 ORDER BY name"
    ), {"cid": company_id})).mappings().all()
    return [{"id": int(r["id"]), "name": r["name"]} for r in rows]


@router.post("/auth/mesero")
async def login_mesero(data: WaiterLoginIn, db: AsyncSession = Depends(get_db)):
    row = (await db.execute(text(
        "SELECT id, name, password, status, plan_blocked "
        "FROM pos_waiters WHERE id = :wid AND company_id = :cid"
    ), {"wid": data.waiter_id, "cid": data.company_id})).mappings().first()

    if not row:
        raise HTTPException(status_code=404, detail="Mesero no encontrado")
    if int(row["status"]) == 0:
        raise HTTPException(status_code=403, detail="Mesero inactivo")
    if row["plan_blocked"]:
        raise HTTPException(status_code=403, detail="Cuenta bloqueada por plan")
    if str(row["password"]) != str(data.pin):
        raise HTTPException(status_code=401, detail="PIN incorrecto")

    token = create_access_token({
        "type": "waiter",
        "waiter_id": int(row["id"]),
        "waiter_name": row["name"],
        "company_id": data.company_id,
    })
    return {"token": token, "waiter": {"id": int(row["id"]), "name": row["name"]}}


# ── 2. MESAS POR ZONA ─────────────────────────────────────────────────────────

@router.get("/mesas")
async def get_mesas(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    payload = await _auth_waiter(authorization)
    cid = payload["company_id"]
    today = _today()

    rows = (await db.execute(text("""
        WITH seq AS (
            SELECT order_number, table_id, amount, time, waiter_id, bill_requested
            FROM pos_orders
            WHERE company_id = :cid AND date = :today
              AND invoice_number = '0' AND cancelled = 0
        )
        SELECT
            tl.id, tl.name, tl.seats, tl.zone_id, tl.active,
            z.name          AS zone_name,
            z.color         AS zone_color,
            z.icon          AS zone_icon,
            z.order_index   AS zone_order,
            s.order_number,
            s.amount,
            s.time          AS order_time,
            s.waiter_id,
            s.bill_requested,
            w.name          AS waiter_name
        FROM pos_tables_layout tl
        LEFT JOIN pos_zones z ON z.id = tl.zone_id AND z.company_id = :cid
        LEFT JOIN seq s ON s.table_id = tl.id
        LEFT JOIN pos_waiters w ON w.id = s.waiter_id AND w.company_id = :cid
        WHERE tl.company_id = :cid AND tl.active = 1
        ORDER BY z.order_index, tl.id
    """), {"cid": cid, "today": today})).mappings().all()

    # Compute daily_seq for occupied tables from a separate query
    seq_rows = (await db.execute(text("""
        SELECT order_number,
               ROW_NUMBER() OVER (PARTITION BY company_id, date ORDER BY time ASC) AS daily_seq
        FROM pos_orders
        WHERE company_id = :cid AND date = :today
          AND invoice_number = '0' AND cancelled = 0
    """), {"cid": cid, "today": today})).mappings().all()
    seq_map = {r["order_number"]: int(r["daily_seq"]) for r in seq_rows}

    zones: dict = {}
    for r in rows:
        zid = r["zone_id"] or 0
        if zid not in zones:
            zones[zid] = {
                "id": zid,
                "name": r["zone_name"] or f"Zona {zid}",
                "color": r["zone_color"] or "#1d4ed8",
                "icon": r["zone_icon"] or "bi-grid",
                "order_index": r["zone_order"] or 0,
                "tables": [],
            }
        status = "free"
        if r["order_number"]:
            status = "bill_requested" if r["bill_requested"] else "occupied"

        zones[zid]["tables"].append({
            "id": r["id"],
            "name": r["name"],
            "seats": r["seats"],
            "status": status,
            "order_number": r["order_number"],
            "amount": r["amount"],
            "order_time": r["order_time"],
            "waiter_id": r["waiter_id"],
            "waiter_name": r["waiter_name"],
            "daily_seq": seq_map.get(r["order_number"]) if r["order_number"] else None,
        })

    return sorted(zones.values(), key=lambda z: z["order_index"])


# ── 3. ABRIR MESA ─────────────────────────────────────────────────────────────

@router.post("/mesa/abrir")
async def abrir_mesa(
    data: AbrirMesaIn,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    payload = await _auth_waiter(authorization)
    cid = payload["company_id"]
    waiter_id = payload["waiter_id"]
    today = _today()

    mesa = (await db.execute(text(
        "SELECT id, name, active FROM pos_tables_layout WHERE id=:tid AND company_id=:cid"
    ), {"tid": data.table_id, "cid": cid})).mappings().first()
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    if not mesa["active"]:
        raise HTTPException(status_code=400, detail="Mesa inactiva")

    existing = (await db.execute(text(
        "SELECT order_number FROM pos_orders "
        "WHERE table_id=:tid AND company_id=:cid AND date=:today "
        "AND invoice_number='0' AND cancelled=0 LIMIT 1"
    ), {"tid": data.table_id, "cid": cid, "today": today})).mappings().first()
    if existing:
        return {"order_number": existing["order_number"], "date": today, "already_open": True}

    order_number = _order_number(cid, data.table_id)
    await db.execute(text("""
        INSERT INTO pos_orders
          (order_number, date, invoice_number, table_id, table_name,
           waiter_id, guests_count, amount, cancelled, delivery,
           bill_requested, company_id, time)
        VALUES
          (:on, :date, '0', :tid, :tname,
           :wid, :guests, 0, 0, 0,
           0, :cid, :time)
    """), {
        "on": order_number, "date": today, "tid": data.table_id,
        "tname": mesa["name"], "wid": waiter_id,
        "guests": data.guests_count, "cid": cid, "time": _time_str(),
    })
    await db.commit()

    return {"order_number": order_number, "date": today, "already_open": False}


# ── 4. ORDEN ACTIVA DE UNA MESA ───────────────────────────────────────────────

@router.get("/mesa/{table_id}/orden")
async def get_orden_mesa(
    table_id: int,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    payload = await _auth_waiter(authorization)
    cid = payload["company_id"]
    today = _today()

    order = (await db.execute(text("""
        SELECT o.order_number, o.date, o.amount, o.time, o.guests_count,
               o.waiter_id, o.bill_requested, o.notes, o.table_name,
               w.name AS waiter_name
        FROM pos_orders o
        LEFT JOIN pos_waiters w ON w.id = o.waiter_id AND w.company_id = o.company_id
        WHERE o.table_id = :tid AND o.company_id = :cid
          AND o.date = :today AND o.invoice_number = '0' AND o.cancelled = 0
        LIMIT 1
    """), {"tid": table_id, "cid": cid, "today": today})).mappings().first()

    if not order:
        return {"order": None, "items": []}

    seq = (await db.execute(text("""
        SELECT daily_seq FROM (
            SELECT order_number,
                   ROW_NUMBER() OVER (PARTITION BY company_id, date ORDER BY time ASC) AS daily_seq
            FROM pos_orders
            WHERE company_id = :cid AND date = :today
              AND invoice_number = '0' AND cancelled = 0
        ) ranked WHERE order_number = :on
    """), {"cid": cid, "today": today, "on": order["order_number"]})).scalar()

    items_rows = (await db.execute(text("""
        SELECT od.dish_id, od.item, od.depends_on, od.quantity, od.amount,
               od.notes, od.changes, od.custom_product, od.dish_time,
               d.name AS dish_name, d.price,
               d.offer_priority   AS has_assembly,
               d.preparation_time AS no_print
        FROM pos_order_details od
        JOIN pos_dishes d ON d.id = od.dish_id AND d.company_id = :cid
        WHERE od.order_number = :on AND od.date = :date
          AND od.invoice_number = '0' AND od.company_id = :cid
          AND od.depends_on = 0
        ORDER BY od.item
    """), {"on": order["order_number"], "date": str(order["date"]), "cid": cid})).mappings().all()

    items = []
    for r in items_rows:
        assembly = []
        if r["custom_product"]:
            try:
                cp = json.loads(r["custom_product"])
                assembly = cp.get("assembly", [])
            except Exception:
                pass
        items.append({
            "dish_id": r["dish_id"],
            "item": r["item"],
            "dish_name": r["dish_name"],
            "quantity": r["quantity"],
            "amount": r["amount"],
            "notes": r["notes"],
            "changes": r["changes"],
            "assembly": assembly,
            "dish_time": r["dish_time"],
            "sent": bool(r["dish_time"]),
        })

    return {
        "order": {
            "order_number": order["order_number"],
            "date": str(order["date"]),
            "amount": order["amount"],
            "time": order["time"],
            "guests_count": order["guests_count"],
            "waiter_id": order["waiter_id"],
            "waiter_name": order["waiter_name"],
            "bill_requested": bool(order["bill_requested"]),
            "table_name": order["table_name"],
            "daily_seq": int(seq) if seq else 1,
        },
        "items": items,
    }


# ── 5. MENÚ (platos con config de armado) ────────────────────────────────────

@router.get("/menu")
async def get_menu(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    payload = await _auth_waiter(authorization)
    cid = payload["company_id"]

    dishes = (await db.execute(text("""
        SELECT
            d.id, d.name, d.price, d.compare_price, d.category_id,
            d.photo_path, d.tax, d.order_index,
            d.offer_priority   AS has_assembly,
            d.preparation_time AS no_print,
            c.name             AS category_name,
            c.order_index      AS cat_order
        FROM pos_dishes d
        LEFT JOIN pos_dish_categories c
               ON c.id = d.category_id
        WHERE d.company_id = :cid AND d.active = 1
        ORDER BY COALESCE(c.order_index, 9999), d.order_index
    """), {"cid": cid})).mappings().all()

    item_printers = (await db.execute(text(
        "SELECT item_id, printer_id FROM pos_item_printers WHERE company_id=:cid"
    ), {"cid": cid})).mappings().all()
    ip_map: dict[int, list] = {}
    for ip in item_printers:
        ip_map.setdefault(int(ip["item_id"]), []).append(int(ip["printer_id"]))

    printers = (await db.execute(text(
        "SELECT id, name FROM pos_printers WHERE company_id=:cid AND is_active=1 ORDER BY id"
    ), {"cid": cid})).mappings().all()

    categories: dict = {}
    for d in dishes:
        cat_id = d["category_id"] or 0
        if cat_id not in categories:
            categories[cat_id] = {
                "category_id": cat_id,
                "category_name": d["category_name"] or "Sin categoría",
                "order_index": d["cat_order"] or 0,
                "dishes": [],
            }
        categories[cat_id]["dishes"].append({
            "id": d["id"],
            "name": d["name"],
            "price": d["price"],
            "compare_price": d["compare_price"],
            "photo_path": d["photo_path"],
            "tax": float(d["tax"]) if d["tax"] else 0,
            "has_assembly": bool(d["has_assembly"]),
            "no_print": bool(d["no_print"]),
            "order_index": d["order_index"],
            "printer_ids": ip_map.get(int(d["id"]), []),
        })

    return {
        "categories": sorted(categories.values(), key=lambda x: x["order_index"]),
        "printers": [{"id": p["id"], "name": p["name"]} for p in printers],
    }


# ── 6. MENÚ DIARIO (opciones de armado para hoy) ─────────────────────────────

@router.get("/menu-diario/{dish_id}")
async def get_menu_diario(
    dish_id: int,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    payload = await _auth_waiter(authorization)
    cid = payload["company_id"]
    today = _today()

    assembly_cats = (await db.execute(text("""
        SELECT da.category_code, da.max_choices, da.is_required, da.print_on_change_only,
               (
                   SELECT dm2.description FROM pos_daily_menu dm2
                   WHERE dm2.company_id = :cid AND dm2.date = :today
                     AND dm2.group_by = da.category_code
                   LIMIT 1
               ) AS category_name
        FROM pos_dish_assembly da
        WHERE da.dish_id = :did AND da.company_id = :cid AND da.is_active = 1
        ORDER BY da.category_code
    """), {"did": dish_id, "cid": cid, "today": today})).mappings().all()

    if not assembly_cats:
        return {"categories": [], "fixed_products": []}

    category_codes = [int(r["category_code"]) for r in assembly_cats]
    placeholders = ", ".join([f":cc{i}" for i in range(len(category_codes))])
    params: dict = {"did": dish_id, "cid": cid, "today": today}
    for i, cc in enumerate(category_codes):
        params[f"cc{i}"] = cc

    options_rows = (await db.execute(text(f"""
        SELECT
            dad.category_code,
            dad.item         AS item_id,
            dad.discount_qty,
            dad.is_default,
            dad.position,
            dm.description   AS item_name,
            IF(dm.id IS NOT NULL, 1, 0) AS available_today
        FROM pos_dish_assembly_detail dad
        LEFT JOIN pos_daily_menu dm
               ON dm.item_id    = dad.item
              AND dm.company_id = :cid
              AND dm.date       = :today
        WHERE dad.dish_id = :did AND dad.company_id = :cid
          AND dad.category_code IN ({placeholders})
        ORDER BY dad.category_code, dad.position
    """), params)).mappings().all()

    options_by_cat: dict[int, list] = {}
    for row in options_rows:
        cc = int(row["category_code"])
        options_by_cat.setdefault(cc, []).append({
            "item_id": row["item_id"],
            "item_name": row["item_name"] or f"Opción {row['item_id']}",
            "discount_qty": float(row["discount_qty"]) if row["discount_qty"] else 1.0,
            "is_default": bool(row["is_default"]),
            "available_today": bool(row["available_today"]),
        })

    fixed = (await db.execute(text("""
        SELECT dp.supplier_id AS item_id, dp.minimum_units AS quantity, dp.description
        FROM pos_dish_products dp
        WHERE dp.dish_id = :did AND dp.company_id = :cid AND dp.active = 1
    """), {"did": dish_id, "cid": cid})).mappings().all()

    result = []
    for cat in assembly_cats:
        cc = int(cat["category_code"])
        result.append({
            "category_code": cc,
            "category_name": cat["category_name"] or f"Categoría {cc}",
            "max_choices": cat["max_choices"],
            "is_required": bool(cat["is_required"]),
            "print_on_change_only": bool(cat["print_on_change_only"]),
            "options": options_by_cat.get(cc, []),
        })

    return {
        "categories": result,
        "fixed_products": [
            {"item_id": f["item_id"], "quantity": f["quantity"], "description": f["description"]}
            for f in fixed
        ],
    }


# ── 7. NOVEDADES PRECARGADAS ──────────────────────────────────────────────────

@router.get("/novedades")
async def get_novedades(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    payload = await _auth_waiter(authorization)
    cid = payload["company_id"]

    notes = (await db.execute(text(
        "SELECT id, name FROM pos_order_notes WHERE company_id=:cid ORDER BY id"
    ), {"cid": cid})).mappings().all()

    return {"notes": [{"id": n["id"], "name": n["name"]} for n in notes]}


# ── 8. AGREGAR ÍTEM A LA ORDEN ────────────────────────────────────────────────

@router.post("/orden/item")
async def agregar_item(
    data: AgregarItemIn,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    payload = await _auth_waiter(authorization)
    cid = payload["company_id"]

    order = (await db.execute(text(
        "SELECT order_number FROM pos_orders "
        "WHERE order_number=:on AND date=:date AND company_id=:cid "
        "AND invoice_number='0' AND cancelled=0 LIMIT 1"
    ), {"on": data.order_number, "date": data.date, "cid": cid})).mappings().first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada o ya cerrada")

    dish = (await db.execute(text(
        "SELECT id, price, tax FROM pos_dishes WHERE id=:did AND company_id=:cid AND active=1"
    ), {"did": data.dish_id, "cid": cid})).mappings().first()
    if not dish:
        raise HTTPException(status_code=404, detail="Plato no encontrado o inactivo")

    max_item = (await db.execute(text(
        "SELECT COALESCE(MAX(item), 0) FROM pos_order_details "
        "WHERE order_number=:on AND date=:date AND company_id=:cid"
    ), {"on": data.order_number, "date": data.date, "cid": cid})).scalar() or 0
    item_num = int(max_item) + 1

    amount = data.amount if data.amount else int(dish["price"] * data.quantity)
    tax_pct = float(dish["tax"]) if dish["tax"] else 0
    pays_tax = 1 if tax_pct > 0 else 0
    tax_val = int(amount * tax_pct / 100) if pays_tax else 0

    custom_product = None
    if data.assembly_selections:
        custom_product = json.dumps(
            {"assembly": [s.model_dump() for s in data.assembly_selections]},
            ensure_ascii=False,
        )

    await db.execute(text("""
        INSERT INTO pos_order_details
          (order_number, date, invoice_number, dish_id, item, depends_on,
           quantity, amount, notes, changes, pays_tax, tax, original_tax,
           custom_product, seat_number, company_id)
        VALUES
          (:on, :date, '0', :did, :item, 0,
           :qty, :amount, :notes, :changes, :pays_tax, :tax, :tax,
           :custom, 0, :cid)
    """), {
        "on": data.order_number, "date": data.date, "did": data.dish_id,
        "item": item_num, "qty": data.quantity, "amount": amount,
        "notes": data.notes, "changes": data.changes,
        "pays_tax": pays_tax, "tax": tax_val,
        "custom": custom_product, "cid": cid,
    })

    # Assembly selections → pos_order_detail_products
    for sel in (data.assembly_selections or []):
        await db.execute(text("""
            INSERT INTO pos_order_detail_products
              (order_number, date, invoice_number, dish_id, item, group_id, item_id, quantity, company_id)
            VALUES (:on, :date, '0', :did, :item, :gid, :iid, :qty, :cid)
            ON DUPLICATE KEY UPDATE quantity = VALUES(quantity)
        """), {
            "on": data.order_number, "date": data.date, "did": data.dish_id,
            "item": item_num, "gid": sel.category_code,
            "iid": sel.item_id, "qty": sel.discount_qty, "cid": cid,
        })

    # Fixed products (group_id=0, always deducted at invoice time)
    fixed_rows = (await db.execute(text(
        "SELECT supplier_id, minimum_units FROM pos_dish_products "
        "WHERE dish_id=:did AND company_id=:cid AND active=1"
    ), {"did": data.dish_id, "cid": cid})).mappings().all()
    for fp in fixed_rows:
        await db.execute(text("""
            INSERT INTO pos_order_detail_products
              (order_number, date, invoice_number, dish_id, item, group_id, item_id, quantity, company_id)
            VALUES (:on, :date, '0', :did, :item, 0, :iid, :qty, :cid)
            ON DUPLICATE KEY UPDATE quantity = VALUES(quantity)
        """), {
            "on": data.order_number, "date": data.date, "did": data.dish_id,
            "item": item_num, "iid": fp["supplier_id"],
            "qty": float(fp["minimum_units"]) * data.quantity, "cid": cid,
        })

    # Recalculate order total
    await _recalc_total(db, data.order_number, data.date, cid)
    await db.commit()

    return {
        "item": item_num, "dish_id": data.dish_id,
        "quantity": data.quantity, "amount": amount,
        "notes": data.notes, "changes": data.changes,
    }


# ── 9. ACTUALIZAR ÍTEM ────────────────────────────────────────────────────────

@router.put("/orden/item")
async def actualizar_item(
    data: ActualizarItemIn,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    payload = await _auth_waiter(authorization)
    cid = payload["company_id"]

    current = (await db.execute(text(
        "SELECT quantity, amount FROM pos_order_details "
        "WHERE order_number=:on AND date=:date AND invoice_number='0' "
        "AND dish_id=:did AND item=:item AND company_id=:cid"
    ), {"on": data.order_number, "date": data.date, "did": data.dish_id, "item": data.item, "cid": cid})).mappings().first()
    if not current:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")

    sets, params = [], {
        "on": data.order_number, "date": data.date,
        "did": data.dish_id, "item": data.item, "cid": cid,
    }

    if data.quantity is not None:
        unit_price = int(current["amount"] / current["quantity"]) if current["quantity"] else 0
        sets += ["quantity = :qty", "amount = :amount"]
        params["qty"] = data.quantity
        params["amount"] = unit_price * data.quantity
    if data.notes is not None:
        sets.append("notes = :notes")
        params["notes"] = data.notes
    if data.changes is not None:
        sets.append("changes = :changes")
        params["changes"] = data.changes

    if sets:
        await db.execute(text(
            f"UPDATE pos_order_details SET {', '.join(sets)} "
            "WHERE order_number=:on AND date=:date AND invoice_number='0' "
            "AND dish_id=:did AND item=:item AND company_id=:cid"
        ), params)
        await _recalc_total(db, data.order_number, data.date, cid)
        await db.commit()

    return {"ok": True}


# ── 10. ELIMINAR ÍTEM ─────────────────────────────────────────────────────────

@router.delete("/orden/item")
async def eliminar_item(
    data: EliminarItemIn,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    payload = await _auth_waiter(authorization)
    cid = payload["company_id"]

    await db.execute(text("""
        DELETE FROM pos_order_detail_products
        WHERE order_number=:on AND date=:date AND invoice_number='0'
          AND dish_id=:did AND item=:item AND company_id=:cid
    """), {"on": data.order_number, "date": data.date, "did": data.dish_id, "item": data.item, "cid": cid})

    await db.execute(text("""
        DELETE FROM pos_order_details
        WHERE order_number=:on AND date=:date AND invoice_number='0'
          AND dish_id=:did AND item=:item AND depends_on=:dep AND company_id=:cid
    """), {"on": data.order_number, "date": data.date, "did": data.dish_id,
           "item": data.item, "dep": data.depends_on, "cid": cid})

    await _recalc_total(db, data.order_number, data.date, cid)
    await db.commit()
    return {"ok": True}


# ── 11. ENVIAR A COCINA ───────────────────────────────────────────────────────

@router.post("/orden/cocina")
async def enviar_cocina(
    data: EnviarCocinaIn,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    payload = await _auth_waiter(authorization)
    cid = payload["company_id"]
    now_str = _now_bog().strftime("%Y-%m-%d %H:%M:%S")

    result = await db.execute(text("""
        UPDATE pos_order_details
        SET dish_time = :now
        WHERE order_number = :on AND date = :date
          AND invoice_number = '0' AND company_id = :cid
          AND (dish_time IS NULL OR dish_time = '')
    """), {"now": now_str, "on": data.order_number, "date": data.date, "cid": cid})

    await db.commit()
    return {"sent": result.rowcount}


# ── 12. SOLICITAR CUENTA ──────────────────────────────────────────────────────

@router.post("/mesa/solicitar-cuenta")
async def solicitar_cuenta(
    data: SolicitarCuentaIn,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    payload = await _auth_waiter(authorization)
    cid = payload["company_id"]
    today = _today()

    await db.execute(text("""
        UPDATE pos_orders SET bill_requested = 1
        WHERE table_id = :tid AND company_id = :cid
          AND date = :today AND invoice_number = '0' AND cancelled = 0
    """), {"tid": data.table_id, "cid": cid, "today": today})
    await db.commit()
    return {"ok": True}


# ── 13. CANCELAR ORDEN ────────────────────────────────────────────────────────

@router.delete("/mesa/cancelar")
async def cancelar_orden(
    data: CancelarOrdenIn,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    payload = await _auth_waiter(authorization)
    cid = payload["company_id"]
    today = _today()

    order = (await db.execute(text(
        "SELECT order_number, date FROM pos_orders "
        "WHERE table_id=:tid AND company_id=:cid AND date=:today "
        "AND invoice_number='0' AND cancelled=0 LIMIT 1"
    ), {"tid": data.table_id, "cid": cid, "today": today})).mappings().first()
    if not order:
        raise HTTPException(status_code=404, detail="No hay orden activa para esta mesa")

    await db.execute(text(
        "UPDATE pos_orders SET cancelled=1 "
        "WHERE order_number=:on AND date=:date AND company_id=:cid"
    ), {"on": order["order_number"], "date": order["date"], "cid": cid})

    await db.commit()
    return {"ok": True}


# ── 14. COCINA TV ─────────────────────────────────────────────────────────────

@router.get("/cocina")
async def get_cocina(
    company_id: int = Query(..., description="ID de empresa (para la pantalla TV, sin auth)"),
    db: AsyncSession = Depends(get_db),
):
    cid = company_id
    today = _today()

    rows = (await db.execute(text("""
        WITH ranked AS (
            SELECT order_number, date, table_name, waiter_id, time, bill_requested,
                   ROW_NUMBER() OVER (
                       PARTITION BY company_id, date ORDER BY time ASC
                   ) AS daily_seq
            FROM pos_orders
            WHERE company_id = :cid AND date = :today
              AND invoice_number = '0' AND cancelled = 0
        )
        SELECT
            r.daily_seq,
            r.table_name,
            r.time          AS order_time,
            r.bill_requested,
            w.name          AS waiter_name,
            od.order_number,
            od.dish_id,
            od.item,
            od.quantity,
            od.notes,
            od.changes,
            od.custom_product,
            od.dish_time,
            d.name          AS dish_name,
            ip.printer_id,
            p.name          AS printer_name
        FROM ranked r
        JOIN pos_order_details od
             ON od.order_number   = r.order_number
            AND od.date           = r.date
            AND od.invoice_number = '0'
            AND od.company_id     = :cid
        JOIN pos_dishes d ON d.id = od.dish_id AND d.company_id = :cid
        LEFT JOIN pos_waiters w ON w.id = r.waiter_id AND w.company_id = :cid
        JOIN pos_item_printers ip ON ip.item_id = od.dish_id AND ip.company_id = :cid
        JOIN pos_printers p
             ON p.id = ip.printer_id AND p.company_id = :cid AND p.is_active = 1
        WHERE od.dish_time IS NOT NULL AND od.dish_time != ''
          AND d.preparation_time = 0
        ORDER BY ip.printer_id, r.daily_seq
    """), {"cid": cid, "today": today})).mappings().all()

    # Initialize all active printers (even empty ones appear as columns)
    all_printers = (await db.execute(text(
        "SELECT id, name FROM pos_printers WHERE company_id=:cid AND is_active=1 ORDER BY id"
    ), {"cid": cid})).mappings().all()

    printer_map: dict = {
        int(p["id"]): {
            "printer_id": int(p["id"]),
            "printer_name": p["name"],
            "orders": {},
        }
        for p in all_printers
    }

    for row in rows:
        pid = int(row["printer_id"])
        oid = row["order_number"]
        if pid not in printer_map:
            continue

        if oid not in printer_map[pid]["orders"]:
            printer_map[pid]["orders"][oid] = {
                "order_number": oid,
                "daily_seq": int(row["daily_seq"]),
                "table_name": row["table_name"],
                "waiter_name": row["waiter_name"],
                "order_time": row["order_time"],
                "bill_requested": bool(row["bill_requested"]),
                "latest_dish_time": row["dish_time"] or "",
                "items": [],
            }
        else:
            if (row["dish_time"] or "") > printer_map[pid]["orders"][oid]["latest_dish_time"]:
                printer_map[pid]["orders"][oid]["latest_dish_time"] = row["dish_time"]

        assembly = []
        if row["custom_product"]:
            try:
                cp = json.loads(row["custom_product"])
                assembly = cp.get("assembly", [])
            except Exception:
                pass

        printer_map[pid]["orders"][oid]["items"].append({
            "dish_id": row["dish_id"],
            "item": row["item"],
            "dish_name": row["dish_name"],
            "quantity": row["quantity"],
            "notes": row["notes"],
            "changes": row["changes"],
            "assembly": assembly,
            "dish_time": row["dish_time"],
        })

    result = []
    for pid in sorted(printer_map.keys()):
        pdata = printer_map[pid]
        orders = sorted(
            pdata["orders"].values(),
            key=lambda x: x["latest_dish_time"],
            reverse=True,
        )
        result.append({
            "printer_id": pdata["printer_id"],
            "printer_name": pdata["printer_name"],
            "orders": orders,
        })

    return result


# ── Helper ────────────────────────────────────────────────────────────────────

async def _recalc_total(db: AsyncSession, order_number: str, date: str, cid: int) -> None:
    await db.execute(text("""
        UPDATE pos_orders o
        SET amount = (
            SELECT COALESCE(SUM(od.amount), 0)
            FROM pos_order_details od
            WHERE od.order_number   = o.order_number
              AND od.date           = o.date
              AND od.invoice_number = '0'
              AND od.company_id     = o.company_id
        )
        WHERE o.order_number = :on AND o.date = :date AND o.company_id = :cid
    """), {"on": order_number, "date": date, "cid": cid})
