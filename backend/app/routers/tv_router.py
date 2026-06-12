"""
tv_router.py — Pantallas TV por código corto + activación por dispositivo.
Permite múltiples pantallas por empresa, cada una filtrada por impresoras.
"""
import json
import re
import secrets
import random
import time
from datetime import datetime, timedelta, date
from typing import Optional, List

# Señales de refresh en memoria (company_id → unix timestamp)
_refresh_signals: dict[int, float] = {}
# Throttle cleanup: máximo una vez por minuto por empresa
_last_cleanup: dict[int, float] = {}

from fastapi import APIRouter, Header, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select

from app.database import get_db, get_datatemppos_db
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.user_model import User

router = APIRouter(prefix="/api/tv", tags=["TV Pantallas"])


# ── Utilidades ────────────────────────────────────────────────────

def _today() -> str:
    return date.today().isoformat()


def _hp_sort_key(t: str) -> int:
    if not t: return 0
    t = t.strip()
    if re.match(r'\d{4}-\d{2}-\d{2}', t):
        m = re.search(r'(\d{1,2}):(\d{2}):(\d{2})', t)
        if m: return int(m.group(1))*3600+int(m.group(2))*60+int(m.group(3))
        return 0
    m = re.match(r'(\d{1,2}):(\d{2}):(\d{2})\s+(a|p)', t, re.IGNORECASE)
    if m:
        h,mn,s = int(m.group(1)),int(m.group(2)),int(m.group(3))
        if m.group(4).lower()=='p' and h!=12: h+=12
        elif m.group(4).lower()=='a' and h==12: h=0
        return h*3600+mn*60+s
    m = re.match(r'(\d{1,2}):(\d{2})', t)
    if m: return int(m.group(1))*3600+int(m.group(2))*60
    return 0


async def _get_admin_user(authorization: str, db: AsyncSession) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido")
    result = await db.execute(
        select(UserSession).where(UserSession.token == token, UserSession.is_active == True)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=401, detail="Sesión inválida")
    uid = payload.get("user_id")
    user = await db.get(User, int(uid)) if uid else None
    if not user:
        result = await db.execute(select(User).where(User.email == payload.get("sub")))
        user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not user.company_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asignada")
    return user


async def _cleanup_zombie_orders(cid: int, db_main: AsyncSession, db_temp: AsyncSession) -> None:
    """Limpia pedidos zombies cada 60s por empresa para evitar table locks frecuentes."""
    now = time.time()
    if now - _last_cleanup.get(cid, 0) < 60:
        return
    _last_cleanup[cid] = now
    today_iso = date.today().isoformat()

    # Buffer de 1 día para evitar borrar pedidos del día local cuando el servidor
    # corre en UTC y la fecha local (VB6) es un día antes de CURDATE() en el server.
    await db_temp.execute(text("""
        DELETE FROM temp_comanda
        WHERE company_id = :cid
          AND Nro_Factura = '0'
          AND Fecha < DATE_SUB(CURDATE(), INTERVAL 1 DAY)
    """), {"cid": cid})

    # Borrar headers donde VB6 actualizó todos los ítems (Nro_Factura!=0) pero no el header
    await db_temp.execute(text("""
        DELETE tc FROM temp_comanda tc
        INNER JOIN (
            SELECT Nro_pedido, company_id
            FROM temp_detalle_comanda_parcial
            WHERE company_id = :cid
            GROUP BY Nro_pedido, company_id
            HAVING SUM(CASE WHEN Nro_Factura = '0' THEN 1 ELSE 0 END) = 0
               AND COUNT(*) > 0
        ) AS billed ON tc.Nro_Pedido = billed.Nro_pedido
            AND tc.company_id = billed.company_id
        WHERE tc.Nro_Factura = '0'
    """), {"cid": cid})

    # Borrar zombies VB6: Nro_Factura='0' cuyo mismo Nro_Pedido ya tiene una fila facturada.
    # VB6 no actualiza la fila '0', sino que inserta una nueva con el número real.
    await db_temp.execute(text("""
        DELETE tc FROM temp_comanda tc
        WHERE tc.company_id = :cid
          AND tc.Nro_Factura = '0'
          AND EXISTS (
              SELECT 1 FROM temp_comanda tc2
              WHERE tc2.company_id = :cid
                AND tc2.Nro_Pedido = tc.Nro_Pedido
                AND tc2.Nro_Factura <> '0'
          )
    """), {"cid": cid})

    # Borrar zombies web: pedidos ya en pos_invoice_details que siguen con Nro_Factura='0'
    inv_rows = (await db_main.execute(text("""
        SELECT DISTINCT order_number
        FROM pos_invoice_details
        WHERE company_id = :cid
          AND date >= CURDATE() - INTERVAL 7 DAY
    """), {"cid": cid})).fetchall()
    if inv_rows:
        inv_quoted = ",".join(f"'{r[0]}'" for r in inv_rows)
        await db_temp.execute(text(f"""
            DELETE FROM temp_detalle_comanda_parcial
            WHERE company_id = :cid
              AND Nro_Factura = '0'
              AND Nro_pedido IN ({inv_quoted})
        """), {"cid": cid})
        await db_temp.execute(text(f"""
            DELETE FROM temp_comanda
            WHERE company_id = :cid
              AND Nro_Factura = '0'
              AND Nro_Pedido IN ({inv_quoted})
        """), {"cid": cid})

    # Borrar detalles huérfanos cuyo header ya no existe
    await db_temp.execute(text("""
        DELETE tdc FROM temp_detalle_comanda_parcial tdc
        LEFT JOIN temp_comanda tc
            ON tc.Nro_Pedido = tdc.Nro_pedido
           AND tc.company_id  = tdc.company_id
        WHERE tdc.company_id = :cid
          AND tc.Nro_Pedido IS NULL
    """), {"cid": cid})

    await db_temp.commit()

    # Obtener pedidos activos tras limpieza para purgar eventos de cocina obsoletos
    active_rows = (await db_temp.execute(text(
        "SELECT Nro_Pedido FROM temp_comanda WHERE company_id=:cid AND Nro_Factura='0'"
    ), {"cid": cid})).fetchall()
    active_orders = [r[0] for r in active_rows]

    if active_orders:
        quoted = ",".join(f"'{o}'" for o in active_orders)
        await db_main.execute(text(f"""
            DELETE FROM pos_kitchen_events
            WHERE company_id = :cid
              AND event_date  = :today
              AND created_at  < NOW() - INTERVAL 10 MINUTE
              AND order_number NOT IN ({quoted})
        """), {"cid": cid, "today": today_iso})
    else:
        await db_main.execute(text("""
            DELETE FROM pos_kitchen_events
            WHERE company_id = :cid
              AND event_date  = :today
              AND created_at  < NOW() - INTERVAL 10 MINUTE
        """), {"cid": cid, "today": today_iso})

    await db_main.commit()


async def _build_cards(
    cid: int,
    db: AsyncSession,
    db_temp: AsyncSession,
    printer_ids_filter: list,
) -> list:
    """Genera tarjetas de cocina para la empresa, filtradas por impresoras."""
    today = _today()
    await _cleanup_zombie_orders(cid, db, db_temp)

    all_printers = (await db.execute(text(
        "SELECT id, name FROM pos_printers WHERE company_id=:cid AND is_active=1 ORDER BY id"
    ), {"cid": cid})).mappings().all()
    printer_map: dict = {
        int(p["id"]): {"printer_id": int(p["id"]), "printer_name": p["name"]}
        for p in all_printers
    }
    if printer_ids_filter:
        printer_map = {k: v for k, v in printer_map.items() if k in printer_ids_filter}
    if not printer_map:
        return []

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

    # Red de seguridad: excluir órdenes ya facturadas en pos_invoice_details
    # aunque el cleanup no haya corrido aún en este ciclo.
    raw_order_numbers = list({r["Nro_Pedido"] for r in order_rows})
    invoiced_set: set = set()
    if raw_order_numbers:
        on_q = ",".join(f"'{o}'" for o in raw_order_numbers)
        inv_check = (await db.execute(text(f"""
            SELECT DISTINCT order_number FROM pos_invoice_details
            WHERE company_id=:cid AND order_number IN ({on_q})
        """), {"cid": cid})).fetchall()
        invoiced_set = {r[0] for r in inv_check}
    if invoiced_set:
        order_rows = [r for r in order_rows if r["Nro_Pedido"] not in invoiced_set]

    dish_ids      = list({int(r["Id_Plato"]) for r in order_rows})
    order_numbers = list({r["Nro_Pedido"] for r in order_rows})
    waiter_ids    = list({int(r["Mesero"]) for r in order_rows if r["Mesero"]})

    dish_info: dict = {}
    if dish_ids:
        id_list = ",".join(str(d) for d in dish_ids)
        drows = (await db.execute(text(
            f"SELECT id, name, preparation_time FROM pos_dishes "
            f"WHERE company_id=:cid AND id IN ({id_list})"
        ), {"cid": cid})).mappings().all()
        dish_info = {int(r["id"]): {"name": r["name"], "no_print": bool(r["preparation_time"])} for r in drows}

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

    waiter_names: dict = {}
    if waiter_ids:
        wrows = (await db.execute(text(
            f"SELECT id, name FROM pos_waiters WHERE company_id=:cid "
            f"AND id IN ({','.join(str(w) for w in waiter_ids)})"
        ), {"cid": cid})).mappings().all()
        waiter_names = {int(r["id"]): r["name"] for r in wrows}

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

    order_first_hora: dict = {}
    for r in order_rows:
        on = r["Nro_Pedido"]
        if on not in order_first_hora:
            order_first_hora[on] = str(r["Hora"] or "")
    daily_seq_map = {on: i+1 for i, on in enumerate(sorted(order_first_hora, key=order_first_hora.get))}

    batch_items: dict = {}
    batch_meta: dict  = {}

    for row in order_rows:
        on  = row["Nro_Pedido"]
        did = int(row["Id_Plato"])
        if dish_info.get(did, {}).get("no_print"): continue
        if on in dispatched_set: continue
        printers_for_dish = printer_for_dish.get(did, [])
        active_printers = [p for p in printers_for_dish if p in printer_map]
        if not active_printers: continue

        movil  = int(row["Movil"] or 0)
        hp_raw = str(row["Hora_Plato"] or "")
        hp     = hp_raw if movil == 1 else hp_raw[:5]
        key    = (on, hp)

        if key not in batch_meta:
            wid = int(row["Mesero"] or 0)
            batch_meta[key] = {
                "mesa": str(row["Mesa"] or ""), "order_hora": str(row["Hora"] or ""),
                "waiter_name": waiter_names.get(wid), "printers": set(),
                "max_hp": str(row["Hora_Plato"] or ""),
            }
        else:
            cur_hp = str(row["Hora_Plato"] or "")
            if cur_hp > batch_meta[key]["max_hp"]:
                batch_meta[key]["max_hp"] = cur_hp
        batch_meta[key]["printers"].update(active_printers)

        assembly = []
        if row["Producto_Personalizado"]:
            try: assembly = json.loads(row["Producto_Personalizado"]).get("assembly", [])
            except Exception: pass

        batch_items.setdefault(key, []).append({
            "dish_id": did, "item": int(row["Item"]),
            "dish_name": dish_info.get(did, {}).get("name", f"Plato {did}"),
            "quantity": float(row["Cantidad"] or 0),
            "notes": row["Novedad"], "changes": row["Cambios"],
            "assembly": assembly, "hora_tomado": str(row["Hora_Tomado"] or ""),
        })

    min_sk_per_printer_order: dict = {}
    for (on, hp), meta in batch_meta.items():
        sk = _hp_sort_key(hp)
        for item_data in batch_items.get((on, hp), []):
            for pid in printer_for_dish.get(item_data["dish_id"], []):
                if pid in meta["printers"]:
                    pkey = (pid, on)
                    if pkey not in min_sk_per_printer_order or sk < min_sk_per_printer_order[pkey][0]:
                        min_sk_per_printer_order[pkey] = (sk, hp)

    all_cards: list = []
    for key, meta in batch_meta.items():
        on, hp = key
        display_hp = meta.get("max_hp") or hp
        items_by_printer: dict = {}
        for item_data in batch_items.get(key, []):
            for pid in printer_for_dish.get(item_data["dish_id"], []):
                if pid in meta["printers"]:
                    items_by_printer.setdefault(pid, []).append(item_data)

        for pid in meta["printers"]:
            if pid not in printer_map: continue
            pid_items = items_by_printer.get(pid, [])
            if not pid_items: continue

            pkey = (pid, on)
            min_entry = min_sk_per_printer_order.get(pkey)
            event_type = "nuevo" if (min_entry is None or hp == min_entry[1]) else "agregado"

            grouped: dict = {}
            for it in pid_items:
                gkey = (it["dish_id"], (it.get("notes") or "").strip(), (it.get("changes") or "").strip())
                if gkey in grouped: grouped[gkey]["quantity"] += it["quantity"]
                else: grouped[gkey] = dict(it)
            pid_items = list(grouped.values())

            all_cards.append({"printer_id": pid, "card": {
                "order_number": on, "event_type": event_type,
                "daily_seq": daily_seq_map.get(on, 0),
                "table_name": meta["mesa"], "order_hora": meta["order_hora"],
                "waiter_name": meta["waiter_name"], "latest_dish_time": display_hp,
                "bill_requested": False, "items": pid_items,
            }})

    # Eventos efímeros
    event_rows = (await db.execute(text("""
        SELECT id, event_type, order_number, table_name, waiter_id, items_snapshot, created_at
        FROM pos_kitchen_events
        WHERE company_id=:cid AND event_date=:today
          AND NOT (event_type = 'cancelado' AND created_at < NOW() - INTERVAL 2 MINUTE)
        ORDER BY created_at ASC
    """), {"cid": cid, "today": today})).mappings().all()

    if event_rows:
        ev_dish_ids: set = set()
        for ev in event_rows:
            if ev["items_snapshot"]:
                try:
                    for it in json.loads(ev["items_snapshot"]):
                        if "dish_id" in it: ev_dish_ids.add(int(it["dish_id"]))
                except Exception: pass
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

        ev_waiter_ids = {int(r["waiter_id"]) for r in event_rows if r["waiter_id"]} - set(waiter_names.keys())
        if ev_waiter_ids:
            wrows2 = (await db.execute(text(
                f"SELECT id, name FROM pos_waiters WHERE company_id=:cid "
                f"AND id IN ({','.join(str(w) for w in ev_waiter_ids)})"
            ), {"cid": cid})).mappings().all()
            for wr in wrows2: waiter_names[int(wr["id"])] = wr["name"]

        for ev in event_rows:
            items_snap = []
            if ev["items_snapshot"]:
                try:
                    items_snap = json.loads(ev["items_snapshot"])
                    for it in items_snap:
                        it.setdefault("assembly", []); it.setdefault("changes", None)
                        it.setdefault("hora_tomado", ""); it.setdefault("item", 0)
                except Exception: pass
            ev_printers: set = set()
            for it in items_snap:
                ev_printers.update(printer_for_dish.get(int(it.get("dish_id", 0)), []))
            if not ev_printers: ev_printers = set(printer_map.keys())
            ev_printers &= set(printer_map.keys())
            wid = int(ev["waiter_id"] or 0)
            card = {
                "order_number": str(ev["order_number"]), "event_type": ev["event_type"],
                "event_id": int(ev["id"]),
                "daily_seq": daily_seq_map.get(str(ev["order_number"])),
                "table_name": str(ev["table_name"] or ""), "order_hora": "",
                "waiter_name": waiter_names.get(wid),
                "latest_dish_time": str(ev["created_at"]),
                "bill_requested": False, "items": items_snap,
            }
            for pid in ev_printers:
                if pid in printer_map: all_cards.append({"printer_id": pid, "card": card})

    result = []
    for pid in sorted(printer_map.keys()):
        pdata = printer_map[pid]
        cards = sorted(
            [c["card"] for c in all_cards if c["printer_id"] == pid],
            key=lambda x: _hp_sort_key(x["latest_dish_time"]),
            reverse=True,
        )
        result.append({"printer_id": pdata["printer_id"], "printer_name": pdata["printer_name"], "orders": cards})
    return result


# ══════════════════════════════════════════════════════════════════
# ADMIN: gestión de pantallas
# ══════════════════════════════════════════════════════════════════

class ScreenCreate(BaseModel):
    name: str
    printer_ids: Optional[List[int]] = None

class ScreenUpdate(BaseModel):
    name: Optional[str] = None
    printer_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None

class ActivateBody(BaseModel):
    code: str
    device_name: Optional[str] = "TV"


@router.get("/screens")
async def list_screens(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_admin_user(authorization, db)
    cid = user.company_id

    screens = (await db.execute(text("""
        SELECT s.id, s.name, s.screen_code, s.printer_ids, s.is_active, s.created_at
        FROM tv_screens s WHERE s.company_id = :cid ORDER BY s.created_at
    """), {"cid": cid})).mappings().all()

    result = []
    for s in screens:
        devices = (await db.execute(text("""
            SELECT id, device_name, activated_at, last_seen, is_active
            FROM tv_screen_devices WHERE screen_id=:sid ORDER BY activated_at DESC
        """), {"sid": s["id"]})).mappings().all()
        result.append({
            "id": s["id"], "name": s["name"], "screen_code": s["screen_code"],
            "printer_ids": json.loads(s["printer_ids"]) if s["printer_ids"] else [],
            "is_active": bool(s["is_active"]),
            "created_at": str(s["created_at"]),
            "url": f"/tv/{s['screen_code']}",
            "devices": [dict(d) for d in devices],
        })

    printers = (await db.execute(text(
        "SELECT id, name FROM pos_printers WHERE company_id=:cid AND is_active=1 ORDER BY name"
    ), {"cid": cid})).mappings().all()

    return {"screens": result, "printers": [dict(p) for p in printers]}


@router.post("/screens")
async def create_screen(
    body: ScreenCreate,
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_admin_user(authorization, db)
    cid = user.company_id

    while True:
        code = secrets.token_urlsafe(6)
        existing = (await db.execute(
            text("SELECT id FROM tv_screens WHERE screen_code=:code"), {"code": code}
        )).first()
        if not existing: break

    await db.execute(text("""
        INSERT INTO tv_screens (company_id, name, screen_code, printer_ids)
        VALUES (:cid, :name, :code, :pids)
    """), {"cid": cid, "name": body.name.strip(), "code": code,
           "pids": json.dumps(body.printer_ids or [])})
    await db.commit()
    return {"screen_code": code, "url": f"/tv/{code}", "message": "Pantalla creada"}


@router.put("/screens/{screen_id}")
async def update_screen(
    screen_id: int,
    body: ScreenUpdate,
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_admin_user(authorization, db)
    cid = user.company_id

    screen = (await db.execute(
        text("SELECT id FROM tv_screens WHERE id=:sid AND company_id=:cid"),
        {"sid": screen_id, "cid": cid}
    )).first()
    if not screen:
        raise HTTPException(status_code=404, detail="Pantalla no encontrada")

    updates, params = [], {"sid": screen_id}
    if body.name is not None:
        updates.append("name=:name"); params["name"] = body.name.strip()
    if body.printer_ids is not None:
        updates.append("printer_ids=:pids"); params["pids"] = json.dumps(body.printer_ids)
    if body.is_active is not None:
        updates.append("is_active=:ia"); params["ia"] = 1 if body.is_active else 0

    if updates:
        await db.execute(text(f"UPDATE tv_screens SET {', '.join(updates)} WHERE id=:sid"), params)
        await db.commit()
    return {"message": "Pantalla actualizada"}


@router.delete("/screens/{screen_id}")
async def delete_screen(
    screen_id: int,
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_admin_user(authorization, db)
    cid = user.company_id
    await db.execute(text("DELETE FROM tv_screens WHERE id=:sid AND company_id=:cid"),
                     {"sid": screen_id, "cid": cid})
    await db.commit()
    return {"message": "Pantalla eliminada"}


@router.delete("/screens/{screen_id}/devices/{device_id}")
async def revoke_device(
    screen_id: int, device_id: int,
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_admin_user(authorization, db)
    cid = user.company_id
    screen = (await db.execute(
        text("SELECT id FROM tv_screens WHERE id=:sid AND company_id=:cid"),
        {"sid": screen_id, "cid": cid}
    )).first()
    if not screen:
        raise HTTPException(status_code=404, detail="Pantalla no encontrada")
    await db.execute(text(
        "UPDATE tv_screen_devices SET is_active=0 WHERE id=:did AND screen_id=:sid"
    ), {"did": device_id, "sid": screen_id})
    await db.commit()
    return {"message": "Dispositivo revocado"}


@router.post("/activate")
async def activate_device(
    body: ActivateBody,
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_admin_user(authorization, db)
    cid = user.company_id

    session = (await db.execute(text("""
        SELECT ts.id, ts.screen_id, ts.poll_token
        FROM tv_sessions ts
        JOIN tv_screens s ON s.id = ts.screen_id
        WHERE ts.activation_code = :code
          AND ts.expires_at > NOW()
          AND ts.device_token IS NULL
          AND s.company_id = :cid
        ORDER BY ts.created_at DESC LIMIT 1
    """), {"code": body.code.strip(), "cid": cid})).mappings().first()

    if not session:
        raise HTTPException(status_code=400, detail="Código inválido, ya usado o expirado")

    device_token = secrets.token_hex(32)

    await db.execute(text("""
        INSERT INTO tv_screen_devices (screen_id, device_token, device_name, activated_at)
        VALUES (:sid, :tok, :dname, NOW())
    """), {"sid": session["screen_id"], "tok": device_token,
           "dname": (body.device_name or "TV").strip()})

    await db.execute(text(
        "UPDATE tv_sessions SET device_token=:tok WHERE id=:id"
    ), {"tok": device_token, "id": session["id"]})

    await db.commit()
    return {"message": "Dispositivo activado"}


# ══════════════════════════════════════════════════════════════════
# TV: endpoints públicos (autenticados por device_token)
# ══════════════════════════════════════════════════════════════════

@router.get("/{code}/init")
async def tv_init(
    code: str,
    device_token: str = Query(default=""),
    poll_token:   str = Query(default=""),
    db: AsyncSession = Depends(get_db),
):
    screen = (await db.execute(text("""
        SELECT id, company_id, name, printer_ids
        FROM tv_screens WHERE screen_code=:code AND is_active=1
    """), {"code": code})).mappings().first()
    if not screen:
        raise HTTPException(status_code=404, detail="Pantalla no encontrada")

    # Dispositivo ya activado
    if device_token:
        device = (await db.execute(text("""
            SELECT id FROM tv_screen_devices
            WHERE screen_id=:sid AND device_token=:tok AND is_active=1
        """), {"sid": screen["id"], "tok": device_token})).first()
        if device:
            await db.execute(text(
                "UPDATE tv_screen_devices SET last_seen=NOW() WHERE id=:id"
            ), {"id": device[0]})
            await db.commit()
            return {
                "status": "active",
                "screen_name": screen["name"],
                "printer_ids": json.loads(screen["printer_ids"]) if screen["printer_ids"] else [],
            }

    # Verificar si la sesión fue activada por el admin
    if poll_token:
        sess = (await db.execute(text("""
            SELECT id, activation_code, device_token
            FROM tv_sessions
            WHERE poll_token=:pt AND screen_id=:sid AND expires_at > NOW()
        """), {"pt": poll_token, "sid": screen["id"]})).mappings().first()

        if sess:
            if sess["device_token"]:
                return {"status": "just_activated", "device_token": sess["device_token"],
                        "screen_name": screen["name"]}
            # Aún pendiente — devolver mismo código
            return {"status": "pending", "activation_code": sess["activation_code"],
                    "poll_token": poll_token, "screen_name": screen["name"], "expires_minutes": 10}

    # Generar nueva sesión (nuevo código de 4 dígitos)
    await db.execute(text(
        "DELETE FROM tv_sessions WHERE screen_id=:sid AND expires_at < NOW()"
    ), {"sid": screen["id"]})

    activation_code = f"{random.randint(0, 9999):04d}"
    new_poll_token  = secrets.token_urlsafe(16)
    expires_at      = datetime.utcnow() + timedelta(minutes=10)

    await db.execute(text("""
        INSERT INTO tv_sessions (screen_id, poll_token, activation_code, expires_at)
        VALUES (:sid, :pt, :ac, :exp)
    """), {"sid": screen["id"], "pt": new_poll_token, "ac": activation_code, "exp": expires_at})
    await db.commit()

    return {"status": "pending", "activation_code": activation_code, "poll_token": new_poll_token,
            "screen_name": screen["name"], "expires_minutes": 10}


@router.get("/{code}/cards")
async def tv_cards(
    code: str,
    device_token: str = Query(...),
    db: AsyncSession = Depends(get_datatemppos_db),   # alias local
    db_main: AsyncSession = Depends(get_db),
):
    screen = (await db_main.execute(text("""
        SELECT id, company_id, name, printer_ids
        FROM tv_screens WHERE screen_code=:code AND is_active=1
    """), {"code": code})).mappings().first()
    if not screen:
        raise HTTPException(status_code=404, detail="Pantalla no encontrada")

    device = (await db_main.execute(text("""
        SELECT id FROM tv_screen_devices
        WHERE screen_id=:sid AND device_token=:tok AND is_active=1
    """), {"sid": screen["id"], "tok": device_token})).first()
    if not device:
        raise HTTPException(status_code=401, detail="Dispositivo no autorizado")

    await db_main.execute(text(
        "UPDATE tv_screen_devices SET last_seen=NOW() WHERE id=:id"
    ), {"id": device[0]})
    await db_main.commit()

    cid = screen["company_id"]
    printer_ids_filter = json.loads(screen["printer_ids"]) if screen["printer_ids"] else []

    cards = await _build_cards(cid, db_main, db, printer_ids_filter)
    refresh_token = str(_refresh_signals.get(cid, 0))

    build_row = (await db_main.execute(text(
        "SELECT config_value FROM system_config WHERE config_key='app_version' LIMIT 1"
    ))).first()
    app_build = build_row[0] if build_row else ""

    return JSONResponse(
        content={"sections": cards, "refresh_token": refresh_token, "app_build": app_build},
        headers={"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"},
    )


@router.post("/screens/force-refresh")
async def force_refresh_all_screens(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    """Fuerza el recargo de todas las pantallas TV activas de la empresa."""
    user = await _get_admin_user(authorization, db)
    _refresh_signals[user.company_id] = time.time()
    return {"message": "Señal de recarga enviada a todas las pantallas"}
