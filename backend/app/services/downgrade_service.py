"""
Motor de Downgrade Automático por Plan.

Cuando un asociado baja de plan, este servicio aplica plan_blocked=1
a los registros que exceden los nuevos límites, sin eliminar datos.

Reglas de prioridad al bloquear:
  - users:    conservar ADMIN más antiguo primero (role_id ASC, id ASC)
  - pos_waiters: conservar más antiguos (id ASC)
  - otros:    conservar más antiguos (id ASC)

Datos históricos (pos_invoices, pos_receipts, tasks ya creadas) NUNCA se bloquean.
Los límites diarios se verifican en el momento de creación, no aquí.
"""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text, func

from app.models.user_model import User
from app.models.product_model import Product
from app.models.product_category_model import ProductCategory
from app.models.worker_model import Worker
from app.models.client_model import Client
from app.models.bodega_item_model import BodegaItem
from app.models.asset_model import Asset
from app.services.plan_limits_service import get_limits


# Mapeo: campo de límite → (Model ORM, columna de orden secundaria)
ORM_RESOURCES = {
    "max_products":    (Product,         "id"),
    "max_categories":  (ProductCategory, "id"),
    "max_workers":     (Worker,          "id"),
    "max_clients":     (Client,          "id"),
    "max_bodega_items": (BodegaItem,     "id"),
    "max_assets":      (Asset,           "id"),
}


async def _block_orm_resource(
    company_id: int,
    model,
    limit: int,
    db: AsyncSession,
    order_columns: list,
) -> list[int]:
    """
    Bloquea registros sobrantes del modelo ORM dado.
    Devuelve IDs bloqueados en esta operación.
    """
    now = datetime.now(timezone.utc)

    # Todos los activos (no bloqueados) de la empresa
    stmt = (
        select(model.id)
        .where(model.company_id == company_id, model.plan_blocked == 0)
        .order_by(*order_columns)
    )
    rows = (await db.execute(stmt)).scalars().all()

    if len(rows) <= limit:
        return []

    to_keep = set(rows[:limit])
    to_block = [r for r in rows if r not in to_keep]

    if to_block:
        await db.execute(
            update(model)
            .where(model.id.in_(to_block))
            .values(plan_blocked=1, plan_blocked_at=now)
        )
    return to_block


async def _unblock_orm_resource(
    company_id: int,
    model,
    record_ids: list[int],
    db: AsyncSession,
) -> list[int]:
    """Desbloquea registros específicos de un modelo ORM."""
    if not record_ids:
        return []
    await db.execute(
        update(model)
        .where(model.company_id == company_id, model.id.in_(record_ids))
        .values(plan_blocked=0, plan_blocked_at=None)
    )
    return record_ids


async def _block_users(company_id: int, limit: int, db: AsyncSession) -> list[int]:
    """
    Bloquea usuarios sobrantes.
    Prioridad: role_id ASC (ADMIN primero), id ASC (más antiguo primero).
    """
    now = datetime.now(timezone.utc)

    stmt = (
        select(User.id)
        .where(User.company_id == company_id, User.plan_blocked == 0)
        .order_by(User.role_id.asc(), User.id.asc())
    )
    rows = (await db.execute(stmt)).scalars().all()

    if len(rows) <= limit:
        return []

    to_keep = set(rows[:limit])
    to_block = [r for r in rows if r not in to_keep]

    if to_block:
        await db.execute(
            update(User)
            .where(User.id.in_(to_block))
            .values(plan_blocked=1, plan_blocked_at=now, is_active=False)
        )
    return to_block


async def _block_waiters(company_id: int, limit: int, db: AsyncSession) -> list[int]:
    """Bloquea meseros POS sobrantes (tabla raw SQL)."""
    now = now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    rows = (await db.execute(
        text("SELECT id FROM pos_waiters WHERE company_id = :cid AND plan_blocked = 0 ORDER BY id ASC"),
        {"cid": company_id},
    )).fetchall()

    ids = [r[0] for r in rows]
    if len(ids) <= limit:
        return []

    to_block = ids[limit:]
    if to_block:
        placeholders = ",".join(str(i) for i in to_block)
        await db.execute(
            text(f"UPDATE pos_waiters SET plan_blocked=1, plan_blocked_at=:ts WHERE id IN ({placeholders})"),
            {"ts": now_str},
        )
    return to_block


async def _unblock_waiters(company_id: int, record_ids: list[int], db: AsyncSession) -> list[int]:
    """Desbloquea meseros POS específicos."""
    if not record_ids:
        return []
    placeholders = ",".join(str(i) for i in record_ids)
    await db.execute(
        text(f"UPDATE pos_waiters SET plan_blocked=0, plan_blocked_at=NULL WHERE company_id=:cid AND id IN ({placeholders})"),
        {"cid": company_id},
    )
    return record_ids


# ─────────────────────────────────────────────────────────────────────────────
# API PÚBLICA
# ─────────────────────────────────────────────────────────────────────────────

async def apply_downgrade_blocks(company_id: int, db: AsyncSession) -> dict:
    """
    Aplica bloqueos según los límites actuales del plan del asociado.
    Llámalo después de haber guardado el nuevo plan en company_plan_limits.

    Retorna un resumen de cuántos registros se bloquearon por tipo.
    """
    limits = await get_limits(company_id, db)
    summary = {}

    # Usuarios
    max_u = limits.get("max_users", -1)
    if max_u != -1:
        blocked = await _block_users(company_id, max_u, db)
        if blocked:
            summary["users"] = blocked

    # Meseros POS
    max_w = limits.get("max_waiters", -1)
    if max_w != -1:
        blocked = await _block_waiters(company_id, max_w, db)
        if blocked:
            summary["pos_waiters"] = blocked

    # Recursos ORM genéricos
    for field, (model, _) in ORM_RESOURCES.items():
        max_val = limits.get(field, -1)
        if max_val == -1:
            continue
        order_col = getattr(model, "id")
        blocked = await _block_orm_resource(company_id, model, max_val, db, [order_col])
        if blocked:
            summary[model.__tablename__] = blocked

    await db.commit()
    return summary


async def preview_downgrade_blocks(company_id: int, new_limits: dict, db: AsyncSession) -> dict:
    """
    Calcula qué se bloquearía si se aplicaran new_limits, SIN modificar la BD.
    Usado por el endpoint de preview antes de confirmar el cambio de plan.

    new_limits: dict con los campos de límite del nuevo plan.
    Retorna: {tabla: {count: N, sample: [nombres...]}}
    """
    preview = {}

    # Usuarios
    max_u = new_limits.get("max_users", -1)
    if max_u != -1:
        rows = (await db.execute(
            select(User.id, User.nombre, User.role_id)
            .where(User.company_id == company_id, User.plan_blocked == 0)
            .order_by(User.role_id.asc(), User.id.asc())
        )).all()
        excess = rows[max_u:]
        if excess:
            preview["users"] = {
                "count": len(excess),
                "sample": [r.nombre for r in excess[:5]],
            }

    # Meseros POS
    max_pw = new_limits.get("max_waiters", -1)
    if max_pw != -1:
        rows = (await db.execute(
            text("SELECT id, name FROM pos_waiters WHERE company_id=:cid AND plan_blocked=0 ORDER BY id ASC"),
            {"cid": company_id},
        )).fetchall()
        excess = rows[max_pw:]
        if excess:
            preview["pos_waiters"] = {
                "count": len(excess),
                "sample": [r[1] for r in excess[:5]],
            }

    # Recursos ORM genéricos
    label_map = {
        "max_products":    (Product,         "products",    "name"),
        "max_categories":  (ProductCategory, "categories",  "name"),
        "max_workers":     (Worker,          "workers",     "name"),
        "max_clients":     (Client,          "clients",     "name"),
        "max_bodega_items": (BodegaItem,     "bodega_items", "nombre"),
        "max_assets":      (Asset,           "assets",      "name"),
    }
    for field, (model, key, name_col) in label_map.items():
        max_val = new_limits.get(field, -1)
        if max_val == -1:
            continue
        name_attr = getattr(model, name_col)
        rows = (await db.execute(
            select(model.id, name_attr)
            .where(model.company_id == company_id, model.plan_blocked == 0)
            .order_by(model.id.asc())
        )).all()
        excess = rows[max_val:]
        if excess:
            preview[key] = {
                "count": len(excess),
                "sample": [r[1] for r in excess[:5]],
            }

    return preview


async def unblock_records(
    company_id: int,
    resource: str,
    record_ids: list[int],
    db: AsyncSession,
) -> dict:
    """
    Desbloquea registros específicos (uso exclusivo SYSADMIN).
    resource: 'users' | 'pos_waiters' | 'products' | 'categories' |
              'workers' | 'clients' | 'bodega_items' | 'assets'
    """
    resource_map = {
        "users":        (User,            None),
        "products":     (Product,         None),
        "categories":   (ProductCategory, None),
        "workers":      (Worker,          None),
        "clients":      (Client,          None),
        "bodega_items": (BodegaItem,      None),
        "assets":       (Asset,           None),
    }

    if resource == "pos_waiters":
        unblocked = await _unblock_waiters(company_id, record_ids, db)
        await db.commit()
        return {"unblocked": unblocked, "resource": resource}

    if resource not in resource_map:
        return {"error": f"Recurso '{resource}' no reconocido"}

    model, _ = resource_map[resource]

    # Para usuarios también reactivamos is_active
    if resource == "users":
        await db.execute(
            update(User)
            .where(User.company_id == company_id, User.id.in_(record_ids))
            .values(plan_blocked=0, plan_blocked_at=None, is_active=True)
        )
    else:
        await _unblock_orm_resource(company_id, model, record_ids, db)

    await db.commit()
    return {"unblocked": record_ids, "resource": resource}


async def get_blocked_summary(company_id: int, db: AsyncSession) -> dict:
    """
    Devuelve todos los registros bloqueados por plan para un asociado.
    Usado por la vista SYSADMIN de desbloqueo manual.
    """
    result = {}

    # Usuarios bloqueados
    rows = (await db.execute(
        select(User.id, User.nombre, User.email, User.role_id)
        .where(User.company_id == company_id, User.plan_blocked == 1)
        .order_by(User.id)
    )).all()
    if rows:
        result["users"] = [{"id": r.id, "name": r.nombre, "email": r.email, "role_id": r.role_id} for r in rows]

    # Meseros bloqueados
    rows = (await db.execute(
        text("SELECT id, name, phone FROM pos_waiters WHERE company_id=:cid AND plan_blocked=1 ORDER BY id"),
        {"cid": company_id},
    )).fetchall()
    if rows:
        result["pos_waiters"] = [{"id": r[0], "name": r[1], "phone": r[2]} for r in rows]

    # Recursos ORM
    label_map = {
        "products":    (Product,         "name"),
        "categories":  (ProductCategory, "name"),
        "workers":     (Worker,          "name"),
        "clients":     (Client,          "name"),
        "bodega_items": (BodegaItem,     "nombre"),
        "assets":      (Asset,           "name"),
    }
    for key, (model, name_col) in label_map.items():
        name_attr = getattr(model, name_col)
        rows = (await db.execute(
            select(model.id, name_attr)
            .where(model.company_id == company_id, model.plan_blocked == 1)
            .order_by(model.id)
        )).all()
        if rows:
            result[key] = [{"id": r[0], "name": r[1]} for r in rows]

    return result
