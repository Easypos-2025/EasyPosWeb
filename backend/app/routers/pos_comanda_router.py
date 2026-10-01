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
from app.services import comanda_armado as armado_svc
from app.auth import tenant
from app.services import clientes as clientes_svc
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
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Acepta tokens de mesero Y tokens de usuario regular (admin desde dashboard).
    La empresa se resuelve con la regla central (app.auth.tenant): X-Company-Id solo
    se acepta si el usuario tiene acceso a esa empresa."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    payload = dict(payload)

    if payload.get("type") == "waiter" or (payload.get("company_id") and not payload.get("user_id")):
        # Mesero: la empresa es la de su token firmado; no puede pedir otra
        own = int(payload.get("company_id") or 0)
        if not own:
            raise HTTPException(status_code=400, detail="company_id requerido")
        payload["company_id"] = tenant.check_company(own, frozenset({own}), x_company_id)
    else:
        # Usuario del sistema: sesión activa + empresa permitida (propia, mismo NIT si es ADMIN, todas si SYSADMIN)
        user = await tenant.user_from_token(db, token)
        payload["company_id"] = await tenant.resolve_company(db, user, x_company_id)

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
    customer_id: Optional[int] = None  # clientes.id_cliente; por defecto 1 = Consumidor Final


class CambiarClienteIn(BaseModel):
    order_number: str
    customer_id: int


class ClienteRapidoIn(BaseModel):
    nombres: str
    cedula: Optional[str] = None
    telefono: Optional[str] = None
    direccion: Optional[str] = None
    mail: Optional[str] = None


class AssemblySelection(BaseModel):
    # Solo se usan category_code + item_id: nombre, cantidad y valor adicional los
    # toma el servidor de la configuración del plato (nunca del navegador).
    category_code: int
    item_id: int
    item_name: Optional[str] = None
    discount_qty: Optional[float] = 1.0


class AgregarItemIn(BaseModel):
    order_number: str
    date: str
    table_id: int
    dish_id: int
    quantity: float = 1
    amount: Optional[int] = 0          # IGNORADO: el precio lo calcula el servidor
    notes: Optional[str] = None
    changes: Optional[str] = None
    assembly_selections: Optional[List[AssemblySelection]] = []
    customer_id: Optional[int] = 0
    custom_description: Optional[str] = None   # platos.Pedir_Descripcion_Producto (IMEI, detalle de trabajo...)
    variant_id: Optional[int] = None           # tamaño (Personal / Dúo / Familiar…) si el plato tiene variantes


class ActualizarItemIn(BaseModel):
    order_number: str
    date: str
    dish_id: int
    item: int
    quantity: Optional[float] = None
    notes: Optional[str] = None
    changes: Optional[str] = None


class AplicarDescuentoItemIn(BaseModel):
    order_number: str
    dish_id: int
    item: int
    id_tipificacion: int  # 0 = "QUITAR DESCUENTO" (restaura el valor original)
    observacion: Optional[str] = None
    monto_pesos: Optional[int] = None  # requerido cuando la tipificación es "Descuento en Pesos" (% = 0, id != 0)


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
        "WHERE company_id=:cid AND status=1 AND plan_blocked=0 AND employee_type=2 ORDER BY name"
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

    # Auto-cancelar pedidos sin ítems (web y escritorio) que nadie tiene abiertos
    await db_temp.execute(text("""
        UPDATE temp_comanda tc
        SET tc.Cancelado = 1
        WHERE tc.company_id = :cid
          AND tc.Nro_Factura = '0'
          AND tc.Cancelado = 0
          -- No tocar pedidos que se están montando: la mesa está abierta en un dispositivo
          -- (temp_mesa_abierta.Abierta = 1). Gracia de 2 min para la apertura.
          AND COALESCE(tc.updated_at, '2000-01-01') < NOW() - INTERVAL 2 MINUTE
          AND NOT EXISTS (
              SELECT 1 FROM temp_mesa_abierta tma
              WHERE tma.company_id = tc.company_id
                AND TRIM(tma.Mesa) = TRIM(tc.Mesa)
                AND tma.Abierta = 1
          )
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
          AND (tma.editing_token IS NULL OR tma.editing_token = '')
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

    # Mesas abiertas en un dispositivo (Abierta = 1): bloqueadas para cualquier otro
    lock_rows = (await db_temp.execute(text("""
        SELECT Id_Mesa, editing_waiter_name, editing_token, Abierta_Desde
        FROM temp_mesa_abierta
        WHERE company_id=:cid AND Abierta = 1
    """), {"cid": cid})).mappings().all()
    locks: dict = {int(r["Id_Mesa"]): {"name": _quien(r), "token": r["editing_token"]} for r in lock_rows}

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
        order_info = order_by_mesa.get(str(r["name"]).strip())
        status = "occupied" if (tid in open_set or order_info is not None) else "free"

        lk = locks.get(tid)
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
            "editing_by":   lk["name"] if lk else None,
        })

    return sorted(zones.values(), key=lambda z: z["order_index"])


# ── 3. ABRIR MESA ─────────────────────────────────────────────────────────────

@router.post("/mesa/abrir")
async def abrir_mesa(
    data: AbrirMesaIn,
    payload: dict = Depends(_auth_comanda),
    x_edit_token: Optional[str] = Header(None),
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
    await _exigir_mesa(db_temp, cid, x_edit_token, table_id=data.table_id)

    # Verificar también en temp_comanda (sin filtro de fecha: órdenes que cruzan medianoche)
    existing = (await db_temp.execute(text("""
        SELECT Nro_Pedido FROM temp_comanda
        WHERE Mesa=:mesa AND company_id=:cid
          AND Nro_Factura='0' AND Cancelado=0
        ORDER BY Fecha DESC
        LIMIT 1
    """), {"mesa": mesa["name"], "cid": cid})).mappings().first()

    if existing:
        # Devuelve el número de pedido existente para redirigir al mesero
        order_num = existing["Nro_Pedido"] if existing else None
        return {"order_number": order_num, "date": today, "already_open": True}

    order_number = _order_number(cid, data.table_id)

    # Cliente del pedido: por defecto 1 = Consumidor Final; si viene otro, debe ser de la empresa
    customer = await clientes_svc.get_cliente(db, cid, data.customer_id or clientes_svc.CONSUMIDOR_FINAL_ID)
    await db.commit()   # por si se creó el Consumidor Final

    # Insertar en temp_comanda (Movil=1 = origen web)
    await db_temp.execute(text("""
        INSERT INTO temp_comanda
            (company_id, Nro_Pedido, Fecha, Nro_Factura, Mesa, Hora,
             Mesero, Cancelado, Valor, Nro_Comenzales, Domicilio, Id_Cliente, Movil, updated_at)
        VALUES
            (:cid, :on, :date, '0', :mesa, :hora,
             :wid, 0, 0, :guests, 0, :cli, 1, NOW())
    """), {
        "cid":    cid,
        "on":     order_number,
        "date":   today,
        "mesa":   mesa["name"],
        "hora":   _time_str(),
        "wid":    waiter_id,
        "guests": data.guests_count,
        "cli":    customer["id_cliente"],
    })

    # temp_mesa_abierta la marca quien ENTRA a la mesa (bloqueo por dispositivo)
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
            SELECT Nro_Pedido, Fecha, Valor, Hora, Nro_Comenzales, Mesero, Novedad, Mesa, Id_Cliente
            FROM temp_comanda
            WHERE Nro_Pedido=:on AND company_id=:cid
              AND Nro_Factura='0' AND Cancelado=0
            LIMIT 1
        """), {"on": order_number, "cid": cid})).mappings().first()
    else:
        # Sin filtro de fecha: un pedido puede cruzar medianoche y seguir activo
        order = (await db_temp.execute(text("""
            SELECT Nro_Pedido, Fecha, Valor, Hora, Nro_Comenzales, Mesero, Novedad, Mesa, Id_Cliente
            FROM temp_comanda
            WHERE Mesa=:mesa AND company_id=:cid
              AND Nro_Factura='0' AND Cancelado=0
            ORDER BY Movil ASC, Fecha DESC, Hora DESC
            LIMIT 1
        """), {"mesa": mesa_name, "cid": cid})).mappings().first()

    if not order:
        return {"order": None, "items": []}

    on    = order["Nro_Pedido"]
    fecha = str(order["Fecha"])

    # Calcular daily_seq
    seq_rows = (await db_temp.execute(text("""
        SELECT Nro_Pedido FROM temp_comanda
        WHERE company_id=:cid AND DATE(Fecha)=:today AND Nro_Factura='0' AND Cancelado=0
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
    # No filtramos por Fecha — Nro_pedido+company_id es suficiente y evita mismatch DATETIME
    items_rows = (await db_temp.execute(text("""
        SELECT Id_Plato, Item, Depende, Cantidad, Valor, Novedad,
               Cambios, Producto_Personalizado, Hora_Plato, Id_Tipificacion
        FROM temp_detalle_comanda_parcial
        WHERE Nro_pedido=:on AND Nro_Factura='0'
          AND company_id=:cid AND Mostrar=1
        ORDER BY Item
    """), {"on": on, "cid": cid})).mappings().all()

    # Nombres de platos desde easyposweb
    dish_ids = list({int(r["Id_Plato"]) for r in items_rows})
    dish_names: dict = {}
    if dish_ids:
        id_list = ",".join(str(d) for d in dish_ids)
        drows = (await db.execute(text(
            f"SELECT id, name FROM pos_dishes WHERE company_id=:cid AND id IN ({id_list})"
        ), {"cid": cid})).mappings().all()
        dish_names = {int(r["id"]): r["name"] for r in drows}

    assembly_map = await armado_svc.assembly_structured(db, db_temp, cid, on, dish_ids)
    # Variantes: el ítem guarda "PLATO - VARIANTE" en Producto_Personalizado
    variantes_por_plato = {d: await armado_svc.dish_variants(db, cid, d) for d in dish_ids}

    def _variante_de(did: int, custom: str):
        base = dish_names.get(did, "")
        for v in sorted(variantes_por_plato.get(did, []), key=lambda x: -len(x["name"])):
            pref = f"{base} - {v['name']}"
            if custom == pref or custom.startswith(pref + " "):
                return v
        return None

    try:
        customer_info = await clientes_svc.get_cliente(db, cid, int(order["Id_Cliente"] or 0) or clientes_svc.CONSUMIDOR_FINAL_ID)
        await db.commit()
    except HTTPException:
        customer_info = {"id_cliente": int(order["Id_Cliente"] or 0), "nombre": f"Cliente {order['Id_Cliente']}"}

    items = []
    for r in items_rows:
        assembly = assembly_map.get(int(r["Item"]), [])
        if not assembly and r["Producto_Personalizado"]:
            try:   # pedidos antiguos: el armado quedó como JSON en Producto_Personalizado
                assembly = json.loads(r["Producto_Personalizado"]).get("assembly", [])
            except Exception:
                pass
        hora_plato = str(r["Hora_Plato"] or "")
        sent = bool(hora_plato and hora_plato not in ("", "0"))
        did = int(r["Id_Plato"])
        var = _variante_de(did, str(r["Producto_Personalizado"] or ""))
        items.append({
            "dish_id":   did,
            "item":      int(r["Item"]),
            "dish_name": (f"{dish_names.get(did, '')} - {var['name']}" if var
                          else dish_names.get(did, f"Plato {did}")),
            "variant_id": var["id"] if var else None,
            "quantity":  float(r["Cantidad"] or 0),
            "amount":    int(r["Valor"] or 0),
            "notes":     r["Novedad"],
            "changes":   r["Cambios"],
            "assembly":  assembly,
            "dish_time": hora_plato,
            "sent":      sent,
            "typification_id": int(r["Id_Tipificacion"] or 0),
            # Nombre de lo que se vende (nombre + descripción personalizada); pedidos antiguos traían JSON
            "custom_product": None if str(r["Producto_Personalizado"] or "").startswith("{")
                              else (r["Producto_Personalizado"] or None),
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
            "customer":     customer_info,
        },
        "items": items,
    }


# ── 5. MENÚ (platos con config de armado) ────────────────────────────────────

@router.get("/menu")
async def get_menu(payload: dict = Depends(_auth_comanda), db: AsyncSession = Depends(get_db)):
    cid = payload["company_id"]

    # active=0 es el convenio VB6 para "producto activo" (activo=no_desactivado).
    # Intenta con columnas extendidas; si fallan, usa fallbacks progresivos.
    # has_assembly = plato de armado (Prioridad_Ofrecer = 1) con al menos una categoría de
    # armado activa en plato_armar (categoria_productos.Porcentaje = 1 y Activa = 1).
    dishes = None
    for sql in [
        # Nivel 1: columnas completas
        """SELECT DISTINCT d.id, d.name, d.price, d.category_id, d.photo_path,
                COALESCE(d.tax, 0) AS tax,
                (COALESCE(d.offer_priority, 0) = 1 AND EXISTS(
                    SELECT 1 FROM pos_dish_assembly da
                    JOIN pos_product_categories pc
                      ON pc.id = da.category_code AND pc.company_id = da.company_id
                     AND pc.percentage = 1 AND pc.is_active = 1
                    WHERE da.dish_id = d.id AND da.company_id = d.company_id AND da.is_active = 1
                )) AS has_assembly,
                COALESCE(d.preparation_time, 0) AS no_print,
                COALESCE(d.ask_product_description, 0) AS ask_description,
                c.name AS category_name
           FROM pos_dishes d
           INNER JOIN pos_dish_categories c
                   ON c.id = d.category_id AND c.company_id = d.company_id
           WHERE d.company_id = :cid AND c.is_active = 1 AND d.active = 0
           ORDER BY c.name, d.name""",
        # Nivel 2: sin tax ni preparation_time
        """SELECT DISTINCT d.id, d.name, d.price, d.category_id, d.photo_path,
                0 AS tax,
                (COALESCE(d.offer_priority, 0) = 1 AND EXISTS(
                    SELECT 1 FROM pos_dish_assembly da
                    JOIN pos_product_categories pc
                      ON pc.id = da.category_code AND pc.company_id = da.company_id
                     AND pc.percentage = 1 AND pc.is_active = 1
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

    # Platos con variantes (Personal / Dúo / Familiar…): al comandar se pide el tamaño
    try:
        con_variantes = {int(r[0]) for r in (await db.execute(text(
            "SELECT DISTINCT dish_id FROM pos_dish_variants WHERE company_id=:cid AND is_active=1"
        ), {"cid": cid})).all()}
    except Exception:
        con_variantes = set()

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
            "has_variants": int(d["id"]) in con_variantes,
            "no_print":    bool(d["no_print"]),
            "ask_description": bool(d.get("ask_description") or 0),
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
    """Opciones de armado del plato para hoy (item_id = supply_items.id_item) + insumos fijos."""
    cid = payload["company_id"]
    cats = await armado_svc.build_assembly(db, cid, dish_id, _today())
    fixed = await armado_svc.fixed_products(db, cid, dish_id)
    for c in cats:
        for o in c["options"]:
            o["available_today"] = True
    variants = await armado_svc.dish_variants(db, cid, dish_id)
    for v in variants:
        v["assembly"] = await armado_svc.variant_assembly(db, cid, v["id"])   # {category_code: max_choices}
    return {
        "variants": variants,
        "categories": cats,
        "fixed_products": [{"item_id": f["item_id"], "quantity": f["quantity"], "description": f["description"]}
                           for f in fixed],
    }


# ── 6b. CLIENTES DEL PEDIDO ───────────────────────────────────────────────────

@router.get("/clientes")
async def buscar_clientes(
    q: Optional[str] = Query(None, max_length=60),
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
):
    """Clientes de la empresa (Consumidor Final siempre primero)."""
    rows = await clientes_svc.buscar(db, payload["company_id"], q)
    await db.commit()
    return rows


@router.post("/clientes", status_code=201)
async def crear_cliente(
    data: ClienteRapidoIn,
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
):
    row = await clientes_svc.crear(db, payload["company_id"], data.nombres, data.cedula,
                                   data.telefono, data.direccion, data.mail)
    await db.commit()
    return row


@router.put("/orden/cliente")
async def cambiar_cliente(
    data: CambiarClienteIn,
    payload: dict = Depends(_auth_comanda),
    x_edit_token: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    """Asigna el cliente al pedido y recalcula los ítems no facturados con su lista de
    precios (o platos.Valor). Los ítems con descuento aplicado conservan su valor."""
    cid = payload["company_id"]
    await _exigir_mesa(db_temp, cid, x_edit_token, order_number=data.order_number)
    order = (await db_temp.execute(text("""
        SELECT Nro_Pedido FROM temp_comanda
        WHERE Nro_Pedido=:on AND company_id=:cid AND Nro_Factura='0' AND Cancelado=0 LIMIT 1
    """), {"on": data.order_number, "cid": cid})).mappings().first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada o ya cerrada")
    customer = await clientes_svc.get_cliente(db, cid, data.customer_id)
    await db.commit()

    await db_temp.execute(text(
        "UPDATE temp_comanda SET Id_Cliente=:cli, updated_at=NOW() WHERE Nro_Pedido=:on AND company_id=:cid"
    ), {"cli": customer["id_cliente"], "on": data.order_number, "cid": cid})

    items = (await db_temp.execute(text("""
        SELECT Id_Plato, Item, Cantidad, COALESCE(Id_Tipificacion,0) AS tip
        FROM temp_detalle_comanda_parcial
        WHERE Nro_pedido=:on AND company_id=:cid AND Nro_Factura='0' AND Mostrar=1
    """), {"on": data.order_number, "cid": cid})).mappings().all()
    extras = {int(r["Item"]): float(r["extra"] or 0) for r in (await db_temp.execute(text("""
        SELECT Item, SUM(Valor_Adicional_Armar) AS extra FROM temp_plato_producto_parcial
        WHERE Nro_Pedido=:on AND company_id=:cid GROUP BY Item
    """), {"on": data.order_number, "cid": cid})).mappings().all()}
    dish_ids = list({int(i["Id_Plato"]) for i in items})
    dishes = {}
    if dish_ids:
        dishes = {int(r["id"]): r for r in (await db.execute(text(
            f"SELECT id, price, tax FROM pos_dishes WHERE company_id=:cid AND id IN ({','.join(str(d) for d in dish_ids)})"
        ), {"cid": cid})).mappings().all()}
    repriced, kept = 0, 0
    for it in items:
        if int(it["tip"]):
            kept += 1
            continue
        d = dishes.get(int(it["Id_Plato"]))
        if not d:
            continue
        base = await armado_svc.client_price(db, cid, customer["id_cliente"], int(it["Id_Plato"]), d["price"])
        amount = int(round((base + extras.get(int(it["Item"]), 0)) * float(it["Cantidad"] or 0)))
        tax_pct = float(d["tax"] or 0)
        tax_val = int(amount * tax_pct / 100) if tax_pct > 0 else 0
        await db_temp.execute(text("""
            UPDATE temp_detalle_comanda_parcial
            SET Valor=:v, Impuesto=:t, Impuesto_Original=:t, updated_at=NOW()
            WHERE Nro_pedido=:on AND company_id=:cid AND Item=:item AND Mostrar=1 AND Nro_Factura='0'
        """), {"v": amount, "t": tax_val, "on": data.order_number, "cid": cid, "item": int(it["Item"])})
        repriced += 1
    await _recalc_total(db_temp, data.order_number, cid)
    await db_temp.commit()
    return {"ok": True, "customer": customer, "repriced": repriced, "kept_with_discount": kept}


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
    x_edit_token: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    cid = payload["company_id"]
    await _exigir_mesa(db_temp, cid, x_edit_token, order_number=data.order_number)

    # Verificar pedido activo — sin filtro de fecha (un pedido puede cruzar días)
    order_row = (await db_temp.execute(text("""
        SELECT Nro_Pedido, Fecha FROM temp_comanda
        WHERE Nro_Pedido=:on AND company_id=:cid
          AND Nro_Factura='0' AND Cancelado=0
        LIMIT 1
    """), {"on": data.order_number, "cid": cid})).mappings().first()
    if not order_row:
        raise HTTPException(status_code=404, detail="Orden no encontrada o ya cerrada")

    # Usar la Fecha real de la DB para todos los INSERT/SELECT posteriores
    real_fecha = order_row["Fecha"]

    # Info del plato desde easyposweb (active=0 → disponible, convención VB6)
    dish = (await db.execute(text("""
        SELECT id, name, price, tax, category_id, COALESCE(active,0) AS active,
               COALESCE(ask_product_description,0) AS ask_description
        FROM pos_dishes WHERE id=:did AND company_id=:cid
    """), {"did": data.dish_id, "cid": cid})).mappings().first()
    if not dish or int(dish["active"]) != 0:
        raise HTTPException(status_code=404, detail="Plato no encontrado o inactivo")
    if not (0 < data.quantity <= 1000):
        raise HTTPException(status_code=400, detail="Cantidad no válida")

    # ── Variante (tamaño): obligatoria si el plato tiene variantes ───────────
    variants = await armado_svc.dish_variants(db, cid, data.dish_id)
    variant = None
    if variants:
        variant = next((v for v in variants if v["id"] == data.variant_id), None)
        if not variant:
            raise HTTPException(status_code=400, detail="Seleccione el tamaño (variante) del producto")
    elif data.variant_id:
        raise HTTPException(status_code=400, detail="Este producto no tiene variantes")

    # ── Armado: validar contra la configuración del plato ────────────────────
    #   Cada selección es UNA porción: un sabor puede repetirse (Jamón ×2 + Cordero ×2).
    #   La variante fija cuántas opciones lleva cada categoría (Personal 2, Dúo 3, Familiar 4).
    cats = await armado_svc.build_assembly(db, cid, data.dish_id, _today())
    if variant:
        por_variante = await armado_svc.variant_assembly(db, cid, variant["id"])
        for c in cats:
            if c["category_code"] in por_variante:
                c["max_choices"] = por_variante[c["category_code"]]
    opts = {c["category_code"]: {o["item_id"]: o for o in c["options"]} for c in cats}
    selected, per_cat = [], {}
    for sel in (data.assembly_selections or [])[:200]:
        opt = opts.get(sel.category_code, {}).get(sel.item_id)
        if not opt:
            raise HTTPException(status_code=400, detail="Opción de armado no disponible para este plato")
        selected.append(opt)
        per_cat[sel.category_code] = per_cat.get(sel.category_code, 0) + 1
    # Exigir cantidad (Exgir_Seleccion) = 1 → exactamente "Opciones permitidas" (Cantidad_Elegir o la
    # de la variante); = 0 → libre, hasta ese máximo (o todas las opciones si es mayor).
    for c in cats:
        n = per_cat.get(c["category_code"], 0)
        # Con variante (tamaño) la cantidad de sabores SIEMPRE es obligatoria
        if (c["is_required"] or variant) and n != c["max_choices"]:
            raise HTTPException(status_code=400,
                detail=f"{c['category_name']}: debe seleccionar {c['max_choices']} opción(es)")
        tope = max(c["max_choices"], len(c["options"])) if not variant else c["max_choices"]
        if n > tope:
            raise HTTPException(status_code=400,
                detail=f"{c['category_name']}: máximo {tope} opción(es)")

    # ── Descripción personalizada (Pedir_Descripcion_Producto) ───────────────
    custom = armado_svc.clean_text(data.custom_description, 200)
    if int(dish["ask_description"]) and not custom:
        raise HTTPException(status_code=400, detail="Este producto requiere una descripción")
    nombre_venta = f"{dish['name']} - {variant['name']}" if variant else dish["name"]
    producto_personalizado = armado_svc.clean_text(f"{nombre_venta} {custom}" if custom else nombre_venta, 1000)

    # Siguiente número de ítem en datatemppos
    max_item = (await db_temp.execute(text(
        "SELECT COALESCE(MAX(Item), 0) FROM temp_detalle_comanda_parcial "
        "WHERE Nro_pedido=:on AND company_id=:cid"
    ), {"on": data.order_number, "cid": cid})).scalar() or 0
    first_item = int(max_item) + 1

    # Una fila por unidad, como el escritorio: permite el pago parcial por ítem.
    # Cantidades decimales (productos por peso) quedan en una sola fila.
    qty = float(data.quantity)
    unidades = [1.0] * int(qty) if qty.is_integer() and qty > 1 else [qty]

    # ── Precio: SIEMPRE calculado en el servidor ─────────────────────────────
    #   lista de precios del cliente del pedido (o platos.Valor) + valor adicional del armado
    cust = (await db_temp.execute(text(
        "SELECT COALESCE(Id_Cliente,0) FROM temp_comanda WHERE Nro_Pedido=:on AND company_id=:cid LIMIT 1"
    ), {"on": data.order_number, "cid": cid})).scalar() or 0
    if variant:
        base = await armado_svc.variant_price(db, cid, int(cust), variant, data.dish_id)
    else:
        base = await armado_svc.client_price(db, cid, int(cust), data.dish_id, dish["price"])
    unit = base + sum(o["supply_price"] for o in selected)
    tax_pct = float(dish["tax"]) if dish["tax"] else 0
    pays_tax = 1 if tax_pct > 0 else 0
    notes = armado_svc.clean_text(data.notes, 250) or None
    changes = armado_svc.clean_text(data.changes, 255) or None
    # Insumos fijos: con las cantidades de la receta de la variante, si la hay
    fixed = (await armado_svc.variant_fixed_products(db, cid, data.dish_id, variant["id"]) if variant
             else await armado_svc.fixed_products(db, cid, data.dish_id))

    total_amount, items_creados = 0, []
    for n, qty_u in enumerate(unidades):
      item_num = first_item + n
      amount = int(round(unit * qty_u))
      tax_val = int(amount * tax_pct / 100) if pays_tax else 0
      total_amount += amount
      items_creados.append(item_num)

      # Insertar ítem en datatemppos (Mostrar=1 = registro maestro)
      await db_temp.execute(text("""
        INSERT INTO temp_detalle_comanda_parcial
            (company_id, Nro_pedido, Fecha, Nro_Factura, Id_Plato, Item, Depende,
             Cantidad, Valor, Novedad, Cambios, Paga_Impuesto, Impuesto, Impuesto_Original,
             Producto_Personalizado, Nro_Puesto, Mostrar, Hora, updated_at)
        VALUES
            (:cid, :on, :fecha, '0', :did, :item, '0',
             :qty, :amount, :notes, :changes, :pays_tax, :tax, :tax,
             :custom, 0, 1, :hora, NOW())
    """), {
        "cid":      cid,
        "on":       data.order_number,
        "fecha":    real_fecha,
        "did":      data.dish_id,
        "item":     item_num,
        "qty":      qty_u,
        "amount":   amount,
        "notes":    notes,
        "changes":  changes,
        "pays_tax": pays_tax,
        "tax":      tax_val,
        "custom":   producto_personalizado,
        "hora":     _time_str(),
    })

      # Insumos a descontar (fijos + seleccionados) y novedades (armado + notas) de esta unidad
      await armado_svc.write_item_products(db_temp, cid, data.order_number, real_fecha,
                                           data.dish_id, item_num, fixed, selected)
      await armado_svc.write_item_armado(db_temp, cid, data.order_number, item_num, bool(cats), selected)
      await armado_svc.write_item_notes(db, db_temp, cid, data.order_number, item_num,
                                        int(dish["category_id"] or 0), notes)

    await _recalc_total(db_temp, data.order_number, cid)
    await db_temp.commit()

    return {
        "item":     items_creados[0],
        "items":    items_creados,
        "dish_id":  data.dish_id,
        "quantity": data.quantity,
        "amount":   total_amount,
        "notes":    notes,
        "changes":  changes,
        "custom_product": producto_personalizado,
        "variant_id": variant["id"] if variant else None,
    }


# ── 9. ACTUALIZAR ÍTEM ────────────────────────────────────────────────────────

@router.put("/orden/item")
async def actualizar_item(
    data: ActualizarItemIn,
    payload: dict = Depends(_auth_comanda),
    x_edit_token: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    cid = payload["company_id"]
    await _exigir_mesa(db_temp, cid, x_edit_token, order_number=data.order_number)

    current = (await db_temp.execute(text("""
        SELECT Cantidad, Valor FROM temp_detalle_comanda_parcial
        WHERE Nro_pedido=:on AND Nro_Factura='0'
          AND Id_Plato=:did AND Item=:item AND company_id=:cid AND Mostrar=1
    """), {
        "on": data.order_number,
        "did": data.dish_id, "item": data.item, "cid": cid,
    })).mappings().first()
    if not current:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")

    sets, params = [], {
        "on": data.order_number,
        "did": data.dish_id, "item": data.item, "cid": cid,
    }

    if data.quantity is not None:
        qty = float(current["Cantidad"])
        unit_price = int(int(current["Valor"]) / qty) if qty else 0
        sets += ["Cantidad = :qty", "Valor = :amount"]
        params["qty"]    = data.quantity
        params["amount"] = unit_price * data.quantity
    if data.quantity is not None and not (0 < data.quantity <= 1000):
        raise HTTPException(status_code=400, detail="Cantidad no válida")
    if data.notes is not None:
        sets.append("Novedad = :notes")
        params["notes"] = armado_svc.clean_text(data.notes, 250) or None
    if data.changes is not None:
        sets.append("Cambios = :changes")
        params["changes"] = armado_svc.clean_text(data.changes, 255) or None

    if data.notes is not None:
        dish_cat = (await db.execute(text(
            "SELECT COALESCE(category_id,0) FROM pos_dishes WHERE id=:did AND company_id=:cid"
        ), {"did": data.dish_id, "cid": cid})).scalar() or 0
        await armado_svc.write_item_notes(db, db_temp, cid, data.order_number, data.item,
                                          int(dish_cat), params["notes"])

    if sets:
        await db_temp.execute(text(
            f"UPDATE temp_detalle_comanda_parcial SET {', '.join(sets)} "
            "WHERE Nro_pedido=:on AND Nro_Factura='0' "
            "AND Id_Plato=:did AND Item=:item AND company_id=:cid AND Mostrar=1"
        ), params)
        await _recalc_total(db_temp, data.order_number, cid)
        await db_temp.commit()

    return {"ok": True}


# ── 9b. TIPIFICACIONES DE DESCUENTO (catálogo, solo lectura para comanda) ──────

@router.get("/tipificaciones-descuento")
async def listar_tipificaciones_descuento(
    payload: dict = Depends(_auth_comanda),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    rows = (await db_temp.execute(text("""
        SELECT Id_Tipificacion, Nombre, Valor_Descuento_Pesos,
               Valor_Descuento_Porcentaje, Exigir_Info_Cliente
        FROM temp_tipificaciones_descuentos
        WHERE company_id = :cid AND Desactivada = 0
        ORDER BY Id_Tipificacion = 0 DESC, Nombre
    """), {"cid": payload["company_id"]})).mappings().all()
    return [{
        "id": r["Id_Tipificacion"],
        "name": r["Nombre"],
        "discount_pesos": float(r["Valor_Descuento_Pesos"] or 0),
        "discount_percentage": int(r["Valor_Descuento_Porcentaje"] or 0),
        "ask_customer_info": bool(r["Exigir_Info_Cliente"]),
    } for r in rows]


# ── 9c. APLICAR / QUITAR DESCUENTO DE UN ÍTEM ───────────────────────────────────
# Tres tipos de tipificación, según sus campos (siempre sobre el ítem clicado
# únicamente — el reparto de un descuento en pesos entre TODOS los ítems del
# recibo es exclusivo de la pantalla de pago/PAGAR, no de aquí):
#   • id_tipificacion = 0 ("QUITAR DESCUENTO")  → restaura Porc_Descuento_General.
#   • id != 0 y Valor_Descuento_Porcentaje > 0 (ej. "Cortesía 100%",
#     "Descuento Empleados 20%")                → % sobre el valor original del ítem.
#   • id != 0 y Valor_Descuento_Porcentaje = 0 ("Descuento en Pesos")
#                                                → se pide el monto por pantalla
#     (monto_pesos) y se resta del valor original del ítem.
# Porc_Descuento_General siempre guarda el valor antes de esta aplicación
# (punto de restauración), y se recalcula el total del pedido igual que
# cualquier otra edición de ítem.

@router.post("/orden/item/descuento")
async def aplicar_descuento_item(
    data: AplicarDescuentoItemIn,
    payload: dict = Depends(_auth_comanda),
    x_edit_token: Optional[str] = Header(None),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    cid = payload["company_id"]
    await _exigir_mesa(db_temp, cid, x_edit_token, order_number=data.order_number)

    current = (await db_temp.execute(text("""
        SELECT Valor, Porc_Descuento_General, Id_Tipificacion
        FROM temp_detalle_comanda_parcial
        WHERE Nro_pedido=:on AND Nro_Factura='0'
          AND Id_Plato=:did AND Item=:item AND company_id=:cid AND Mostrar=1
    """), {"on": data.order_number, "did": data.dish_id, "item": data.item, "cid": cid})).mappings().first()
    if not current:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")

    tiene_descuento = int(current["Id_Tipificacion"] or 0) != 0
    original = int(current["Porc_Descuento_General"]) if tiene_descuento else int(current["Valor"])

    params = {"on": data.order_number, "did": data.dish_id, "item": data.item, "cid": cid}

    if data.id_tipificacion == 0:
        nuevo_valor = original
        sets = "Valor=:v, Porc_Descuento_Plato=:v, Porc_Descuento_General=:orig, Id_Tipificacion=0"
        params.update({"v": nuevo_valor, "orig": original})
    else:
        tip = (await db_temp.execute(text("""
            SELECT Nombre, Valor_Descuento_Porcentaje, Exigir_Info_Cliente
            FROM temp_tipificaciones_descuentos
            WHERE Id_Tipificacion=:tid AND company_id=:cid AND Desactivada=0
        """), {"tid": data.id_tipificacion, "cid": cid})).mappings().first()
        if not tip:
            raise HTTPException(status_code=404, detail="Tipificación no encontrada o inactiva")
        if tip["Exigir_Info_Cliente"] and not (data.observacion or "").strip():
            raise HTTPException(status_code=422, detail=f'"{tip["Nombre"]}" requiere una observación')

        porcentaje = int(tip["Valor_Descuento_Porcentaje"] or 0)
        if porcentaje > 0:
            nuevo_valor = max(0, round(original * (1 - porcentaje / 100)))
        else:
            monto = int(data.monto_pesos or 0)
            if monto <= 0:
                raise HTTPException(status_code=422, detail=f'"{tip["Nombre"]}" requiere el valor a descontar')
            nuevo_valor = max(0, original - monto)

        sets = "Valor=:v, Porc_Descuento_Plato=:v, Porc_Descuento_General=:orig, Id_Tipificacion=:tid"
        params.update({"v": nuevo_valor, "orig": original, "tid": data.id_tipificacion})

    if data.observacion:
        sets += ", Novedad=:obs"
        params["obs"] = data.observacion[:250]

    await db_temp.execute(text(
        f"UPDATE temp_detalle_comanda_parcial SET {sets} "
        "WHERE Nro_pedido=:on AND Nro_Factura='0' "
        "AND Id_Plato=:did AND Item=:item AND company_id=:cid AND Mostrar=1"
    ), params)

    await _recalc_total(db_temp, data.order_number, cid)
    await db_temp.commit()
    return {"ok": True, "valor": params["v"]}


# ── 10. ELIMINAR ÍTEM ─────────────────────────────────────────────────────────

@router.delete("/orden/item")
async def eliminar_item(
    data: EliminarItemIn,
    payload: dict = Depends(_auth_comanda),
    x_edit_token: Optional[str] = Header(None),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    cid = payload["company_id"]
    await _exigir_mesa(db_temp, cid, x_edit_token, order_number=data.order_number)

    # Borrar insumos (armado + fijos) y novedades del ítem
    await armado_svc.delete_item_temp(db_temp, cid, data.order_number, data.dish_id, data.item)

    # Borrar ítem principal — solo por Nro_pedido sin Fecha (evita mismatch DATETIME)
    await db_temp.execute(text("""
        DELETE FROM temp_detalle_comanda_parcial
        WHERE Nro_pedido=:on AND Nro_Factura='0'
          AND Id_Plato=:did AND Item=:item AND company_id=:cid
    """), {
        "on": data.order_number,
        "did": data.dish_id, "item": data.item, "cid": cid,
    })

    await _recalc_total(db_temp, data.order_number, cid)
    await db_temp.commit()
    return {"ok": True}


# ── 11. ENVIAR A COCINA ───────────────────────────────────────────────────────

@router.post("/orden/cocina")
async def enviar_cocina(
    data: EnviarCocinaIn,
    payload: dict = Depends(_auth_comanda),
    x_edit_token: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    cid = payload["company_id"]
    await _exigir_mesa(db_temp, cid, x_edit_token, order_number=data.order_number)
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
    # Sin filtro de fecha: puede haber pedidos pendientes de días anteriores (igual que /mesas).
    order = (await db_temp.execute(text("""
        SELECT Nro_Pedido, Fecha, Mesa, Hora, Mesero, Valor, Salio FROM temp_comanda
        WHERE Mesa=:mesa AND company_id=:cid
          AND Nro_Factura='0' AND Cancelado=0
        LIMIT 1
    """), {"mesa": mesa_name, "cid": cid})).mappings().first()
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

    # ── Marcar mesa como cerrada en temp_mesa_abierta (y liberar su toma) ──────
    await db_temp.execute(text("""
        UPDATE temp_mesa_abierta
        SET Abierta=0, Abierta_Desde=NULL, updated_at=NOW(),
            editing_waiter_name=NULL, editing_since=NULL, editing_token=NULL
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


# ── 14. BLOQUEO DE MESA-CUENTA ────────────────────────────────────────────────
# temp_mesa_abierta.Abierta = 1 → la mesa-cuenta está abierta en un dispositivo y queda
# BLOQUEADA para cualquier otro: otro mesero, otro dispositivo o el mismo usuario en otro
# equipo o pestaña. Abierta_Desde = nombre del dispositivo; editing_token identifica la
# sesión de la pestaña que la tiene (solo esa pestaña puede seguir trabajando en ella).
# Se libera al salir o enviar, al pagar la cuenta completa, o por el administrador en
# Cuentas Abiertas (cierre inesperado). No vence sola. Tampoco se puede pagar abierta.

import secrets as _secrets

_TOKEN_RE = re.compile(r"^[A-Za-z0-9-]{8,64}$")


def _token_valido(token: Optional[str]) -> Optional[str]:
    t = (token or "").strip()
    return t if _TOKEN_RE.match(t) else None


def _quien(row) -> str:
    """Texto 'USUARIO en DISPOSITIVO' de una mesa bloqueada."""
    nombre = (row.get("editing_waiter_name") or "").strip()
    disp = (row.get("Abierta_Desde") or "").strip()
    if nombre and disp:
        return f"{nombre} en {disp}"
    return nombre or (f"el dispositivo {disp}" if disp else "otro dispositivo")


async def _dueno_mesa(db_temp: AsyncSession, cid: int, table_id: Optional[int] = None,
                      mesa_name: Optional[str] = None):
    if table_id is not None:
        q, p = "company_id=:cid AND Id_Mesa=:tid", {"cid": cid, "tid": table_id}
    else:
        q, p = "company_id=:cid AND TRIM(Mesa)=TRIM(:mesa)", {"cid": cid, "mesa": mesa_name or ""}
    return (await db_temp.execute(text(f"""
        SELECT Id_Mesa, editing_waiter_name, editing_token, Abierta_Desde FROM temp_mesa_abierta
        WHERE {q} AND Abierta = 1
        LIMIT 1
    """), p)).mappings().first()


async def _exigir_mesa(db_temp: AsyncSession, cid: int, token: Optional[str],
                       table_id: Optional[int] = None, order_number: Optional[str] = None) -> None:
    """409 si la mesa (o la mesa del pedido) está abierta en OTRO dispositivo/pestaña."""
    if table_id is None:
        mesa = (await db_temp.execute(text(
            "SELECT Mesa FROM temp_comanda WHERE company_id=:cid AND Nro_Pedido=:on LIMIT 1"
        ), {"cid": cid, "on": order_number})).scalar()
        if mesa is None:
            return
        lock = await _dueno_mesa(db_temp, cid, mesa_name=mesa)
    else:
        lock = await _dueno_mesa(db_temp, cid, table_id=table_id)
    tk = _token_valido(token)
    if lock and (not tk or lock["editing_token"] != tk):
        raise HTTPException(status_code=409, detail=f"La mesa está abierta por {_quien(lock)}")


class EditLockIn(BaseModel):
    waiter_name: str
    token: str                          # sesión de la pestaña (generado por el dispositivo)
    device_name: Optional[str] = None   # nombre del dispositivo → temp_mesa_abierta.Abierta_Desde


@router.post("/mesa/{table_id}/editar")
async def adquirir_lock(
    table_id: int,
    data: EditLockIn,
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    """Abre la mesa en este dispositivo (Abierta = 1). 409 si ya está abierta en otro
    dispositivo o pestaña, aunque sea el mismo usuario."""
    cid = payload["company_id"]
    token = _token_valido(data.token)
    if not token:
        raise HTTPException(status_code=422, detail="Token de dispositivo inválido")
    mesa = (await db.execute(text(
        "SELECT id, name FROM pos_tables_layout WHERE id=:tid AND company_id=:cid"
    ), {"tid": table_id, "cid": cid})).mappings().first()
    if not mesa:
        raise HTTPException(status_code=404, detail="Mesa no encontrada")
    nombre = re.sub(r"[\x00-\x1f<>]", "", (data.waiter_name or "")).strip()[:100] or "Usuario"
    dispositivo = re.sub(r"[\x00-\x1f<>]", "", (data.device_name or "")).strip()[:100] or "Dispositivo web"

    # Apertura atómica: solo si nadie la tiene abierta (o es esta misma pestaña, p. ej. al recargar)
    await db_temp.execute(text("""
        INSERT IGNORE INTO temp_mesa_abierta (company_id, Id_Mesa, Mesa, Abierta, updated_at)
        VALUES (:cid, :tid, :mesa, 0, NOW())
    """), {"cid": cid, "tid": table_id, "mesa": mesa["name"]})
    await db_temp.execute(text("""
        UPDATE temp_mesa_abierta
        SET Abierta = 1, Abierta_Desde = :disp, Mesa = :mesa,
            editing_waiter_name = :name, editing_since = NOW(), editing_token = :token, updated_at = NOW()
        WHERE company_id=:cid AND Id_Mesa=:tid
          AND (COALESCE(Abierta, 0) = 0 OR editing_token = :token)
    """), {"cid": cid, "tid": table_id, "mesa": mesa["name"], "name": nombre, "disp": dispositivo, "token": token})
    await db_temp.commit()
    dueno = (await db_temp.execute(text("""
        SELECT Abierta, editing_waiter_name, editing_token, Abierta_Desde
        FROM temp_mesa_abierta WHERE company_id=:cid AND Id_Mesa=:tid
    """), {"cid": cid, "tid": table_id})).mappings().first()
    if not dueno or int(dueno["Abierta"] or 0) != 1 or dueno["editing_token"] != token:
        raise HTTPException(status_code=409, detail=f"La mesa está abierta por {_quien(dueno or {})}")
    return {"ok": True, "token": token}


@router.delete("/mesa/{table_id}/editar")
async def liberar_lock(
    table_id: int,
    token: str,
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
    db_temp: AsyncSession = Depends(get_datatemppos_db),
):
    """Cierra la mesa en este dispositivo (Abierta = 0). Solo la pestaña que la abrió.
    Si el pedido quedó sin ítems se cancela."""
    cid = payload["company_id"]
    token = _token_valido(token)
    if not token:
        return {"ok": True}
    r = await db_temp.execute(text("""
        UPDATE temp_mesa_abierta
        SET Abierta = 0, Abierta_Desde = NULL, updated_at = NOW(),
            editing_waiter_name = NULL, editing_since = NULL, editing_token = NULL
        WHERE company_id=:cid AND Id_Mesa=:tid AND editing_token=:token
    """), {"cid": cid, "tid": table_id, "token": token})
    if r.rowcount:
        mesa = (await db.execute(text(
            "SELECT name FROM pos_tables_layout WHERE id=:tid AND company_id=:cid"
        ), {"tid": table_id, "cid": cid})).scalar()
        if mesa is not None:
            await db_temp.execute(text("""
                UPDATE temp_comanda tc SET tc.Cancelado = 1
                WHERE tc.company_id=:cid AND TRIM(tc.Mesa)=TRIM(:mesa)
                  AND tc.Nro_Factura='0' AND tc.Cancelado=0
                  AND NOT EXISTS (
                      SELECT 1 FROM temp_detalle_comanda_parcial tdc
                      WHERE tdc.company_id=tc.company_id AND tdc.Nro_pedido=tc.Nro_Pedido
                        AND tdc.Nro_Factura='0'
                  )
            """), {"cid": cid, "mesa": mesa})
    await db_temp.commit()
    return {"ok": True}


# ── 15. COCINA TV ─────────────────────────────────────────────────────────────

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

    # Armado elegido: registro 1/1 de temp_novedades_plato_pedido (formato escritorio)
    armado_map = await armado_svc.armado_names(db_temp, cid, list({r["Nro_Pedido"] for r in order_rows}))

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

        assembly = [{"item_name": n} for n in armado_map.get((on, int(row["Item"])), [])]
        if not assembly and row["Producto_Personalizado"]:
            try:   # pedidos antiguos con el armado en JSON
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


async def _recalc_total(db_temp: AsyncSession, order_number: str, cid: int) -> None:
    """Recalcula el total de un pedido en temp_comanda desde sus ítems en datatemppos."""
    await db_temp.execute(text("""
        UPDATE temp_comanda tc
        SET tc.Valor = (
            SELECT COALESCE(SUM(tdc.Valor), 0)
            FROM temp_detalle_comanda_parcial tdc
            WHERE tdc.Nro_pedido  = tc.Nro_Pedido
              AND tdc.Nro_Factura = '0'
              AND tdc.company_id  = tc.company_id
              AND tdc.Mostrar     = 1
        )
        WHERE tc.Nro_Pedido  = :on
          AND tc.company_id  = :cid
    """), {"on": order_number, "cid": cid})


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
# Un menú por día (Id_Menu = consecutivo, fecha). Se muestran TODAS las categorías de armado
# activas (categoria_productos.Porcentaje = 1 y Activa = 1), aun sin insumos; dentro de cada
# una, sus insumos de armado (inventario_porciones.Armar_Plato = 1, Agrupar = categoría).
# Se guardan solo los insumos marcados; si no hay ninguno se borra el menú de ese día.
# Solo se arma el de HOY; otras fechas se consultan e imprimen.

_FECHA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _fecha_valida(d: Optional[str]) -> str:
    d = (d or "").strip()
    if not _FECHA_RE.match(d):
        raise HTTPException(status_code=422, detail="Fecha inválida (AAAA-MM-DD)")
    try:
        datetime.strptime(d, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=422, detail="Fecha inválida")
    return d


class GuardarMenuDiarioIn(BaseModel):
    date: str
    selected_ids: List[int]


@router.get("/menu-diario-admin")
async def get_menu_diario_admin(
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
):
    """Menú de HOY: todas las categorías de armado activas (aun sin insumos) con sus insumos
    de armado; is_selected según lo guardado hoy."""
    cid = payload["company_id"]
    target_date = _today()

    cats = (await db.execute(text("""
        SELECT id, name FROM pos_product_categories
        WHERE company_id = :cid AND percentage = 1 AND is_active = 1
        ORDER BY name
    """), {"cid": cid})).mappings().all()
    items_rows = (await db.execute(text("""
        SELECT si.id_item, si.description AS item_name, si.agrupar AS group_id
        FROM supply_items si
        INNER JOIN pos_product_categories pc
                ON pc.id = si.agrupar AND pc.company_id = si.company_id
               AND pc.percentage = 1 AND pc.is_active = 1
        WHERE si.company_id = :cid AND si.is_active = 1 AND si.armar_plato = 1
        ORDER BY si.description
    """), {"cid": cid})).mappings().all()
    saved = (await db.execute(text("""
        SELECT item_id, menu_id FROM pos_daily_menu
        WHERE company_id = :cid AND date = :d AND COALESCE(selected, 1) = 1
    """), {"cid": cid, "d": target_date})).mappings().all()
    selected_ids = {int(r["item_id"]) for r in saved}
    menu_id = max((int(r["menu_id"]) for r in saved), default=None)

    por_cat: dict = {}
    for r in items_rows:
        por_cat.setdefault(int(r["group_id"]), []).append({
            "item_id": int(r["id_item"]),
            "item_name": r["item_name"] or f"Insumo {r['id_item']}",
            "is_selected": int(r["id_item"]) in selected_ids,
        })
    return {
        "date": target_date,
        "menu_id": menu_id,
        "categories": [{"group_id": int(c["id"]), "group_name": c["name"] or f"Categoría {c['id']}",
                        "items": por_cat.get(int(c["id"]), [])} for c in cats],
    }


async def _menu_guardado(db: AsyncSession, cid: int, d: str) -> dict:
    """Menú guardado de una fecha: categorías (orden alfabético) con sus insumos marcados
    (orden alfabético). Las categorías sin insumos no se incluyen."""
    rows = (await db.execute(text("""
        SELECT dm.menu_id, dm.group_by, dm.item_id,
               COALESCE(pc.name, dm.category) AS categoria,
               COALESCE(si.description, dm.description) AS insumo
        FROM pos_daily_menu dm
        LEFT JOIN pos_product_categories pc ON pc.company_id = dm.company_id AND pc.id = dm.group_by
        LEFT JOIN supply_items si ON si.company_id = dm.company_id AND si.id_item = dm.item_id
        WHERE dm.company_id = :cid AND dm.date = :d AND COALESCE(dm.selected, 1) = 1
    """), {"cid": cid, "d": d})).mappings().all()
    grupos: dict = {}
    for r in rows:
        nombre = (r["categoria"] or f"Categoría {r['group_by']}").strip()
        grupos.setdefault(nombre, []).append((r["insumo"] or f"Insumo {r['item_id']}").strip())
    return {
        "date": d,
        "menu_id": max((int(r["menu_id"]) for r in rows), default=None),
        "categories": [{"name": k, "items": sorted(v, key=str.upper)}
                       for k, v in sorted(grupos.items(), key=lambda kv: kv[0].upper())],
    }


@router.get("/menu-diario-admin/consulta")
async def consultar_menu_diario(
    date: str = Query(...),
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
):
    """Menú armado de cualquier fecha (solo lectura, para ver e imprimir)."""
    return await _menu_guardado(db, payload["company_id"], _fecha_valida(date))


class ImprimirMenuIn(BaseModel):
    date: str
    printer_id: int
    raw: bool = False


def _tirilla_menu(d: dict, width: int = 32) -> bytes:
    from app.routers.pos_recibo_impresion_router import _ascii
    ESC = b"\x1b"
    INIT, BOLD_ON, BOLD_OFF = ESC + b"@", ESC + b"E\x01", ESC + b"E\x00"
    CENTER, LEFT, CUT, LF = ESC + b"a\x01", ESC + b"a\x00", b"\x1dV\x42\x00", b"\n"
    buf = bytearray(INIT)

    def line(t="", bold=False, center=False):
        buf.extend((BOLD_ON if bold else b"") + (CENTER if center else LEFT) + _ascii(t) + LF + (BOLD_OFF if bold else b""))

    line(d.get("empresa") or "", bold=True, center=True)
    line("MENU DEL DIA", bold=True, center=True)
    fecha = datetime.strptime(d["date"], "%Y-%m-%d").strftime("%d/%m/%Y")
    line(f"{fecha}   Menu No. {d['menu_id'] or '-'}", center=True)
    line("-" * width)
    for c in d["categories"]:
        line(c["name"], bold=True)
        for i in c["items"]:
            t = f"  - {i}"
            while t:
                line(t[:width])
                t = ("    " + t[width:]) if len(t) > width else ""
        line()
    buf.extend(LF * 3 + CUT)
    return bytes(buf)


@router.post("/menu-diario-admin/imprimir")
async def imprimir_menu_diario(
    data: ImprimirMenuIn,
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
):
    from app.routers.pos_recibo_impresion_router import enviar_tirilla
    cid = payload["company_id"]
    d = _fecha_valida(data.date)

    async def datos():
        m = await _menu_guardado(db, cid, d)
        if not m["categories"]:
            raise HTTPException(status_code=404, detail="No hay menú guardado para esa fecha")
        m["empresa"] = (await db.execute(text(
            "SELECT name FROM companies WHERE id_company = :cid"), {"cid": cid})).scalar() or ""
        return m

    return await enviar_tirilla(db, cid, data.printer_id, data.raw, datos, armar=_tirilla_menu)


@router.post("/menu-diario-admin/guardar")
async def guardar_menu_diario(
    data: GuardarMenuDiarioIn,
    payload: dict = Depends(_auth_comanda),
    db: AsyncSession = Depends(get_db),
):
    """Guarda el menú de HOY (pizarra limpia): borra el de la fecha y re-inserta los insumos
    marcados con el Id_Menu del día. Sin insumos marcados → se borra el menú de esa fecha."""
    cid = payload["company_id"]
    d = _fecha_valida(data.date)
    if d != _today():
        raise HTTPException(status_code=422, detail="Solo se puede armar el menú del día de hoy")
    ids = sorted({int(i) for i in data.selected_ids if int(i) > 0})[:500]

    # Id_Menu: se conserva el de la fecha; si no existe, el siguiente de la empresa
    menu_id = (await db.execute(text(
        "SELECT MAX(menu_id) FROM pos_daily_menu WHERE company_id = :cid AND date = :d"
    ), {"cid": cid, "d": d})).scalar()
    if not menu_id:
        menu_id = int((await db.execute(text(
            "SELECT COALESCE(MAX(menu_id), 0) FROM pos_daily_menu WHERE company_id = :cid"
        ), {"cid": cid})).scalar() or 0) + 1

    await db.execute(text("DELETE FROM pos_daily_menu WHERE company_id = :cid AND date = :d"),
                     {"cid": cid, "d": d})
    if ids:
        ph = ", ".join(f":id{i}" for i in range(len(ids)))
        params: dict = {"cid": cid, "d": d, "mid": int(menu_id), **{f"id{i}": v for i, v in enumerate(ids)}}
        await db.execute(text(f"""
            INSERT INTO pos_daily_menu
                (company_id, menu_id, item_id, date, category, description, group_by, selected, synced, updated_at)
            SELECT si.company_id, :mid, si.id_item, :d,
                   pc.name, si.description, si.agrupar, 1, 0, NOW()
            FROM supply_items si
            INNER JOIN pos_product_categories pc
                   ON si.agrupar = pc.id AND pc.company_id = :cid
                  AND pc.percentage = 1 AND pc.is_active = 1
            WHERE si.company_id = :cid AND si.armar_plato = 1 AND si.id_item IN ({ph})
            ON DUPLICATE KEY UPDATE date = :d, selected = 1, updated_at = NOW()
        """), params)
    await db.commit()
    return {"ok": True, "date": d, "menu_id": int(menu_id) if ids else None, "selected_count": len(ids)}
