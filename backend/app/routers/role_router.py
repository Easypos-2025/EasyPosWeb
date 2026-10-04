from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, text

from app.database import get_db
from app.models.role_model import Role
from app.models.role_module_model import RoleModule
from app.models.system_module_model import SystemModule
from app.models.user_model import User
from app.auth.dependencies import get_current_user
from app.services.plan_limits_service import check_limit
from app.services.permisos import permisos_usuario

router = APIRouter(prefix="/roles", tags=["Roles"])


TIPOS_ACCESO = ("interno", "remoto_login", "remoto_publico")


def _tipo_acceso(data: dict, actual: str = "interno") -> str:
    t = (data.get("access_type") or actual or "interno").strip()
    if t not in TIPOS_ACCESO:
        raise HTTPException(status_code=422, detail="Tipo de acceso no válido")
    return t


def _ser(r: Role) -> dict:
    return {"id": r.id, "name": r.name, "description": r.description,
            "company_id": r.company_id, "is_system": r.is_system,
            "access_type": r.access_type or "interno"}


async def _is_system(user: User, db: AsyncSession) -> bool:
    role = await db.get(Role, user.role_id)
    return role.is_system if role else False


@router.get("/")
async def get_roles(
    company_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if await _is_system(current_user, db):
        if company_id is None:
            raise HTTPException(status_code=400, detail="Se requiere company_id para consultar roles")
        cid = company_id
    else:
        cid = current_user.company_id

    result = await db.execute(
        select(Role).where(Role.company_id == cid, Role.is_system == False).order_by(Role.name)
    )
    return [_ser(r) for r in result.scalars().all()]


@router.post("/")
async def create_role(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if await _is_system(current_user, db):
        cid = data.get("company_id")
        if not cid:
            raise HTTPException(status_code=400, detail="company_id requerido")
    else:
        cid = current_user.company_id
        await check_limit(cid, "max_roles", Role, db)

    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    result = await db.execute(select(Role).where(Role.name == name, Role.company_id == cid))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Ya existe un rol '{name}' en esta empresa")

    role = Role(name=name, description=(data.get("description") or "").strip(), company_id=cid, is_system=False,
                access_type=_tipo_acceso(data))
    db.add(role)
    await db.commit()
    await db.refresh(role)
    # Control de Acceso inicial: un rol Admin con todo; los demás sin permisos (el Admin los activa
    # en Roles → Control de Acceso: todo depende del rol, no del perfil de negocio)
    if "ADMIN" in name.upper():
        await db.execute(text("""
            INSERT IGNORE INTO role_access_permissions (role_id, perm_key)
            SELECT :rid, perm_key FROM access_permissions WHERE is_active = 1
        """), {"rid": role.id})
        await db.commit()
    return _ser(role)


@router.put("/{role_id}")
async def update_role(
    role_id: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    if not await _is_system(current_user, db) and role.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Sin permisos")

    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    result = await db.execute(select(Role).where(Role.name == name, Role.company_id == role.company_id, Role.id != role_id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Ya existe un rol '{name}'")

    role.name = name
    role.description = (data.get("description") or "").strip()
    role.access_type = _tipo_acceso(data, role.access_type)
    await db.commit()
    await db.refresh(role)
    return _ser(role)


@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    if not await _is_system(current_user, db) and role.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Sin permisos")
    await db.delete(role)
    await db.commit()
    return {"message": "Rol eliminado"}


@router.get("/{role_id}/modules/")
async def get_modules_by_role(
    role_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await _rol_de_mi_empresa(db, current_user, role_id)

    if await _is_system(current_user, db):
        result = await db.execute(select(SystemModule).order_by(SystemModule.order_index))
    else:
        result = await db.execute(select(SystemModule).where(SystemModule.is_sysadmin == False).order_by(SystemModule.order_index))
    modules = result.scalars().all()

    result = await db.execute(select(RoleModule).where(RoleModule.role_id == role_id))
    permissions_map = {rm.module_id: rm for rm in result.scalars().all()}

    return [
        {
            "module_id":    m.id,
            "module_name":  m.name,
            "module_route": m.route or "",
            "can_view":     permissions_map[m.id].can_view     if m.id in permissions_map else False,
            "can_view_all": permissions_map[m.id].can_view_all if m.id in permissions_map else False,
            "can_create":   permissions_map[m.id].can_create   if m.id in permissions_map else False,
            "can_edit":     permissions_map[m.id].can_edit     if m.id in permissions_map else False,
            "can_delete":   permissions_map[m.id].can_delete   if m.id in permissions_map else False,
        }
        for m in modules
    ]


@router.post("/{role_id}/modules/")
async def assign_modules_to_role(
    role_id: int,
    modules: List[dict],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    if not await _is_system(current_user, db) and role.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Sin permisos")

    await db.execute(delete(RoleModule).where(RoleModule.role_id == role_id))

    for m in modules:
        db.add(RoleModule(
            role_id=role_id, module_id=m["module_id"],
            can_view=m.get("can_view", True), can_view_all=m.get("can_view_all", False),
            can_create=m.get("can_create", False),
            can_edit=m.get("can_edit", False), can_delete=m.get("can_delete", False),
        ))

    await db.commit()
    return {"message": "Módulos asignados correctamente"}


# ═══════════════════════════════════════════════════════════════════════════
# Control de Acceso por rol (permisos especiales; catálogo en access_permissions)
# ═══════════════════════════════════════════════════════════════════════════
async def _rol_de_mi_empresa(db: AsyncSession, current_user: User, role_id: int) -> Role:
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    if not await _is_system(current_user, db) and role.company_id != current_user.company_id:
        raise HTTPException(status_code=403, detail="Sin permisos")
    return role


@router.get("/access/catalog")
async def access_catalog(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(text("""
        SELECT perm_key, name, group_name, description FROM access_permissions
        WHERE is_active = 1 ORDER BY order_index, name
    """))).mappings().all()
    return [dict(r) for r in rows]


@router.get("/access/me")
async def my_access(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return sorted(await permisos_usuario(db, current_user))


@router.get("/{role_id}/access")
async def role_access(
    role_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _rol_de_mi_empresa(db, current_user, role_id)
    return sorted((await db.execute(text(
        "SELECT perm_key FROM role_access_permissions WHERE role_id = :rid"
    ), {"rid": role_id})).scalars().all())


@router.put("/{role_id}/access")
async def save_role_access(
    role_id: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reemplaza los permisos especiales del rol. Solo un Admin (o SYSADMIN) puede cambiarlos."""
    from app.routers.pos_shift_router import _es_admin
    await _rol_de_mi_empresa(db, current_user, role_id)
    if not await _es_admin(db, current_user):
        raise HTTPException(status_code=403, detail="Solo un administrador puede cambiar el Control de Acceso")
    claves = data.get("keys")
    if not isinstance(claves, list) or len(claves) > 200:
        raise HTTPException(status_code=422, detail="Lista de permisos no válida")
    validas = set((await db.execute(text("SELECT perm_key FROM access_permissions WHERE is_active = 1"))).scalars().all())
    claves = sorted({str(k) for k in claves} & validas)
    await db.execute(text("DELETE FROM role_access_permissions WHERE role_id = :rid"), {"rid": role_id})
    for k in claves:
        await db.execute(text("INSERT INTO role_access_permissions (role_id, perm_key) VALUES (:rid, :k)"),
                         {"rid": role_id, "k": k})
    await db.commit()
    return {"ok": True, "keys": claves}
