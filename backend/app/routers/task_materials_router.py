from fastapi import APIRouter, Depends, Header, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.task_material_model import TaskMaterial
from app.models.task_expense_model import TaskExpense
from app.models.user_model import User
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from datetime import date

router = APIRouter(prefix="/task-materials", tags=["TaskMaterials"])


def _get_user(authorization: str, db: Session):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    session = db.query(UserSession).filter(
        UserSession.token == token, UserSession.is_active == True
    ).first()
    if not session or not payload:
        raise HTTPException(status_code=401, detail="Sesión inválida")
    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


# ══════════════════════════════════════════════════════
# MATERIALES
# ══════════════════════════════════════════════════════

@router.get("/{task_id}")
def get_materials(task_id: int, db: Session = Depends(get_db)):
    items = db.query(TaskMaterial).filter(TaskMaterial.task_id == task_id)\
               .order_by(TaskMaterial.created_at.asc()).all()
    return [_ser_mat(m) for m in items]


@router.post("/{task_id}")
def add_material(
    task_id: int,
    data: dict = Body(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)
    name = data.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre del material es obligatorio")

    qty  = float(data.get("quantity", 1))
    cost = float(data.get("unit_cost", 0))

    m = TaskMaterial(
        task_id=    task_id,
        name=       name,
        unit=       data.get("unit", ""),
        quantity=   qty,
        unit_cost=  cost,
        total_cost= round(qty * cost, 2),
        created_by= user.id,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return _ser_mat(m)


@router.put("/{material_id}")
def update_material(
    material_id: int,
    data: dict = Body(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    _get_user(authorization, db)
    m = db.query(TaskMaterial).filter(TaskMaterial.id == material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Material no encontrado")

    m.name      = data.get("name", m.name).strip()
    m.unit      = data.get("unit", m.unit)
    m.quantity  = float(data.get("quantity", m.quantity))
    m.unit_cost = float(data.get("unit_cost", m.unit_cost))
    m.total_cost= round(m.quantity * m.unit_cost, 2)

    db.commit()
    db.refresh(m)
    return _ser_mat(m)


@router.delete("/{material_id}")
def delete_material(
    material_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    _get_user(authorization, db)
    m = db.query(TaskMaterial).filter(TaskMaterial.id == material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Material no encontrado")
    db.delete(m)
    db.commit()
    return {"message": "Material eliminado"}


# ══════════════════════════════════════════════════════
# GASTOS — mismo router, prefijo /task-expenses
# ══════════════════════════════════════════════════════

expenses_router = APIRouter(prefix="/task-expenses", tags=["TaskExpenses"])


@expenses_router.get("/{task_id}")
def get_expenses(task_id: int, db: Session = Depends(get_db)):
    items = db.query(TaskExpense).filter(TaskExpense.task_id == task_id)\
               .order_by(TaskExpense.created_at.asc()).all()
    return [_ser_exp(e) for e in items]


@expenses_router.post("/{task_id}")
def add_expense(
    task_id: int,
    data: dict = Body(...),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)
    concept = data.get("concept", "").strip()
    if not concept:
        raise HTTPException(status_code=400, detail="El concepto del gasto es obligatorio")

    pd_str = data.get("payment_date")
    pd = date.fromisoformat(pd_str) if pd_str else None

    e = TaskExpense(
        task_id=      task_id,
        concept=      concept,
        amount=       float(data.get("amount", 0)),
        payment_date= pd,
        receipt_ref=  data.get("receipt_ref", ""),
        created_by=   user.id,
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return _ser_exp(e)


@expenses_router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    _get_user(authorization, db)
    e = db.query(TaskExpense).filter(TaskExpense.id == expense_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    db.delete(e)
    db.commit()
    return {"message": "Gasto eliminado"}


# ── Serializers ──────────────────────────────────────
def _ser_mat(m: TaskMaterial):
    return {
        "id": m.id, "task_id": m.task_id, "name": m.name,
        "unit": m.unit, "quantity": m.quantity,
        "unit_cost": m.unit_cost, "total_cost": m.total_cost,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }

def _ser_exp(e: TaskExpense):
    return {
        "id": e.id, "task_id": e.task_id, "concept": e.concept,
        "amount": e.amount,
        "payment_date": e.payment_date.isoformat() if e.payment_date else None,
        "receipt_ref": e.receipt_ref,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }
