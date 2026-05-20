import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.database import get_db
from app.models.help_article_model import HelpArticle
from app.models.company_model import Company
from app.auth.dependencies import get_current_user, require_sysadmin
from app.models.user_model import User
from app.utils.storage import upload_file, delete_file

router = APIRouter(prefix="/help", tags=["Help"])

ALLOWED_GIF = {".gif", ".webp", ".png", ".jpg", ".jpeg"}
MAX_GIF_MB  = 8


def _ser(a: HelpArticle) -> dict:
    return {
        "id":          a.id,
        "profile_id":  a.profile_id,
        "category":    a.category,
        "title":       a.title,
        "description": a.description,
        "gif_url":     a.gif_url,
        "keywords":    a.keywords,
        "order_index": a.order_index,
        "is_active":   a.is_active,
        "created_at":  a.created_at.isoformat() if a.created_at else None,
        "updated_at":  a.updated_at.isoformat() if a.updated_at else None,
    }


# ── Endpoint público autenticado — vista del asociado ────────────────────────

@router.get("/")
async def list_help(
    q: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna artículos activos para el perfil del asociado + artículos generales (profile_id=NULL).
    Si q está presente filtra por title, description o keywords.
    """
    company = await db.get(Company, current_user.company_id)
    profile_id = company.business_profile_id if company else None

    stmt = select(HelpArticle).where(
        HelpArticle.is_active == 1,
        or_(
            HelpArticle.profile_id == profile_id,
            HelpArticle.profile_id.is_(None),
        )
    )

    if q and q.strip():
        term = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                HelpArticle.title.ilike(term),
                HelpArticle.description.ilike(term),
                HelpArticle.keywords.ilike(term),
                HelpArticle.category.ilike(term),
            )
        )

    stmt = stmt.order_by(HelpArticle.category, HelpArticle.order_index, HelpArticle.id)
    result = await db.execute(stmt)
    return [_ser(a) for a in result.scalars().all()]


# ── Endpoints SYSADMIN ────────────────────────────────────────────────────────

@router.get("/admin/list")
async def admin_list(
    profile_id: int = None,
    _: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(HelpArticle).order_by(HelpArticle.profile_id.nulls_first(), HelpArticle.category, HelpArticle.order_index)
    if profile_id is not None:
        stmt = select(HelpArticle).where(HelpArticle.profile_id == profile_id).order_by(HelpArticle.category, HelpArticle.order_index)
    result = await db.execute(stmt)
    return [_ser(a) for a in result.scalars().all()]


@router.post("/")
async def create_article(
    data: dict = Body(...),
    _: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    title = (data.get("title") or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="El título es requerido")

    article = HelpArticle(
        profile_id  = data.get("profile_id") or None,
        category    = (data.get("category") or "General").strip(),
        title       = title,
        description = (data.get("description") or "").strip() or None,
        gif_url     = (data.get("gif_url") or "").strip() or None,
        keywords    = (data.get("keywords") or "").strip() or None,
        order_index = int(data.get("order_index") or 0),
        is_active   = int(data.get("is_active") if data.get("is_active") is not None else 1),
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)
    return _ser(article)


@router.put("/{article_id}")
async def update_article(
    article_id: int,
    data: dict = Body(...),
    _: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    article = await db.get(HelpArticle, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")

    if "title" in data:
        title = (data["title"] or "").strip()
        if not title:
            raise HTTPException(status_code=400, detail="El título es requerido")
        article.title = title
    if "profile_id" in data:
        article.profile_id = data["profile_id"] or None
    if "category" in data:
        article.category = (data["category"] or "General").strip()
    if "description" in data:
        article.description = (data["description"] or "").strip() or None
    if "gif_url" in data:
        article.gif_url = (data["gif_url"] or "").strip() or None
    if "keywords" in data:
        article.keywords = (data["keywords"] or "").strip() or None
    if "order_index" in data:
        article.order_index = int(data["order_index"] or 0)
    if "is_active" in data:
        article.is_active = int(data["is_active"])

    await db.commit()
    await db.refresh(article)
    return _ser(article)


@router.delete("/{article_id}")
async def delete_article(
    article_id: int,
    _: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    article = await db.get(HelpArticle, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
    if article.gif_url and article.gif_url.startswith("/uploads/"):
        await delete_file(article.gif_url)
    await db.delete(article)
    await db.commit()
    return {"ok": True}


@router.post("/{article_id}/upload-gif")
async def upload_gif(
    article_id: int,
    file: UploadFile = File(...),
    _: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    article = await db.get(HelpArticle, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_GIF:
        raise HTTPException(status_code=400, detail="Formato no permitido. Usa GIF, WEBP, PNG o JPG")

    content = await file.read()
    if len(content) > MAX_GIF_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"El archivo supera {MAX_GIF_MB} MB")

    # Eliminar GIF anterior si existe
    if article.gif_url and article.gif_url.startswith("/uploads/"):
        await delete_file(article.gif_url)

    safe_name = f"help_{article_id}_{uuid.uuid4().hex[:8]}{ext}"
    url = await upload_file(content, f"help/{safe_name}")
    article.gif_url = url
    await db.commit()
    return {"gif_url": url}
