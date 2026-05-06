from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.database import get_db
from app.models.price_list_model import PriceList
from app.models.price_list_item_model import PriceListItem
from app.models.product_model import Product
from app.auth.dependencies import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/price-lists", tags=["PriceLists"])


def _ser(pl: PriceList) -> dict:
    return {"id": pl.id, "company_id": pl.company_id, "name": pl.name, "description": pl.description,
            "is_default": pl.is_default, "is_active": pl.is_active,
            "created_at": pl.created_at.isoformat() if pl.created_at else None}


@router.get("/")
async def list_price_lists(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PriceList).where(PriceList.company_id == current_user.company_id, PriceList.is_active == 1).order_by(PriceList.name))
    return [_ser(pl) for pl in result.scalars().all()]


@router.post("/")
async def create_price_list(data: dict = Body(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not (data.get("name") or "").strip():
        raise HTTPException(status_code=400, detail="El nombre es requerido")
    is_default = int(data.get("is_default", 0))
    if is_default:
        await db.execute(update(PriceList).where(PriceList.company_id == current_user.company_id).values(is_default=0))
    pl = PriceList(company_id=current_user.company_id, name=data["name"].strip(),
                   description=(data.get("description") or "").strip() or None, is_default=is_default)
    db.add(pl)
    await db.commit()
    await db.refresh(pl)
    return _ser(pl)


@router.put("/{plid}")
async def update_price_list(plid: int, data: dict = Body(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PriceList).where(PriceList.id == plid, PriceList.company_id == current_user.company_id))
    pl = result.scalar_one_or_none()
    if not pl:
        raise HTTPException(status_code=404, detail="Lista no encontrada")
    if "name"        in data: pl.name        = data["name"].strip()
    if "description" in data: pl.description = (data["description"] or "").strip() or None
    if "is_active"   in data: pl.is_active   = int(data["is_active"])
    if data.get("is_default"):
        await db.execute(update(PriceList).where(PriceList.company_id == current_user.company_id).values(is_default=0))
        pl.is_default = 1
    await db.commit()
    await db.refresh(pl)
    return _ser(pl)


@router.delete("/{plid}")
async def delete_price_list(plid: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PriceList).where(PriceList.id == plid, PriceList.company_id == current_user.company_id))
    pl = result.scalar_one_or_none()
    if not pl:
        raise HTTPException(status_code=404, detail="Lista no encontrada")
    if pl.is_default:
        raise HTTPException(status_code=409, detail="No puedes eliminar la lista predeterminada")
    pl.is_active = 0
    await db.commit()
    return {"ok": True}


@router.get("/{plid}/items")
async def list_items(plid: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PriceList).where(PriceList.id == plid, PriceList.company_id == current_user.company_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Lista no encontrada")
    result = await db.execute(select(PriceListItem).where(PriceListItem.price_list_id == plid, PriceListItem.is_active == 1))
    items = []
    for i in result.scalars().all():
        prod = await db.get(Product, i.product_id)
        items.append({"id": i.id, "price_list_id": i.price_list_id, "product_id": i.product_id,
                      "product_name": prod.name if prod else "—", "product_code": prod.code if prod else None,
                      "presentation_id": i.presentation_id, "price": float(i.price), "is_active": i.is_active})
    return items


@router.post("/{plid}/items")
async def upsert_item(plid: int, data: dict = Body(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PriceList).where(PriceList.id == plid, PriceList.company_id == current_user.company_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Lista no encontrada")
    result = await db.execute(select(PriceListItem).where(PriceListItem.price_list_id == plid,
                                                           PriceListItem.product_id == data["product_id"],
                                                           PriceListItem.presentation_id == data.get("presentation_id")))
    existing = result.scalar_one_or_none()
    if existing:
        existing.price = float(data["price"])
        existing.is_active = 1
    else:
        db.add(PriceListItem(price_list_id=plid, product_id=data["product_id"],
                             presentation_id=data.get("presentation_id"), price=float(data["price"])))
    await db.commit()
    return {"ok": True}


@router.delete("/{plid}/items/{item_id}")
async def delete_item(plid: int, item_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PriceList).where(PriceList.id == plid, PriceList.company_id == current_user.company_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Lista no encontrada")
    result = await db.execute(select(PriceListItem).where(PriceListItem.id == item_id, PriceListItem.price_list_id == plid))
    i = result.scalar_one_or_none()
    if not i:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    i.is_active = 0
    await db.commit()
    return {"ok": True}
