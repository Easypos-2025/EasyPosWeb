from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.supplier_model import Supplier
from app.auth.dependencies import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


def _ser(s: Supplier) -> dict:
    return {
        "id":           s.id,
        "company_id":   s.company_id,
        "name":         s.name,
        "nit":          s.nit,
        "contact_name": s.contact_name,
        "email":        s.email,
        "phone":        s.phone,
        "address":      s.address,
        "notes":        s.notes,
        "is_active":    s.is_active,
        "created_at":   s.created_at.isoformat() if s.created_at else None,
    }


@router.get("/")
async def list_suppliers(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Supplier).where(Supplier.company_id == current_user.company_id).order_by(Supplier.name)
    )
    return [_ser(s) for s in result.scalars().all()]


@router.post("/")
async def create_supplier(data: dict = Body(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not (data.get("name") or "").strip():
        raise HTTPException(status_code=400, detail="El nombre es requerido")
    s = Supplier(
        company_id=current_user.company_id,
        name=data["name"].strip(),
        nit=(data.get("nit") or "").strip() or None,
        contact_name=(data.get("contact_name") or "").strip() or None,
        email=(data.get("email") or "").strip() or None,
        phone=(data.get("phone") or "").strip() or None,
        address=(data.get("address") or "").strip() or None,
        notes=(data.get("notes") or "").strip() or None,
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return _ser(s)


@router.put("/{sid}")
async def update_supplier(sid: int, data: dict = Body(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Supplier).where(Supplier.id == sid, Supplier.company_id == current_user.company_id)
    )
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    if "name"         in data: s.name         = data["name"].strip()
    if "nit"          in data: s.nit          = (data["nit"] or "").strip() or None
    if "contact_name" in data: s.contact_name = (data["contact_name"] or "").strip() or None
    if "email"        in data: s.email        = (data["email"] or "").strip() or None
    if "phone"        in data: s.phone        = (data["phone"] or "").strip() or None
    if "address"      in data: s.address      = (data["address"] or "").strip() or None
    if "notes"        in data: s.notes        = (data["notes"] or "").strip() or None
    if "is_active"    in data: s.is_active    = int(data["is_active"])
    await db.commit()
    await db.refresh(s)
    return _ser(s)


@router.delete("/{sid}")
async def delete_supplier(sid: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Supplier).where(Supplier.id == sid, Supplier.company_id == current_user.company_id)
    )
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    s.is_active = 0
    await db.commit()
    return {"ok": True}
