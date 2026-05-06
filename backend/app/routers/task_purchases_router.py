from fastapi import APIRouter, Depends, Header, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.task_purchase_model import TaskPurchase
from app.models.user_model import User
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from datetime import date

router = APIRouter(prefix="/task-purchases", tags=["TaskPurchases"])


async def _get_user(authorization: str, db: AsyncSession):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    result = await db.execute(select(UserSession).where(UserSession.token == token, UserSession.is_active == True))
    if not result.scalar_one_or_none() or not payload:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    result = await db.execute(select(User).where(User.email == payload.get("sub")))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


def _ser(p: TaskPurchase):
    return {"id": p.id, "task_id": p.task_id, "concept": p.concept, "amount": p.amount,
            "purchase_date": p.purchase_date.isoformat() if p.purchase_date else None,
            "supplier": p.supplier, "invoice_ref": p.invoice_ref,
            "created_at": p.created_at.isoformat() if p.created_at else None}


@router.get("/{task_id:int}")
async def get_purchases(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskPurchase).where(TaskPurchase.task_id == task_id).order_by(TaskPurchase.created_at.asc()))
    return [_ser(p) for p in result.scalars().all()]


@router.post("/{task_id:int}")
async def add_purchase(task_id: int, data: dict = Body(...), authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    concept = (data.get("concept") or "").strip()
    if not concept:
        raise HTTPException(status_code=400, detail="El concepto de la compra es obligatorio")
    pd_str = data.get("purchase_date")
    pd = date.fromisoformat(pd_str) if pd_str else None
    item = TaskPurchase(task_id=task_id, concept=concept, amount=float(data.get("amount", 0)),
                        purchase_date=pd, supplier=(data.get("supplier") or "").strip() or None,
                        invoice_ref=(data.get("invoice_ref") or "").strip() or None, created_by=user.id)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return _ser(item)


@router.delete("/{purchase_id:int}")
async def delete_purchase(purchase_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_user(authorization, db)
    result = await db.execute(select(TaskPurchase).where(TaskPurchase.id == purchase_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    await db.delete(item)
    await db.commit()
    return {"message": "Compra eliminada"}
