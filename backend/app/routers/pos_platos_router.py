import io
import uuid
from datetime import date, datetime, timezone, timedelta

_BOG = timezone(timedelta(hours=-5))

def _today() -> str:
    return datetime.now(_BOG).date().isoformat()
from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends, Header, HTTPException, Query, UploadFile, File
from PIL import Image
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.database import get_db
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.user_model import User
from app.utils.storage import upload_file, delete_file
from app.services import comanda_armado as armado_svc

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
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not user.company_id:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asignada")
    from app.auth.tenant import apply_selected_company
    return await apply_selected_company(db, user)   # empresa del topbar (validada)


async def _check_dish(db: AsyncSession, cid: int, dish_id: int) -> None:
    """Verifica que el plato exista y pertenezca a la empresa del usuario."""
    ok = (await db.execute(text(
        "SELECT 1 FROM pos_dishes WHERE id=:id AND company_id=:cid"
    ), {"id": dish_id, "cid": cid})).scalar()
    if not ok:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")


async def _get_supply(db: AsyncSession, cid: int, id_item: int):
    """Insumo activo de la empresa por id_item (= Posicion del escritorio)."""
    row = (await db.execute(text("""
        SELECT id_grupo, id_item, posicion, description
        FROM supply_items
        WHERE company_id=:cid AND id_item=:iid AND is_active=1
        LIMIT 1
    """), {"cid": cid, "iid": id_item})).mappings().first()
    if not row:
        raise HTTPException(status_code=400, detail="Insumo no válido para esta empresa")
    return row


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

Flag   = Annotated[int, Field(ge=0, le=1)]
Money  = Annotated[float, Field(ge=0, le=2_000_000_000)]
Qty    = Annotated[float, Field(gt=0, le=1_000_000)]
Name   = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=250)]
Code   = Annotated[str, StringConstraints(strip_whitespace=True, max_length=250)]
Text   = Annotated[str, StringConstraints(max_length=5000)]


# Campos de pos_dishes (= platos del escritorio). Varios son campos REUTILIZADOS:
#   wholesale_price  (Precio_x_Mayor)       → Precio Mínimo
#   pre_preparation  (Preparacion_Previa)   → Pedir Peso
#   offer            (Ofrecer)              → No Sumar en Venta
#   preparation_time (Tiempo)               → No Imprime Comanda
#   extra_print      (Impresion_Extra)      → Desactivar al Vender ('1'/'0')
#   offer_priority   (Prioridad_Ofrecer)    → Armar Producto
#   active           (Activo)               → Desactivar  (0 = activo, 1 = desactivado)
class ItemUpdate(BaseModel):
    name:                    Optional[Name]  = None
    product_code:            Optional[Code]  = None
    price:                   Optional[Annotated[int, Field(ge=0, le=2_000_000_000)]] = None
    compare_price:           Optional[Annotated[int, Field(ge=0, le=2_000_000_000)]] = None
    category_id:             Optional[int]   = None
    description:             Optional[Text]  = None
    procedure:               Optional[Text]  = None
    tax:                     Optional[Annotated[float, Field(ge=0, le=100)]] = None
    wholesale_price:         Optional[Money] = None
    product_cost:            Optional[Money] = None
    minimum_stock:           Optional[Annotated[float, Field(ge=0, le=1_000_000_000)]] = None
    ask_sale_price:          Optional[Flag]  = None
    ask_product_description: Optional[Flag]  = None
    pre_preparation:         Optional[Flag]  = None
    offer:                   Optional[Flag]  = None
    preparation_time:        Optional[Flag]  = None
    extra_print:             Optional[Flag]  = None
    offer_priority:          Optional[Flag]  = None
    active:                  Optional[Flag]  = None


class ItemIn(ItemUpdate):
    name: Name
    price: Annotated[int, Field(ge=0, le=2_000_000_000)] = 0


# Columnas editables de pos_dishes (lista blanca para el UPDATE dinámico)
_DISH_COLUMNS = (
    "name", "product_code", "price", "compare_price", "category_id", "description",
    "procedure", "tax", "wholesale_price", "product_cost", "minimum_stock",
    "ask_sale_price", "ask_product_description", "pre_preparation", "offer",
    "preparation_time", "extra_print", "offer_priority", "active",
)


class PortionIn(BaseModel):
    id_item:   Annotated[int, Field(ge=1)]
    porciones: Qty = 1


class PortionUpdate(BaseModel):
    porciones: Qty


class PresentationIn(BaseModel):
    measure_id:         Annotated[int, Field(ge=1)]
    supplier_id:        Annotated[int, Field(ge=0)] = 0
    minimum_units:      Qty = 1
    presentation_value: Money = 0


class PresentationUpdate(BaseModel):
    minimum_units:      Qty
    presentation_value: Money


class PrinterAssignIn(BaseModel):
    printer_id:   Annotated[int, Field(ge=1)]
    print_copies: Annotated[int, Field(ge=1, le=10)] = 1

class PrintersIn(BaseModel):
    printers: Annotated[List[PrinterAssignIn], Field(max_length=50)]

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
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    price: Annotated[int, Field(ge=0, le=2_000_000_000)] = 0
    compare_price: Optional[Annotated[int, Field(ge=0, le=2_000_000_000)]] = None
    order_index: Optional[int] = 0
    is_default: bool = False

class OrderIn(BaseModel):
    ids: List[int]


def _dish_params(values: dict) -> dict:
    """Normaliza valores antes de grabar en pos_dishes."""
    out = dict(values)
    if "extra_print" in out and out["extra_print"] is not None:
        out["extra_print"] = str(int(out["extra_print"]))   # columna varchar en VB6
    return out


async def _check_category(db: AsyncSession, cid: int, category_id: Optional[int]) -> None:
    if category_id is None:
        return
    ok = (await db.execute(text(
        "SELECT 1 FROM pos_dish_categories WHERE id=:id AND company_id=:cid"
    ), {"id": category_id, "cid": cid})).scalar()
    if not ok:
        raise HTTPException(status_code=400, detail="Categoría no válida para esta empresa")


async def _upsert_general_price(db: AsyncSession, cid: int, dish_id: int, price: int,
                                id_presentacion: int = 0) -> None:
    """Lista general (id_lista=0, id_cliente=0) = espejo de platos.Valor y, por variante,
    de su precio (id_presentacion = id de la variante)."""
    await db.execute(text("""
        INSERT INTO pos_customer_price_list
            (id_lista, id_cliente, id_producto, id_presentacion,
             precio_producto, fecha, activa, company_id)
        VALUES (0, 0, :id, :pres, :precio, :fecha, 1, :cid)
        ON DUPLICATE KEY UPDATE
            precio_producto=VALUES(precio_producto), fecha=VALUES(fecha), updated_at=NOW()
    """), {"id": dish_id, "pres": id_presentacion, "precio": price, "fecha": _today(), "cid": cid})


# ─── CRUD Artículos ────────────────────────────────────────────────────────────

@router.get("")
async def listar(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    rows = (await db.execute(text("""
        SELECT
            d.id, d.name, d.price, d.compare_price, d.category_id, d.active,
            d.description, d.procedure, d.tax, d.photo_path, d.product_code,
            d.wholesale_price, d.product_cost, d.minimum_stock,
            d.ask_sale_price, d.ask_product_description, d.pre_preparation,
            d.offer, d.preparation_time, d.offer_priority,
            IF(COALESCE(d.extra_print,'0') = '1', 1, 0) AS extra_print,
            COALESCE(d.order_index, 0) AS order_index,
            c.name  AS category_name,
            (SELECT COUNT(*) FROM inventario_porciones_plato ip
             WHERE ip.id_plato=d.id AND ip.company_id=d.company_id)                  AS portion_count,
            (SELECT COUNT(*) FROM pos_dish_products dp
             WHERE dp.dish_id=d.id AND dp.company_id=d.company_id)                   AS presentation_count,
            (SELECT COUNT(*) FROM pos_item_printers ip
             WHERE ip.item_id=d.id AND ip.company_id=d.company_id)                   AS printer_count,
            (SELECT COUNT(*) FROM pos_dish_assembly da
             WHERE da.dish_id=d.id AND da.company_id=d.company_id)                   AS assembly_count,
            (SELECT COUNT(*) FROM pos_dish_variants v
             WHERE v.dish_id=d.id AND v.company_id=d.company_id AND v.is_active=1)   AS variant_count
        FROM pos_dishes d
        LEFT JOIN pos_dish_categories c
               ON c.id=d.category_id AND c.company_id=d.company_id
        WHERE d.company_id=:cid
        ORDER BY c.name, COALESCE(d.order_index,0), d.name
    """), {"cid": user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.post("", status_code=201)
async def crear(data: ItemIn, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    cid  = user.company_id
    await _check_category(db, cid, data.category_id)

    max_id = (await db.execute(text(
        "SELECT COALESCE(MAX(id), 0) FROM pos_dishes WHERE company_id=:cid FOR UPDATE"
    ), {"cid": cid})).scalar() or 0
    new_id = int(max_id) + 1

    values = _dish_params({k: getattr(data, k) for k in _DISH_COLUMNS})
    for k in ("tax", "wholesale_price", "product_cost", "minimum_stock",
              "ask_sale_price", "ask_product_description", "pre_preparation",
              "offer", "preparation_time", "offer_priority", "active"):
        if values[k] is None:
            values[k] = 0            # active=0 → producto ACTIVO (convención VB6)
    if values["extra_print"] is None:
        values["extra_print"] = "0"
    if not values["product_code"]:
        values["product_code"] = f"WEB-{new_id}"

    cols = ", ".join(f"`{c}`" for c in _DISH_COLUMNS)
    phs  = ", ".join(f":{c}" for c in _DISH_COLUMNS)
    await db.execute(text(f"""
        INSERT INTO pos_dishes (id, company_id, synced, updated_at, {cols})
        VALUES (:id, :cid, 0, NOW(), {phs})
    """), {"id": new_id, "cid": cid, **values})

    await _upsert_general_price(db, cid, new_id, data.price)
    await db.commit()
    return {"ok": True, "id": new_id}


@router.put("/orden")
async def actualizar_orden(data: OrderIn, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    for idx, iid in enumerate(data.ids):
        await db.execute(text(
            "UPDATE pos_dishes SET order_index=:ord WHERE id=:id AND company_id=:cid"
        ), {"ord": idx, "id": iid, "cid": user.company_id})
    await db.commit()
    return {"ok": True}


@router.put("/{item_id}")
async def actualizar(
    item_id: int, data: ItemUpdate,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    """Actualización parcial: solo se graban los campos enviados."""
    user = await _get_user(authorization, db)
    cid  = user.company_id
    await _check_dish(db, cid, item_id)

    values = _dish_params(data.model_dump(exclude_unset=True))
    if "name" in values and not values["name"]:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")
    if "category_id" in values:
        await _check_category(db, cid, values["category_id"])
    values = {k: v for k, v in values.items() if k in _DISH_COLUMNS}
    if not values:
        return {"ok": True}

    sets = ", ".join(f"`{k}`=:{k}" for k in values)
    await db.execute(text(
        f"UPDATE pos_dishes SET {sets}, synced=0, updated_at=NOW() WHERE id=:id AND company_id=:cid"
    ), {"id": item_id, "cid": cid, **values})

    if values.get("price") is not None:
        await _upsert_general_price(db, cid, item_id, values["price"])
        # Con variantes, el precio del plato es el de la variante por defecto
        await db.execute(text("""
            UPDATE pos_dish_variants SET price=:p
            WHERE dish_id=:did AND company_id=:cid AND is_active=1 AND is_default=1
        """), {"p": values["price"], "did": item_id, "cid": cid})
        await _sync_precio_default(db, cid, item_id)

    await db.commit()
    return {"ok": True}


@router.delete("/{item_id}")
async def eliminar(item_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    """Desactivar (soft): active=1 = desactivado en la convención VB6."""
    user = await _get_user(authorization, db)
    await _check_dish(db, user.company_id, item_id)
    await db.execute(text(
        "UPDATE pos_dishes SET active=1, synced=0, updated_at=NOW() WHERE id=:id AND company_id=:cid"
    ), {"id": item_id, "cid": user.company_id})
    await db.commit()
    return {"ok": True}


@router.delete("/{item_id}/definitivo")
async def eliminar_definitivo(item_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    cid = user.company_id
    await _check_dish(db, cid, item_id)

    # Bloquear si tiene ventas facturadas
    ventas = (await db.execute(text(
        "SELECT COUNT(*) FROM pos_order_details "
        "WHERE dish_id=:id AND company_id=:cid AND invoice_number != '0'"
    ), {"id": item_id, "cid": cid})).scalar() or 0
    if int(ventas) > 0:
        raise HTTPException(status_code=409,
            detail=f"No se puede eliminar: el artículo tiene {ventas} venta(s) registrada(s) en facturas o recibos.")

    # Bloquear si tiene pedidos abiertos
    pedidos = (await db.execute(text(
        "SELECT COUNT(*) FROM pos_order_details "
        "WHERE dish_id=:id AND company_id=:cid AND invoice_number='0'"
    ), {"id": item_id, "cid": cid})).scalar() or 0
    if int(pedidos) > 0:
        raise HTTPException(status_code=409,
            detail=f"No se puede eliminar: el artículo tiene {pedidos} ítem(s) en pedidos activos.")

    # Eliminar en cascada (sin dependencias externas)
    for sql in [
        "DELETE FROM pos_dish_assembly_detail   WHERE dish_id=:id  AND company_id=:cid",
        "DELETE FROM pos_dish_assembly          WHERE dish_id=:id  AND company_id=:cid",
        "DELETE FROM pos_dish_products          WHERE dish_id=:id  AND company_id=:cid",
        "DELETE FROM inventario_porciones_plato WHERE id_plato=:id AND company_id=:cid",
        "DELETE FROM pos_item_printers          WHERE item_id=:id  AND company_id=:cid",
        "DELETE FROM pos_dish_variants          WHERE dish_id=:id  AND company_id=:cid",
        "DELETE FROM pos_item_modifiers         WHERE item_id=:id  AND company_id=:cid",
        "DELETE FROM pos_customer_price_list    WHERE id_producto=:id AND company_id=:cid",
        "DELETE FROM pos_dishes                 WHERE id=:id       AND company_id=:cid",
    ]:
        await db.execute(text(sql), {"id": item_id, "cid": cid})

    await db.commit()
    return {"ok": True}


# ─── Catálogos de apoyo (insumos, formas de medida, proveedores) ──────────────

@router.get("/insumos/buscar")
async def buscar_insumos(
    categoria: Optional[int] = Query(None, ge=0),
    armado: bool = Query(False),          # True = solo insumos de armado (Armar_Plato = 1)
    q: Optional[str] = Query(None, max_length=60),
    limit: int = Query(100, ge=1, le=300),
    authorization: str = Header(None), db: AsyncSession = Depends(get_db),
):
    """Insumos activos de la empresa por categoría (supply_items.agrupar) y/o nombre."""
    user = await _get_user(authorization, db)
    sql = """
        SELECT si.id_item, si.id_grupo, si.posicion, si.description, si.code,
               si.agrupar AS category_id, pc.name AS category_name
        FROM supply_items si
        LEFT JOIN pos_product_categories pc
               ON pc.id = si.agrupar AND pc.company_id = si.company_id
        WHERE si.company_id = :cid AND si.is_active = 1
    """
    params: dict = {"cid": user.company_id, "lim": limit}
    if categoria:
        sql += " AND si.agrupar = :cat"
        params["cat"] = categoria
    if armado:
        sql += " AND si.armar_plato = 1"
    term = (q or "").strip()
    if term:
        # Escapar comodines de LIKE para que el texto se busque literal
        term = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        sql += " AND si.description LIKE :q"
        params["q"] = f"%{term}%"
    sql += " ORDER BY si.description LIMIT :lim"
    rows = (await db.execute(text(sql), params)).mappings().all()
    return [dict(r) for r in rows]


@router.get("/catalogos/formas-medida")
async def get_formas_medida(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    rows = (await db.execute(text(
        "SELECT id, name FROM pos_measure_forms WHERE company_id=:cid AND is_active=1 ORDER BY name"   # Activa: 1 = activa
    ), {"cid": user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.get("/catalogos/proveedores")
async def get_proveedores(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    rows = (await db.execute(text(
        "SELECT id_proveedor AS id, name FROM suppliers "
        "WHERE company_id=:cid AND is_active=1 AND id_proveedor IS NOT NULL ORDER BY name"
    ), {"cid": user.company_id})).mappings().all()
    return [dict(r) for r in rows]


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
    """Variantes del plato con su receta (cantidades de los insumos fijos del plato) y la
    cantidad de sabores por categoría de armado."""
    user = await _get_user(authorization, db)
    cid = user.company_id
    await _check_dish(db, cid, item_id)
    rows = (await db.execute(text("""
        SELECT id, name, price, compare_price, order_index, COALESCE(is_default, 0) AS is_default
        FROM pos_dish_variants
        WHERE dish_id=:did AND company_id=:cid AND is_active=1
        ORDER BY order_index, id
    """), {"did": item_id, "cid": cid})).mappings().all()
    if not rows:
        return []
    fijos = await armado_svc.fixed_products(db, cid, item_id)
    cats = (await db.execute(text("""
        SELECT da.category_code, da.max_choices, pc.name AS category_name
        FROM pos_dish_assembly da
        LEFT JOIN pos_product_categories pc ON pc.id = da.category_code AND pc.company_id = da.company_id
        WHERE da.dish_id = :did AND da.company_id = :cid AND da.is_active = 1
        ORDER BY da.category_code
    """), {"did": item_id, "cid": cid})).mappings().all()
    ids = ",".join(str(int(r["id"])) for r in rows)
    recetas = (await db.execute(text(
        f"SELECT variant_id, id_item, porciones FROM pos_dish_variant_products WHERE company_id=:cid AND variant_id IN ({ids})"
    ), {"cid": cid})).all()
    sabores = (await db.execute(text(
        f"SELECT variant_id, category_code, max_choices FROM pos_dish_variant_assembly WHERE company_id=:cid AND variant_id IN ({ids})"
    ), {"cid": cid})).all()
    rec_map = {(int(v), int(i)): float(q) for v, i, q in recetas}
    sab_map = {(int(v), int(c)): int(m) for v, c, m in sabores}
    out = []
    for r in rows:
        vid = int(r["id"])
        out.append({
            "id": vid, "name": r["name"], "price": int(r["price"] or 0),
            "compare_price": r["compare_price"], "order_index": r["order_index"],
            "is_default": bool(r["is_default"]),
            "receta": [{"id_item": f["item_id"], "description": f["description"] or f"Insumo {f['item_id']}",
                        "plato_qty": f["quantity"], "porciones": rec_map.get((vid, f["item_id"]), f["quantity"])}
                       for f in fijos],
            "sabores": [{"category_code": int(c["category_code"]),
                         "category_name": c["category_name"] or f"Categoría {c['category_code']}",
                         "plato_max": int(c["max_choices"] or 1),
                         "max_choices": sab_map.get((vid, int(c["category_code"])), int(c["max_choices"] or 1))}
                        for c in cats],
        })
    return out


async def _sync_precio_default(db: AsyncSession, cid: int, dish_id: int) -> None:
    """La variante por defecto define el precio del plato (garantiza que siempre haya una)."""
    vars_ = await armado_svc.dish_variants(db, cid, dish_id)
    if not vars_:
        return
    default = next((v for v in vars_ if v["is_default"]), None)
    if not default:
        default = vars_[0]
        await db.execute(text(
            "UPDATE pos_dish_variants SET is_default=1 WHERE id=:id AND company_id=:cid"
        ), {"id": default["id"], "cid": cid})
    await db.execute(text(
        "UPDATE pos_dishes SET price=:p, synced=0 WHERE id=:did AND company_id=:cid"
    ), {"p": default["price"], "did": dish_id, "cid": cid})
    # Lista general (por defecto): precio del plato y de cada variante
    await _upsert_general_price(db, cid, dish_id, default["price"])
    for v in vars_:
        await _upsert_general_price(db, cid, dish_id, v["price"], id_presentacion=v["id"])


async def _check_variant(db: AsyncSession, cid: int, dish_id: int, var_id: int) -> None:
    ok = (await db.execute(text(
        "SELECT 1 FROM pos_dish_variants WHERE id=:id AND dish_id=:did AND company_id=:cid AND is_active=1"
    ), {"id": var_id, "did": dish_id, "cid": cid})).scalar()
    if not ok:
        raise HTTPException(status_code=404, detail="Variante no encontrada")


@router.post("/{item_id}/variantes", status_code=201)
async def crear_variante(
    item_id: int, data: VariantIn,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    cid = user.company_id
    await _check_dish(db, cid, item_id)
    name = armado_svc.clean_text(data.name, 100)
    if not name:
        raise HTTPException(status_code=422, detail="El nombre de la variante es obligatorio")
    if data.is_default:
        await db.execute(text(
            "UPDATE pos_dish_variants SET is_default=0 WHERE dish_id=:did AND company_id=:cid"
        ), {"did": item_id, "cid": cid})
    res = await db.execute(text("""
        INSERT INTO pos_dish_variants (company_id, dish_id, name, price, compare_price, order_index, is_default)
        VALUES (:cid, :did, :name, :price, :cp, :ord, :def)
    """), {"cid": cid, "did": item_id, "name": name, "price": data.price, "cp": data.compare_price,
           "ord": data.order_index, "def": int(bool(data.is_default))})
    await _sync_precio_default(db, cid, item_id)
    await db.commit()
    return {"ok": True, "id": res.lastrowid}


@router.put("/{item_id}/variantes/{var_id}")
async def actualizar_variante(
    item_id: int, var_id: int, data: VariantIn,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    cid = user.company_id
    await _check_variant(db, cid, item_id, var_id)
    name = armado_svc.clean_text(data.name, 100)
    if not name:
        raise HTTPException(status_code=422, detail="El nombre de la variante es obligatorio")
    if data.is_default:
        await db.execute(text(
            "UPDATE pos_dish_variants SET is_default=0 WHERE dish_id=:did AND company_id=:cid AND id<>:id"
        ), {"did": item_id, "cid": cid, "id": var_id})
    await db.execute(text("""
        UPDATE pos_dish_variants
        SET name=:name, price=:price, compare_price=:cp, order_index=:ord, is_default=:def
        WHERE id=:id AND dish_id=:did AND company_id=:cid
    """), {"id": var_id, "did": item_id, "cid": cid, "name": name, "price": data.price,
           "cp": data.compare_price, "ord": data.order_index, "def": int(bool(data.is_default))})
    await _sync_precio_default(db, cid, item_id)
    await db.commit()
    return {"ok": True}


@router.delete("/{item_id}/variantes/{var_id}")
async def eliminar_variante(
    item_id: int, var_id: int,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    cid = user.company_id
    await _check_variant(db, cid, item_id, var_id)
    await db.execute(text(
        "UPDATE pos_dish_variants SET is_active=0, is_default=0 WHERE id=:id AND dish_id=:did AND company_id=:cid"
    ), {"id": var_id, "did": item_id, "cid": cid})
    await _sync_precio_default(db, cid, item_id)
    await db.commit()
    return {"ok": True}


class VarianteRecetaLinea(BaseModel):
    id_item: Annotated[int, Field(ge=1)]
    porciones: Annotated[float, Field(ge=0, le=1_000_000)]


class VarianteRecetaIn(BaseModel):
    items: Annotated[List[VarianteRecetaLinea], Field(max_length=300)]


@router.put("/{item_id}/variantes/{var_id}/receta")
async def guardar_receta_variante(
    item_id: int, var_id: int, data: VarianteRecetaIn,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    """Ajusta las cantidades de los insumos fijos del plato para esta variante (no agrega
    ni quita insumos: solo se aceptan los insumos fijos del plato)."""
    user = await _get_user(authorization, db)
    cid = user.company_id
    await _check_variant(db, cid, item_id, var_id)
    fijos = {f["item_id"] for f in await armado_svc.fixed_products(db, cid, item_id)}
    for ln in data.items:
        if ln.id_item not in fijos:
            raise HTTPException(status_code=422, detail="Solo se pueden ajustar los insumos fijos del plato")
    for ln in data.items:
        await db.execute(text("""
            INSERT INTO pos_dish_variant_products (company_id, variant_id, id_item, porciones)
            VALUES (:cid, :vid, :iid, :q)
            ON DUPLICATE KEY UPDATE porciones = VALUES(porciones)
        """), {"cid": cid, "vid": var_id, "iid": ln.id_item, "q": ln.porciones})
    await db.commit()
    return {"ok": True}


class VarianteSaborLinea(BaseModel):
    category_code: Annotated[int, Field(ge=1)]
    max_choices: Annotated[int, Field(ge=1, le=50)]


class VarianteSaboresIn(BaseModel):
    categorias: Annotated[List[VarianteSaborLinea], Field(max_length=100)]


@router.put("/{item_id}/variantes/{var_id}/sabores")
async def guardar_sabores_variante(
    item_id: int, var_id: int, data: VarianteSaboresIn,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    """Cantidad de opciones (sabores) por categoría de armado en esta variante."""
    user = await _get_user(authorization, db)
    cid = user.company_id
    await _check_variant(db, cid, item_id, var_id)
    cats = {int(r[0]) for r in (await db.execute(text(
        "SELECT category_code FROM pos_dish_assembly WHERE dish_id=:did AND company_id=:cid"
    ), {"did": item_id, "cid": cid})).all()}
    for ln in data.categorias:
        if ln.category_code not in cats:
            raise HTTPException(status_code=422, detail="La categoría no es de armado de este plato")
    for ln in data.categorias:
        await db.execute(text("""
            INSERT INTO pos_dish_variant_assembly (company_id, variant_id, category_code, max_choices)
            VALUES (:cid, :vid, :cc, :mc)
            ON DUPLICATE KEY UPDATE max_choices = VALUES(max_choices)
        """), {"cid": cid, "vid": var_id, "cc": ln.category_code, "mc": ln.max_choices})
    await db.commit()
    return {"ok": True}


# ─── Insumos FIJOS (inventario_porciones_plato) ───────────────────────────────
# Se descuentan SIEMPRE al vender el plato (además de lo que se elija al armar).
# Convención escritorio: Cantidad = Unidad_Minima = Porciones_A_Desccontar,
# Posicion = supply_items.posicion.

@router.get("/{item_id}/insumos-fijos")
async def get_insumos_fijos(item_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    rows = (await db.execute(text("""
        SELECT ipp.id_item, ipp.id_grupo, ipp.porciones_a_desccontar AS porciones, ipp.posicion,
               si.description AS insumo_nombre, si.code AS insumo_code,
               pc.name AS category_name
        FROM inventario_porciones_plato ipp
        LEFT JOIN supply_items si
               ON si.company_id = ipp.company_id AND si.id_item = ipp.id_item AND si.id_grupo = ipp.id_grupo
        LEFT JOIN pos_product_categories pc
               ON pc.id = si.agrupar AND pc.company_id = ipp.company_id
        WHERE ipp.id_plato = :did AND ipp.company_id = :cid
        ORDER BY si.description
    """), {"did": item_id, "cid": user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.post("/{item_id}/insumos-fijos", status_code=201)
async def add_insumo_fijo(
    item_id: int, data: PortionIn,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    cid = user.company_id
    await _check_dish(db, cid, item_id)
    sup = await _get_supply(db, cid, data.id_item)
    await db.execute(text("""
        INSERT INTO inventario_porciones_plato
            (company_id, id_plato, id_grupo, id_item, cantidad, unidad_minima,
             porciones_a_desccontar, posicion, opcion_cambiar, enviada_mysql)
        VALUES (:cid, :did, :gid, :iid, :p, :p, :p, :pos, 0, 0)
        ON DUPLICATE KEY UPDATE
            cantidad=VALUES(cantidad), unidad_minima=VALUES(unidad_minima),
            porciones_a_desccontar=VALUES(porciones_a_desccontar),
            posicion=VALUES(posicion), enviada_mysql=0, updated_at=NOW()
    """), {"cid": cid, "did": item_id, "gid": sup["id_grupo"], "iid": sup["id_item"],
           "p": data.porciones, "pos": sup["posicion"] or sup["id_item"]})
    await db.commit()
    return {"ok": True}


@router.put("/{item_id}/insumos-fijos/{id_item}")
async def upd_insumo_fijo(
    item_id: int, id_item: int, data: PortionUpdate,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    res = await db.execute(text("""
        UPDATE inventario_porciones_plato
        SET cantidad=:p, unidad_minima=:p, porciones_a_desccontar=:p, enviada_mysql=0, updated_at=NOW()
        WHERE id_plato=:did AND id_item=:iid AND company_id=:cid
    """), {"p": data.porciones, "did": item_id, "iid": id_item, "cid": user.company_id})
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Insumo no asignado a este artículo")
    await db.commit()
    return {"ok": True}


@router.delete("/{item_id}/insumos-fijos/{id_item}")
async def del_insumo_fijo(
    item_id: int, id_item: int,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    await db.execute(text(
        "DELETE FROM inventario_porciones_plato WHERE id_plato=:did AND id_item=:iid AND company_id=:cid"
    ), {"did": item_id, "iid": id_item, "cid": user.company_id})
    await db.commit()
    return {"ok": True}


# ─── Presentaciones (pos_dish_products = plato_producto) ──────────────────────
# PK: (company_id, dish_id, supplier_id, measure_id). active=0 → activa (convención VB6).
# supplier_id = suppliers.id_proveedor (= proveedores.Id_Proveedor del escritorio).

@router.get("/{item_id}/presentaciones")
async def get_presentaciones(item_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    rows = (await db.execute(text("""
        SELECT dp.measure_id, dp.supplier_id, dp.minimum_units, dp.presentation_value,
               COALESCE(mf.name, dp.description) AS measure_name,
               s.name AS supplier_name
        FROM pos_dish_products dp
        LEFT JOIN pos_measure_forms mf ON mf.id = dp.measure_id AND mf.company_id = dp.company_id
        LEFT JOIN suppliers s          ON s.id_proveedor = dp.supplier_id AND s.company_id = dp.company_id
        WHERE dp.dish_id = :did AND dp.company_id = :cid
        ORDER BY dp.measure_id
    """), {"did": item_id, "cid": user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.post("/{item_id}/presentaciones", status_code=201)
async def add_presentacion(
    item_id: int, data: PresentationIn,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    cid = user.company_id
    await _check_dish(db, cid, item_id)
    measure_name = (await db.execute(text(
        "SELECT name FROM pos_measure_forms WHERE id=:id AND company_id=:cid"
    ), {"id": data.measure_id, "cid": cid})).scalar()
    if not measure_name:
        raise HTTPException(status_code=400, detail="Presentación no válida para esta empresa")
    if data.supplier_id:
        ok = (await db.execute(text(
            "SELECT 1 FROM suppliers WHERE id_proveedor=:id AND company_id=:cid"
        ), {"id": data.supplier_id, "cid": cid})).scalar()
        if not ok:
            raise HTTPException(status_code=400, detail="Proveedor no válido para esta empresa")
    await db.execute(text("""
        INSERT INTO pos_dish_products
            (company_id, dish_id, supplier_id, measure_id, minimum_units,
             presentation_value, description, active, synced)
        VALUES (:cid, :did, :sup, :mid, :mu, :pv, :desc, 0, 0)
        ON DUPLICATE KEY UPDATE
            minimum_units=VALUES(minimum_units), presentation_value=VALUES(presentation_value),
            description=VALUES(description), active=0, synced=0, updated_at=NOW()
    """), {"cid": cid, "did": item_id, "sup": data.supplier_id, "mid": data.measure_id,
           "mu": data.minimum_units, "pv": data.presentation_value, "desc": measure_name[:50]})
    await db.commit()
    return {"ok": True}


@router.put("/{item_id}/presentaciones/{measure_id}/{supplier_id}")
async def upd_presentacion(
    item_id: int, measure_id: int, supplier_id: int, data: PresentationUpdate,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    res = await db.execute(text("""
        UPDATE pos_dish_products
        SET minimum_units=:mu, presentation_value=:pv, synced=0, updated_at=NOW()
        WHERE dish_id=:did AND measure_id=:mid AND supplier_id=:sup AND company_id=:cid
    """), {"mu": data.minimum_units, "pv": data.presentation_value, "did": item_id,
           "mid": measure_id, "sup": supplier_id, "cid": user.company_id})
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Presentación no encontrada")
    await db.commit()
    return {"ok": True}


@router.delete("/{item_id}/presentaciones/{measure_id}/{supplier_id}")
async def del_presentacion(
    item_id: int, measure_id: int, supplier_id: int,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    await db.execute(text("""
        DELETE FROM pos_dish_products
        WHERE dish_id=:did AND measure_id=:mid AND supplier_id=:sup AND company_id=:cid
    """), {"did": item_id, "mid": measure_id, "sup": supplier_id, "cid": user.company_id})
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
    await _check_dish(db, cid, item_id)
    valid = {int(r[0]) for r in (await db.execute(text(
        "SELECT id FROM pos_printers WHERE company_id=:cid"
    ), {"cid": cid})).all()}
    if any(p.printer_id not in valid for p in data.printers):
        raise HTTPException(status_code=400, detail="Impresora no válida para esta empresa")
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


# ─── Armado VB6 (pos_dish_assembly = plato_armar / pos_dish_assembly_detail = plato_armar_detalle) ──
#   max_choices          = Cantidad_Elegir            (Opciones Permitidas)
#   is_required          = Exgir_Seleccion            (Exigir Cantidad)
#   print_on_change_only = Imprimir_Armar_Solo_Cambio (Imprimir si hay cambios)
#   position             = Posicion  = supply_items.id_item
#   discount_qty         = Cantidad_Descontar
#   supply_price         = Precio_Insumo               (Valor Adicional)
#   is_default           = Por_Default

class ArmadoCategoriaIn(BaseModel):
    category_code:        Annotated[int, Field(ge=1)]
    max_choices:          Annotated[int, Field(ge=1, le=50)] = 1
    is_required:          Flag = 0
    print_on_change_only: Flag = 0


class ArmadoCategoriaUpdate(BaseModel):
    max_choices:          Annotated[int, Field(ge=1, le=50)]
    is_required:          Flag = 0
    print_on_change_only: Flag = 0


class ArmadoOpcionIn(BaseModel):
    position:     Annotated[int, Field(ge=1)]      # supply_items.id_item
    discount_qty: Qty = 1
    supply_price: Money = 0
    is_default:   Flag = 0


class ArmadoOpcionUpdate(BaseModel):
    discount_qty: Qty = 1
    supply_price: Money = 0
    is_default:   Flag = 0


@router.get("/armado/categorias-disponibles")
async def get_categorias_armado(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    """Categorías de insumos (pos_product_categories = categoria_productos)."""
    user = await _get_user(authorization, db)
    rows = (await db.execute(text(
        "SELECT id, name, COALESCE(percentage,0) AS percentage, COALESCE(is_active,0) AS is_active "
        "FROM pos_product_categories WHERE company_id=:cid ORDER BY name"
    ), {"cid": user.company_id})).mappings().all()
    # is_assembly: categoría de armado (categoria_productos.Porcentaje = 1 y Activa = 1)
    return [{"id": int(r["id"]), "name": r["name"],
             "is_assembly": float(r["percentage"] or 0) == 1 and int(r["is_active"] or 0) == 1} for r in rows]


@router.get("/{item_id}/armado")
async def get_armado(item_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    cid = user.company_id

    cats = (await db.execute(text("""
        SELECT da.category_code, da.max_choices, da.is_required, da.print_on_change_only,
               pc.name AS category_name,
               (COALESCE(pc.percentage, 0) = 1 AND COALESCE(pc.is_active, 0) = 1) AS is_assembly
        FROM pos_dish_assembly da
        LEFT JOIN pos_product_categories pc
               ON pc.id = da.category_code AND pc.company_id = da.company_id
        WHERE da.dish_id = :did AND da.company_id = :cid
        ORDER BY da.category_code
    """), {"did": item_id, "cid": cid})).mappings().all()
    if not cats:
        return []

    opts = (await db.execute(text("""
        SELECT dad.category_code, dad.position, dad.discount_qty, dad.supply_price, dad.is_default,
               COALESCE(si.description, CONCAT('Insumo ', dad.position)) AS item_name
        FROM pos_dish_assembly_detail dad
        LEFT JOIN supply_items si
               ON si.id_item = dad.position AND si.company_id = dad.company_id
        WHERE dad.dish_id = :did AND dad.company_id = :cid
        ORDER BY dad.category_code, item_name
    """), {"did": item_id, "cid": cid})).mappings().all()

    by_cat: dict = {}
    for o in opts:
        by_cat.setdefault(int(o["category_code"]), []).append({
            "position":     int(o["position"]),
            "item_name":    o["item_name"],
            "discount_qty": float(o["discount_qty"] or 1),
            "supply_price": float(o["supply_price"] or 0),
            "is_default":   bool(o["is_default"]),
        })

    return [{
        "category_code":        int(c["category_code"]),
        "category_name":        c["category_name"] or f"Categoría {c['category_code']}",
        "max_choices":          int(c["max_choices"] or 1),
        "is_required":          bool(c["is_required"]),
        "print_on_change_only": bool(c["print_on_change_only"]),
        "is_assembly":          bool(c["is_assembly"]),
        "options":              by_cat.get(int(c["category_code"]), []),
    } for c in cats]


@router.post("/{item_id}/armado/categoria", status_code=201)
async def add_armado_categoria(
    item_id: int, data: ArmadoCategoriaIn,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    cid = user.company_id
    await _check_dish(db, cid, item_id)
    ok = (await db.execute(text(
        "SELECT 1 FROM pos_product_categories WHERE id=:id AND company_id=:cid "
        "AND percentage = 1 AND is_active = 1"
    ), {"id": data.category_code, "cid": cid})).scalar()
    if not ok:
        raise HTTPException(status_code=400, detail="La categoría no es de armado o está inactiva")
    await db.execute(text("""
        INSERT INTO pos_dish_assembly
            (dish_id, company_id, category_code, max_choices, is_required, is_active, print_on_change_only, synced)
        VALUES (:did, :cid, :cc, :mc, :req, 1, :poc, 0)
        ON DUPLICATE KEY UPDATE
            max_choices=VALUES(max_choices), is_required=VALUES(is_required),
            print_on_change_only=VALUES(print_on_change_only), is_active=1, synced=0
    """), {"did": item_id, "cid": cid, "cc": data.category_code,
           "mc": data.max_choices, "req": data.is_required, "poc": data.print_on_change_only})
    await db.commit()
    return {"ok": True}


@router.put("/{item_id}/armado/categoria/{category_code}")
async def upd_armado_categoria(
    item_id: int, category_code: int, data: ArmadoCategoriaUpdate,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    res = await db.execute(text("""
        UPDATE pos_dish_assembly
        SET max_choices=:mc, is_required=:req, print_on_change_only=:poc, synced=0
        WHERE dish_id=:did AND company_id=:cid AND category_code=:cc
    """), {"mc": data.max_choices, "req": data.is_required, "poc": data.print_on_change_only,
           "did": item_id, "cid": user.company_id, "cc": category_code})
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Categoría de armado no encontrada")
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
    cat = (await db.execute(text(
        "SELECT 1 FROM pos_dish_assembly WHERE dish_id=:did AND company_id=:cid AND category_code=:cc"
    ), {"did": item_id, "cid": cid, "cc": category_code})).scalar()
    if not cat:
        raise HTTPException(status_code=404, detail="Categoría de armado no encontrada")
    sup = await _get_supply(db, cid, data.position)
    # Insumo de armado de esta categoría: inventario_porciones.Armar_Plato = 1 y Agrupar = Cod_Categoria
    es_de_categoria = (await db.execute(text(
        "SELECT 1 FROM supply_items WHERE company_id=:cid AND id_item=:iid "
        "AND agrupar=:cc AND armar_plato=1"
    ), {"cid": cid, "iid": sup["id_item"], "cc": category_code})).scalar()
    if not es_de_categoria:
        raise HTTPException(status_code=422,
                            detail="El insumo no es de armado de esta categoría (Armar Plato y Agrupar)")
    dup = (await db.execute(text(
        "SELECT 1 FROM pos_dish_assembly_detail "
        "WHERE dish_id=:did AND company_id=:cid AND category_code=:cc AND position=:pos"
    ), {"did": item_id, "cid": cid, "cc": category_code, "pos": sup["id_item"]})).scalar()
    if dup:
        raise HTTPException(status_code=409, detail="El insumo ya está en esta categoría")
    max_item = (await db.execute(text(
        "SELECT COALESCE(MAX(item),0) FROM pos_dish_assembly_detail "
        "WHERE dish_id=:did AND company_id=:cid AND category_code=:cc"
    ), {"did": item_id, "cid": cid, "cc": category_code})).scalar() or 0
    await db.execute(text("""
        INSERT INTO pos_dish_assembly_detail
            (dish_id, company_id, category_code, item, position, supply_price, discount_qty, is_default, synced)
        VALUES (:did, :cid, :cc, :itm, :pos, :sp, :dq, :def, 0)
    """), {"did": item_id, "cid": cid, "cc": category_code, "itm": int(max_item) + 1,
           "pos": sup["id_item"], "sp": data.supply_price, "dq": data.discount_qty,
           "def": data.is_default})
    await db.commit()
    return {"ok": True}


@router.put("/{item_id}/armado/categoria/{category_code}/opcion/{position}")
async def update_armado_opcion(
    item_id: int, category_code: int, position: int, data: ArmadoOpcionUpdate,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    res = await db.execute(text("""
        UPDATE pos_dish_assembly_detail
        SET discount_qty=:dq, supply_price=:sp, is_default=:def, synced=0
        WHERE dish_id=:did AND company_id=:cid AND category_code=:cc AND position=:pos
    """), {"did": item_id, "cid": user.company_id, "cc": category_code, "pos": position,
           "dq": data.discount_qty, "sp": data.supply_price, "def": data.is_default})
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Opción de armado no encontrada")
    await db.commit()
    return {"ok": True}


@router.delete("/{item_id}/armado/categoria/{category_code}/opcion/{position}")
async def del_armado_opcion(
    item_id: int, category_code: int, position: int,
    authorization: str = Header(None), db: AsyncSession = Depends(get_db)
):
    user = await _get_user(authorization, db)
    await db.execute(text(
        "DELETE FROM pos_dish_assembly_detail "
        "WHERE dish_id=:did AND company_id=:cid AND category_code=:cc AND position=:pos"
    ), {"did": item_id, "cid": user.company_id, "cc": category_code, "pos": position})
    await db.commit()
    return {"ok": True}
