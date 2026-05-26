from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.product_model import Product
from app.services.plan_limits_service import check_limit
from app.models.product_category_model import ProductCategory
from app.models.product_reference_model import ProductReference
from app.models.product_recipe_model import ProductRecipe
from app.models.product_presentation_model import ProductPresentation
from app.models.supply_item_model import SupplyItem
from app.auth.dependencies import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/products", tags=["Products"])
VALID_BEHAVIORS = ("recipe", "presentation", "serialized", "weight", "direct")


async def _ser(p: Product, db: AsyncSession) -> dict:
    cat = await db.get(ProductCategory, p.category_id) if p.category_id else None
    ref = await db.get(ProductReference, p.reference_id) if p.reference_id else None
    return {"id": p.id, "company_id": p.company_id, "code": p.code, "name": p.name,
            "description": p.description, "photo_url": p.photo_url,
            "category_id": p.category_id, "category_name": cat.name if cat else None,
            "reference_id": p.reference_id, "reference_name": ref.name if ref else None,
            "inventory_behavior": p.inventory_behavior, "base_price": float(p.base_price),
            "cost_price": float(p.cost_price), "tax_rate": float(p.tax_rate),
            "min_stock": float(p.min_stock), "ask_price": p.ask_price,
            "ask_description": p.ask_description, "is_active": p.is_active,
            "created_at": p.created_at.isoformat() if p.created_at else None}


@router.get("/")
async def list_products(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.company_id == current_user.company_id).order_by(Product.name))
    return [await _ser(p, db) for p in result.scalars().all()]


@router.post("/")
async def create_product(data: dict = Body(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await check_limit(current_user.company_id, "max_products", Product, db,
                      extra_filters=[Product.is_active == 1])
    if not (data.get("name") or "").strip():
        raise HTTPException(status_code=400, detail="El nombre es requerido")
    behavior = data.get("inventory_behavior", "direct")
    if behavior not in VALID_BEHAVIORS:
        raise HTTPException(status_code=400, detail=f"Comportamiento inválido. Válidos: {VALID_BEHAVIORS}")
    p = Product(company_id=current_user.company_id, code=(data.get("code") or "").strip() or None,
                name=data["name"].strip(), description=(data.get("description") or "").strip() or None,
                photo_url=(data.get("photo_url") or "").strip() or None,
                category_id=data.get("category_id"), reference_id=data.get("reference_id"),
                inventory_behavior=behavior, base_price=float(data.get("base_price") or 0),
                cost_price=float(data.get("cost_price") or 0), tax_rate=float(data.get("tax_rate") or 0),
                min_stock=float(data.get("min_stock") or 0), ask_price=int(data.get("ask_price", 0)),
                ask_description=int(data.get("ask_description", 0)))
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return await _ser(p, db)


@router.put("/{pid}")
async def update_product(pid: int, data: dict = Body(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == pid, Product.company_id == current_user.company_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    if "code"               in data: p.code               = (data["code"] or "").strip() or None
    if "name"               in data: p.name               = data["name"].strip()
    if "description"        in data: p.description        = (data["description"] or "").strip() or None
    if "photo_url"          in data: p.photo_url          = (data["photo_url"] or "").strip() or None
    if "category_id"        in data: p.category_id        = data["category_id"]
    if "reference_id"       in data: p.reference_id       = data["reference_id"]
    if "base_price"         in data: p.base_price         = float(data["base_price"] or 0)
    if "cost_price"         in data: p.cost_price         = float(data["cost_price"] or 0)
    if "tax_rate"           in data: p.tax_rate           = float(data["tax_rate"] or 0)
    if "min_stock"          in data: p.min_stock          = float(data["min_stock"] or 0)
    if "ask_price"          in data: p.ask_price          = int(data["ask_price"])
    if "ask_description"    in data: p.ask_description    = int(data["ask_description"])
    if "is_active"          in data: p.is_active          = int(data["is_active"])
    if "inventory_behavior" in data:
        if data["inventory_behavior"] not in VALID_BEHAVIORS:
            raise HTTPException(status_code=400, detail="Comportamiento inválido")
        p.inventory_behavior = data["inventory_behavior"]
    await db.commit()
    await db.refresh(p)
    return await _ser(p, db)


@router.delete("/{pid}")
async def delete_product(pid: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == pid, Product.company_id == current_user.company_id))
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    p.is_active = 0
    await db.commit()
    return {"ok": True}


@router.get("/{pid}/recipe")
async def get_recipe(pid: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == pid, Product.company_id == current_user.company_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    result = await db.execute(select(ProductRecipe).where(ProductRecipe.product_id == pid))
    items = []
    for r in result.scalars().all():
        si = await db.get(SupplyItem, r.supply_item_id)
        items.append({"id": r.id, "supply_item_id": r.supply_item_id,
                      "supply_item_name": si.name if si else "—",
                      "qty_required": float(r.qty_required), "unit_id": r.unit_id})
    return items


@router.post("/{pid}/recipe")
async def add_recipe_line(pid: int, data: dict = Body(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == pid, Product.company_id == current_user.company_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    r = ProductRecipe(product_id=pid, supply_item_id=data["supply_item_id"],
                      qty_required=float(data.get("qty_required", 1)), unit_id=data.get("unit_id"))
    db.add(r)
    await db.commit()
    await db.refresh(r)
    si = await db.get(SupplyItem, r.supply_item_id)
    return {"id": r.id, "supply_item_id": r.supply_item_id, "supply_item_name": si.name if si else "—",
            "qty_required": float(r.qty_required), "unit_id": r.unit_id}


@router.delete("/{pid}/recipe/{rid}")
async def delete_recipe_line(pid: int, rid: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == pid, Product.company_id == current_user.company_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    result = await db.execute(select(ProductRecipe).where(ProductRecipe.id == rid, ProductRecipe.product_id == pid))
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Línea de receta no encontrada")
    await db.delete(r)
    await db.commit()
    return {"ok": True}


@router.get("/{pid}/presentations")
async def get_presentations(pid: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == pid, Product.company_id == current_user.company_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    result = await db.execute(select(ProductPresentation).where(ProductPresentation.product_id == pid, ProductPresentation.is_active == 1))
    return [{"id": r.id, "name": r.name, "factor": float(r.factor), "barcode": r.barcode,
             "price": float(r.price) if r.price is not None else None,
             "supply_item_id": r.supply_item_id, "is_active": r.is_active}
            for r in result.scalars().all()]


@router.post("/{pid}/presentations")
async def add_presentation(pid: int, data: dict = Body(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == pid, Product.company_id == current_user.company_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    pr = ProductPresentation(product_id=pid, supply_item_id=data.get("supply_item_id"),
                              name=data["name"].strip(), factor=float(data.get("factor", 1)),
                              barcode=(data.get("barcode") or "").strip() or None,
                              price=float(data["price"]) if data.get("price") is not None else None)
    db.add(pr)
    await db.commit()
    await db.refresh(pr)
    return {"id": pr.id, "name": pr.name, "factor": float(pr.factor), "barcode": pr.barcode,
            "price": float(pr.price) if pr.price is not None else None,
            "supply_item_id": pr.supply_item_id, "is_active": pr.is_active}


@router.delete("/{pid}/presentations/{prid}")
async def delete_presentation(pid: int, prid: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == pid, Product.company_id == current_user.company_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    result = await db.execute(select(ProductPresentation).where(ProductPresentation.id == prid, ProductPresentation.product_id == pid))
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Presentación no encontrada")
    pr.is_active = 0
    await db.commit()
    return {"ok": True}
