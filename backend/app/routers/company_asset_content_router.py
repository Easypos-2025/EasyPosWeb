from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.company_asset_content_model import CompanyAssetContent
from app.auth.dependencies import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/asset-content", tags=["AssetContent"])


def _ser(c: CompanyAssetContent) -> dict:
    return {
        "id": c.id, "company_id": c.company_id, "type": c.type,
        "content": c.content, "order_index": c.order_index, "is_active": c.is_active,
    }


@router.get("/")
async def list_content(
    type: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(CompanyAssetContent).where(
        CompanyAssetContent.company_id == current_user.company_id,
        CompanyAssetContent.is_active == 1,
    )
    if type in ("requisito", "observacion"):
        stmt = stmt.where(CompanyAssetContent.type == type)
    stmt = stmt.order_by(CompanyAssetContent.type, CompanyAssetContent.order_index)
    result = await db.execute(stmt)
    return [_ser(c) for c in result.scalars().all()]


@router.get("/all")
async def list_all_content(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CompanyAssetContent)
        .where(CompanyAssetContent.company_id == current_user.company_id)
        .order_by(CompanyAssetContent.type, CompanyAssetContent.order_index)
    )
    return [_ser(c) for c in result.scalars().all()]


@router.get("/public/{company_id}")
async def list_public_content(company_id: int, type: str = None, db: AsyncSession = Depends(get_db)):
    """Endpoint público para la landing del activo."""
    stmt = select(CompanyAssetContent).where(
        CompanyAssetContent.company_id == company_id,
        CompanyAssetContent.is_active == 1,
    )
    if type in ("requisito", "observacion"):
        stmt = stmt.where(CompanyAssetContent.type == type)
    stmt = stmt.order_by(CompanyAssetContent.order_index)
    result = await db.execute(stmt)
    return [_ser(c) for c in result.scalars().all()]


@router.post("/")
async def create_content(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = (data.get("content") or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="El contenido es obligatorio")
    type_ = data.get("type", "requisito")
    if type_ not in ("requisito", "observacion"):
        raise HTTPException(status_code=400, detail="Tipo debe ser 'requisito' u 'observacion'")
    c = CompanyAssetContent(
        company_id  = current_user.company_id,
        type        = type_,
        content     = content,
        order_index = int(data.get("order_index") or 0),
        is_active   = int(data.get("is_active") if data.get("is_active") is not None else 1),
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return _ser(c)


@router.put("/{content_id}")
async def update_content(
    content_id: int,
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CompanyAssetContent).where(
            CompanyAssetContent.id == content_id,
            CompanyAssetContent.company_id == current_user.company_id,
        )
    )
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    if "content" in data:
        c.content = (data["content"] or "").strip() or c.content
    if "type" in data and data["type"] in ("requisito", "observacion"):
        c.type = data["type"]
    if "order_index" in data:
        c.order_index = int(data["order_index"] or 0)
    if "is_active" in data:
        c.is_active = int(data["is_active"])
    await db.commit()
    await db.refresh(c)
    return _ser(c)


@router.delete("/{content_id}")
async def delete_content(
    content_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CompanyAssetContent).where(
            CompanyAssetContent.id == content_id,
            CompanyAssetContent.company_id == current_user.company_id,
        )
    )
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    await db.delete(c)
    await db.commit()
    return {"ok": True}
