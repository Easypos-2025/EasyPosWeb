from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.task_model import Task
from app.models.user_model import User
from app.models.asset_model import Asset
from app.models.company_model import Company
from app.auth.jwt_handler import decode_access_token
from app.models.user_session_model import UserSession
from app.models.role_model import Role

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
def get_stats(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Token requerido")

    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)

    session = db.query(UserSession).filter(
        UserSession.token == token,
        UserSession.is_active == True
    ).first()

    if not session or payload is None:
        raise HTTPException(status_code=401, detail="Sesión inválida")

    email = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    role = db.query(Role).filter(Role.id == user.role_id).first()
    is_system = role.is_system if role else False

    if is_system:
        total_companies = db.query(Company).count()
        total_users = db.query(User).count()
        total_assets = db.query(Asset).count()
        total_tasks = db.query(Task).count()
    else:
        total_companies = 1
        total_users = db.query(User).filter(User.company_id == user.company_id).count()
        total_assets = db.query(Asset).filter(Asset.company_id == user.company_id).count() if hasattr(Asset, 'company_id') else db.query(Asset).count()
        total_tasks = db.query(Task).count()

    return {
        "total_companies": total_companies,
        "total_users": total_users,
        "total_assets": total_assets,
        "total_tasks": total_tasks,
        "is_system": is_system
    }
