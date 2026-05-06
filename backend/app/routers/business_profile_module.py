from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database import get_db
from app.models.business_profile_module import BusinessProfileModule

router = APIRouter(prefix="/business-profile-module", tags=["BusinessProfileModule"])


@router.put("/reorder/")
async def reorder_modules(data: list[dict], db: AsyncSession = Depends(get_db)):
    if not data:
        return {"message": "Sin datos"}

    result = await db.execute(select(BusinessProfileModule).where(BusinessProfileModule.id == data[0]["id"]))
    first = result.scalar_one_or_none()

    if first:
        keep_ids = [item["id"] for item in data]
        await db.execute(
            delete(BusinessProfileModule).where(
                BusinessProfileModule.business_profile_id == first.business_profile_id,
                BusinessProfileModule.id.notin_(keep_ids)
            )
        )

    for item in data:
        result = await db.execute(select(BusinessProfileModule).where(BusinessProfileModule.id == item["id"]))
        module = result.scalar_one_or_none()
        if module:
            module.sort_order = item["sort_order"]
            module.parent_id = int(item["parent_id"]) if item.get("parent_id") is not None else None

    await db.commit()
    return {"message": "Orden actualizado correctamente"}
