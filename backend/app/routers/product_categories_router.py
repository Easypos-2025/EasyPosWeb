from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.product_category_model import ProductCategory
from app.auth.dependencies import get_current_user
from app.models.user_model import User
from app.services.plan_limits_service import check_limit

router = APIRouter(prefix="/product-categories", tags=["ProductCategories"])


def _ser(c: ProductCategory) -> dict:
    return {
        "id":          c.id,
        "company_id":  c.company_id,
        "name":        c.name,
        "description": c.description,
        "color":       c.color,
        "icon":        c.icon,
        "is_active":   c.is_active,
        "created_at":  c.created_at.isoformat() if c.created_at else None,
    }


@router.get("/")
async def list_categories(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductCategory)
        .where(ProductCategory.company_id == current_user.company_id, ProductCategory.is_active == 1)
        .order_by(ProductCategory.name)
    )
    return [_ser(c) for c in result.scalars().all()]


@router.post("/")
async def create_category(data: dict = Body(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await check_limit(current_user.company_id, "max_categories", ProductCategory, db,
                      extra_filters=[ProductCategory.is_active == 1])
    if not (data.get("name") or "").strip():
        raise HTTPException(status_code=400, detail="El nombre es requerido")
    c = ProductCategory(
        company_id=current_user.company_id,
        name=data["name"].strip(),
        description=(data.get("description") or "").strip() or None,
        color=(data.get("color") or "").strip() or None,
        icon=(data.get("icon") or "").strip() or None,
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return _ser(c)


@router.put("/{cid}")
async def update_category(cid: int, data: dict = Body(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductCategory).where(ProductCategory.id == cid, ProductCategory.company_id == current_user.company_id)
    )
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    if "name"        in data: c.name        = data["name"].strip()
    if "description" in data: c.description = (data["description"] or "").strip() or None
    if "color"       in data: c.color       = (data["color"] or "").strip() or None
    if "icon"        in data: c.icon        = (data["icon"] or "").strip() or None
    if "is_active"   in data: c.is_active   = int(data["is_active"])
    await db.commit()
    await db.refresh(c)
    return _ser(c)


@router.delete("/{cid}")
async def delete_category(cid: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductCategory).where(ProductCategory.id == cid, ProductCategory.company_id == current_user.company_id)
    )
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    c.is_active = 0
    await db.commit()
    return {"ok": True}
