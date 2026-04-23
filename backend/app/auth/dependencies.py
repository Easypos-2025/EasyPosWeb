from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user_model import User
from app.auth.jwt_handler import decode_access_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.role_model import Role
from app.database import get_db



#security = HTTPBearer()
security = HTTPBearer(auto_error=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Solo usa HTTPBearer (Swagger y frontend)
    """

    try:
        if not credentials or not credentials.credentials:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated"
            )

        token = credentials.credentials

        payload = decode_access_token(token)

        if payload is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        email = payload.get("sub")

        if not email:
            raise HTTPException(
                status_code=401,
                detail="Token inválido"
            )

        user = db.query(User).filter(User.email == email).first()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Usuario no encontrado"
            )

        return user

    except Exception as e:
        print("ERROR REAL:", str(e))
        raise HTTPException(
            status_code=401,
            detail="No autorizado"
        )
        
#ADMIN(felxible)
def require_admin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role = db.get(Role, current_user.role_id)

    if not role:
        raise HTTPException(status_code=403, detail="Rol no válido")

    # 🔥 OPCIÓN 1 (RECOMENDADA)
    if role.is_system:
        return current_user

    ## 🔥 OPCIÓN 2 (SI QUIERES ADMIN NORMAL TAMBIÉN)
    #if role.name == "ADMIN":
    #    return current_user

    raise HTTPException(
        status_code=403,
        detail="Acceso solo para administradores"
    )

# SYSADMIN    
def require_sysadmin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role = db.get(Role, current_user.role_id)

    if not role or not role.is_system:
        raise HTTPException(status_code=403, detail="Solo SYSADMIN")

    return current_user

#GENERICO(muy poderoso)
def require_role(role_name: str):
    def checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        role = db.get(Role, current_user.role_id)

        if not role or role.name != role_name:
            raise HTTPException(status_code=403, detail="Acceso denegado")

        return current_user

    return checker





