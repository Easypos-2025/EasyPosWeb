from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.supply_item_model import SupplyItem
from app.models.stock_movement_model import StockMovement
from app.auth.dependencies import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/supply-items", tags=["SupplyItems"])


async def _resolve_unit(item: SupplyItem, db: AsyncSession) -> str:
    if not item.unit_id:
        return None
    from app.models.unidad_medida_model import UnidadMedida
    u = await db.get(UnidadMedida, item.unit_id)
    return f"{u.name} ({u.abreviatura})" if u else None


def _ser(item: SupplyItem, unit_name=None) -> dict:
    return {"id": item.id, "company_id": item.company_id, "code": item.code, "name": item.name,
            "description": item.description, "unit_id": item.unit_id, "unit_name": unit_name,
            "cost_price": float(item.cost_price), "stock_qty": float(item.stock_qty),
            "min_stock": float(item.min_stock), "waste_pct": float(item.waste_pct),
            "control_stock": item.control_stock, "is_active": item.is_active,
            "created_at": item.created_at.isoformat() if item.created_at else None}


async def _record_movement(db: AsyncSession, item: SupplyItem, mtype: str, qty: float, qty_before: float, user_id: int, notes: str = None):
    mov = StockMovement(company_id=item.company_id, supply_item_id=item.id, movement_type=mtype,
                        qty=qty, qty_before=qty_before, qty_after=qty_before + qty,
                        reference_type="manual", notes=notes, created_by=user_id)
    db.add(mov)
    await db.flush()


@router.get("/")
async def list_supply_items(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SupplyItem).where(SupplyItem.company_id == current_user.company_id).order_by(SupplyItem.name))
    return [_ser(i, await _resolve_unit(i, db)) for i in result.scalars().all()]


@router.post("/")
async def create_supply_item(data: dict = Body(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not (data.get("name") or "").strip():
        raise HTTPException(status_code=400, detail="El nombre es requerido")
    item = SupplyItem(company_id=current_user.company_id, code=(data.get("code") or "").strip() or None,
                      name=data["name"].strip(), description=(data.get("description") or "").strip() or None,
                      unit_id=data.get("unit_id"), cost_price=float(data.get("cost_price") or 0),
                      stock_qty=float(data.get("stock_qty") or 0), min_stock=float(data.get("min_stock") or 0),
                      waste_pct=float(data.get("waste_pct") or 0), control_stock=int(data.get("control_stock", 1)))
    db.add(item)
    await db.commit()
    await db.refresh(item)
    if item.control_stock and float(item.stock_qty) != 0:
        await _record_movement(db, item, "adjustment", float(item.stock_qty), 0, current_user.id, "Stock inicial")
        await db.commit()
    return _ser(item, await _resolve_unit(item, db))


@router.put("/{iid}")
async def update_supply_item(iid: int, data: dict = Body(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SupplyItem).where(SupplyItem.id == iid, SupplyItem.company_id == current_user.company_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    if "code"          in data: item.code          = (data["code"] or "").strip() or None
    if "name"          in data: item.name          = data["name"].strip()
    if "description"   in data: item.description   = (data["description"] or "").strip() or None
    if "unit_id"       in data: item.unit_id       = data["unit_id"]
    if "cost_price"    in data: item.cost_price    = float(data["cost_price"] or 0)
    if "min_stock"     in data: item.min_stock     = float(data["min_stock"] or 0)
    if "waste_pct"     in data: item.waste_pct     = float(data["waste_pct"] or 0)
    if "control_stock" in data: item.control_stock = int(data["control_stock"])
    if "is_active"     in data: item.is_active     = int(data["is_active"])
    if "stock_qty" in data:
        new_qty = float(data["stock_qty"] or 0)
        old_qty = float(item.stock_qty)
        if new_qty != old_qty:
            await _record_movement(db, item, "adjustment", new_qty - old_qty, old_qty, current_user.id, data.get("adjustment_notes") or "Ajuste manual")
        item.stock_qty = new_qty
    await db.commit()
    await db.refresh(item)
    return _ser(item, await _resolve_unit(item, db))


@router.delete("/{iid}")
async def delete_supply_item(iid: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SupplyItem).where(SupplyItem.id == iid, SupplyItem.company_id == current_user.company_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    item.is_active = 0
    await db.commit()
    return {"ok": True}


@router.get("/{iid}/movements")
async def get_movements(iid: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SupplyItem).where(SupplyItem.id == iid, SupplyItem.company_id == current_user.company_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    result = await db.execute(select(StockMovement).where(StockMovement.supply_item_id == iid).order_by(StockMovement.created_at.desc()).limit(100))
    return [{"id": m.id, "type": m.movement_type, "qty": float(m.qty),
             "qty_before": float(m.qty_before), "qty_after": float(m.qty_after),
             "reference_type": m.reference_type, "reference_id": m.reference_id,
             "notes": m.notes, "created_at": m.created_at.isoformat() if m.created_at else None}
            for m in result.scalars().all()]
