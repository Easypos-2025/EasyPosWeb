from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.product_category_model import ProductCategory
from app.auth.dependencies import get_current_user
from app.models.user_model import User

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
def list_categories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [_ser(c) for c in db.query(ProductCategory).filter(
        ProductCategory.company_id == current_user.company_id,
        ProductCategory.is_active == 1
    ).order_by(ProductCategory.name).all()]


@router.post("/")
def create_category(data: dict = Body(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not (data.get("name") or "").strip():
        raise HTTPException(status_code=400, detail="El nombre es requerido")
    c = ProductCategory(
        company_id=current_user.company_id,
        name=data["name"].strip(),
        description=(data.get("description") or "").strip() or None,
        color=(data.get("color") or "").strip() or None,
        icon=(data.get("icon") or "").strip() or None,
    )
    db.add(c); db.commit(); db.refresh(c)
    return _ser(c)


@router.put("/{cid}")
def update_category(cid: int, data: dict = Body(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.query(ProductCategory).filter(ProductCategory.id == cid, ProductCategory.company_id == current_user.company_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    if "name"        in data: c.name        = data["name"].strip()
    if "description" in data: c.description = (data["description"] or "").strip() or None
    if "color"       in data: c.color       = (data["color"] or "").strip() or None
    if "icon"        in data: c.icon        = (data["icon"] or "").strip() or None
    if "is_active"   in data: c.is_active   = int(data["is_active"])
    db.commit(); db.refresh(c)
    return _ser(c)


@router.delete("/{cid}")
def delete_category(cid: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.query(ProductCategory).filter(ProductCategory.id == cid, ProductCategory.company_id == current_user.company_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    c.is_active = 0
    db.commit()
    return {"ok": True}
