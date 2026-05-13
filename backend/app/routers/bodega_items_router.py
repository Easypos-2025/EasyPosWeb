from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.bodega_item_model import BodegaItem
from app.auth.dependencies import get_current_user
from app.models.user_model import User
from app.services.plan_limits_service import check_limit

router = APIRouter(prefix="/bodega-items", tags=["BodegaItems"])


def _ser(b: BodegaItem):
    return {
        "id": b.id, "company_id": b.company_id, "nombre": b.nombre,
        "descripcion": b.descripcion, "codigo": b.codigo,
        "cantidad_total": b.cantidad_total, "cantidad_disponible": b.cantidad_disponible,
        "unidad_id": b.unidad_id, "ubicacion_bodega": b.ubicacion_bodega,
        "is_active": b.is_active,
        "created_at": b.created_at.isoformat() if b.created_at else None,
    }


@router.get("/")
async def list_items(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BodegaItem)
        .where(BodegaItem.company_id == current_user.company_id, BodegaItem.is_active == 1)
        .order_by(BodegaItem.nombre)
    )
    return [_ser(i) for i in result.scalars().all()]


@router.post("/")
async def create_item(
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await check_limit(current_user.company_id, "max_bodega_items", BodegaItem, db)
    nombre = (data.get("nombre") or "").strip()
    if not nombre:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    cantidad = int(data.get("cantidad_total", 1))
    if cantidad < 1:
        raise HTTPException(status_code=400, detail="La cantidad debe ser al menos 1")

    item = BodegaItem(
        company_id=current_user.company_id,
        nombre=nombre,
        descripcion=(data.get("descripcion") or "").strip() or None,
        codigo=(data.get("codigo") or "").strip() or None,
        cantidad_total=cantidad,
        cantidad_disponible=cantidad,
        unidad_id=data.get("unidad_id") or None,
        ubicacion_bodega=(data.get("ubicacion_bodega") or "").strip() or None,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return _ser(item)


@router.put("/{item_id}")
async def update_item(
    item_id: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(BodegaItem).where(BodegaItem.id == item_id, BodegaItem.company_id == current_user.company_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")

    nombre = (data.get("nombre") or "").strip()
    if not nombre:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    nueva_cantidad = int(data.get("cantidad_total", item.cantidad_total))
    prestados = item.cantidad_total - item.cantidad_disponible
    if nueva_cantidad < prestados:
        raise HTTPException(
            status_code=409,
            detail=f"No puedes reducir el total a {nueva_cantidad}: hay {prestados} unidad(es) en préstamo"
        )

    diff = nueva_cantidad - item.cantidad_total
    item.nombre              = nombre
    item.descripcion         = (data.get("descripcion") or "").strip() or None
    item.codigo              = (data.get("codigo") or "").strip() or None
    item.cantidad_total      = nueva_cantidad
    item.cantidad_disponible = item.cantidad_disponible + diff
    item.unidad_id           = data.get("unidad_id") or None
    item.ubicacion_bodega    = (data.get("ubicacion_bodega") or "").strip() or None
    item.is_active           = int(data.get("is_active", item.is_active))
    await db.commit()
    await db.refresh(item)
    return _ser(item)


@router.delete("/{item_id}")
async def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(BodegaItem).where(BodegaItem.id == item_id, BodegaItem.company_id == current_user.company_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")

    prestados = item.cantidad_total - item.cantidad_disponible
    if prestados > 0:
        raise HTTPException(
            status_code=409,
            detail=f"No se puede eliminar: hay {prestados} unidad(es) en préstamo"
        )

    await db.delete(item)
    await db.commit()
    return {"message": "Artículo eliminado"}
