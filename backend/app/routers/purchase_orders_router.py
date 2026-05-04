from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.purchase_order_model import PurchaseOrder
from app.models.purchase_order_item_model import PurchaseOrderItem
from app.models.supply_item_model import SupplyItem
from app.models.supplier_model import Supplier
from app.models.stock_movement_model import StockMovement
from app.auth.dependencies import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/purchase-orders", tags=["PurchaseOrders"])


def _ser_order(o: PurchaseOrder, db: Session) -> dict:
    sup = db.get(Supplier, o.supplier_id) if o.supplier_id else None
    return {
        "id":           o.id,
        "company_id":   o.company_id,
        "supplier_id":  o.supplier_id,
        "supplier_name": sup.name if sup else None,
        "invoice_no":   o.invoice_no,
        "order_date":   o.order_date.isoformat() if o.order_date else None,
        "total_amount": float(o.total_amount),
        "notes":        o.notes,
        "status":       o.status,
        "created_at":   o.created_at.isoformat() if o.created_at else None,
    }


def _ser_item(i: PurchaseOrderItem, db: Session) -> dict:
    si = db.get(SupplyItem, i.supply_item_id)
    return {
        "id":                i.id,
        "purchase_order_id": i.purchase_order_id,
        "supply_item_id":    i.supply_item_id,
        "supply_item_name":  si.name if si else "—",
        "qty":               float(i.qty),
        "unit_price":        float(i.unit_price),
        "subtotal":          float(i.subtotal),
        "presentation_name": i.presentation_name,
    }


@router.get("/")
def list_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = db.query(PurchaseOrder).filter(
        PurchaseOrder.company_id == current_user.company_id
    ).order_by(PurchaseOrder.order_date.desc()).all()
    return [_ser_order(o, db) for o in orders]


@router.post("/")
def create_order(data: dict = Body(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        order_date = date.fromisoformat(data.get("order_date") or date.today().isoformat())
    except ValueError:
        order_date = date.today()

    o = PurchaseOrder(
        company_id=current_user.company_id,
        supplier_id=data.get("supplier_id"),
        invoice_no=(data.get("invoice_no") or "").strip() or None,
        order_date=order_date,
        notes=(data.get("notes") or "").strip() or None,
        status="draft",
        created_by=current_user.id,
    )
    db.add(o); db.commit(); db.refresh(o)

    items_data = data.get("items", [])
    total = 0
    for item_d in items_data:
        qty = float(item_d.get("qty", 0))
        unit_price = float(item_d.get("unit_price", 0))
        subtotal = round(qty * unit_price, 2)
        total += subtotal
        it = PurchaseOrderItem(
            purchase_order_id=o.id,
            supply_item_id=item_d["supply_item_id"],
            qty=qty,
            unit_price=unit_price,
            subtotal=subtotal,
            presentation_name=(item_d.get("presentation_name") or "").strip() or None,
        )
        db.add(it)

    o.total_amount = round(total, 2)
    db.commit(); db.refresh(o)
    return _ser_order(o, db)


@router.get("/{oid}")
def get_order(oid: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    o = db.query(PurchaseOrder).filter(PurchaseOrder.id == oid, PurchaseOrder.company_id == current_user.company_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    items = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.purchase_order_id == oid).all()
    result = _ser_order(o, db)
    result["items"] = [_ser_item(i, db) for i in items]
    return result


@router.post("/{oid}/confirm")
def confirm_order(oid: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    o = db.query(PurchaseOrder).filter(PurchaseOrder.id == oid, PurchaseOrder.company_id == current_user.company_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if o.status != "draft":
        raise HTTPException(status_code=409, detail=f"La orden ya está en estado '{o.status}'")

    items = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.purchase_order_id == oid).all()
    for it in items:
        si = db.get(SupplyItem, it.supply_item_id)
        if si and si.control_stock:
            qty_before = float(si.stock_qty)
            si.stock_qty = qty_before + float(it.qty)
            si.cost_price = float(it.unit_price)
            mov = StockMovement(
                company_id=current_user.company_id,
                supply_item_id=si.id,
                movement_type="purchase",
                qty=float(it.qty),
                qty_before=qty_before,
                qty_after=float(si.stock_qty),
                reference_type="purchase_order",
                reference_id=o.id,
                notes=f"Factura {o.invoice_no or 'S/N'}",
                created_by=current_user.id,
            )
            db.add(mov)

    o.status = "confirmed"
    db.commit()
    return {"ok": True, "message": "Entrada confirmada y stock actualizado"}


@router.patch("/{oid}/cancel")
def cancel_order(oid: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    o = db.query(PurchaseOrder).filter(PurchaseOrder.id == oid, PurchaseOrder.company_id == current_user.company_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    if o.status == "confirmed":
        raise HTTPException(status_code=409, detail="No puedes cancelar una orden ya confirmada")
    o.status = "cancelled"
    db.commit()
    return {"ok": True}
