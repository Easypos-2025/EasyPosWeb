import io
import uuid
from datetime import date, datetime, timezone, timedelta

_BOG = timezone(timedelta(hours=-5))
def _today() -> str:
    return datetime.now(_BOG).date().isoformat()
from typing import Optional, List

from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, File
from PIL import Image
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.database import get_db
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.user_model import User
from app.utils.storage import upload_file, delete_file

router = APIRouter(prefix="/api/pos-catalogo/platos", tags=["POS Items"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


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
    uid = payload.get("user_id")
    user = await db.get(User, int(uid)) if uid else None
    if not user:
        r = await db.execute(select(User).where(User.email == payload.get("sub")))
        user = r.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not user.company_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asignada")
    return user


def _process_image(content: bytes) -> bytes:
    """Redimensiona y recorta la imagen a 800x800 WebP centrado."""
    img = Image.open(io.BytesIO(content)).convert("RGB")
    w, h = img.size
    # Escalar para que el lado corto sea 800px
    scale = 800 / min(w, h)
    new_w, new_h = int(w * scale), int(h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    # Recorte central 800x800
    left = (new_w - 800) // 2
    top  = (new_h - 800) // 2
    img  = img.crop((left, top, left + 800, top + 800))
    out  = io.BytesIO()
    img.save(out, format="WEBP", quality=85)
    return out.getvalue()


# ─── Schemas ──────────────────────────────────────────────────────────────────

class ItemIn(BaseModel):
    name: str
    price: Optional[int] = 0
    compare_price: Optional[int] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    tax: Optional[float] = 0
    active: Optional[int] = 1

class IngredientIn(BaseModel):
    supply_item_id: int
    quantity: float = 1
    unit_id: Optional[int] = None
    description: Optional[str] = None

class PrinterAssignIn(BaseModel):
    printer_id: int
    print_copies: int = 1

class PrintersIn(BaseModel):
    printers: List[PrinterAssignIn]

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

class VariantIn(BaseModel):
    name: str
    price: int = 0
    compare_price: Optional[int] = None
    order_index: Optional[int] = 0

class OrderIn(BaseModel):
    ids: List[int]


# ─── CRUD Artículos ────────────────────────────────────────────────────────────

@router.get("")
async def listar(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    rows = (await db.execute(text("""
        SELECT
            d.id, d.name, d.price, d.compare_price, d.category_id, d.active,
            d.description, d.tax, d.photo_path, d.product_code,
            COALESCE(d.order_index, 0) AS order_index,
            c.name  AS category_name,
            NULL    AS category_color,
            0       AS category_order,
            (SELECT COUNT(*) FROM pos_dish_products dp
             WHERE dp.dish_id=d.id AND dp.company_id=d.company_id AND dp.active=1)   AS ingredient_count,
            (SELECT COUNT(*) FROM pos_item_printers ip
             WHERE ip.item_id=d.id AND ip.company_id=d.company_id)                   AS printer_count,
            (SELECT COUNT(*) FROM pos_item_modifiers m
             WHERE m.item_id=d.id AND m.company_id=d.company_id AND m.is_active=1)   AS modifier_count,
            (SELECT COUNT(*) FROM pos_dish_variants v
             WHERE v.dish_id=d.id AND v.company_id=d.company_id AND v.is_active=1)   AS variant_count,
            cpl.precio_producto AS list_price
        FROM pos_dishes d
        LEFT JOIN pos_dish_categories c
               ON c.id=d.category_id AND c.company_id=d.company_id
        LEFT JOIN pos_customer_price_list cpl
               ON cpl.id_producto=d.id AND cpl.company_id=d.company_id
              AND cpl.id_lista=0 AND cpl.id_cliente=0
        WHERE d.company_id=:cid
        ORDER BY c.name, COALESCE(d.order_index,0), d.name
    """), {"cid": user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.post("", status_code=201)
async def crear(data: ItemIn, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    cid  = user.company_id
    today = _today()

    max_id = (await db.execute(text(
        "SELECT COALESCE(MAX(id), 0) FROM pos_dishes WHERE company_id=:cid"
    ), {"cid": cid})).scalar() or 0
    new_id = int(max_id) + 1

    await db.execute(text("""
        INSERT INTO pos_dishes
            (id, name, price, compare_price, category_id, description,
             tax, active, product_code, synced, company_id, updated_at)
        VALUES
            (:id, :name, :price, :cp, :cat, :desc,
             :tax, :active, :code, 0, :cid, NOW())
    """), {
        "id": new_id, "name": data.name, "price": data.price, "cp": data.compare_price,
        "cat": data.category_id, "desc": data.description,
        "tax": data.tax, "active": data.active,
        "code": f"WEB-{new_id}", "cid": cid,
    })

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


# PUT /orden debe ir ANTES de PUT /{item_id} para no ser capturado como parámetro
@router.put("/orden")
async def actualizar_orden(data: OrderIn, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    for idx, item_id in enumerate(data.ids):
        await db.execute(text(
            "UPDATE pos_dishes SET order_index=:ord WHERE id=:id AND company_id=:cid"
        ), {"ord": idx, "id": item_id, "cid": user.company_id})
    await db.commit()
    return {"ok": True}


@router.put("/{item_id}")
async def actualizar(
    item_id: int, data: ItemIn,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    cid  = user.company_id

    await db.execute(text("""
        UPDATE pos_dishes
        SET name=:name, price=:price, compare_price=:cp, category_id=:cat,
            description=:desc, tax=:tax, active=:active, updated_at=NOW()
        WHERE id=:id AND company_id=:cid
    """), {"id": item_id, "cid": cid, "name": data.name, "price": data.price,
           "cp": data.compare_price, "cat": data.category_id,
           "desc": data.description, "tax": data.tax, "active": data.active})

    await db.execute(text("""
        UPDATE pos_customer_price_list
        SET precio_producto=:precio, fecha=:fecha, updated_at=NOW()
        WHERE id_producto=:id AND id_lista=0 AND id_cliente=0 AND company_id=:cid
    """), {"id": item_id, "precio": data.price,
           "fecha": _today(), "cid": cid})

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


# ─── Foto (photo_path) ────────────────────────────────────────────────────────

@router.post("/{item_id}/foto")
async def upload_foto(
    item_id: int,
    file: UploadFile = File(...),
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(authorization, db)
    cid  = user.company_id

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de archivo no permitido")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Imagen demasiado grande (máx 10 MB)")

    webp_bytes = _process_image(content)

    # Eliminar foto anterior si existe
    old_path = (await db.execute(text(
        "SELECT photo_path FROM pos_dishes WHERE id=:id AND company_id=:cid"
    ), {"id": item_id, "cid": cid})).scalar_one_or_none()
    if old_path:
        await delete_file(old_path)

    filename = f"dishes/{cid}/{item_id}_{uuid.uuid4().hex[:8]}.webp"
    url = await upload_file(webp_bytes, filename)

    await db.execute(text(
        "UPDATE pos_dishes SET photo_path=:url, updated_at=NOW() WHERE id=:id AND company_id=:cid"
    ), {"url": url, "id": item_id, "cid": cid})
    await db.commit()
    return {"ok": True, "url": url}


@router.delete("/{item_id}/foto")
async def delete_foto(item_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    cid  = user.company_id
    old_path = (await db.execute(text(
        "SELECT photo_path FROM pos_dishes WHERE id=:id AND company_id=:cid"
    ), {"id": item_id, "cid": cid})).scalar_one_or_none()
    if old_path:
        await delete_file(old_path)
    await db.execute(text(
        "UPDATE pos_dishes SET photo_path=NULL, updated_at=NOW() WHERE id=:id AND company_id=:cid"
    ), {"id": item_id, "cid": cid})
    await db.commit()
    return {"ok": True}


# ─── Variantes de precio ───────────────────────────────────────────────────────

@router.get("/{item_id}/variantes")
async def get_variantes(item_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    rows = (await db.execute(text("""
        SELECT id, name, price, compare_price, order_index
        FROM pos_dish_variants
        WHERE dish_id=:did AND company_id=:cid AND is_active=1
        ORDER BY order_index, id
    """), {"did": item_id, "cid": user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.post("/{item_id}/variantes", status_code=201)
async def crear_variante(
    item_id: int, data: VariantIn,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    await db.execute(text("""
        INSERT INTO pos_dish_variants (company_id, dish_id, name, price, compare_price, order_index)
        VALUES (:cid, :did, :name, :price, :cp, :ord)
    """), {"cid": user.company_id, "did": item_id, "name": data.name,
           "price": data.price, "cp": data.compare_price, "ord": data.order_index})
    await db.commit()
    return {"ok": True}


@router.put("/{item_id}/variantes/{var_id}")
async def actualizar_variante(
    item_id: int, var_id: int, data: VariantIn,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    await db.execute(text("""
        UPDATE pos_dish_variants
        SET name=:name, price=:price, compare_price=:cp, order_index=:ord
        WHERE id=:id AND dish_id=:did AND company_id=:cid
    """), {"id": var_id, "did": item_id, "cid": user.company_id,
           "name": data.name, "price": data.price,
           "cp": data.compare_price, "ord": data.order_index})
    await db.commit()
    return {"ok": True}


@router.delete("/{item_id}/variantes/{var_id}")
async def eliminar_variante(
    item_id: int, var_id: int,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    await db.execute(text(
        "UPDATE pos_dish_variants SET is_active=0 WHERE id=:id AND dish_id=:did AND company_id=:cid"
    ), {"id": var_id, "did": item_id, "cid": user.company_id})
    await db.commit()
    return {"ok": True}


# ─── Ingredientes / Receta ────────────────────────────────────────────────────

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
            s.description   AS insumo_nombre,
            s.code          AS insumo_code,
            mu.name         AS unit_nombre,
            mu.abreviatura  AS unit_abrev
        FROM pos_dish_products dp
        JOIN supply_items s ON s.id = dp.supplier_id AND s.company_id = :cid
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
    valid = (await db.execute(text(
        "SELECT id FROM supply_items WHERE id=:sid AND company_id=:cid AND is_active=1"
    ), {"sid": data.supply_item_id, "cid": user.company_id})).fetchone()
    if not valid:
        raise HTTPException(status_code=400, detail="Insumo no válido para esta empresa")
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


# ─── Impresoras ───────────────────────────────────────────────────────────────

@router.get("/{item_id}/impresoras")
async def get_impresoras(item_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    rows = (await db.execute(text("""
        SELECT p.id, p.name, p.connection_type, p.ip,
               CASE WHEN ip.id IS NOT NULL THEN 1 ELSE 0 END AS assigned,
               COALESCE(ip.print_copies, 1) AS print_copies
        FROM pos_printers p
        LEFT JOIN pos_item_printers ip
               ON ip.printer_id=p.id AND ip.item_id=:iid AND ip.company_id=:cid
        WHERE p.company_id=:cid
        ORDER BY p.is_active DESC, p.name
    """), {"iid": item_id, "cid": user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.put("/{item_id}/impresoras")
async def set_impresoras(
    item_id: int, data: PrintersIn,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    cid  = user.company_id
    await db.execute(text(
        "DELETE FROM pos_item_printers WHERE item_id=:iid AND company_id=:cid"
    ), {"iid": item_id, "cid": cid})
    for p in data.printers:
        await db.execute(text(
            "INSERT IGNORE INTO pos_item_printers (company_id, item_id, printer_id, print_copies) VALUES (:cid,:iid,:pid,:copies)"
        ), {"cid": cid, "iid": item_id, "pid": p.printer_id, "copies": p.print_copies})
    await db.commit()
    return {"ok": True}


# ─── Modificadores ────────────────────────────────────────────────────────────

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


# ─── Armado VB6 (pos_dish_assembly) ──────────────────────────────────────────

@router.get("/{item_id}/armado")
async def get_armado(item_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    cid = user.company_id

    cats = None
    for sql_cats in [
        # Nivel 1: con nombre desde pos_product_categories
        """SELECT da.category_code, da.max_choices, da.is_required, da.is_active,
                  (SELECT pc.name FROM pos_product_categories pc
                   WHERE pc.id = da.category_code AND pc.company_id = :cid LIMIT 1) AS category_name
           FROM pos_dish_assembly da
           WHERE da.dish_id = :did AND da.company_id = :cid
           ORDER BY da.category_code""",
        # Nivel 2: sin nombre (fallback)
        """SELECT da.category_code, da.max_choices, da.is_required, da.is_active,
                  NULL AS category_name
           FROM pos_dish_assembly da
           WHERE da.dish_id = :did AND da.company_id = :cid
           ORDER BY da.category_code""",
    ]:
        try:
            rows = (await db.execute(text(sql_cats), {"did": item_id, "cid": cid})).mappings().all()
            cats = rows
            break
        except Exception:
            continue

    if not cats:
        return []

    result = []
    for cat in cats:
        cc = int(cat["category_code"])
        options = (await db.execute(text("""
            SELECT dad.item AS item_id, dad.discount_qty, dad.position, dad.is_default,
                   COALESCE(si.description, CONCAT('Opción ', dad.position)) AS item_name
            FROM pos_dish_assembly_detail dad
            LEFT JOIN supply_items si
                   ON si.id_item = dad.position AND si.company_id = :cid
            WHERE dad.dish_id = :did AND dad.company_id = :cid AND dad.category_code = :cc
            ORDER BY dad.position
        """), {"did": item_id, "cid": cid, "cc": cc})).mappings().all()

        result.append({
            "category_code": cc,
            "category_name": cat["category_name"] or f"Categoría {cc}",
            "max_choices":   int(cat["max_choices"] or 1),
            "is_required":   bool(cat["is_required"]),
            "is_active":     bool(cat["is_active"]),
            "options":       [dict(o) for o in options],
        })

    return result


# Lista de categorías disponibles para armado (pos_product_categories)
@router.get("/armado/categorias-disponibles")
async def get_categorias_armado(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    rows = (await db.execute(text(
        "SELECT id, name FROM pos_product_categories WHERE company_id=:cid ORDER BY name"
    ), {"cid": user.company_id})).mappings().all()
    return [{"id": int(r["id"]), "name": r["name"]} for r in rows]


class ArmadoCategoriaIn(BaseModel):
    category_code: int
    max_choices: Optional[int] = 1
    is_required: Optional[int] = 0


class ArmadoOpcionIn(BaseModel):
    position: int        # supply_items.id_item
    discount_qty: Optional[float] = 1
    is_default: Optional[int] = 0


@router.post("/{item_id}/armado/categoria", status_code=201)
async def add_armado_categoria(
    item_id: int, data: ArmadoCategoriaIn,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    cid = user.company_id
    await db.execute(text("""
        INSERT INTO pos_dish_assembly
            (dish_id, company_id, category_code, max_choices, is_required, is_active, print_on_change_only)
        VALUES (:did, :cid, :cc, :mc, :req, 1, 0)
        ON DUPLICATE KEY UPDATE
            max_choices=VALUES(max_choices), is_required=VALUES(is_required), is_active=1
    """), {"did": item_id, "cid": cid, "cc": data.category_code,
           "mc": data.max_choices, "req": data.is_required})
    await db.commit()
    return {"ok": True}


@router.delete("/{item_id}/armado/categoria/{category_code}")
async def del_armado_categoria(
    item_id: int, category_code: int,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    cid = user.company_id
    await db.execute(text(
        "DELETE FROM pos_dish_assembly_detail WHERE dish_id=:did AND company_id=:cid AND category_code=:cc"
    ), {"did": item_id, "cid": cid, "cc": category_code})
    await db.execute(text(
        "DELETE FROM pos_dish_assembly WHERE dish_id=:did AND company_id=:cid AND category_code=:cc"
    ), {"did": item_id, "cid": cid, "cc": category_code})
    await db.commit()
    return {"ok": True}


@router.post("/{item_id}/armado/categoria/{category_code}/opcion", status_code=201)
async def add_armado_opcion(
    item_id: int, category_code: int, data: ArmadoOpcionIn,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    cid = user.company_id
    max_item = (await db.execute(text(
        "SELECT COALESCE(MAX(item),0) FROM pos_dish_assembly_detail "
        "WHERE dish_id=:did AND company_id=:cid AND category_code=:cc"
    ), {"did": item_id, "cid": cid, "cc": category_code})).scalar() or 0
    new_item = int(max_item) + 1
    await db.execute(text("""
        INSERT INTO pos_dish_assembly_detail
            (dish_id, company_id, category_code, item, position, discount_qty, is_default, is_active)
        VALUES (:did, :cid, :cc, :itm, :pos, :dq, :def, 1)
    """), {"did": item_id, "cid": cid, "cc": category_code,
           "itm": new_item, "pos": data.position,
           "dq": data.discount_qty, "def": data.is_default})
    await db.commit()
    return {"ok": True, "item": new_item}


@router.delete("/{item_id}/armado/categoria/{category_code}/opcion/{position}")
async def del_armado_opcion(
    item_id: int, category_code: int, position: int,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    cid = user.company_id
    await db.execute(text(
        "DELETE FROM pos_dish_assembly_detail "
        "WHERE dish_id=:did AND company_id=:cid AND category_code=:cc AND position=:pos"
    ), {"did": item_id, "cid": cid, "cc": category_code, "pos": position})
    await db.commit()
    return {"ok": True}


@router.put("/{item_id}/armado/categoria/{category_code}/opcion/{position}")
async def update_armado_opcion(
    item_id: int, category_code: int, position: int, data: ArmadoOpcionIn,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    cid = user.company_id
    await db.execute(text("""
        UPDATE pos_dish_assembly_detail
        SET discount_qty=:dq, is_default=:def
        WHERE dish_id=:did AND company_id=:cid AND category_code=:cc AND position=:pos
    """), {"did": item_id, "cid": cid, "cc": category_code,
           "pos": position, "dq": data.discount_qty, "def": data.is_default})
    await db.commit()
    return {"ok": True}
