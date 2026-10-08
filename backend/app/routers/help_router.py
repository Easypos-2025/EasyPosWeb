import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, case

from app.database import get_db
from app.models.help_article_model import HelpArticle
from app.models.company_model import Company
from app.auth.dependencies import get_current_user, require_sysadmin
from app.models.user_model import User
from app.utils.storage import upload_file, delete_file

router = APIRouter(prefix="/help", tags=["Help"])

ALLOWED_GIF = {".gif", ".webp", ".png", ".jpg", ".jpeg", ".mp4", ".webm"}
MAX_GIF_MB  = 20   # nginx permite 25M (client_max_body_size)


def _tipo_real(content: bytes) -> Optional[str]:
    """Extensión según el contenido real del archivo (no según el nombre)."""
    if content[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if content[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if content[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return ".webp"
    if content[4:8] == b"ftyp":
        return ".mp4"
    if content[:4] == b"\x1a\x45\xdf\xa3":
        return ".webm"
    return None


async def _borrar_archivo(url: Optional[str]) -> None:
    """Borra el archivo del artículo esté en disco local o en DO Spaces."""
    if url and (url.startswith("/uploads/") or "/help/help_" in url):
        await delete_file(url)


def _ser(a: HelpArticle) -> dict:
    return {
        "id":          a.id,
        "profile_id":  a.profile_id,
        "view_route":  a.view_route,
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
    _: User = Depends(require_sysadmin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(HelpArticle).order_by(
        case((HelpArticle.profile_id.is_(None), 0), else_=1),
        HelpArticle.profile_id,
        HelpArticle.category,
        HelpArticle.order_index,
        HelpArticle.id,
    )
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
        view_route  = (data.get("view_route") or "").strip() or None,
        category    = (data.get("category") or "General").strip(),
        title       = title,
        description = (data.get("description") or "").strip() or None,
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
    if "view_route" in data:
        article.view_route = (data["view_route"] or "").strip() or None
    if "category" in data:
        article.category = (data["category"] or "General").strip()
    if "description" in data:
        article.description = (data["description"] or "").strip() or None
    if "gif_url" in data:
        # Solo se permite quitarlo; la URL la asigna únicamente upload-gif
        if not (data["gif_url"] or "").strip() and article.gif_url:
            await _borrar_archivo(article.gif_url)
            article.gif_url = None
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
    await _borrar_archivo(article.gif_url)
    await db.delete(article)
    await db.commit()
    return {"ok": True}


@router.get("/by-route")
async def get_by_route(
    route: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Devuelve el primer artículo activo asociado a una ruta de vista."""
    stmt = select(HelpArticle).where(
        HelpArticle.is_active == 1,
        HelpArticle.view_route == route,
    ).order_by(HelpArticle.order_index, HelpArticle.id).limit(1)
    result = await db.execute(stmt)
    article = result.scalars().first()
    if not article:
        return None
    return _ser(article)


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
        raise HTTPException(status_code=400, detail="Formato no permitido. Usa GIF, WEBP, PNG, JPG, MP4 o WEBM")

    # Leer con tope para no cargar en memoria archivos más grandes que el límite
    limite = MAX_GIF_MB * 1024 * 1024
    content = await file.read(limite + 1)
    if len(content) > limite:
        raise HTTPException(status_code=413, detail=f"El archivo supera {MAX_GIF_MB} MB")

    real = _tipo_real(content)
    if not real:
        raise HTTPException(status_code=400, detail="El contenido del archivo no es una imagen o video válido")
    ext = real

    # Eliminar archivo anterior si existe
    await _borrar_archivo(article.gif_url)

    safe_name = f"help_{article_id}_{uuid.uuid4().hex[:8]}{ext}"
    url = await upload_file(content, f"help/{safe_name}")
    article.gif_url = url
    await db.commit()
    return {"gif_url": url}
