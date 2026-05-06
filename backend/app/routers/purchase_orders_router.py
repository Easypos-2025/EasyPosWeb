from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.purchase_order_model import PurchaseOrder
from app.models.purchase_order_item_model import PurchaseOrderItem
from app.models.supply_item_model import SupplyItem
from app.models.supplier_model import Supplier
from app.models.stock_movement_model import StockMovement
from app.auth.dependencies import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/purchase-orders", tags=["PurchaseOrders"])


async def _ser_order(o: PurchaseOrder, db: AsyncSession) -> dict:
    sup = await db.get(Supplier, o.supplier_id) if o.supplier_id else None
    return {"id": o.id, "company_id": o.company_id, "supplier_id": o.supplier_id,
            "supplier_name": sup.name if sup else None, "invoice_no": o.invoice_no,
            "order_date": o.order_date.isoformat() if o.order_date else None,
            "total_amount": float(o.total_amount), "notes": o.notes, "status": o.status,
            "created_at": o.created_at.isoformat() if o.created_at else None}


async def _ser_item(i: PurchaseOrderItem, db: AsyncSession) -> dict:
    si = await db.get(SupplyItem, i.supply_item_id)
    return {"id": i.id, "purchase_order_id": i.purchase_order_id, "supply_item_id": i.supply_item_id,
            "supply_item_name": si.name if si else "—", "qty": float(i.qty),
            "unit_price": float(i.unit_price), "subtotal": float(i.subtotal),
            "presentation_name": i.presentation_name}


@router.get("/")
async def list_orders(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.company_id == current_user.company_id).order_by(PurchaseOrder.order_date.desc()))
    return [await _ser_order(o, db) for o in result.scalars().all()]


@router.post("/")
async def create_order(data: dict = Body(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        order_date = date.fromisoformat(data.get("order_date") or date.today().isoformat())
    except ValueError:
        order_date = date.today()
    o = PurchaseOrder(company_id=current_user.company_id, supplier_id=data.get("supplier_id"),
                      invoice_no=(data.get("invoice_no") or "").strip() or None,
                      order_date=order_date, notes=(data.get("notes") or "").strip() or None,
                      status="draft", created_by=current_user.id)
    db.add(o)
    await db.commit()
    await db.refresh(o)
    total = 0
    for item_d in data.get("items", []):
        qty = float(item_d.get("qty", 0))
        unit_price = float(item_d.get("unit_price", 0))
        subtotal = round(qty * unit_price, 2)
        total += subtotal
        db.add(PurchaseOrderItem(purchase_order_id=o.id, supply_item_id=item_d["supply_item_id"],
                                  qty=qty, unit_price=unit_price, subtotal=subtotal,
                                  presentation_name=(item_d.get("presentation_name") or "").strip() or None))
    o.total_amount = round(total, 2)
    await db.commit()
    await db.refresh(o)
    return await _ser_order(o, db)


@router.get("/{oid}")
async def get_order(oid: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == oid, PurchaseOrder.company_id == current_user.company_id))
    o = result.scalar_one_or_none()
    if not o:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    result = await db.execute(select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == oid))
    items = result.scalars().all()
    order_data = await _ser_order(o, db)
    order_data["items"] = [await _ser_item(i, db) for i in items]
    return order_data


@router.post("/{oid}/confirm")
async def confirm_order(oid: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == oid, PurchaseOrder.company_id == current_user.company_id))
    o = result.scalar_one_or_none()
    if not o:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if o.status != "draft":
        raise HTTPException(status_code=409, detail=f"La orden ya está en estado '{o.status}'")
    result = await db.execute(select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == oid))
    for it in result.scalars().all():
        si = await db.get(SupplyItem, it.supply_item_id)
        if si and si.control_stock:
            qty_before = float(si.stock_qty)
            si.stock_qty = qty_before + float(it.qty)
            si.cost_price = float(it.unit_price)
            db.add(StockMovement(company_id=current_user.company_id, supply_item_id=si.id,
                                  movement_type="purchase", qty=float(it.qty),
                                  qty_before=qty_before, qty_after=float(si.stock_qty),
                                  reference_type="purchase_order", reference_id=o.id,
                                  notes=f"Factura {o.invoice_no or 'S/N'}", created_by=current_user.id))
    o.status = "confirmed"
    await db.commit()
    return {"ok": True, "message": "Entrada confirmada y stock actualizado"}


@router.patch("/{oid}/cancel")
async def cancel_order(oid: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == oid, PurchaseOrder.company_id == current_user.company_id))
    o = result.scalar_one_or_none()
    if not o:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if o.status == "confirmed":
        raise HTTPException(status_code=409, detail="No puedes cancelar una orden ya confirmada")
    o.status = "cancelled"
    await db.commit()
    return {"ok": True}
