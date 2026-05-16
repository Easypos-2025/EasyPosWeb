from datetime import date, datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.database import get_db
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.user_model import User

router = APIRouter(prefix="/api/pos-catalogo/platos", tags=["POS Items"])


async def _get_user(authorization: str, db: AsyncSession) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token inválido")
    r = await db.execute(select(UserSession).where(UserSession.token == token, UserSession.is_active == True))
    if not r.scalar_one_or_none():
        raise HTTPException(status_code=401, detail="Sesión inválida")
    r = await db.execute(select(User).where(User.email == payload.get("sub")))
    user = r.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not user.company_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asignada")
    return user


# ─── Schemas ──────────────────────────────────────────────────────────────────

class ItemIn(BaseModel):
    name: str
    price: Optional[int] = 0
    category_id: Optional[int] = None
    description: Optional[str] = None
    tax: Optional[float] = 0
    active: Optional[int] = 1

class IngredientIn(BaseModel):
    supply_item_id: int       # → pos_dish_products.supplier_id
    quantity: float = 1       # → pos_dish_products.minimum_units
    unit_id: Optional[int] = None   # → pos_dish_products.measure_id
    description: Optional[str] = None

class PrintersIn(BaseModel):
    printer_ids: List[int]

class ModifierGroupIn(BaseModel):
    name: str
    is_required: Optional[int] = 0
    is_multiple: Optional[int] = 0
    min_selection: Optional[int] = 0
    max_selection: Optional[int] = 1
    sort_order: Optional[int] = 0

class ModifierOptionIn(BaseModel):
    name: str
    extra_price: Optional[float] = 0
    supply_item_id: Optional[int] = None
    quantity: Optional[float] = 1
    sort_order: Optional[int] = 0


# ─── CRUD Artículos (pos_dishes) ──────────────────────────────────────────────

@router.get("")
async def listar(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    rows = (await db.execute(text("""
        SELECT
            d.id, d.name, d.price, d.category_id, d.active,
            d.description, d.tax, d.photo_path, d.product_code,
            c.name  AS category_name,
            c.color AS category_color,
            (SELECT COUNT(*) FROM pos_dish_products dp
             WHERE dp.dish_id=d.id AND dp.company_id=d.company_id AND dp.active=1)  AS ingredient_count,
            (SELECT COUNT(*) FROM pos_item_printers ip
             WHERE ip.item_id=d.id AND ip.company_id=d.company_id)                  AS printer_count,
            cpl.precio_producto AS list_price
        FROM pos_dishes d
        LEFT JOIN pos_item_categories c
               ON c.id=d.category_id AND c.company_id=d.company_id
        LEFT JOIN pos_customer_price_list cpl
               ON cpl.id_producto=d.id AND cpl.company_id=d.company_id
              AND cpl.id_lista=0 AND cpl.id_cliente=0
        WHERE d.company_id=:cid
        ORDER BY c.name, d.name
    """), {"cid": user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.post("", status_code=201)
async def crear(data: ItemIn, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    cid = user.company_id
    today = date.today().isoformat()

    # Siguiente ID disponible para la empresa (pos_dishes no tiene auto-increment)
    max_id = (await db.execute(text(
        "SELECT COALESCE(MAX(id), 0) FROM pos_dishes WHERE company_id=:cid"
    ), {"cid": cid})).scalar() or 0
    new_id = int(max_id) + 1

    await db.execute(text("""
        INSERT INTO pos_dishes
            (id, name, price, category_id, description, tax, active,
             product_code, synced, company_id, updated_at)
        VALUES
            (:id, :name, :price, :cat, :desc, :tax, :active,
             :code, 0, :cid, NOW())
    """), {
        "id": new_id, "name": data.name, "price": data.price,
        "cat": data.category_id, "desc": data.description,
        "tax": data.tax, "active": data.active,
        "code": f"WEB-{new_id}", "cid": cid,
    })

    # Auto-insertar en lista de precios general
    await db.execute(text("""
        INSERT INTO pos_customer_price_list
            (id_lista, id_cliente, id_producto, id_presentacion,
             precio_producto, fecha, activa, company_id)
        VALUES (0, 0, :id, NULL, :precio, :fecha, 1, :cid)
        ON DUPLICATE KEY UPDATE
            precio_producto=VALUES(precio_producto), activa=1, updated_at=NOW()
    """), {"id": new_id, "precio": data.price, "fecha": today, "cid": cid})

    await db.commit()
    return {"ok": True, "id": new_id}


@router.put("/{item_id}")
async def actualizar(
    item_id: int, data: ItemIn,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    cid = user.company_id

    await db.execute(text("""
        UPDATE pos_dishes
        SET name=:name, price=:price, category_id=:cat,
            description=:desc, tax=:tax, active=:active, updated_at=NOW()
        WHERE id=:id AND company_id=:cid
    """), {"id": item_id, "cid": cid, "name": data.name, "price": data.price,
           "cat": data.category_id, "desc": data.description,
           "tax": data.tax, "active": data.active})

    # Sync precio en lista general
    await db.execute(text("""
        UPDATE pos_customer_price_list
        SET precio_producto=:precio, fecha=:fecha, updated_at=NOW()
        WHERE id_producto=:id AND id_lista=0 AND id_cliente=0 AND company_id=:cid
    """), {"id": item_id, "precio": data.price,
           "fecha": date.today().isoformat(), "cid": cid})

    await db.commit()
    return {"ok": True}


@router.delete("/{item_id}")
async def eliminar(item_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    await db.execute(text(
        "UPDATE pos_dishes SET active=0, updated_at=NOW() WHERE id=:id AND company_id=:cid"
    ), {"id": item_id, "cid": user.company_id})
    await db.execute(text(
        "UPDATE pos_customer_price_list SET activa=0 WHERE id_producto=:id AND company_id=:cid"
    ), {"id": item_id, "cid": user.company_id})
    await db.commit()
    return {"ok": True}


# ─── Ingredientes / Receta (pos_dish_products) ────────────────────────────────
# pos_dish_products: dish_id, supplier_id(=insumo), measure_id, minimum_units, description

@router.get("/{item_id}/ingredientes")
async def get_ingredientes(item_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    rows = (await db.execute(text("""
        SELECT
            dp.supplier_id  AS insumo_id,
            dp.minimum_units AS cantidad,
            dp.measure_id   AS unit_id,
            dp.description,
            dp.active,
            s.name          AS insumo_nombre,
            s.code          AS insumo_code,
            mu.name         AS unit_nombre,
            mu.abreviatura  AS unit_abrev
        FROM pos_dish_products dp
        JOIN supply_items s ON s.id = dp.supplier_id
        LEFT JOIN measurement_units mu ON mu.id = dp.measure_id
        WHERE dp.dish_id=:pid AND dp.company_id=:cid AND dp.active=1
        ORDER BY s.name
    """), {"pid": item_id, "cid": user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.post("/{item_id}/ingredientes", status_code=201)
async def add_ingrediente(
    item_id: int, data: IngredientIn,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    await db.execute(text("""
        INSERT INTO pos_dish_products
            (dish_id, supplier_id, measure_id, minimum_units, description, active, synced, company_id)
        VALUES (:dish, :sup, :measure, :qty, :desc, 1, 0, :cid)
        ON DUPLICATE KEY UPDATE
            minimum_units=VALUES(minimum_units),
            measure_id=VALUES(measure_id),
            description=VALUES(description),
            active=1
    """), {
        "dish": item_id, "sup": data.supply_item_id,
        "measure": data.unit_id or 0, "qty": data.quantity,
        "desc": data.description or "", "cid": user.company_id,
    })
    await db.commit()
    return {"ok": True}


@router.delete("/{item_id}/ingredientes/{insumo_id}")
async def del_ingrediente(
    item_id: int, insumo_id: int,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    await db.execute(text("""
        UPDATE pos_dish_products SET active=0
        WHERE dish_id=:dish AND supplier_id=:sup AND company_id=:cid
    """), {"dish": item_id, "sup": insumo_id, "cid": user.company_id})
    await db.commit()
    return {"ok": True}


# ─── Impresoras del artículo (pos_item_printers) ──────────────────────────────

@router.get("/{item_id}/impresoras")
async def get_impresoras(item_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    rows = (await db.execute(text("""
        SELECT p.id, p.name, p.connection_type, p.ip,
               CASE WHEN ip.id IS NOT NULL THEN 1 ELSE 0 END AS assigned
        FROM pos_printers p
        LEFT JOIN pos_item_printers ip
               ON ip.printer_id=p.id AND ip.item_id=:iid AND ip.company_id=:cid
        WHERE p.company_id=:cid AND p.is_active=1
        ORDER BY p.name
    """), {"iid": item_id, "cid": user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.put("/{item_id}/impresoras")
async def set_impresoras(
    item_id: int, data: PrintersIn,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    cid = user.company_id
    await db.execute(text(
        "DELETE FROM pos_item_printers WHERE item_id=:iid AND company_id=:cid"
    ), {"iid": item_id, "cid": cid})
    for pid in data.printer_ids:
        await db.execute(text(
            "INSERT IGNORE INTO pos_item_printers (company_id, item_id, printer_id) VALUES (:cid,:iid,:pid)"
        ), {"cid": cid, "iid": item_id, "pid": pid})
    await db.commit()
    return {"ok": True}


# ─── Modificadores (pos_item_modifiers + pos_item_modifier_options) ───────────

@router.get("/{item_id}/modificadores")
async def get_modificadores(item_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    groups = (await db.execute(text("""
        SELECT * FROM pos_item_modifiers
        WHERE item_id=:iid AND company_id=:cid AND is_active=1
        ORDER BY sort_order, id
    """), {"iid": item_id, "cid": user.company_id})).mappings().all()
    result = []
    for g in groups:
        options = (await db.execute(text("""
            SELECT o.*, s.name AS supply_name
            FROM pos_item_modifier_options o
            LEFT JOIN supply_items s ON s.id=o.supply_item_id
            WHERE o.modifier_id=:mid AND o.company_id=:cid AND o.is_active=1
            ORDER BY o.sort_order, o.id
        """), {"mid": g["id"], "cid": user.company_id})).mappings().all()
        row = dict(g)
        row["options"] = [dict(o) for o in options]
        result.append(row)
    return result


@router.post("/{item_id}/modificadores", status_code=201)
async def crear_modificador(
    item_id: int, data: ModifierGroupIn,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    await db.execute(text("""
        INSERT INTO pos_item_modifiers
            (company_id, item_id, name, is_required, is_multiple,
             min_selection, max_selection, sort_order)
        VALUES (:cid,:iid,:name,:req,:mul,:min,:max,:ord)
    """), {"cid": user.company_id, "iid": item_id, "name": data.name,
           "req": data.is_required, "mul": data.is_multiple,
           "min": data.min_selection, "max": data.max_selection, "ord": data.sort_order})
    await db.commit()
    row = (await db.execute(text(
        "SELECT * FROM pos_item_modifiers WHERE company_id=:cid AND item_id=:iid ORDER BY id DESC LIMIT 1"
    ), {"cid": user.company_id, "iid": item_id})).mappings().one()
    return dict(row)


@router.delete("/{item_id}/modificadores/{mod_id}")
async def eliminar_modificador(
    item_id: int, mod_id: int,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    await db.execute(text(
        "UPDATE pos_item_modifiers SET is_active=0 WHERE id=:id AND item_id=:iid AND company_id=:cid"
    ), {"id": mod_id, "iid": item_id, "cid": user.company_id})
    await db.execute(text(
        "UPDATE pos_item_modifier_options SET is_active=0 WHERE modifier_id=:mid AND company_id=:cid"
    ), {"mid": mod_id, "cid": user.company_id})
    await db.commit()
    return {"ok": True}


@router.post("/{item_id}/modificadores/{mod_id}/opciones", status_code=201)
async def crear_opcion(
    item_id: int, mod_id: int, data: ModifierOptionIn,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    await db.execute(text("""
        INSERT INTO pos_item_modifier_options
            (company_id, modifier_id, name, extra_price, supply_item_id, quantity, sort_order)
        VALUES (:cid,:mid,:name,:price,:sid,:qty,:ord)
    """), {"cid": user.company_id, "mid": mod_id, "name": data.name,
           "price": data.extra_price, "sid": data.supply_item_id,
           "qty": data.quantity, "ord": data.sort_order})
    await db.commit()
    return {"ok": True}


@router.delete("/{item_id}/modificadores/{mod_id}/opciones/{opt_id}")
async def eliminar_opcion(
    item_id: int, mod_id: int, opt_id: int,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    await db.execute(text(
        "UPDATE pos_item_modifier_options SET is_active=0 "
        "WHERE id=:id AND modifier_id=:mid AND company_id=:cid"
    ), {"id": opt_id, "mid": mod_id, "cid": user.company_id})
    await db.commit()
    return {"ok": True}
