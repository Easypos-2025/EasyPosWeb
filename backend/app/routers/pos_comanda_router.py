"""
POS Comanda — Modalidad B: Servicio a Mesas
Pedidos activos → datatemppos (temp_comanda, temp_detalle_comanda_parcial, etc.)
Datos de referencia → easyposweb (menú, zonas, meseros, impresoras, pos_kitchen_status)
"""
from datetime import datetime, timezone, timedelta
import json
import re
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, List

from app.database import get_db, get_datatemppos_db
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


def _parse_table_id_from_order(order_number: str) -> int:
    """Extrae table_id del formato WEB-{cid}-{table_id}-{ts}."""
    try:
        parts = order_number.split("-")
        if len(parts) >= 3:
            return int(parts[2])
    except Exception:
        pass
    return 0


async def _auth_comanda(
    authorization: str = Header(None),
    x_company_id: Optional[int] = Header(None, alias="X-Company-Id"),
) -> dict:
    """Acepta tokens de mesero Y tokens de usuario regular (admin desde dashboard)."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    payload = dict(payload)
    if x_company_id:
        payload["company_id"] = x_company_id
    if not payload.get("company_id"):
        raise HTTPException(status_code=400, detail="company_id requerido")
    if "waiter_id" not in payload:
        payload["waiter_id"] = 0
    return payload


# ── Schemas ───────────────────────────────────────────────────────────────────

class WaiterLoginIn(BaseModel):
    company_id: int
    waiter_id: int
    pin: str


class AbrirMesaIn(BaseModel):
    table_id: int
    guests_count: Optional[int] = 1
    waiter_id: Optional[int] = None  # Admin puede pasarlo explícitamente


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
async def get_mesas(
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    cid = payload["company_id"]
    today = _today()

    # Auto-cancelar pedidos sin ítems (web y escritorio)
    await db_temp.execute(text("""
        UPDATE temp_comanda tc
        SET tc.Cancelado = 1
        WHERE tc.company_id = :cid
          AND tc.Nro_Factura = '0'
          AND tc.Cancelado = 0
          AND NOT EXISTS (
              SELECT 1 FROM temp_detalle_comanda_parcial tdc
              WHERE tdc.Nro_pedido = tc.Nro_Pedido
                AND tdc.Fecha = tc.Fecha
                AND tdc.company_id = tc.company_id
                AND tdc.Nro_Factura = '0'
          )
    """), {"cid": cid})
    # Cerrar en temp_mesa_abierta las mesas que ya no tienen pedido activo
    await db_temp.execute(text("""
        UPDATE temp_mesa_abierta tma
        SET tma.Abierta = 0, tma.Abierta_Desde = NULL, tma.updated_at = NOW()
        WHERE tma.company_id = :cid
          AND tma.Abierta = 1
          AND NOT EXISTS (
              SELECT 1 FROM temp_comanda tc
              WHERE tc.company_id = :cid
                AND tc.Mesa = tma.Mesa
                AND tc.Cancelado = 0
                AND tc.Nro_Factura = '0'
          )
    """), {"cid": cid})
    await db_temp.commit()

    # Layout de mesas y zonas desde easyposweb
    layout_rows = (await db.execute(text("""
        SELECT
            tl.id, tl.name, tl.seats, tl.zone_id, tl.active,
            z.name          AS zone_name,
            z.color         AS zone_color,
            z.icon          AS zone_icon,
            z.order_index   AS zone_order
        FROM pos_tables_layout tl
        LEFT JOIN pos_zones z ON z.id = tl.zone_id AND z.company_id = :cid
        WHERE tl.company_id = :cid
        ORDER BY z.order_index, tl.id
    """), {"cid": cid})).mappings().all()

    # Mesas abiertas desde datatemppos
    open_rows = (await db_temp.execute(text(
        "SELECT Id_Mesa FROM temp_mesa_abierta WHERE company_id=:cid AND Abierta=1"
    ), {"cid": cid})).mappings().all()
    open_set = {int(r["Id_Mesa"]) for r in open_rows}

    # Pedidos activos desde datatemppos (sin filtro de fecha — incluye pendientes de días anteriores)
    order_rows = (await db_temp.execute(text("""
        SELECT Nro_Pedido, Mesa, Mesero, Hora, Valor
        FROM temp_comanda
        WHERE company_id=:cid AND Nro_Factura='0' AND Cancelado=0
        ORDER BY Hora ASC
    """), {"cid": cid})).mappings().all()

    # Mapa: nombre de mesa → info del pedido (con daily_seq calculado)
    order_by_mesa: dict = {}
    for seq_num, o in enumerate(order_rows, start=1):
        mesa_key = str(o["Mesa"] or "").strip()
        if mesa_key and mesa_key not in order_by_mesa:
            order_by_mesa[mesa_key] = {
                "order_number": o["Nro_Pedido"],
                "amount":       int(o["Valor"] or 0),
                "order_time":   str(o["Hora"] or ""),
                "waiter_id":    int(o["Mesero"] or 0),
                "daily_seq":    seq_num,
            }

    # Nombres de meseros desde easyposweb
    waiter_ids = {v["waiter_id"] for v in order_by_mesa.values() if v["waiter_id"]}
    waiter_names: dict = {}
    if waiter_ids:
        id_list = ",".join(str(w) for w in waiter_ids)
        wrows = (await db.execute(text(
            f"SELECT id, name FROM pos_waiters WHERE company_id=:cid AND id IN ({id_list})"
        ), {"cid": cid})).mappings().all()
        waiter_names = {int(r["id"]): r["name"] for r in wrows}

    # Construir respuesta por zonas
    zones: dict = {}
    for r in layout_rows:
        zid = r["zone_id"] or 0
        if zid not in zones:
            zones[zid] = {
                "id":          zid,
                "name":        r["zone_name"] or f"Zona {zid}",
                "color":       r["zone_color"] or "#1d4ed8",
                "icon":        r["zone_icon"] or "bi-grid",
                "order_index": r["zone_order"] or 0,
                "tables":      [],
            }

        tid = int(r["id"])
        status = "occupied" if tid in open_set else "free"
        order_info = order_by_mesa.get(str(r["name"]).strip()) if status == "occupied" else None

        zones[zid]["tables"].append({
            "id":          tid,
            "name":        r["name"],
            "seats":       r["seats"],
            "status":      status,
            "order_number": order_info["order_number"] if order_info else None,
            "amount":       order_info["amount"] if order_info else None,
            "order_time":   order_info["order_time"] if order_info else None,
            "waiter_id":    order_info["waiter_id"] if order_info else None,
            "waiter_name":  waiter_names.get(order_info["waiter_id"]) if order_info else None,
            "daily_seq":    order_info["daily_seq"] if order_info else None,
        })

    return sorted(zones.values(), key=lambda z: z["order_index"])


# ── 3. ABRIR MESA ─────────────────────────────────────────────────────────────

@router.post("/mesa/abrir")
async def abrir_mesa(
    data: AbrirMesaIn,
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    cid = payload["company_id"]
    waiter_id = data.waiter_id if data.waiter_id is not None else payload.get("waiter_id", 0)
    today = _today()

    mesa = (await db.execute(text(
        "SELECT id, name, active FROM pos_tables_layout WHERE id=:tid AND company_id=:cid"
    ), {"tid": data.table_id, "cid": cid})).mappings().first()
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")

    # Verificar si ya existe un pedido activo para esta mesa (cualquier origen)
    existing = (await db_temp.execute(text("""
        SELECT Nro_Pedido FROM temp_comanda
        WHERE Mesa=:mesa AND company_id=:cid AND Fecha=:today
          AND Nro_Factura='0' AND Cancelado=0
        LIMIT 1
    """), {"mesa": mesa["name"], "cid": cid, "today": today})).mappings().first()
    if existing:
        return {"order_number": existing["Nro_Pedido"], "date": today, "already_open": True}

    order_number = _order_number(cid, data.table_id)

    # Insertar en temp_comanda (Movil=1 = origen web)
    await db_temp.execute(text("""
        INSERT INTO temp_comanda
            (company_id, Nro_Pedido, Fecha, Nro_Factura, Mesa, Hora,
             Mesero, Cancelado, Valor, Nro_Comenzales, Domicilio, Id_Cliente, Movil, updated_at)
        VALUES
            (:cid, :on, :date, '0', :mesa, :hora,
             :wid, 0, 0, :guests, 0, 0, 1, NOW())
    """), {
        "cid":    cid,
        "on":     order_number,
        "date":   today,
        "mesa":   mesa["name"],
        "hora":   _time_str(),
        "wid":    waiter_id,
        "guests": data.guests_count,
    })

    # Marcar mesa como abierta en temp_mesa_abierta
    await db_temp.execute(text("""
        INSERT INTO temp_mesa_abierta
            (company_id, Id_Mesa, Mesa, Abierta, Abierta_Desde, updated_at)
        VALUES (:cid, :tid, :mesa, 1, NOW(), NOW())
        ON DUPLICATE KEY UPDATE
            Mesa          = VALUES(Mesa),
            Abierta       = 1,
            Abierta_Desde = CASE WHEN Abierta = 0 THEN NOW() ELSE Abierta_Desde END,
            updated_at    = NOW()
    """), {"cid": cid, "tid": data.table_id, "mesa": mesa["name"]})

    await db_temp.commit()
    return {"order_number": order_number, "date": today, "already_open": False}


# ── 4. ORDEN ACTIVA DE UNA MESA ───────────────────────────────────────────────

@router.get("/mesa/{table_id}/orden")
async def get_orden_mesa(
    table_id: int,
    order_number: Optional[str] = Query(None),
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    cid = payload["company_id"]
    today = _today()

    # Obtener nombre de mesa desde easyposweb
    mesa_row = (await db.execute(text(
        "SELECT name FROM pos_tables_layout WHERE id=:tid AND company_id=:cid"
    ), {"tid": table_id, "cid": cid})).mappings().first()
    if not mesa_row:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    mesa_name = str(mesa_row["name"])

    # Pedido activo desde datatemppos
    # Si viene order_number (pedido VB6 conocido): lookup directo por Nro_Pedido
    # Si no: buscar por mesa, prefiriendo Movil=0 (VB6) sobre Movil=1 (web)
    if order_number:
        order = (await db_temp.execute(text("""
            SELECT Nro_Pedido, Fecha, Valor, Hora, Nro_Comenzales, Mesero, Novedad, Mesa
            FROM temp_comanda
            WHERE Nro_Pedido=:on AND company_id=:cid AND Fecha=:today
              AND Nro_Factura='0' AND Cancelado=0
            LIMIT 1
        """), {"on": order_number, "cid": cid, "today": today})).mappings().first()
    else:
        order = (await db_temp.execute(text("""
            SELECT Nro_Pedido, Fecha, Valor, Hora, Nro_Comenzales, Mesero, Novedad, Mesa
            FROM temp_comanda
            WHERE Mesa=:mesa AND company_id=:cid AND Fecha=:today
              AND Nro_Factura='0' AND Cancelado=0
            ORDER BY Movil ASC, Hora ASC
            LIMIT 1
        """), {"mesa": mesa_name, "cid": cid, "today": today})).mappings().first()

    if not order:
        return {"order": None, "items": []}

    on    = order["Nro_Pedido"]
    fecha = str(order["Fecha"])

    # Calcular daily_seq
    seq_rows = (await db_temp.execute(text("""
        SELECT Nro_Pedido FROM temp_comanda
        WHERE company_id=:cid AND Fecha=:today AND Nro_Factura='0' AND Cancelado=0
        ORDER BY Hora ASC
    """), {"cid": cid, "today": today})).mappings().all()
    seq_map = {r["Nro_Pedido"]: i + 1 for i, r in enumerate(seq_rows)}

    # Nombre del mesero desde easyposweb
    waiter_id = int(order["Mesero"] or 0)
    waiter_name = None
    if waiter_id:
        wrow = (await db.execute(text(
            "SELECT name FROM pos_waiters WHERE id=:wid AND company_id=:cid"
        ), {"wid": waiter_id, "cid": cid})).mappings().first()
        waiter_name = wrow["name"] if wrow else None

    # Ítems del pedido desde datatemppos (solo registros maestros: Mostrar=1)
    items_rows = (await db_temp.execute(text("""
        SELECT Id_Plato, Item, Depende, Cantidad, Valor, Novedad,
               Cambios, Producto_Personalizado, Hora_Plato
        FROM temp_detalle_comanda_parcial
        WHERE Nro_pedido=:on AND Fecha=:fecha AND Nro_Factura='0'
          AND company_id=:cid AND Mostrar=1
        ORDER BY Item
    """), {"on": on, "fecha": fecha, "cid": cid})).mappings().all()

    # Nombres de platos desde easyposweb
    dish_ids = list({int(r["Id_Plato"]) for r in items_rows})
    dish_names: dict = {}
    if dish_ids:
        id_list = ",".join(str(d) for d in dish_ids)
        drows = (await db.execute(text(
            f"SELECT id, name FROM pos_dishes WHERE company_id=:cid AND id IN ({id_list})"
        ), {"cid": cid})).mappings().all()
        dish_names = {int(r["id"]): r["name"] for r in drows}

    items = []
    for r in items_rows:
        assembly = []
        if r["Producto_Personalizado"]:
            try:
                cp = json.loads(r["Producto_Personalizado"])
                assembly = cp.get("assembly", [])
            except Exception:
                pass
        hora_plato = str(r["Hora_Plato"] or "")
        sent = bool(hora_plato and hora_plato not in ("", "0"))
        items.append({
            "dish_id":   int(r["Id_Plato"]),
            "item":      int(r["Item"]),
            "dish_name": dish_names.get(int(r["Id_Plato"]), f"Plato {r['Id_Plato']}"),
            "quantity":  float(r["Cantidad"] or 0),
            "amount":    int(r["Valor"] or 0),
            "notes":     r["Novedad"],
            "changes":   r["Cambios"],
            "assembly":  assembly,
            "dish_time": hora_plato,
            "sent":      sent,
        })

    return {
        "order": {
            "order_number": on,
            "date":         fecha,
            "amount":       int(order["Valor"] or 0),
            "time":         str(order["Hora"] or ""),
            "guests_count": int(order["Nro_Comenzales"] or 0),
            "waiter_id":    waiter_id,
            "waiter_name":  waiter_name,
            "table_name":   order["Mesa"],
            "daily_seq":    seq_map.get(on, 1),
        },
        "items": items,
    }


# ── 5. MENÚ (platos con config de armado) ────────────────────────────────────

@router.get("/menu")
async def get_menu(payload: dict = Depends(_auth_comanda), db: AsyncSession = Depends(get_db)):
    cid = payload["company_id"]

    # active=0 es el convenio VB6 para "producto activo" (activo=no_desactivado).
    # Intenta con columnas extendidas; si fallan, usa fallbacks progresivos.
    # has_assembly = true si:
    #   offer_priority=1 (menú del día) O existe en pos_dish_assembly (opciones de armado)
    # Ambos casos son mutuamente excluyentes por diseño VB6.
    dishes = None
    for sql in [
        # Nivel 1: columnas completas
        """SELECT DISTINCT d.id, d.name, d.price, d.category_id, d.photo_path,
                COALESCE(d.tax, 0) AS tax,
                (COALESCE(d.offer_priority, 0) = 1 OR EXISTS(
                    SELECT 1 FROM pos_dish_assembly da
                    WHERE da.dish_id = d.id AND da.company_id = d.company_id AND da.is_active = 1
                )) AS has_assembly,
                COALESCE(d.preparation_time, 0) AS no_print,
                c.name AS category_name
           FROM pos_dishes d
           INNER JOIN pos_dish_categories c
                   ON c.id = d.category_id AND c.company_id = d.company_id
           WHERE d.company_id = :cid AND c.is_active = 1 AND d.active = 0
           ORDER BY c.name, d.name""",
        # Nivel 2: sin tax ni preparation_time
        """SELECT DISTINCT d.id, d.name, d.price, d.category_id, d.photo_path,
                0 AS tax,
                (COALESCE(d.offer_priority, 0) = 1 OR EXISTS(
                    SELECT 1 FROM pos_dish_assembly da
                    WHERE da.dish_id = d.id AND da.company_id = d.company_id AND da.is_active = 1
                )) AS has_assembly,
                0 AS no_print,
                c.name AS category_name
           FROM pos_dishes d
           INNER JOIN pos_dish_categories c
                   ON c.id = d.category_id AND c.company_id = d.company_id
           WHERE d.company_id = :cid AND c.is_active = 1 AND d.active = 0
           ORDER BY c.name, d.name""",
        # Nivel 3: último recurso sin columnas opcionales
        """SELECT DISTINCT d.id, d.name, d.price, d.category_id, d.photo_path,
                0 AS tax, 0 AS has_assembly, 0 AS no_print,
                c.name AS category_name
           FROM pos_dishes d
           INNER JOIN pos_dish_categories c
                   ON c.id = d.category_id AND c.company_id = d.company_id
           WHERE d.company_id = :cid AND c.is_active = 1
           ORDER BY c.name, d.name""",
    ]:
        try:
            dishes = (await db.execute(text(sql), {"cid": cid})).mappings().all()
            break
        except Exception:
            continue
    if dishes is None:
        dishes = []

    ip_map: dict[int, list] = {}
    printers = []
    try:
        item_printers = (await db.execute(text(
            "SELECT item_id, printer_id FROM pos_item_printers WHERE company_id=:cid"
        ), {"cid": cid})).mappings().all()
        for ip in item_printers:
            ip_map.setdefault(int(ip["item_id"]), []).append(int(ip["printer_id"]))
        printers = (await db.execute(text(
            "SELECT id, name FROM pos_printers WHERE company_id=:cid AND is_active=1 ORDER BY id"
        ), {"cid": cid})).mappings().all()
    except Exception:
        pass  # tablas de impresoras aún no creadas en esta BD

    categories: dict = {}
    for d in dishes:
        cat_id = d["category_id"] or 0
        if cat_id not in categories:
            categories[cat_id] = {
                "category_id":   cat_id,
                "category_name": d["category_name"] or "Sin categoría",
                "dishes":        [],
            }
        categories[cat_id]["dishes"].append({
            "id":          d["id"],
            "name":        d["name"],
            "price":       d["price"],
            "photo_path":  d["photo_path"] or None,
            "tax":         float(d["tax"]) if d["tax"] else 0,
            "has_assembly": bool(d["has_assembly"]),
            "no_print":    bool(d["no_print"]),
            "printer_ids": ip_map.get(int(d["id"]), []),
        })

    return {
        "categories": list(categories.values()),
        "printers":   [{"id": p["id"], "name": p["name"]} for p in printers],
    }


# ── 6. MENÚ DIARIO (opciones de armado para hoy) ─────────────────────────────

@router.get("/menu-diario/{dish_id}")
async def get_menu_diario(
    dish_id: int,
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
):
    cid = payload["company_id"]
    today = _today()

    # ── Verificar si es plato de Menú del Día (offer_priority=1) ──────────────
    dish_row = (await db.execute(text(
        "SELECT COALESCE(offer_priority,0) AS offer_priority FROM pos_dishes WHERE id=:did AND company_id=:cid"
    ), {"did": dish_id, "cid": cid})).mappings().first()
    is_daily_menu = bool(dish_row and int(dish_row["offer_priority"]) == 1)

    # ── Categorías de armado desde pos_dish_assembly ───────────────────────────
    assembly_cats = None
    for sql_cats in [
        """SELECT da.category_code, da.max_choices, da.is_required, da.print_on_change_only,
                  (SELECT pc2.name FROM pos_product_categories pc2
                   WHERE pc2.id = da.category_code AND pc2.company_id = :cid LIMIT 1) AS category_name
           FROM pos_dish_assembly da
           WHERE da.dish_id = :did AND da.company_id = :cid AND da.is_active = 1
           ORDER BY da.category_code""",
        """SELECT da.category_code, da.max_choices, da.is_required, da.print_on_change_only,
                  NULL AS category_name
           FROM pos_dish_assembly da
           WHERE da.dish_id = :did AND da.company_id = :cid AND da.is_active = 1
           ORDER BY da.category_code""",
    ]:
        try:
            rows = (await db.execute(text(sql_cats), {"did": dish_id, "cid": cid})).mappings().all()
            assembly_cats = rows
            break
        except Exception:
            continue

    if not assembly_cats:
        return {"categories": [], "fixed_products": []}

    category_codes = [int(r["category_code"]) for r in assembly_cats]
    placeholders = ", ".join([f":cc{i}" for i in range(len(category_codes))])
    params: dict = {"did": dish_id, "cid": cid, "today": today}
    for i, cc in enumerate(category_codes):
        params[f"cc{i}"] = cc

    options_by_cat: dict[int, list] = {}

    if is_daily_menu:
        # Para Menú del Día: las opciones vienen directamente de pos_daily_menu
        # agrupadas por menu_id (= pos_product_categories.id = category_code).
        # Solo se muestran los ítems que el admin seleccionó para hoy.
        daily_rows = (await db.execute(text(f"""
            SELECT dm.menu_id AS category_code,
                   dm.item_id,
                   dm.description AS item_name
            FROM pos_daily_menu dm
            WHERE dm.company_id = :cid
              AND dm.date       = :today
              AND dm.menu_id    IN ({placeholders})
            ORDER BY dm.menu_id, dm.description
        """), params)).mappings().all()

        for row in daily_rows:
            cc = int(row["category_code"])
            options_by_cat.setdefault(cc, []).append({
                "item_id":         row["item_id"],
                "item_name":       row["item_name"] or f"Opción {row['item_id']}",
                "discount_qty":    1.0,
                "is_default":      False,
                "available_today": True,
            })
    else:
        # Para platos con armado fijo: pos_dish_assembly_detail + filtro daily_menu
        # JOIN correcto: dm.item_id = dad.position (supply_items.id_item)
        options_rows = (await db.execute(text(f"""
            SELECT
                dad.category_code,
                dad.item                                        AS item_id,
                dad.discount_qty,
                dad.is_default,
                dad.position,
                COALESCE(si.description, si.description)        AS item_name,
                IF(dm.id IS NOT NULL, 1, 0)                     AS available_today
            FROM pos_dish_assembly_detail dad
            LEFT JOIN pos_daily_menu dm
                   ON dm.item_id    = dad.position
                  AND dm.company_id = :cid
                  AND dm.date       = :today
            LEFT JOIN supply_items si
                   ON si.id_item    = dad.position
                  AND si.company_id = :cid
            WHERE dad.dish_id = :did AND dad.company_id = :cid
              AND dad.category_code IN ({placeholders})
            ORDER BY dad.category_code, dad.position
        """), params)).mappings().all()

        for row in options_rows:
            cc = int(row["category_code"])
            options_by_cat.setdefault(cc, []).append({
                "item_id":         row["item_id"],
                "item_name":       row["item_name"] or f"Opción {row['item_id']}",
                "discount_qty":    float(row["discount_qty"]) if row["discount_qty"] else 1.0,
                "is_default":      bool(row["is_default"]),
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
            "category_code":        cc,
            "category_name":        cat["category_name"] or f"Categoría {cc}",
            "max_choices":          cat["max_choices"],
            "is_required":          bool(cat["is_required"]),
            "print_on_change_only": bool(cat["print_on_change_only"]),
            "options":              options_by_cat.get(cc, []),
        })

    return {
        "categories":     result,
        "fixed_products": [
            {"item_id": f["item_id"], "quantity": f["quantity"], "description": f["description"]}
            for f in fixed
        ],
    }


# ── 7. NOVEDADES PRECARGADAS ──────────────────────────────────────────────────

@router.get("/novedades")
async def get_novedades(payload: dict = Depends(_auth_comanda), db: AsyncSession = Depends(get_db)):
    cid = payload["company_id"]

    notes = None
    for sql in [
        "SELECT id, name, COALESCE(cod_categoria, 0) AS cod_categoria FROM pos_dish_note_categories WHERE company_id=:cid ORDER BY cod_categoria, id",
        "SELECT id, name, 0 AS cod_categoria FROM pos_order_notes WHERE company_id=:cid ORDER BY id",
    ]:
        try:
            rows = (await db.execute(text(sql), {"cid": cid})).mappings().all()
            notes = rows
            break
        except Exception:
            continue

    if notes is None:
        notes = []

    return {"notes": [{"id": n["id"], "name": n["name"], "cod_categoria": n["cod_categoria"]} for n in notes]}


# ── 8. AGREGAR ÍTEM A LA ORDEN ────────────────────────────────────────────────

@router.post("/orden/item")
async def agregar_item(
    data: AgregarItemIn,
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    cid = payload["company_id"]

    # Verificar pedido activo en datatemppos
    order = (await db_temp.execute(text("""
        SELECT Nro_Pedido FROM temp_comanda
        WHERE Nro_Pedido=:on AND Fecha=:date AND company_id=:cid
          AND Nro_Factura='0' AND Cancelado=0
        LIMIT 1
    """), {"on": data.order_number, "date": data.date, "cid": cid})).mappings().first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada o ya cerrada")

    # Info del plato desde easyposweb
    dish = (await db.execute(text(
        "SELECT id, price, tax FROM pos_dishes WHERE id=:did AND company_id=:cid"
    ), {"did": data.dish_id, "cid": cid})).mappings().first()
    if not dish:
        raise HTTPException(status_code=404, detail="Plato no encontrado o inactivo")

    # Siguiente número de ítem en datatemppos
    max_item = (await db_temp.execute(text(
        "SELECT COALESCE(MAX(Item), 0) FROM temp_detalle_comanda_parcial "
        "WHERE Nro_pedido=:on AND Fecha=:date AND company_id=:cid"
    ), {"on": data.order_number, "date": data.date, "cid": cid})).scalar() or 0
    item_num = int(max_item) + 1

    amount = data.amount if data.amount else int(dish["price"] * data.quantity)
    tax_pct = float(dish["tax"]) if dish["tax"] else 0
    pays_tax = 1 if tax_pct > 0 else 0
    tax_val  = int(amount * tax_pct / 100) if pays_tax else 0

    custom_product = None
    if data.assembly_selections:
        custom_product = json.dumps(
            {"assembly": [s.model_dump() for s in data.assembly_selections]},
            ensure_ascii=False,
        )

    # Insertar ítem en datatemppos (Mostrar=1 = registro maestro)
    await db_temp.execute(text("""
        INSERT INTO temp_detalle_comanda_parcial
            (company_id, Nro_pedido, Fecha, Nro_Factura, Id_Plato, Item, Depende,
             Cantidad, Valor, Novedad, Cambios, Paga_Impuesto, Impuesto, Impuesto_Original,
             Producto_Personalizado, Nro_Puesto, Mostrar, Hora, updated_at)
        VALUES
            (:cid, :on, :date, '0', :did, :item, '0',
             :qty, :amount, :notes, :changes, :pays_tax, :tax, :tax,
             :custom, 0, 1, :hora, NOW())
    """), {
        "cid":      cid,
        "on":       data.order_number,
        "date":     data.date,
        "did":      data.dish_id,
        "item":     item_num,
        "qty":      data.quantity,
        "amount":   amount,
        "notes":    data.notes,
        "changes":  data.changes,
        "pays_tax": pays_tax,
        "tax":      tax_val,
        "custom":   custom_product,
        "hora":     _time_str(),
    })

    # Armado → temp_plato_producto_parcial
    for sel in (data.assembly_selections or []):
        await db_temp.execute(text("""
            INSERT INTO temp_plato_producto_parcial
                (company_id, Nro_Pedido, Fecha, Nro_Factura,
                 Id_Plato, Item, Id_Grupo, Id_Item, Cantidad, updated_at)
            VALUES
                (:cid, :on, :date, '0',
                 :did, :item, :gid, :iid, :qty, NOW())
            ON DUPLICATE KEY UPDATE Cantidad = VALUES(Cantidad)
        """), {
            "cid":  cid,
            "on":   data.order_number,
            "date": data.date,
            "did":  data.dish_id,
            "item": item_num,
            "gid":  sel.category_code,
            "iid":  sel.item_id,
            "qty":  sel.discount_qty,
        })

    await _recalc_total(db_temp, data.order_number, data.date, cid)
    await db_temp.commit()

    return {
        "item":     item_num,
        "dish_id":  data.dish_id,
        "quantity": data.quantity,
        "amount":   amount,
        "notes":    data.notes,
        "changes":  data.changes,
    }


# ── 9. ACTUALIZAR ÍTEM ────────────────────────────────────────────────────────

@router.put("/orden/item")
async def actualizar_item(
    data: ActualizarItemIn,
    payload: dict = Depends(_auth_comanda),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    cid = payload["company_id"]

    current = (await db_temp.execute(text("""
        SELECT Cantidad, Valor FROM temp_detalle_comanda_parcial
        WHERE Nro_pedido=:on AND Fecha=:date AND Nro_Factura='0'
          AND Id_Plato=:did AND Item=:item AND company_id=:cid AND Mostrar=1
    """), {
        "on": data.order_number, "date": data.date,
        "did": data.dish_id, "item": data.item, "cid": cid,
    })).mappings().first()
    if not current:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")

    sets, params = [], {
        "on": data.order_number, "date": data.date,
        "did": data.dish_id, "item": data.item, "cid": cid,
    }

    if data.quantity is not None:
        qty = float(current["Cantidad"])
        unit_price = int(int(current["Valor"]) / qty) if qty else 0
        sets += ["Cantidad = :qty", "Valor = :amount"]
        params["qty"]    = data.quantity
        params["amount"] = unit_price * data.quantity
    if data.notes is not None:
        sets.append("Novedad = :notes")
        params["notes"] = data.notes
    if data.changes is not None:
        sets.append("Cambios = :changes")
        params["changes"] = data.changes

    if sets:
        await db_temp.execute(text(
            f"UPDATE temp_detalle_comanda_parcial SET {', '.join(sets)} "
            "WHERE Nro_pedido=:on AND Fecha=:date AND Nro_Factura='0' "
            "AND Id_Plato=:did AND Item=:item AND company_id=:cid AND Mostrar=1"
        ), params)
        await _recalc_total(db_temp, data.order_number, data.date, cid)
        await db_temp.commit()

    return {"ok": True}


# ── 10. ELIMINAR ÍTEM ─────────────────────────────────────────────────────────

@router.delete("/orden/item")
async def eliminar_item(
    data: EliminarItemIn,
    payload: dict = Depends(_auth_comanda),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    cid = payload["company_id"]

    # Borrar armado del ítem
    await db_temp.execute(text("""
        DELETE FROM temp_plato_producto_parcial
        WHERE Nro_Pedido=:on AND Id_Plato=:did AND Item=:item AND company_id=:cid
    """), {
        "on": data.order_number, "did": data.dish_id,
        "item": data.item, "cid": cid,
    })

    # Borrar ítem principal
    await db_temp.execute(text("""
        DELETE FROM temp_detalle_comanda_parcial
        WHERE Nro_pedido=:on AND Fecha=:date AND Nro_Factura='0'
          AND Id_Plato=:did AND Item=:item AND company_id=:cid
    """), {
        "on": data.order_number, "date": data.date,
        "did": data.dish_id, "item": data.item, "cid": cid,
    })

    await _recalc_total(db_temp, data.order_number, data.date, cid)
    await db_temp.commit()
    return {"ok": True}


# ── 11. ENVIAR A COCINA ───────────────────────────────────────────────────────

@router.post("/orden/cocina")
async def enviar_cocina(
    data: EnviarCocinaIn,
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    cid = payload["company_id"]
    now_str = _now_bog().strftime("%Y-%m-%d %H:%M:%S")

    # Determinar si es PEDIDO NUEVO (tc.Salio=0) o PEDIDO AGREGADO (tc.Salio=1)
    order = (await db_temp.execute(text("""
        SELECT Salio FROM temp_comanda
        WHERE Nro_Pedido=:on AND Fecha=:date AND company_id=:cid
          AND Nro_Factura='0' AND Cancelado=0
        LIMIT 1
    """), {"on": data.order_number, "date": data.date, "cid": cid})).mappings().first()

    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    is_nuevo = int(order["Salio"] or 0) == 0
    tipo = "nuevo" if is_nuevo else "agregado"

    # Si es NUEVO: activar visibilidad del pedido completo en tc
    if is_nuevo:
        await db_temp.execute(text("""
            UPDATE temp_comanda SET Salio = 1
            WHERE Nro_Pedido=:on AND Fecha=:date AND company_id=:cid
        """), {"on": data.order_number, "date": data.date, "cid": cid})

    # Marcar con Hora_Plato solo los ítems aún no enviados (Salio=0)
    result = await db_temp.execute(text("""
        UPDATE temp_detalle_comanda_parcial
        SET Hora_Plato = :now, Salio = 1
        WHERE Nro_pedido = :on AND Fecha = :date
          AND Nro_Factura = '0' AND company_id = :cid
          AND Salio = 0
    """), {"now": now_str, "on": data.order_number, "date": data.date, "cid": cid})

    await db_temp.commit()

    # Archivar snapshot de ítems comandados para trazabilidad
    # (INSERT IGNORE → idempotente; se acumulan nuevos ítems en envíos adicionales)
    try:
        await archive_commands_to_history(db_temp, db, cid, [data.order_number], "kitchen_send")
    except Exception:
        pass  # Best-effort: no bloquear el flujo principal

    return {"tipo": tipo, "sent": result.rowcount}


# ── 12. SOLICITAR CUENTA ──────────────────────────────────────────────────────

@router.post("/mesa/solicitar-cuenta")
async def solicitar_cuenta(
    data: SolicitarCuentaIn,
    payload: dict = Depends(_auth_comanda),
):
    return {"ok": True}


# ── 13. CANCELAR ORDEN ────────────────────────────────────────────────────────

@router.delete("/mesa/cancelar")
async def cancelar_orden(
    data: CancelarOrdenIn,
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    cid = payload["company_id"]
    today = _today()

    # Obtener nombre de mesa desde easyposweb
    mesa_row = (await db.execute(text(
        "SELECT name FROM pos_tables_layout WHERE id=:tid AND company_id=:cid"
    ), {"tid": data.table_id, "cid": cid})).mappings().first()
    if not mesa_row:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    mesa_name = str(mesa_row["name"])

    # Buscar pedido activo en datatemppos (con Salio para saber si ya fue a cocina)
    order = (await db_temp.execute(text("""
        SELECT Nro_Pedido, Fecha, Mesa, Hora, Mesero, Valor, Salio FROM temp_comanda
        WHERE Mesa=:mesa AND company_id=:cid AND Fecha=:today
          AND Nro_Factura='0' AND Cancelado=0
        LIMIT 1
    """), {"mesa": mesa_name, "cid": cid, "today": today})).mappings().first()
    if not order:
        raise HTTPException(status_code=404, detail="No hay orden activa para esta mesa")

    on    = str(order["Nro_Pedido"])
    fecha = str(order["Fecha"])

    # ── Obtener todos los ítems del pedido (para TV + historial) ──────────────
    all_items = (await db_temp.execute(text("""
        SELECT Id_Plato, Item, Cantidad, Valor, Novedad, Cambios,
               Hora_Plato, Mostrar, Salio, Nro_Factura
        FROM temp_detalle_comanda_parcial
        WHERE Nro_pedido=:on AND Fecha=:date AND company_id=:cid
    """), {"on": on, "date": fecha, "cid": cid})).mappings().all()

    # ── Evento TV CANCELADO (solo si ya salió a cocina) ───────────────────────
    tv_notified = 0
    if int(order["Salio"] or 0) == 1:
        kitchen_items = [r for r in all_items if int(r["Mostrar"] or 0) == 1 and int(r["Salio"] or 0) == 1]
        dish_ids_ev = list({int(r["Id_Plato"]) for r in kitchen_items})
        dish_names_ev: dict = {}
        if dish_ids_ev:
            id_list = ",".join(str(d) for d in dish_ids_ev)
            drows = (await db.execute(text(
                f"SELECT id, name FROM pos_dishes WHERE company_id=:cid AND id IN ({id_list})"
            ), {"cid": cid})).mappings().all()
            dish_names_ev = {int(r["id"]): r["name"] for r in drows}

        snapshot = json.dumps([{
            "dish_id":    int(r["Id_Plato"]),
            "dish_name":  dish_names_ev.get(int(r["Id_Plato"]), f"Plato {r['Id_Plato']}"),
            "quantity":   float(r["Cantidad"] or 0),
            "notes":      str(r["Novedad"] or ""),
            "hora_tomado": str(r.get("Hora_Plato") or ""),
            "assembly":   [],
            "changes":    None,
        } for r in kitchen_items], ensure_ascii=False)

        await db.execute(text("""
            INSERT INTO pos_kitchen_events
                (company_id, event_type, order_number, table_name, waiter_id,
                 items_snapshot, event_date, created_at)
            VALUES (:cid, 'cancelado', :on, :mesa, :wid, :snap, :edate, NOW())
        """), {
            "cid":   cid,
            "on":    on,
            "mesa":  str(order["Mesa"]),
            "wid":   int(order["Mesero"] or 0),
            "snap":  snapshot,
            "edate": today,
        })
        tv_notified = 1

    # ── Archivar cabecera en historico_comandas_eliminadas ────────────────────
    quien = str(payload.get("sub") or payload.get("name") or "web")
    await db.execute(text("""
        INSERT INTO historico_comandas_eliminadas
            (company_id, Nro_Pedido, Fecha, Nro_Factura, Mesa, Hora,
             Mesero, Cancelado, Valor, Salio, Mostrar,
             Motivo_Eliminacion, Quien_Elimino, tv_notified, updated_at)
        VALUES
            (:cid, :np, :fecha, '0', :mesa, :hora,
             :mesero, 1, :valor, :salio, 1,
             '', :quien, :tv_notified, NOW())
        ON DUPLICATE KEY UPDATE
            Quien_Elimino = VALUES(Quien_Elimino),
            tv_notified   = GREATEST(tv_notified, VALUES(tv_notified)),
            updated_at    = NOW()
    """), {
        "cid":         cid,
        "np":          on,
        "fecha":       fecha,
        "mesa":        str(order["Mesa"]),
        "hora":        str(order.get("Hora") or ""),
        "mesero":      int(order["Mesero"] or 0),
        "valor":       float(order.get("Valor") or 0),
        "salio":       int(order["Salio"] or 0),
        "quien":       quien,
        "tv_notified": tv_notified,
    })

    # ── Archivar ítems en historico_detalle_comanda_eliminadas ────────────────
    for it in all_items:
        await db.execute(text("""
            INSERT IGNORE INTO historico_detalle_comanda_eliminadas
                (company_id, Nro_pedido, Fecha, Nro_Factura,
                 Id_Plato, Item, Cantidad, Valor, Novedad, Cambios,
                 Hora_Plato, Mostrar, Salio, updated_at)
            VALUES
                (:cid, :np, :fecha, '0',
                 :dish_id, :item, :qty, :valor, :novedad, :cambios,
                 :hora_plato, :mostrar, :salio, NOW())
        """), {
            "cid":       cid,
            "np":        on,
            "fecha":     fecha,
            "dish_id":   int(it["Id_Plato"] or 0),
            "item":      int(it["Item"] or 0),
            "qty":       float(it["Cantidad"] or 0),
            "valor":     float(it["Valor"] or 0),
            "novedad":   str(it["Novedad"] or ""),
            "cambios":   str(it["Cambios"] or ""),
            "hora_plato": str(it["Hora_Plato"] or ""),
            "mostrar":   int(it["Mostrar"] or 0),
            "salio":     int(it["Salio"] or 0),
        })

    await db.commit()

    # ── Borrar de las 4 tablas temp (hard delete) ─────────────────────────────
    await db_temp.execute(text("""
        DELETE FROM temp_detalle_comanda_parcial
        WHERE Nro_pedido=:on AND Fecha=:date AND company_id=:cid
    """), {"on": on, "date": fecha, "cid": cid})

    await db_temp.execute(text("""
        DELETE FROM temp_plato_producto_parcial
        WHERE Nro_Pedido=:on AND company_id=:cid
    """), {"on": on, "cid": cid})

    await db_temp.execute(text("""
        DELETE FROM temp_novedades_plato_pedido
        WHERE Nro_Pedido=:on AND company_id=:cid
    """), {"on": on, "cid": cid})

    await db_temp.execute(text("""
        DELETE FROM temp_comanda
        WHERE Nro_Pedido=:on AND Fecha=:date AND company_id=:cid
    """), {"on": on, "date": fecha, "cid": cid})

    # ── Marcar mesa como cerrada en temp_mesa_abierta ─────────────────────────
    await db_temp.execute(text("""
        UPDATE temp_mesa_abierta
        SET Abierta=0, Abierta_Desde=NULL, updated_at=NOW()
        WHERE Id_Mesa=:tid AND company_id=:cid
    """), {"tid": data.table_id, "cid": cid})

    await db_temp.commit()
    return {"ok": True}


# ── 14b. DESPACHAR PEDIDO (marcar como entregado, sale de TV) ────────────────

class DespacharIn(BaseModel):
    order_number: str
    date: str


class ReenviarIn(BaseModel):
    order_number: str
    date: str


class ReimprimirIn(BaseModel):
    order_number: str
    date: str


@router.post("/orden/despachar")
async def despachar_orden(
    data: DespacharIn,
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
):
    cid = payload["company_id"]
    await db.execute(text("""
        INSERT INTO pos_kitchen_status (order_number, date, company_id, dispatched, resent_at)
        VALUES (:on, :date, :cid, 1, NULL)
        ON DUPLICATE KEY UPDATE dispatched = 1, resent_at = NULL
    """), {"on": data.order_number, "date": data.date, "cid": cid})
    await db.commit()
    return {"ok": True}


@router.post("/orden/reenviar")
async def reenviar_orden(
    data: ReenviarIn,
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
):
    cid = payload["company_id"]
    await db.execute(text("""
        INSERT INTO pos_kitchen_status (order_number, date, company_id, dispatched, resent_at)
        VALUES (:on, :date, :cid, 0, NOW())
        ON DUPLICATE KEY UPDATE dispatched = 0, resent_at = NOW()
    """), {"on": data.order_number, "date": data.date, "cid": cid})
    await db.commit()
    return {"ok": True}


@router.post("/orden/reimprimir")
async def reimprimir_orden(
    data: ReimprimirIn,
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    """Genera evento REIMPRESIÓN: pone el pedido al inicio de la cola de TV."""
    cid = payload["company_id"]
    today = _today()

    order = (await db_temp.execute(text("""
        SELECT Nro_Pedido, Fecha, Mesa, Mesero, Salio FROM temp_comanda
        WHERE Nro_Pedido=:on AND Fecha=:date AND company_id=:cid
          AND Nro_Factura='0' AND Cancelado=0
        LIMIT 1
    """), {"on": data.order_number, "date": data.date, "cid": cid})).mappings().first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if not int(order["Salio"] or 0):
        raise HTTPException(status_code=400, detail="El pedido aún no ha sido enviado a cocina")

    items_rows = (await db_temp.execute(text("""
        SELECT Id_Plato, Cantidad, Novedad, Hora AS hora_tomado
        FROM temp_detalle_comanda_parcial
        WHERE Nro_pedido=:on AND Fecha=:date AND Nro_Factura='0'
          AND company_id=:cid AND Mostrar=1 AND Salio=1
    """), {"on": data.order_number, "date": data.date, "cid": cid})).mappings().all()
    if not items_rows:
        raise HTTPException(status_code=400, detail="Sin ítems enviados para reimprimir")

    dish_ids_ev = list({int(r["Id_Plato"]) for r in items_rows})
    dish_names_ev: dict = {}
    if dish_ids_ev:
        id_list = ",".join(str(d) for d in dish_ids_ev)
        drows = (await db.execute(text(
            f"SELECT id, name FROM pos_dishes WHERE company_id=:cid AND id IN ({id_list})"
        ), {"cid": cid})).mappings().all()
        dish_names_ev = {int(r["id"]): r["name"] for r in drows}

    snapshot = json.dumps([{
        "dish_id":    int(r["Id_Plato"]),
        "dish_name":  dish_names_ev.get(int(r["Id_Plato"]), f"Plato {r['Id_Plato']}"),
        "quantity":   float(r["Cantidad"] or 0),
        "notes":      str(r["Novedad"] or ""),
        "hora_tomado": str(r["hora_tomado"] or ""),
        "assembly":   [],
        "changes":    None,
    } for r in items_rows], ensure_ascii=False)

    await db.execute(text("""
        INSERT INTO pos_kitchen_events
            (company_id, event_type, order_number, table_name, waiter_id,
             items_snapshot, event_date, created_at)
        VALUES (:cid, 'reimpresion', :on, :mesa, :wid, :snap, :edate, NOW())
    """), {
        "cid":   cid,
        "on":    data.order_number,
        "mesa":  str(order["Mesa"]),
        "wid":   int(order["Mesero"] or 0),
        "snap":  snapshot,
        "edate": today,
    })
    await db.commit()
    return {"ok": True, "items": len(items_rows)}


# ── 14c. PEDIDOS EN TV (dashboard admin) ──────────────────────────────────────

@router.get("/cocina-pedidos")
async def get_cocina_pedidos(
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    """Lista órdenes actualmente visibles en la pantalla de cocina TV."""
    cid = payload["company_id"]
    today = _today()

    # Pedidos activos — solo los visibles en TV (mismos criterios que _build_cards)
    order_rows = (await db_temp.execute(text("""
        SELECT Nro_Pedido, Fecha, Mesa, Valor, Hora, Mesero
        FROM temp_comanda
        WHERE company_id=:cid AND Nro_Factura='0' AND Cancelado=0
          AND (Movil = 0 OR Salio = 1)
        ORDER BY Hora ASC
    """), {"cid": cid})).mappings().all()

    if not order_rows:
        return []

    order_numbers = [r["Nro_Pedido"] for r in order_rows]
    on_quoted = ",".join(f"'{o}'" for o in order_numbers)

    # Excluir pedidos ya facturados en pos_invoice_details (misma red de seguridad que TV)
    inv_rows = (await db.execute(text(
        f"SELECT DISTINCT order_number FROM pos_invoice_details "
        f"WHERE company_id=:cid AND order_number IN ({on_quoted})"
    ), {"cid": cid})).mappings().all()
    invoiced_set = {r["order_number"] for r in inv_rows}

    # Pedidos ya despachados desde easyposweb
    ks_rows = (await db.execute(text(
        f"SELECT order_number FROM pos_kitchen_status "
        f"WHERE company_id=:cid AND date=:today AND dispatched=1 "
        f"AND order_number IN ({on_quoted})"
    ), {"cid": cid, "today": today})).mappings().all()
    dispatched_set = {r["order_number"] for r in ks_rows}

    # Ítems enviados (Hora_Plato establecida) por pedido desde datatemppos
    detail_rows = (await db_temp.execute(text(
        f"SELECT Nro_pedido, Id_Plato, COUNT(*) AS cnt "
        f"FROM temp_detalle_comanda_parcial "
        f"WHERE company_id=:cid AND Nro_Factura='0' AND Mostrar=1 "
        f"AND Hora_Plato IS NOT NULL AND Hora_Plato NOT IN ('', '0') "
        f"AND Nro_pedido IN ({on_quoted}) "
        f"GROUP BY Nro_pedido, Id_Plato"
    ), {"cid": cid})).mappings().all()

    sent_count: dict = {}
    dish_ids_sent: set = set()
    for r in detail_rows:
        on = r["Nro_pedido"]
        sent_count[on] = sent_count.get(on, 0) + int(r["cnt"])
        dish_ids_sent.add(int(r["Id_Plato"]))

    # Nombres de platos desde easyposweb
    dish_names: dict = {}
    if dish_ids_sent:
        id_list = ",".join(str(d) for d in dish_ids_sent)
        drows = (await db.execute(text(
            f"SELECT id, name FROM pos_dishes WHERE company_id=:cid AND id IN ({id_list})"
        ), {"cid": cid})).mappings().all()
        dish_names = {int(r["id"]): r["name"] for r in drows}

    # Preview de platos enviados por pedido
    preview_per_order: dict = {}
    for r in detail_rows:
        on = r["Nro_pedido"]
        dn = dish_names.get(int(r["Id_Plato"]), "")
        if dn:
            preview_per_order.setdefault(on, []).append(dn)

    # Nombres de meseros desde easyposweb
    waiter_ids = {int(r["Mesero"]) for r in order_rows if r["Mesero"]}
    waiter_names: dict = {}
    if waiter_ids:
        id_list = ",".join(str(w) for w in waiter_ids)
        wrows = (await db.execute(text(
            f"SELECT id, name FROM pos_waiters WHERE company_id=:cid AND id IN ({id_list})"
        ), {"cid": cid})).mappings().all()
        waiter_names = {int(r["id"]): r["name"] for r in wrows}

    result = []
    for r in order_rows:
        on = r["Nro_Pedido"]
        if on in dispatched_set:
            continue
        if on in invoiced_set:
            continue
        if sent_count.get(on, 0) == 0:
            continue
        waiter_id = int(r["Mesero"] or 0)
        result.append({
            "order_number":  on,
            "date":          str(r["Fecha"]),
            "table_name":    r["Mesa"],
            "waiter_name":   waiter_names.get(waiter_id),
            "order_time":    str(r["Hora"] or "")[:5],
            "amount":        float(r["Valor"] or 0),
            "item_count":    sent_count.get(on, 0),
            "items_preview": ", ".join(preview_per_order.get(on, [])[:5]),
        })

    return result


# ── 14. COCINA TV ─────────────────────────────────────────────────────────────

@router.get("/cocina/tv-config")
async def get_tv_config(
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
):
    """Retorna (y genera si no existe) el token TV de la empresa."""
    cid = payload["company_id"]
    row = (await db.execute(text(
        "SELECT kitchen_tv_token FROM companies WHERE id_company = :cid"
    ), {"cid": cid})).mappings().first()
    token = row["kitchen_tv_token"] if row else None
    if not token:
        token = secrets.token_hex(32)
        await db.execute(text(
            "UPDATE companies SET kitchen_tv_token = :tok WHERE id_company = :cid"
        ), {"tok": token, "cid": cid})
        await db.commit()
    return {"token": token}


@router.post("/cocina/tv-token/regenerar")
async def regenerar_tv_token(
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
):
    """Genera un nuevo token TV, invalidando el anterior."""
    cid = payload["company_id"]
    token = secrets.token_hex(32)
    await db.execute(text(
        "UPDATE companies SET kitchen_tv_token = :tok WHERE id_company = :cid"
    ), {"tok": token, "cid": cid})
    await db.commit()
    return {"token": token}


@router.get("/cocina")
async def get_cocina(
    token: str = Query(..., description="Token TV de la empresa (opaco, sin exponer company_id)"),
    db: AsyncSession = Depends(get_db),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    # 1. Resolver token → company_id desde easyposweb
    company_row = (await db.execute(text(
        "SELECT id_company FROM companies WHERE kitchen_tv_token = :tok LIMIT 1"
    ), {"tok": token})).mappings().first()
    if not company_row:
        raise HTTPException(status_code=403, detail="Token de cocina inválido")
    cid = int(company_row["id_company"])
    today = _today()

    # 2. Impresoras activas
    all_printers = (await db.execute(text(
        "SELECT id, name FROM pos_printers WHERE company_id=:cid AND is_active=1 ORDER BY id"
    ), {"cid": cid})).mappings().all()
    printer_map: dict = {
        int(p["id"]): {"printer_id": int(p["id"]), "printer_name": p["name"]}
        for p in all_printers
    }
    if not printer_map:
        return []

    # 3. Pedidos activos + ítems (solo enviados: Hora_Plato establecida; web: tc.Salio=1)
    order_rows = (await db_temp.execute(text("""
        SELECT tc.Nro_Pedido, tc.Mesa, tc.Hora, tc.Mesero, tc.Movil,
               tdc.Id_Plato, tdc.Item, tdc.Cantidad,
               tdc.Novedad, tdc.Cambios, tdc.Hora_Plato,
               tdc.Hora AS Hora_Tomado, tdc.Producto_Personalizado
        FROM temp_comanda tc
        JOIN temp_detalle_comanda_parcial tdc
             ON tdc.Nro_pedido  = tc.Nro_Pedido
            AND tdc.Fecha       = tc.Fecha
            AND tdc.Nro_Factura = '0'
            AND tdc.company_id  = :cid
            AND tdc.Mostrar     = 1
            AND tdc.Hora_Plato IS NOT NULL
            AND tdc.Hora_Plato NOT IN ('', '0')
        WHERE tc.company_id  = :cid
          AND tc.Nro_Factura = '0'
          AND tc.Cancelado   = 0
          AND (tc.Movil = 0 OR tc.Salio = 1)
        ORDER BY tc.Hora ASC, tdc.Hora_Plato ASC, tdc.Item ASC
    """), {"cid": cid})).mappings().all()

    # 4. Colectar IDs para lookups
    dish_ids      = list({int(r["Id_Plato"]) for r in order_rows})
    order_numbers = list({r["Nro_Pedido"] for r in order_rows})
    waiter_ids    = list({int(r["Mesero"]) for r in order_rows if r["Mesero"]})

    # 5. Info de platos
    dish_info: dict = {}
    if dish_ids:
        id_list = ",".join(str(d) for d in dish_ids)
        drows = (await db.execute(text(
            f"SELECT id, name, preparation_time FROM pos_dishes "
            f"WHERE company_id=:cid AND id IN ({id_list})"
        ), {"cid": cid})).mappings().all()
        dish_info = {int(r["id"]): {"name": r["name"], "no_print": bool(r["preparation_time"])} for r in drows}

    # 6. Impresoras por plato
    printer_for_dish: dict = {}
    if dish_ids:
        id_list = ",".join(str(d) for d in dish_ids)
        prows = (await db.execute(text(
            f"SELECT ip.item_id, ip.printer_id FROM pos_item_printers ip "
            f"JOIN pos_printers p ON p.id=ip.printer_id AND p.company_id=:cid AND p.is_active=1 "
            f"WHERE ip.company_id=:cid AND ip.item_id IN ({id_list})"
        ), {"cid": cid})).mappings().all()
        for pr in prows:
            printer_for_dish.setdefault(int(pr["item_id"]), []).append(int(pr["printer_id"]))

    # 7. Nombres de meseros
    waiter_names: dict = {}
    if waiter_ids:
        wrows = (await db.execute(text(
            f"SELECT id, name FROM pos_waiters WHERE company_id=:cid "
            f"AND id IN ({','.join(str(w) for w in waiter_ids)})"
        ), {"cid": cid})).mappings().all()
        waiter_names = {int(r["id"]): r["name"] for r in wrows}

    # 8. Pedidos despachados
    dispatched_set: set = set()
    if order_numbers:
        on_quoted = ",".join(f"'{o}'" for o in order_numbers)
        ksrows = (await db.execute(text(
            f"SELECT order_number FROM pos_kitchen_status "
            f"WHERE company_id=:cid AND date=:today AND dispatched=1 "
            f"AND order_number IN ({on_quoted})"
        ), {"cid": cid, "today": today})).mappings().all()
        dispatched_set = {r["order_number"] for r in ksrows}

    # Limpiar datatemppos: borrar pedidos despachados para que no persistan en TV
    if dispatched_set:
        for _on in list(dispatched_set):
            await db_temp.execute(text(
                "DELETE FROM temp_detalle_comanda_parcial WHERE Nro_pedido=:on AND company_id=:cid"
            ), {"on": _on, "cid": cid})
            await db_temp.execute(text(
                "DELETE FROM temp_comanda WHERE Nro_Pedido=:on AND company_id=:cid"
            ), {"on": _on, "cid": cid})
        await db_temp.commit()

    # 9. daily_seq por hora de apertura
    order_first_hora: dict = {}
    for r in order_rows:
        on = r["Nro_Pedido"]
        if on not in order_first_hora:
            order_first_hora[on] = str(r["Hora"] or "")
    daily_seq_map = {on: i + 1 for i, on in enumerate(sorted(order_first_hora, key=order_first_hora.get))}

    # 10. Agrupar ítems por (order_number, Hora_Plato) → lotes/batches
    batch_items: dict = {}  # (on, hp) → [item_data]
    batch_meta: dict  = {}  # (on, hp) → {mesa, order_hora, mesero, printers}

    for row in order_rows:
        on  = row["Nro_Pedido"]
        did = int(row["Id_Plato"])

        if dish_info.get(did, {}).get("no_print"):
            continue
        if on in dispatched_set:
            continue
        printers_for_dish = printer_for_dish.get(did, [])
        if not printers_for_dish:
            continue

        # Movil=0 (VB6): agrupa por minuto (HH:MM) para que ítems del mismo
        # "envío a cocina" queden en un batch, pero envíos posteriores generen
        # un batch nuevo → etiqueta PEDIDO AGREGADO correcta.
        movil  = int(row["Movil"] or 0)
        hp_raw = str(row["Hora_Plato"] or "")
        hp     = hp_raw if movil == 1 else hp_raw[:5]   # "HH:MM" para VB6
        key    = (on, hp)

        if key not in batch_meta:
            wid = int(row["Mesero"] or 0)
            batch_meta[key] = {
                "order_number": on,
                "hora_plato":   hp,
                "mesa":         str(row["Mesa"] or ""),
                "order_hora":   str(row["Hora"] or ""),
                "waiter_id":    wid,
                "waiter_name":  waiter_names.get(wid),
                "printers":     set(),
                "max_hp":       str(row["Hora_Plato"] or ""),
            }
        else:
            # Actualizar max_hp para usar el timestamp más reciente como referencia de tiempo
            cur_hp = str(row["Hora_Plato"] or "")
            if cur_hp > batch_meta[key]["max_hp"]:
                batch_meta[key]["max_hp"] = cur_hp
        batch_meta[key]["printers"].update(printers_for_dish)

        assembly = []
        if row["Producto_Personalizado"]:
            try:
                assembly = json.loads(row["Producto_Personalizado"]).get("assembly", [])
            except Exception:
                pass

        batch_items.setdefault(key, []).append({
            "dish_id":     did,
            "item":        int(row["Item"]),
            "dish_name":   dish_info.get(did, {}).get("name", f"Plato {did}"),
            "quantity":    float(row["Cantidad"] or 0),
            "notes":       row["Novedad"],
            "changes":     row["Cambios"],
            "assembly":    assembly,
            "hora_tomado": str(row["Hora_Tomado"] or ""),
        })

    # 11. Mínimo Hora_Plato por (impresora, pedido) — NUEVO solo cuando ESA impresora
    #     ve por primera vez ese pedido; AGREGADO si ya tenía ítems anteriores.
    #     Se usa _hp_sort_key para comparación numérica correcta (evita "7:10:" > "12:07").
    min_sk_per_printer_order: dict = {}  # (pid, on) → (sort_key, hp_string)
    for (on, hp), meta in batch_meta.items():
        sk = _hp_sort_key(hp)
        for item_data in batch_items.get((on, hp), []):
            for pid in printer_for_dish.get(item_data["dish_id"], []):
                if pid in meta["printers"]:
                    pkey = (pid, on)
                    if pkey not in min_sk_per_printer_order or sk < min_sk_per_printer_order[pkey][0]:
                        min_sk_per_printer_order[pkey] = (sk, hp)

    # 12. Construir tarjetas de órdenes vivas — cada impresora ve solo SUS ítems
    all_cards: list = []  # [{printer_id, card}]
    for key, meta in batch_meta.items():
        on, hp = key
        display_hp = meta.get("max_hp") or hp

        # Agrupar ítems del batch por impresora
        items_by_printer: dict = {}
        for item_data in batch_items.get(key, []):
            for pid in printer_for_dish.get(item_data["dish_id"], []):
                if pid in meta["printers"]:
                    items_by_printer.setdefault(pid, []).append(item_data)

        for pid in meta["printers"]:
            if pid not in printer_map:
                continue
            pid_items = items_by_printer.get(pid, [])
            if not pid_items:
                continue

            # event_type basado en el mínimo POR ESTA IMPRESORA para este pedido
            pkey = (pid, on)
            min_entry = min_sk_per_printer_order.get(pkey)
            event_type = "nuevo" if (min_entry is None or hp == min_entry[1]) else "agregado"

            # Agrupar ítems idénticos (mismo plato + misma novedad + mismos cambios)
            grouped: dict = {}
            for it in pid_items:
                gkey = (it["dish_id"], (it.get("notes") or "").strip(), (it.get("changes") or "").strip())
                if gkey in grouped:
                    grouped[gkey]["quantity"] += it["quantity"]
                else:
                    grouped[gkey] = dict(it)
            pid_items = list(grouped.values())

            card = {
                "order_number":     on,
                "event_type":       event_type,
                "daily_seq":        daily_seq_map.get(on, 0),
                "table_name":       meta["mesa"],
                "order_hora":       meta["order_hora"],
                "waiter_name":      meta["waiter_name"],
                "latest_dish_time": display_hp,
                "bill_requested":   False,
                "items":            pid_items,
            }
            all_cards.append({"printer_id": pid, "card": card})

    # 13. Eventos efímeros del día (CANCELADO + REIMPRESION) desde easyposweb
    # CANCELADO expira a los 2 min — se oculta solo en el siguiente ciclo de polling
    event_rows = (await db.execute(text("""
        SELECT id, event_type, order_number, table_name, waiter_id,
               items_snapshot, created_at
        FROM pos_kitchen_events
        WHERE company_id=:cid AND event_date=:today
          AND NOT (event_type = 'cancelado' AND created_at < NOW() - INTERVAL 2 MINUTE)
        ORDER BY created_at ASC
    """), {"cid": cid, "today": today})).mappings().all()

    if event_rows:
        # Lookup impresoras para los platos del snapshot (puede no estar en printer_for_dish)
        ev_dish_ids: set = set()
        for ev in event_rows:
            if ev["items_snapshot"]:
                try:
                    for it in json.loads(ev["items_snapshot"]):
                        if "dish_id" in it:
                            ev_dish_ids.add(int(it["dish_id"]))
                except Exception:
                    pass
        missing_ids = ev_dish_ids - set(printer_for_dish.keys())
        if missing_ids:
            id_list2 = ",".join(str(d) for d in missing_ids)
            prows2 = (await db.execute(text(
                f"SELECT ip.item_id, ip.printer_id FROM pos_item_printers ip "
                f"JOIN pos_printers p ON p.id=ip.printer_id AND p.company_id=:cid AND p.is_active=1 "
                f"WHERE ip.company_id=:cid AND ip.item_id IN ({id_list2})"
            ), {"cid": cid})).mappings().all()
            for pr in prows2:
                printer_for_dish.setdefault(int(pr["item_id"]), []).append(int(pr["printer_id"]))

        # Lookup meseros de eventos no cargados aún
        ev_waiter_ids = {int(r["waiter_id"]) for r in event_rows if r["waiter_id"]} - set(waiter_names.keys())
        if ev_waiter_ids:
            wrows2 = (await db.execute(text(
                f"SELECT id, name FROM pos_waiters WHERE company_id=:cid "
                f"AND id IN ({','.join(str(w) for w in ev_waiter_ids)})"
            ), {"cid": cid})).mappings().all()
            for wr in wrows2:
                waiter_names[int(wr["id"])] = wr["name"]

        for ev in event_rows:
            items_snap = []
            if ev["items_snapshot"]:
                try:
                    items_snap = json.loads(ev["items_snapshot"])
                    for it in items_snap:
                        it.setdefault("assembly", [])
                        it.setdefault("changes", None)
                        it.setdefault("hora_tomado", "")
                        it.setdefault("item", 0)
                except Exception:
                    pass

            # Calcular impresoras desde los dish_ids del snapshot
            ev_printers: set = set()
            for it in items_snap:
                did = int(it.get("dish_id", 0))
                ev_printers.update(printer_for_dish.get(did, []))
            if not ev_printers:
                ev_printers = set(printer_map.keys())  # fallback: todas

            wid = int(ev["waiter_id"] or 0)
            card = {
                "order_number":     str(ev["order_number"]),
                "event_type":       ev["event_type"],
                "event_id":         int(ev["id"]),
                "daily_seq":        daily_seq_map.get(str(ev["order_number"])),
                "table_name":       str(ev["table_name"] or ""),
                "order_hora":       "",
                "waiter_name":      waiter_names.get(wid),
                "latest_dish_time": str(ev["created_at"]),
                "bill_requested":   False,
                "items":            items_snap,
            }
            for pid in ev_printers:
                if pid in printer_map:
                    all_cards.append({"printer_id": pid, "card": card})

    # 14. Ensamblar resultado por impresora (sort DESC por latest_dish_time → más nuevo arriba)
    result = []
    for pid in sorted(printer_map.keys()):
        pdata = printer_map[pid]
        cards = sorted(
            [c["card"] for c in all_cards if c["printer_id"] == pid],
            key=lambda x: _hp_sort_key(x["latest_dish_time"]),
            reverse=True,
        )
        result.append({
            "printer_id":   pdata["printer_id"],
            "printer_name": pdata["printer_name"],
            "orders":       cards,
        })

    return result


# ── Helper ────────────────────────────────────────────────────────────────────

def _hp_sort_key(t: str) -> int:
    """
    Convierte Hora_Plato (locale colombiana) o datetime ISO a segundos-desde-medianoche.
    Necesario porque "7:10:23 a. m." > "12:07:43 p. m." como string, rompiendo el orden.
    """
    if not t:
        return 0
    t = t.strip()
    # ISO datetime "2026-06-06 12:08:40" — extraer solo la parte hora
    if re.match(r'\d{4}-\d{2}-\d{2}', t):
        m = re.search(r'(\d{1,2}):(\d{2}):(\d{2})', t)
        if m:
            return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
        return 0
    # Locale colombiana "7:10:23 a. m." / "12:07:43 p. m."
    m = re.match(r'(\d{1,2}):(\d{2}):(\d{2})\s+(a|p)', t, re.IGNORECASE)
    if m:
        h, mn, s = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if m.group(4).lower() == 'p' and h != 12:
            h += 12
        elif m.group(4).lower() == 'a' and h == 12:
            h = 0
        return h * 3600 + mn * 60 + s
    # Truncado "7:10:" o "12:07"
    m = re.match(r'(\d{1,2}):(\d{2})', t)
    if m:
        return int(m.group(1)) * 3600 + int(m.group(2)) * 60
    return 0


async def _recalc_total(db_temp: AsyncSession, order_number: str, date: str, cid: int) -> None:
    """Recalcula el total de un pedido en temp_comanda desde sus ítems en datatemppos."""
    await db_temp.execute(text("""
        UPDATE temp_comanda tc
        SET tc.Valor = (
            SELECT COALESCE(SUM(tdc.Valor), 0)
            FROM temp_detalle_comanda_parcial tdc
            WHERE tdc.Nro_pedido  = tc.Nro_Pedido
              AND tdc.Fecha       = tc.Fecha
              AND tdc.Nro_Factura = '0'
              AND tdc.company_id  = tc.company_id
              AND tdc.Mostrar     = 1
        )
        WHERE tc.Nro_Pedido   = :on
          AND tc.Fecha        = :date
          AND tc.company_id   = :cid
    """), {"on": order_number, "date": date, "cid": cid})


# ═══════════════════════════════════════════════════════════════
# GET — Trazabilidad de pedidos eliminados
# ═══════════════════════════════════════════════════════════════

@router.get("/historico-eliminadas")
async def get_historico_eliminadas(
    fecha_desde:   Optional[str] = Query(None),
    fecha_hasta:   Optional[str] = Query(None),
    mesa:          Optional[str] = Query(None),
    quien_elimino: Optional[str] = Query(None),
    auth: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
):
    cid = int(auth["company_id"])
    today = _today()
    since = fecha_desde or today
    until = fecha_hasta or today

    # Headers
    sql_params: dict = {"cid": cid, "since": since, "until": until}
    sql_where = "WHERE h.company_id = :cid AND h.Fecha BETWEEN :since AND :until"
    if mesa:
        sql_where += " AND h.Mesa LIKE :mesa"
        sql_params["mesa"] = f"%{mesa}%"
    if quien_elimino:
        sql_where += " AND h.Quien_Elimino LIKE :quien"
        sql_params["quien"] = f"%{quien_elimino}%"

    orders_rows = (await db.execute(text(f"""
        SELECT h.id, h.Nro_Pedido, h.Fecha, h.Nro_Factura,
               h.Mesa, h.Hora, h.Mesero, h.Valor,
               h.Novedad, h.Quien_Elimino, h.Motivo_Eliminacion,
               h.created_at,
               COUNT(d.id) AS total_items,
               COALESCE(SUM(d.Cantidad), 0) AS total_qty
        FROM historico_comandas_eliminadas h
        LEFT JOIN historico_detalle_comanda_eliminadas d
               ON d.company_id = h.company_id
              AND d.Nro_Pedido = h.Nro_Pedido
              AND d.Fecha      = h.Fecha
        {sql_where}
        GROUP BY h.id
        ORDER BY h.Fecha DESC, h.Hora DESC
        LIMIT 500
    """), sql_params)).mappings().all()

    orders = []
    for row in orders_rows:
        # Fetch items for this order
        items_rows = (await db.execute(text("""
            SELECT Id_Plato, Item, Cantidad, Valor, Novedad, Cambios,
                   Cortesia, Hora_Plato, Producto_Personalizado
            FROM historico_detalle_comanda_eliminadas
            WHERE company_id = :cid AND Nro_Pedido = :np AND Fecha = :fecha
            ORDER BY Item ASC
        """), {"cid": cid, "np": row["Nro_Pedido"], "fecha": str(row["Fecha"])})).mappings().all()

        orders.append({
            "id":                 row["id"],
            "order_number":       row["Nro_Pedido"],
            "date":               str(row["Fecha"]),
            "invoice_number":     row["Nro_Factura"],
            "table_name":         row["Mesa"],
            "time":               str(row["Hora"] or ""),
            "waiter_id":          row["Mesero"],
            "amount":             float(row["Valor"] or 0),
            "notes":              row["Novedad"],
            "quien_elimino":      row["Quien_Elimino"],
            "motivo_eliminacion": row["Motivo_Eliminacion"],
            "created_at":         str(row["created_at"] or ""),
            "total_items":        int(row["total_items"] or 0),
            "items": [
                {
                    "dish_id":       it["Id_Plato"],
                    "item":          it["Item"],
                    "quantity":      float(it["Cantidad"] or 0),
                    "amount":        float(it["Valor"] or 0),
                    "notes":         it["Novedad"],
                    "changes":       it["Cambios"],
                    "complimentary": it["Cortesia"],
                    "dish_time":     str(it["Hora_Plato"] or ""),
                    "custom_product": it["Producto_Personalizado"],
                }
                for it in items_rows
            ],
        })

    return {"total": len(orders), "orders": orders}


# ── MENÚ DIARIO — GESTIÓN ADMIN ──────────────────────────────────────────────

class GuardarMenuDiarioIn(BaseModel):
    date: str
    selected_ids: List[int]


@router.get("/menu-diario-admin")
async def get_menu_diario_admin(
    date: Optional[str] = Query(None),
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
):
    """
    Devuelve todos los insumos de menú agrupados por categoría.
    Marca is_selected según pos_daily_menu para la fecha dada.
    No hace auto-init: la fuente de verdad son supply_items.
    """
    cid = payload["company_id"]
    target_date = date or _today()

    items_rows = (await db.execute(text("""
        SELECT si.id_item, si.description AS item_name,
               si.Agrupar AS group_id,
               pc.name    AS group_name
        FROM supply_items si
        INNER JOIN pos_product_categories pc
               ON si.Agrupar = pc.id AND pc.company_id = :cid
        WHERE si.company_id = :cid
          AND si.is_active   = 1
          AND pc.percentage  = 1
          AND si.control_stock = 1
        ORDER BY pc.name, si.description
    """), {"cid": cid})).mappings().all()

    if not items_rows:
        return {"date": target_date, "categories": []}

    # IDs guardados para hoy (solo los que el admin seleccionó)
    saved_rows = (await db.execute(text("""
        SELECT item_id FROM pos_daily_menu
        WHERE company_id = :cid AND date = :d
    """), {"cid": cid, "d": target_date})).mappings().all()
    selected_ids = {int(r["item_id"]) for r in saved_rows}

    categories: dict = {}
    for row in items_rows:
        gid = int(row["group_id"])
        if gid not in categories:
            categories[gid] = {
                "group_id":   gid,
                "group_name": row["group_name"] or f"Categoría {gid}",
                "items":      [],
            }
        categories[gid]["items"].append({
            "item_id":     int(row["id_item"]),
            "item_name":   row["item_name"] or f"Ítem {row['id_item']}",
            "is_selected": int(row["id_item"]) in selected_ids,
        })

    return {"date": target_date, "categories": list(categories.values())}


@router.post("/menu-diario-admin/guardar")
async def guardar_menu_diario(
    data: GuardarMenuDiarioIn,
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
):
    """
    Guarda el menú del día con lógica DELETE+INSERT (pizarra limpia):
    1. Borra todos los registros de esa fecha.
    2. Re-inserta solo los seleccionados tomando datos de supply_items.
    Esto evita el bug donde ítems previamente no seleccionados no pueden
    re-seleccionarse porque ya no existen en la tabla.
    """
    cid = payload["company_id"]
    d   = data.date

    # Pizarra limpia para esta fecha
    await db.execute(text("""
        DELETE FROM pos_daily_menu WHERE company_id = :cid AND date = :d
    """), {"cid": cid, "d": d})

    if data.selected_ids:
        placeholders = ", ".join([f":id{i}" for i in range(len(data.selected_ids))])
        params: dict = {"cid": cid, "d": d}
        for i, sid in enumerate(data.selected_ids):
            params[f"id{i}"] = sid

        # Re-insertar seleccionados con datos frescos de supply_items
        await db.execute(text(f"""
            INSERT INTO pos_daily_menu
                (company_id, menu_id, item_id, date, category, description, group_by, selected, synced, updated_at)
            SELECT si.company_id, si.Agrupar, si.id_item, :d,
                   pc.name, si.description, si.Agrupar, 1, 0, NOW()
            FROM supply_items si
            INNER JOIN pos_product_categories pc
                   ON si.Agrupar = pc.id AND pc.company_id = :cid
            WHERE si.company_id = :cid AND si.id_item IN ({placeholders})
            ON DUPLICATE KEY UPDATE date = :d, selected = 1, updated_at = NOW()
        """), params)

    await db.commit()
    return {"ok": True, "date": d, "selected_count": len(data.selected_ids)}
