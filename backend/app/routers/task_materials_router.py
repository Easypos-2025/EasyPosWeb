from fastapi import APIRouter, Depends, Header, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.task_material_model import TaskMaterial
from app.models.task_expense_model import TaskExpense
from app.models.user_model import User
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from datetime import date

router = APIRouter(prefix="/task-materials", tags=["TaskMaterials"])


async def _get_user(authorization: str, db: AsyncSession):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    result = await db.execute(select(UserSession).where(UserSession.token == token, UserSession.is_active == True))
    if not result.scalar_one_or_none() or not payload:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    uid = payload.get("user_id")
    user = await db.get(User, int(uid)) if uid else None
    if not user:
        result = await db.execute(select(User).where(User.email == payload.get("sub")))
        user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


def _ser_mat(m: TaskMaterial):
    return {"id": m.id, "task_id": m.task_id, "name": m.name, "unit": m.unit,
            "quantity": m.quantity, "unit_cost": m.unit_cost, "total_cost": m.total_cost,
            "created_at": m.created_at.isoformat() if m.created_at else None}

def _ser_exp(e: TaskExpense):
    return {"id": e.id, "task_id": e.task_id, "concept": e.concept, "amount": e.amount,
            "payment_date": e.payment_date.isoformat() if e.payment_date else None,
            "receipt_ref": e.receipt_ref, "created_at": e.created_at.isoformat() if e.created_at else None}


@router.get("/{task_id:int}")
async def get_materials(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskMaterial).where(TaskMaterial.task_id == task_id).order_by(TaskMaterial.created_at.asc()))
    return [_ser_mat(m) for m in result.scalars().all()]


@router.post("/{task_id:int}")
async def add_material(task_id: int, data: dict = Body(...), authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    name = data.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre del material es obligatorio")
    qty = float(data.get("quantity", 1))
    cost = float(data.get("unit_cost", 0))
    m = TaskMaterial(task_id=task_id, name=name, unit=data.get("unit", ""),
                     quantity=qty, unit_cost=cost, total_cost=round(qty * cost, 2), created_by=user.id)
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return _ser_mat(m)


@router.put("/{material_id:int}")
async def update_material(material_id: int, data: dict = Body(...), authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_user(authorization, db)
    result = await db.execute(select(TaskMaterial).where(TaskMaterial.id == material_id))
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Material no encontrado")
    m.name = data.get("name", m.name).strip()
    m.unit = data.get("unit", m.unit)
    m.quantity = float(data.get("quantity", m.quantity))
    m.unit_cost = float(data.get("unit_cost", m.unit_cost))
    m.total_cost = round(m.quantity * m.unit_cost, 2)
    await db.commit()
    await db.refresh(m)
    return _ser_mat(m)


@router.delete("/{material_id:int}")
async def delete_material(material_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_user(authorization, db)
    result = await db.execute(select(TaskMaterial).where(TaskMaterial.id == material_id))
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Material no encontrado")
    await db.delete(m)
    await db.commit()
    return {"message": "Material eliminado"}


# ── GASTOS ──────────────────────────────────────────────────────
expenses_router = APIRouter(prefix="/task-expenses", tags=["TaskExpenses"])


@expenses_router.get("/{task_id}")
async def get_expenses(task_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskExpense).where(TaskExpense.task_id == task_id).order_by(TaskExpense.created_at.asc()))
    return [_ser_exp(e) for e in result.scalars().all()]


@expenses_router.post("/{task_id}")
async def add_expense(task_id: int, data: dict = Body(...), authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    user = await _get_user(authorization, db)
    concept = data.get("concept", "").strip()
    if not concept:
        raise HTTPException(status_code=400, detail="El concepto del gasto es obligatorio")
    pd_str = data.get("payment_date")
    pd = date.fromisoformat(pd_str) if pd_str else None
    e = TaskExpense(task_id=task_id, concept=concept, amount=float(data.get("amount", 0)),
                    payment_date=pd, receipt_ref=data.get("receipt_ref", ""), created_by=user.id)
    db.add(e)
    await db.commit()
    await db.refresh(e)
    return _ser_exp(e)


@expenses_router.delete("/{expense_id}")
async def delete_expense(expense_id: int, authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    await _get_user(authorization, db)
    result = await db.execute(select(TaskExpense).where(TaskExpense.id == expense_id))
    e = result.scalar_one_or_none()
    if not e:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    await db.delete(e)
    await db.commit()
    return {"message": "Gasto eliminado"}
