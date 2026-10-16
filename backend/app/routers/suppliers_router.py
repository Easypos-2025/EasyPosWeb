"""
Proveedores (suppliers = proveedores del escritorio).

Campos del escritorio → web:
  Id_Proveedor     → id_proveedor (consecutivo por empresa, lo asigna el sistema)
  Empresa          → name              (obligatorio)
  Nit              → nit               (obligatorio, único por empresa)
  Telefono_Celular → telefono_celular  (obligatorio)
  Mail_Empresa → email · Direccion → address · Telefono_Fijo → phone · Observaciones → notes (opcionales)
  Activo           → is_active
"""
import re
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, StringConstraints, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.database import get_db
from app.models.supplier_model import Supplier
from app.auth.dependencies import get_current_user
from app.models.user_model import User
from app.auth.bodega_guard import bloqueo_bodega

router = APIRouter(prefix="/suppliers", tags=["Suppliers"],
                   dependencies=[Depends(bloqueo_bodega("Los proveedores"))])

# Longitudes de la tabla proveedores del escritorio
Txt50  = Annotated[str, StringConstraints(strip_whitespace=True, max_length=50)]
Txt255 = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SupplierIn(BaseModel):
    name:             Optional[Txt255] = None
    nit:              Optional[Txt50]  = None
    telefono_celular: Optional[Txt50]  = None
    email:            Optional[Txt255] = None
    address:          Optional[Txt50]  = None
    phone:            Optional[Txt50]  = None
    notes:            Optional[Txt50]  = None
    is_active:        Optional[Annotated[int, Field(ge=0, le=1)]] = None

    @field_validator("email")
    @classmethod
    def _email(cls, v):
        if v and not _EMAIL.match(v):
            raise ValueError("Correo no válido")
        return v


_OBLIGATORIOS = (("name", "El nombre del proveedor es obligatorio"),
                 ("nit", "El NIT es obligatorio"),
                 ("telefono_celular", "El teléfono celular es obligatorio"))


def _ser(s: Supplier) -> dict:
    return {
        "id":           s.id,
        "id_proveedor": s.id_proveedor,
        "telefono_celular": s.telefono_celular,
        "company_id":   s.company_id,
        "name":         s.name,
        "nit":          s.nit,
        "contact_name": s.contact_name,
        "email":        s.email,
        "phone":        s.phone,
        "address":      s.address,
        "notes":        s.notes,
        "is_active":    s.is_active,
        "created_at":   s.created_at.isoformat() if s.created_at else None,
    }


async def _get(db: AsyncSession, cid: int, sid: int) -> Supplier:
    s = (await db.execute(
        select(Supplier).where(Supplier.id == sid, Supplier.company_id == cid)
    )).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return s


async def _nit_libre(db: AsyncSession, cid: int, nit: str, excepto: Optional[int] = None):
    dup = (await db.execute(text("""
        SELECT name FROM suppliers
        WHERE company_id = :cid AND UPPER(TRIM(nit)) = UPPER(:nit) AND id <> :ex
        LIMIT 1
    """), {"cid": cid, "nit": nit, "ex": excepto or 0})).scalar()
    if dup:
        raise HTTPException(status_code=409, detail=f"Ya existe un proveedor con ese NIT ({dup})")


@router.get("/")
async def list_suppliers(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Supplier).where(Supplier.company_id == current_user.company_id).order_by(Supplier.name)
    )
    return [_ser(s) for s in result.scalars().all()]


@router.post("/")
async def create_supplier(data: SupplierIn, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = current_user.company_id
    for campo, msg in _OBLIGATORIOS:
        if not getattr(data, campo):
            raise HTTPException(status_code=400, detail=msg)
    await _nit_libre(db, cid, data.nit)
    # Consecutivo por empresa (= Id_Proveedor del escritorio); FOR UPDATE evita repetidos en concurrencia
    # Con escritorio: Id_Proveedor provisional; el escritorio le asigna el real al sincronizar
    from app.services import sede_maestros, sede_pedidos
    id_proveedor = await sede_maestros.siguiente_id(db, "suppliers", "id_proveedor", cid,
                                                    await sede_pedidos.tiene_sede(db, cid))
    s = Supplier(
        company_id=cid,
        id_proveedor=id_proveedor,
        synced=0,
        name=data.name,
        nit=data.nit,
        telefono_celular=data.telefono_celular,
        email=data.email or None,
        phone=data.phone or None,
        address=data.address or None,
        notes=data.notes or None,
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return _ser(s)


@router.put("/{sid}")
async def update_supplier(sid: int, data: SupplierIn, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = current_user.company_id
    s = await _get(db, cid, sid)
    sent = data.model_fields_set
    for campo, msg in _OBLIGATORIOS:
        if campo in sent and not getattr(data, campo):
            raise HTTPException(status_code=400, detail=msg)
    if "nit" in sent:
        await _nit_libre(db, cid, data.nit, excepto=s.id)
    for campo in ("name", "nit", "telefono_celular"):
        if campo in sent:
            setattr(s, campo, getattr(data, campo))
    for campo in ("email", "phone", "address", "notes"):
        if campo in sent:
            setattr(s, campo, getattr(data, campo) or None)
    if "is_active" in sent and data.is_active is not None:
        s.is_active = data.is_active
    s.synced = 0
    await db.commit()
    await db.refresh(s)
    return _ser(s)


async def _usos(db: AsyncSession, s: Supplier) -> dict:
    """Dónde está en uso el proveedor. Las tablas del escritorio lo referencian por id_proveedor;
    órdenes de compra y seriales por suppliers.id."""
    p = {"cid": s.company_id, "pid": s.id_proveedor or -1, "sid": s.id}
    insumos = (await db.execute(text("""
        SELECT DISTINCT COALESCE(si.description, CONCAT('Insumo #', ip.id_insumo)) AS n
        FROM insumos_proveedor ip
        LEFT JOIN supply_items si ON si.company_id = ip.company_id AND si.id_item = ip.id_insumo
        WHERE ip.company_id = :cid AND ip.id_proveedor = :pid
        ORDER BY n LIMIT 50
    """), p)).scalars().all()
    productos = (await db.execute(text("""
        SELECT DISTINCT description FROM pos_dish_products
        WHERE company_id = :cid AND supplier_id = :pid
        ORDER BY description LIMIT 50
    """), p)).scalars().all()
    conteos = {}
    for clave, sql in (
        ("entradas", "SELECT COUNT(*) FROM inventory_entries WHERE company_id = :cid AND id_proveedor = :pid"),
        ("salidas",  "SELECT COUNT(*) FROM inventory_exits WHERE company_id = :cid AND id_proveedor = :pid"),
        ("facturas", "SELECT COUNT(*) FROM facturas_proveedor WHERE company_id = :cid AND id_proveedor = :pid"),
        ("lotes",    "SELECT COUNT(*) FROM inv_lotes WHERE company_id = :cid AND id_proveedor = :pid"),
        ("ordenes",  "SELECT COUNT(*) FROM purchase_orders WHERE company_id = :cid AND supplier_id = :sid"),
        ("seriales", "SELECT COUNT(*) FROM serialized_items WHERE supplier_id = :sid"),
    ):
        conteos[clave] = int((await db.execute(text(sql), p)).scalar() or 0)
    en_uso = bool(insumos or productos or any(conteos.values()))
    return {"en_uso": en_uso, "insumos": list(insumos), "productos": list(productos), **conteos}


@router.get("/{sid}/uso")
async def supplier_usage(sid: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.services import sede_pedidos
    s = await _get(db, current_user.company_id, sid)
    usos = await _usos(db, s)
    usos["con_escritorio"] = bool(await sede_pedidos.tiene_sede(db, current_user.company_id))
    return usos


@router.delete("/{sid}")
async def delete_supplier(sid: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Elimina el proveedor solo si no está en uso en ninguna tabla. Con escritorio no se elimina
    (el borrado no viaja al escritorio): allí solo se desactiva."""
    from app.services import sede_pedidos
    cid = current_user.company_id
    s = await _get(db, cid, sid)
    if await sede_pedidos.tiene_sede(db, cid):
        raise HTTPException(status_code=409, detail="Esta empresa trabaja con escritorio: el proveedor solo se puede desactivar")
    if (await _usos(db, s))["en_uso"]:
        raise HTTPException(status_code=409, detail="El proveedor está en uso y no se puede eliminar")
    await db.delete(s)
    await db.commit()
    return {"ok": True}
