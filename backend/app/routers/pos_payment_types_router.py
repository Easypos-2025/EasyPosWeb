from fastapi import Depends
from app.auth.tenant import tenant_guard
import io
import uuid

from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from PIL import Image, ImageOps
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.utils.storage import upload_file, delete_file

# Aislamiento multi-tenant: valida todo company_id que envíe el navegador (CLAUDE.md §6)
router = APIRouter(prefix="/api/payment-types", tags=["Payment Types"], dependencies=[Depends(tenant_guard)])


# ─── Billetes rápidos (pago en efectivo) — máx. 10 por empresa, con foto ──────
# Declarados antes de /{payment_id} para que esa ruta no los capture.
_MAX_BILLETES = 10
_FOTO_MAX_BYTES = 5 * 1024 * 1024
_FOTO_TIPOS = {"image/jpeg", "image/png", "image/webp"}


def _procesar_foto_billete(content: bytes) -> bytes:
    """Valida que sea una imagen real (JPEG/PNG/WebP) y la re-codifica a WebP de máx.
    640 px: descarta metadatos y cualquier contenido que no sea la imagen."""
    try:
        with Image.open(io.BytesIO(content)) as probe:
            if probe.format not in ("JPEG", "PNG", "WEBP"):
                raise ValueError
            probe.verify()
        img = Image.open(io.BytesIO(content))
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((640, 640), Image.LANCZOS)
        out = io.BytesIO()
        img.save(out, format="WEBP", quality=82)
        return out.getvalue()
    except (ValueError, OSError, Image.DecompressionBombError):
        raise HTTPException(status_code=400, detail="El archivo no es una imagen válida (JPG, PNG o WebP)")


@router.get("/billetes")
async def list_billetes(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rows = (await db.execute(text(
        "SELECT value, image_path FROM pos_cash_denominations WHERE company_id = :cid ORDER BY sort_order, value DESC"
    ), {"cid": current_user.company_id})).mappings().all()
    return [{"value": int(r["value"]), "image_path": r["image_path"]} for r in rows]


@router.put("/billetes")
async def set_billetes(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Reemplaza la lista de billetes de la empresa (valores enteros > 0, sin repetir).
    Cada billete que se mantiene conserva su foto; la de los eliminados se borra."""
    raw = body.get("values") or []
    if not isinstance(raw, list):
        raise HTTPException(status_code=422, detail="values debe ser una lista")
    try:
        values = [int(v) for v in raw]
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Los valores deben ser números enteros")
    values = list(dict.fromkeys(v for v in values if 0 < v <= 100_000_000))
    if len(values) > _MAX_BILLETES:
        raise HTTPException(status_code=422, detail=f"Máximo {_MAX_BILLETES} billetes")
    cid = current_user.company_id
    fotos = {int(r[0]): r[1] for r in (await db.execute(text(
        "SELECT value, image_path FROM pos_cash_denominations WHERE company_id = :cid"
    ), {"cid": cid})).all()}
    await db.execute(text("DELETE FROM pos_cash_denominations WHERE company_id = :cid"), {"cid": cid})
    for i, v in enumerate(values):
        await db.execute(text(
            "INSERT INTO pos_cash_denominations (company_id, value, sort_order, image_path) VALUES (:cid, :v, :o, :img)"
        ), {"cid": cid, "v": v, "o": i, "img": fotos.get(v)})
    await db.commit()
    for v, path in fotos.items():
        if path and v not in values:
            await delete_file(path)
    return {"ok": True, "billetes": [{"value": v, "image_path": fotos.get(v)} for v in values]}


@router.post("/billetes/{value}/foto")
async def foto_billete(
    value: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    cid = current_user.company_id
    old = (await db.execute(text(
        "SELECT image_path FROM pos_cash_denominations WHERE company_id = :cid AND value = :v"
    ), {"cid": cid, "v": value})).first()
    if old is None:
        raise HTTPException(status_code=404, detail="Guarde primero el billete")
    if file.content_type not in _FOTO_TIPOS:
        raise HTTPException(status_code=400, detail="Tipo de archivo no permitido (JPG, PNG o WebP)")
    content = await file.read(_FOTO_MAX_BYTES + 1)
    if len(content) > _FOTO_MAX_BYTES:
        raise HTTPException(status_code=400, detail="Imagen demasiado grande (máx 5 MB)")
    webp = _procesar_foto_billete(content)
    url = await upload_file(webp, f"billetes/{cid}/{value}_{uuid.uuid4().hex[:12]}.webp")
    await db.execute(text(
        "UPDATE pos_cash_denominations SET image_path = :url WHERE company_id = :cid AND value = :v"
    ), {"url": url, "cid": cid, "v": value})
    await db.commit()
    if old[0]:
        await delete_file(old[0])
    return {"ok": True, "image_path": url}


@router.delete("/billetes/{value}/foto")
async def quitar_foto_billete(
    value: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    cid = current_user.company_id
    old = (await db.execute(text(
        "SELECT image_path FROM pos_cash_denominations WHERE company_id = :cid AND value = :v"
    ), {"cid": cid, "v": value})).scalar()
    await db.execute(text(
        "UPDATE pos_cash_denominations SET image_path = NULL WHERE company_id = :cid AND value = :v"
    ), {"cid": cid, "v": value})
    await db.commit()
    if old:
        await delete_file(old)
    return {"ok": True}

# ─── Listar ────────────────────────────────────────────────────────────────────
@router.get("")
async def list_payment_types(
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    rows = (await db.execute(text("""
        SELECT id, company_id, name, is_active, is_default,
               select_card, ask_notes,
               validate_amount, validate_number, ask_customer
        FROM pos_payment_types
        WHERE company_id = :cid
        ORDER BY is_default DESC, id ASC
    """), {"cid": company_id})).mappings().all()
    return [dict(r) for r in rows]


# ─── Crear ─────────────────────────────────────────────────────────────────────
@router.post("")
async def create_payment_type(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = body.get("company_id")
    name       = (body.get("name") or "").strip()
    if not company_id or not name:
        raise HTTPException(status_code=422, detail="company_id y name son requeridos")

    # Siguiente id para esta empresa
    row = (await db.execute(text(
        "SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM pos_payment_types WHERE company_id = :cid"
    ), {"cid": company_id})).mappings().first()
    next_id = int(row["next_id"])

    is_default = int(bool(body.get("is_default", 0)))

    # Si es default, quitar default al resto
    if is_default:
        await db.execute(text(
            "UPDATE pos_payment_types SET is_default = 0 WHERE company_id = :cid"
        ), {"cid": company_id})

    await db.execute(text("""
        INSERT INTO pos_payment_types
            (id, company_id, name, is_active, is_default,
             select_card, ask_notes,
             validate_amount, validate_number, ask_customer, synced)
        VALUES
            (:id, :cid, :name, :active, :def,
             :card, :notes, :val_amt, :val_num, :ask_cust, 0)
    """), {
        "id":       next_id,
        "cid":      company_id,
        "name":     name,
        "active":   int(bool(body.get("is_active", 1))),
        "def":      is_default,
        "card":     int(bool(body.get("select_card", 0))),
        "notes":    int(bool(body.get("ask_notes", 0))),
        "val_amt":  int(bool(body.get("validate_amount", 0))),
        "val_num":  int(bool(body.get("validate_number", 0))),
        "ask_cust": int(bool(body.get("ask_customer", 0))),
    })
    await db.commit()

    return {"id": next_id, "company_id": company_id, "name": name}


# ─── Actualizar ────────────────────────────────────────────────────────────────
@router.put("/{payment_id}")
async def update_payment_type(
    payment_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = body.get("company_id")
    name       = (body.get("name") or "").strip()
    if not company_id or not name:
        raise HTTPException(status_code=422, detail="company_id y name son requeridos")

    exists = (await db.execute(text(
        "SELECT id FROM pos_payment_types WHERE id = :pid AND company_id = :cid"
    ), {"pid": payment_id, "cid": company_id})).mappings().first()
    if not exists:
        raise HTTPException(status_code=404, detail="Forma de pago no encontrada")

    is_default = int(bool(body.get("is_default", 0)))
    if is_default:
        await db.execute(text(
            "UPDATE pos_payment_types SET is_default = 0 WHERE company_id = :cid AND id != :pid"
        ), {"cid": company_id, "pid": payment_id})

    await db.execute(text("""
        UPDATE pos_payment_types SET
            name             = :name,
            is_active        = :active,
            is_default       = :def,
            select_card      = :card,
            ask_notes        = :notes,
            validate_amount  = :val_amt,
            validate_number  = :val_num,
            ask_customer     = :ask_cust
        WHERE id = :pid AND company_id = :cid
    """), {
        "name":     name,
        "active":   int(bool(body.get("is_active", 1))),
        "def":      is_default,
        "card":     int(bool(body.get("select_card", 0))),
        "notes":    int(bool(body.get("ask_notes", 0))),
        "val_amt":  int(bool(body.get("validate_amount", 0))),
        "val_num":  int(bool(body.get("validate_number", 0))),
        "ask_cust": int(bool(body.get("ask_customer", 0))),
        "pid":      payment_id,
        "cid":      company_id,
    })
    await db.commit()
    return {"ok": True}


# ─── Eliminar ──────────────────────────────────────────────────────────────────
@router.delete("/{payment_id}")
async def delete_payment_type(
    payment_id: int,
    company_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Verificar que no tenga pagos registrados
    used = (await db.execute(text("""
        SELECT COUNT(*) AS cnt FROM pos_receipt_payment_methods
        WHERE payment_method_id = :pid AND company_id = :cid
    """), {"pid": payment_id, "cid": company_id})).mappings().first()

    if used and int(used["cnt"]) > 0:
        raise HTTPException(
            status_code=409,
            detail=f"No se puede eliminar: esta forma de pago tiene {used['cnt']} pago(s) registrado(s)"
        )

    await db.execute(text(
        "DELETE FROM pos_payment_types WHERE id = :pid AND company_id = :cid"
    ), {"pid": payment_id, "cid": company_id})
    await db.commit()
    return {"ok": True}


# ─── Toggle activo ─────────────────────────────────────────────────────────────
@router.patch("/{payment_id}/toggle-active")
async def toggle_active(
    payment_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    company_id = body.get("company_id")
    if not company_id:
        raise HTTPException(status_code=422, detail="company_id requerido")

    row = (await db.execute(text(
        "SELECT is_active FROM pos_payment_types WHERE id = :pid AND company_id = :cid"
    ), {"pid": payment_id, "cid": company_id})).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Forma de pago no encontrada")

    new_val = 0 if row["is_active"] else 1
    await db.execute(text(
        "UPDATE pos_payment_types SET is_active = :v WHERE id = :pid AND company_id = :cid"
    ), {"v": new_val, "pid": payment_id, "cid": company_id})
    await db.commit()
    return {"is_active": new_val}
