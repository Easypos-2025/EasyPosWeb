from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models.topbar_menu_item_model import TopbarMenuItem
from app.models.user_model import User
from app.models.role_model import Role
from app.models.user_session_model import UserSession
from app.models.company_plan_model import CompanyPlan
from app.auth.jwt_handler import decode_access_token
from app.schemas.topbar_menu_schema import TopbarMenuItemCreate, TopbarMenuItemUpdate

router = APIRouter(prefix="/topbar-menu", tags=["TopbarMenu"])


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


def _is_sysadmin(user: User, db: Session) -> bool:
    role = db.query(Role).filter(Role.id == user.role_id).first()
    return role.is_system if role else False


def _ser(item: TopbarMenuItem):
    return {
        "id": item.id,
        "name": item.name,
        "key": item.key,
        "icon": item.icon,
        "route": item.route,
        "has_evidence": item.has_evidence,
        "min_plan_id": item.min_plan_id,
        "is_active": item.is_active,
        "order_index": item.order_index,
    }


# -------------------------------------------------------
# GET — ítems activos filtrados por plan del usuario
# -------------------------------------------------------
@router.get("")
def get_menu_items(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)

    company_plan = db.query(CompanyPlan).filter(
        CompanyPlan.company_id == user.company_id,
        CompanyPlan.is_active == True
    ).first()
    plan_id = company_plan.plan_id if company_plan else 1

    items = db.query(TopbarMenuItem).filter(
        TopbarMenuItem.is_active == True,
        or_(TopbarMenuItem.min_plan_id == None, TopbarMenuItem.min_plan_id <= plan_id)
    ).order_by(TopbarMenuItem.order_index).all()

    return [_ser(i) for i in items]


# -------------------------------------------------------
# GET ALL — SYSADMIN: todos los ítems sin filtro
# -------------------------------------------------------
@router.get("/all")
def get_all_menu_items(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)
    if not _is_sysadmin(user, db):
        raise HTTPException(status_code=403, detail="Acceso restringido a SYSADMIN")

    items = db.query(TopbarMenuItem).order_by(TopbarMenuItem.order_index).all()
    return [_ser(i) for i in items]


# -------------------------------------------------------
# POST — SYSADMIN: crear ítem
# -------------------------------------------------------
@router.post("")
def create_menu_item(
    data: TopbarMenuItemCreate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)
    if not _is_sysadmin(user, db):
        raise HTTPException(status_code=403, detail="Acceso restringido a SYSADMIN")

    existing = db.query(TopbarMenuItem).filter(TopbarMenuItem.key == data.key).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un ítem con esa clave")

    item = TopbarMenuItem(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return _ser(item)


# -------------------------------------------------------
# PUT — SYSADMIN: actualizar ítem
# -------------------------------------------------------
@router.put("/{item_id}")
def update_menu_item(
    item_id: int,
    data: TopbarMenuItemUpdate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)
    if not _is_sysadmin(user, db):
        raise HTTPException(status_code=403, detail="Acceso restringido a SYSADMIN")

    item = db.query(TopbarMenuItem).filter(TopbarMenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return _ser(item)


# -------------------------------------------------------
# DELETE — SYSADMIN: eliminar ítem
# -------------------------------------------------------
@router.delete("/{item_id}")
def delete_menu_item(
    item_id: int,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)
    if not _is_sysadmin(user, db):
        raise HTTPException(status_code=403, detail="Acceso restringido a SYSADMIN")

    item = db.query(TopbarMenuItem).filter(TopbarMenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")

    db.delete(item)
    db.commit()
    return {"ok": True}
