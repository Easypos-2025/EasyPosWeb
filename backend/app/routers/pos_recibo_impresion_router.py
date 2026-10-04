"""
Impresión del Recibo de restaurante (pantalla de pago y reimpresión desde Consulta de Ventas).

  GET  /api/pos/recibo-impresion/impresoras     impresoras activas + la predeterminada
  GET  /api/pos/recibo-impresion/{receipt}      datos del recibo para la vista previa
  POST /api/pos/recibo-impresion/imprimir       tirilla ESC/POS (red: la envía el servidor;
                                                USB/Bluetooth: devuelve los bytes, raw=True)

Impresora predeterminada: la de la caja del turno abierto del usuario
(pos_cash_registers.printer_id = cajas.Id_Impresora); si la caja no tiene, la general de
configuracion_facturacion.impresora_facturas.

La empresa sale SIEMPRE de la sesión (tenant); un company_id del navegador solo se acepta si
el usuario tiene acceso (tenant_guard) y no se usa para consultar.
"""
import base64
import socket
import unicodedata
from collections import OrderedDict
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from app.services.error_log import log_error
from pydantic import BaseModel, Field, StringConstraints
from typing_extensions import Annotated
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.tenant import tenant_guard
from app.models.user_model import User
from app.routers.pos_shift_router import _id_caja_header, _turno_abierto
from app.services import config_facturacion as cfg_svc

router = APIRouter(prefix="/api/pos/recibo-impresion", tags=["POS Recibo Impresión"],
                   dependencies=[Depends(tenant_guard)])

ReceiptNo = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50,
                                             pattern=r"^[A-Za-z0-9_-]+$")]


async def _impresora_default(db: AsyncSession, cid: int, uid: int, id_caja: Optional[int] = None) -> Optional[int]:
    turno = await _turno_abierto(db, cid, uid, id_caja)
    if turno and turno.get("register_number"):
        pid = (await db.execute(text(
            "SELECT printer_id FROM pos_cash_registers WHERE company_id=:cid AND id=:caja"
        ), {"cid": cid, "caja": int(turno["register_number"])})).scalar()
        if pid:
            return int(pid)
    cfg = await cfg_svc.get_config(db, cid)
    return cfg["impresora_facturas"] or None


@router.get("/impresoras")
async def impresoras(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cid = current_user.company_id
    rows = (await db.execute(text("""
        SELECT id, name, ip, port, connection_type, bluetooth_address, usb_device_id
        FROM pos_printers WHERE company_id = :cid AND is_active = 1 ORDER BY id
    """), {"cid": cid})).mappings().all()
    default_id = await _impresora_default(db, cid, current_user.id, _id_caja_header(request))
    await db.commit()
    out = [dict(r) | {"is_default": int(r["id"]) == default_id} for r in rows]
    out.sort(key=lambda p: not p["is_default"])          # la predeterminada primero
    return out


async def _datos_recibo(db: AsyncSession, cid: int, rn: str) -> dict:
    rc = (await db.execute(text("""
        SELECT receipt_number, date, time, COALESCE(cash_amount,0) total, COALESCE(discount,0) discount,
               COALESCE(tip,0) tip, COALESCE(amount_without_tip,0) venta, COALESCE(customer_id,1) customer_id
        FROM pos_receipts WHERE company_id = :cid AND receipt_number = :rn AND voided = 0
        LIMIT 1
    """), {"cid": cid, "rn": rn})).mappings().first()
    if not rc:
        raise HTTPException(status_code=404, detail="Recibo no encontrado")

    orden = (await db.execute(text("""
        SELECT ro.order_number, ro.table_name, ro.notes, COALESCE(w.name,'') mesero
        FROM pos_receipt_orders ro
        LEFT JOIN pos_waiters w ON w.id = ro.waiter_id AND w.company_id = ro.company_id
        WHERE ro.company_id = :cid AND ro.receipt_number = :rn AND ro.date = :d
        LIMIT 1
    """), {"cid": cid, "rn": rn, "d": rc["date"]})).mappings().first() or {}

    detalle = (await db.execute(text("""
        SELECT od.item, od.quantity, COALESCE(od.amount,0) amount, COALESCE(od.notes,'') notes,
               COALESCE(od.custom_product,'') custom, COALESCE(d.name, '') dish
        FROM pos_receipt_order_details od
        LEFT JOIN pos_dishes d ON d.id = od.dish_id AND d.company_id = od.company_id
        WHERE od.company_id = :cid AND od.receipt_number = :rn AND od.date = :d
        ORDER BY od.item
    """), {"cid": cid, "rn": rn, "d": rc["date"]})).mappings().all()

    # Agrupado igual que la "Vista previa": producto + armado + valor unitario
    grupos: "OrderedDict[tuple, dict]" = OrderedDict()
    for r in detalle:
        qty = float(r["quantity"] or 0)
        amount = float(r["amount"] or 0)
        custom = str(r["custom"] or "")
        nombre = custom if custom and not custom.startswith("{") else (r["dish"] or "Producto")
        unit = round(amount / qty) if qty else amount
        k = (nombre, r["notes"], unit)
        g = grupos.setdefault(k, {"nombre": nombre, "detalle": r["notes"], "cantidad": 0.0,
                                  "precio": unit, "total": 0.0})
        g["cantidad"] += qty
        g["total"] += amount
    items = [g | {"cantidad": int(g["cantidad"]) if float(g["cantidad"]).is_integer() else g["cantidad"]}
             for g in grupos.values()]

    pagos = (await db.execute(text("""
        SELECT COALESCE(pt.name, 'Pago') name, prm.amount
        FROM pos_receipt_payment_methods prm
        LEFT JOIN pos_payment_types pt ON pt.id = prm.payment_method_id AND pt.company_id = prm.company_id
        WHERE prm.company_id = :cid AND prm.invoice_number = :rn AND prm.date = :d
        ORDER BY prm.item
    """), {"cid": cid, "rn": rn, "d": rc["date"]})).mappings().all()

    domicilio = float((await db.execute(text(
        "SELECT COALESCE(SUM(amount),0) FROM receipt_delivery_fees WHERE company_id=:cid AND invoice_number=:rn AND date=:d"
    ), {"cid": cid, "rn": rn, "d": rc["date"]})).scalar() or 0)

    cli = (await db.execute(text("""
        SELECT TRIM(CONCAT(COALESCE(nombres,''),' ',COALESCE(apellidos,''))) nombre, cedula, telefono, direccion
        FROM clientes WHERE company_id=:cid AND id_cliente=:id LIMIT 1
    """), {"cid": cid, "id": int(rc["customer_id"] or 1)})).mappings().first()

    emp = (await db.execute(text(
        "SELECT name, identification_number nit, dv, address, phone FROM companies WHERE id_company=:cid"
    ), {"cid": cid})).mappings().first() or {}
    tip_label = (await db.execute(text(
        "SELECT tip_label FROM company_configs WHERE company_id=:cid"
    ), {"cid": cid})).scalar() or "Propina"
    cfg = await cfg_svc.get_config(db, cid)
    await db.commit()

    venta, descuento, tip = float(rc["venta"]), float(rc["discount"]), float(rc["tip"])
    return {
        "empresa": {
            "nombre": emp.get("name") or "EasyPos",
            "nit": (f"{emp.get('nit')}-{emp.get('dv')}" if emp.get("dv") not in (None, "") else emp.get("nit")) or "",
            "direccion": emp.get("address") or "", "telefono": emp.get("phone") or "",
            "encabezado": cfg["imprimir_encabezado_factura"],
        },
        "receipt_number": str(rc["receipt_number"]),
        "fecha": str(rc["date"]), "hora": str(rc["time"] or "")[:8],
        "order_number": orden.get("order_number") or "",
        "mesa": orden.get("table_name") or "", "mesero": orden.get("mesero") or "",
        "observacion": orden.get("notes") or "",
        "cliente": dict(cli) if (cli and cfg["imprimir_datos_cliente"]) else ({"nombre": cli["nombre"]} if cli else None),
        "items": items,
        "subtotal": venta + descuento, "descuento": descuento, "venta": venta,
        "tip": tip, "tipLabel": tip_label, "domicilio": domicilio, "total": float(rc["total"]),
        "pagos": [{"name": p["name"], "amount": float(p["amount"] or 0)} for p in pagos],
        "resolucion_propina": cfg["resolucion_propina"] if (tip and cfg["imprimir_resolucion_propina"]) else "",
        "mensaje": cfg["mensaje_factura"],
    }


@router.get("/{receipt_number}")
async def datos_recibo(
    receipt_number: ReceiptNo,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await _datos_recibo(db, current_user.company_id, receipt_number)


# ─── Tirilla ESC/POS ─────────────────────────────────────────────────────────
class ImprimirIn(BaseModel):
    printer_id: Annotated[int, Field(ge=0)]
    receipt_number: ReceiptNo
    raw: bool = False
    company_id: Optional[int] = None      # lo valida tenant_guard; no se usa para consultar


def _ascii(t) -> bytes:
    # Las térmicas no imprimen bien tildes/ñ en UTF-8: se pasan a ASCII (á→a, ñ→n)
    return unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore")


def _money(v: float) -> str:
    return "$" + f"{int(round(v or 0)):,}".replace(",", ".")


def _tirilla(d: dict, width: int = 32) -> bytes:
    ESC = b"\x1b"
    INIT, BOLD_ON, BOLD_OFF = ESC + b"@", ESC + b"E\x01", ESC + b"E\x00"
    CENTER, LEFT, CUT, LF = ESC + b"a\x01", ESC + b"a\x00", b"\x1dV\x42\x00", b"\n"
    buf = bytearray(INIT)

    def line(t="", bold=False, center=False):
        buf.extend((BOLD_ON if bold else b"") + (CENTER if center else LEFT) + _ascii(t) + LF + (BOLD_OFF if bold else b""))

    def wrap(t, indent=""):
        t = str(t or "")
        while t:
            line(indent + t[: width - len(indent)])
            t = t[width - len(indent):]

    def dl(a, b, bold=False):
        a = str(a)[: max(1, width - len(b) - 1)]
        line(a + " " * max(1, width - len(a) - len(b)) + b, bold=bold)

    sep = "-" * width
    e = d["empresa"]
    line(e["nombre"], bold=True, center=True)
    if e["encabezado"]:
        if e["nit"]: line(f"NIT {e['nit']}", center=True)
        if e["direccion"]: line(e["direccion"], center=True)
        if e["telefono"]: line(f"Tel. {e['telefono']}", center=True)
    line(d.get("titulo") or "RECIBO DE VENTA", bold=True, center=True)
    if d.get("receipt_number"):
        line(f"Recibo No. {d['receipt_number']}", center=True)
    line(f"{d['fecha']}  {d['hora']}", center=True)
    if d["order_number"]: wrap(f"Pedido: {d['order_number']}")
    if d["mesa"]: line(f"Mesa: {d['mesa']}")
    if d["mesero"]: line(f"Mesero: {d['mesero']}")
    c = d.get("cliente")
    if c:
        wrap(f"Cliente: {c.get('nombre','')}")
        if c.get("cedula"): line(f"C.C./NIT: {c['cedula']}")
        if c.get("telefono"): line(f"Tel: {c['telefono']}")
        if c.get("direccion"): wrap(f"Dir: {c['direccion']}")
    line(sep)
    for it in d["items"]:
        dl(f"{it['cantidad']} {it['nombre']}", _money(it["total"]))
        if it["detalle"]: wrap(it["detalle"], "   ")
    line(sep)
    dl("Subtotal", _money(d["subtotal"]))
    if d["descuento"]: dl("Descuento", "-" + _money(d["descuento"]))
    if d["descuento"]: dl("Venta", _money(d["venta"]))
    if d["tip"]: dl(d["tipLabel"], _money(d["tip"]))
    if d["domicilio"]: dl("Domicilio", _money(d["domicilio"]))
    dl("TOTAL", _money(d["total"]), bold=True)
    line(sep)
    for p in d["pagos"]:
        dl(p["name"], _money(p["amount"]))
    if d["observacion"]:
        line(sep); wrap(f"Obs: {d['observacion']}")
    if d["resolucion_propina"]:
        line(sep); wrap(d["resolucion_propina"])
    line(sep)
    line(d["mensaje"] or "Gracias por su compra!", center=True)
    buf.extend(LF * 4 + CUT)
    return bytes(buf)


async def enviar_tirilla(db: AsyncSession, cid: int, printer_id: int, raw: bool, datos_fn, armar=None) -> dict:
    """Valida la impresora de la empresa y envía la tirilla (red) o devuelve los bytes
    (USB/Bluetooth). `datos_fn` es una corrutina que arma los datos solo si la impresora es válida."""
    printer = (await db.execute(text("""
        SELECT name, ip, port, LOWER(COALESCE(connection_type,'')) connection_type
        FROM pos_printers WHERE id=:pid AND company_id=:cid AND is_active=1
    """), {"pid": printer_id, "cid": cid})).mappings().first()
    if not printer:
        raise HTTPException(status_code=404, detail="Impresora no encontrada o inactiva")
    directa = printer["connection_type"] in ("bluetooth", "usb")
    if directa and not raw:
        raise HTTPException(status_code=400, detail="Esta impresora es USB/Bluetooth: se imprime desde el dispositivo, no por red")
    if not directa and not printer["ip"]:
        raise HTTPException(status_code=400, detail="La impresora de red no tiene IP configurada")

    data = (armar or _tirilla)(await datos_fn())
    if raw:
        return {"ok": True, "printer": printer["name"], "data_b64": base64.b64encode(data).decode()}
    try:
        with socket.create_connection((printer["ip"], int(printer["port"] or 9100)), timeout=5) as s:
            s.sendall(data)
    except OSError as e:
        log_error(e, tipo="IMPRESION", contexto={"impresora": printer["name"], "ip": printer["ip"], "puerto": printer["port"]})
        raise HTTPException(status_code=502, detail=f"No se pudo conectar con la impresora {printer['name']} ({printer['ip']}:{printer['port'] or 9100}). Verifique que esté encendida y en la misma red.")
    return {"ok": True, "printer": printer["name"]}


@router.post("/imprimir")
async def imprimir(
    body: ImprimirIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cid = current_user.company_id
    return await enviar_tirilla(db, cid, body.printer_id, body.raw,
                                lambda: _datos_recibo(db, cid, body.receipt_number))
