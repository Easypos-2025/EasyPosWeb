"""
Insumos (supply_items = inventario_porciones del escritorio).

Mapeo de la pantalla "Crear Nuevo Insumo" del escritorio:
  Nombre                     → description
  Unidad Uso                 → unit_uso_id      (pos_measure_forms; también unit_id al crear)
  Costo por Und de Uso       → cost_price
  Stock Mínimo               → min_stock
  Categoría                  → agrupar          (pos_product_categories)
  Este producto se controla  → control_stock
  Producto Preparado         → producto_preparado
  Insumo para Cambios        → opcion_cambios
  Opción para Armar          → armar_plato
  Producto Centro Producción → centro_produccion
  Código Insumo              → code
  Fecha Vencimiento          → fecha_vence
  Id_Item / Id_Grupo / Posicion → asignados por el sistema (solo lectura)
  "Valor al Vender" NO es del insumo: va por plato en plato_armar_detalle.Precio_Insumo.

Tablas relacionadas (Id_Insumo = id_item):
  insumos_proveedor     → proveedores asignados al insumo
  insumos_forma_medida  → formas de medida con su cantidad de unidades mínimas
"""
from datetime import date
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.database import get_db
from app.models.supply_item_model import SupplyItem
from app.models.stock_movement_model import StockMovement
from app.auth.dependencies import get_current_user
from app.models.user_model import User
from app.services.supply_keys import next_id_item, upsert_stock_row, DEFAULT_ID_GRUPO

router = APIRouter(prefix="/supply-items", tags=["SupplyItems"])

Flag  = Annotated[int, Field(ge=0, le=1)]
Money = Annotated[float, Field(ge=0, le=2_000_000_000)]
Name  = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class SupplyIn(BaseModel):
    description:        Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]] = None
    code:               Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=50)]] = None
    unit_id:            Optional[int]  = None
    unit_uso_id:        Optional[int]  = None
    category_id:        Optional[int]  = None
    cost_price:         Optional[Money] = None
    stock_qty:          Optional[Annotated[float, Field(ge=-1_000_000_000, le=1_000_000_000)]] = None
    min_stock:          Optional[Annotated[float, Field(ge=0, le=1_000_000_000)]] = None
    waste_pct:          Optional[Annotated[float, Field(ge=0, le=100)]] = None
    control_stock:      Optional[Flag] = None
    producto_preparado: Optional[Flag] = None
    opcion_cambios:     Optional[Flag] = None
    armar_plato:        Optional[Flag] = None
    centro_produccion:  Optional[Flag] = None
    is_active:          Optional[Flag] = None
    fecha_vence:        Optional[date] = None
    adjustment_notes:   Optional[Annotated[str, StringConstraints(max_length=255)]] = None


class ProveedoresIn(BaseModel):
    ids: Annotated[List[Annotated[int, Field(ge=1)]], Field(max_length=100)]


class FormaMedidaItem(BaseModel):
    id_forma_medida:       Annotated[int, Field(ge=1)]
    cant_unidades_minimas: Annotated[float, Field(gt=0, le=1_000_000)] = 1


class FormasMedidaIn(BaseModel):
    items: Annotated[List[FormaMedidaItem], Field(max_length=100)]


class CatalogoIn(BaseModel):
    name: Name


# Campos simples que se copian tal cual del payload al modelo
_SIMPLE = ("cost_price", "min_stock", "waste_pct", "control_stock", "producto_preparado",
           "opcion_cambios", "armar_plato", "centro_produccion", "is_active", "fecha_vence")


async def _measure_name(db: AsyncSession, cid: int, mid: Optional[int]) -> Optional[str]:
    if not mid:
        return None
    row = (await db.execute(
        text("SELECT name FROM pos_measure_forms WHERE id = :id AND company_id = :cid"),
        {"id": mid, "cid": cid}
    )).mappings().first()
    return row["name"] if row else None


async def _valid_measure(db: AsyncSession, cid: int, mid: Optional[int]) -> Optional[int]:
    if not mid:
        return None
    if not await _measure_name(db, cid, mid):
        raise HTTPException(status_code=400, detail="Forma de medida no válida para esta empresa")
    return mid


async def _valid_category(db: AsyncSession, cid: int, category_id) -> int:
    """Categoría de insumo (pos_product_categories) → supply_items.agrupar. 0 = sin categoría."""
    if not category_id:
        return 0
    ok = (await db.execute(text(
        "SELECT 1 FROM pos_product_categories WHERE id = :id AND company_id = :cid"
    ), {"id": int(category_id), "cid": cid})).scalar()
    if not ok:
        raise HTTPException(status_code=400, detail="Categoría no válida para esta empresa")
    return int(category_id)


def _ser(item: SupplyItem, unit_name=None) -> dict:
    return {"id": item.id, "company_id": item.company_id, "code": item.code,
            "description": item.description, "unit_id": item.unit_id, "unit_name": unit_name,
            "unit_uso_id": item.unit_uso_id,
            "cost_price": float(item.cost_price or 0), "stock_qty": float(item.stock_qty or 0),
            "min_stock": float(item.min_stock or 0), "waste_pct": float(item.waste_pct or 0),
            "control_stock": item.control_stock, "is_active": item.is_active,
            "producto_preparado": item.producto_preparado, "opcion_cambios": item.opcion_cambios,
            "armar_plato": item.armar_plato, "centro_produccion": item.centro_produccion,
            "fecha_vence": item.fecha_vence.isoformat() if item.fecha_vence else None,
            "id_item": item.id_item, "id_grupo": item.id_grupo, "posicion": item.posicion,
            "category_id": item.agrupar or None,
            "created_at": item.created_at.isoformat() if item.created_at else None}


async def _record_movement(db: AsyncSession, item: SupplyItem, mtype: str, qty: float, qty_before: float, user_id: int, notes: str = None):
    mov = StockMovement(company_id=item.company_id, supply_item_id=item.id, movement_type=mtype,
                        qty=qty, qty_before=qty_before, qty_after=qty_before + qty,
                        reference_type="manual", notes=notes, created_by=user_id)
    db.add(mov)
    await db.flush()


async def _get_item(db: AsyncSession, cid: int, iid: int) -> SupplyItem:
    item = (await db.execute(select(SupplyItem).where(
        SupplyItem.id == iid, SupplyItem.company_id == cid))).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    return item


# ─── Catálogos de apoyo (formas de medida y categorías de insumo) ─────────────

@router.get("/catalogos/formas-medida")
async def list_formas_medida(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(text(
        "SELECT id, name, is_active FROM pos_measure_forms WHERE company_id = :cid ORDER BY name"
    ), {"cid": current_user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.post("/catalogos/formas-medida", status_code=201)
async def create_forma_medida(data: CatalogoIn, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = current_user.company_id
    dup = (await db.execute(text(
        "SELECT id FROM pos_measure_forms WHERE company_id = :cid AND UPPER(name) = UPPER(:n)"
    ), {"cid": cid, "n": data.name})).scalar()
    if dup:
        raise HTTPException(status_code=409, detail="Ya existe una forma de medida con ese nombre")
    nid = int((await db.execute(text(
        "SELECT COALESCE(MAX(id), 0) + 1 FROM pos_measure_forms WHERE company_id = :cid FOR UPDATE"
    ), {"cid": cid})).scalar())
    await db.execute(text(
        "INSERT INTO pos_measure_forms (id, company_id, name, is_active, synced) VALUES (:id, :cid, :n, 1, 0)"   # forma_medida.Activa: 1 = activa
    ), {"id": nid, "cid": cid, "n": data.name})
    await db.commit()
    return {"id": nid, "name": data.name, "is_active": 1}


@router.get("/catalogos/categorias")
async def list_categorias(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(text(
        "SELECT id, name FROM pos_product_categories WHERE company_id = :cid ORDER BY name"
    ), {"cid": current_user.company_id})).mappings().all()
    return [dict(r) for r in rows]


@router.post("/catalogos/categorias", status_code=201)
async def create_categoria(data: CatalogoIn, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = current_user.company_id
    dup = (await db.execute(text(
        "SELECT id FROM pos_product_categories WHERE company_id = :cid AND UPPER(name) = UPPER(:n)"
    ), {"cid": cid, "n": data.name})).scalar()
    if dup:
        raise HTTPException(status_code=409, detail="Ya existe una categoría con ese nombre")
    nid = int((await db.execute(text(
        "SELECT COALESCE(MAX(id), 0) + 1 FROM pos_product_categories WHERE company_id = :cid FOR UPDATE"
    ), {"cid": cid})).scalar())
    await db.execute(text(
        "INSERT INTO pos_product_categories (id, company_id, name, is_active, synced) VALUES (:id, :cid, :n, 1, 0)"
    ), {"id": nid, "cid": cid, "n": data.name})
    await db.commit()
    return {"id": nid, "name": data.name}


# ─── CRUD insumos ─────────────────────────────────────────────────────────────

@router.get("/")
async def list_supply_items(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = current_user.company_id
    units = {int(r["id"]): r["name"] for r in (await db.execute(text(
        "SELECT id, name FROM pos_measure_forms WHERE company_id = :cid"
    ), {"cid": cid})).mappings().all()}
    result = await db.execute(select(SupplyItem).where(SupplyItem.company_id == cid).order_by(SupplyItem.description))
    return [_ser(i, units.get(i.unit_uso_id or i.unit_id or 0)) for i in result.scalars().all()]


@router.post("/")
async def create_supply_item(data: SupplyIn, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = current_user.company_id
    if not data.description:
        raise HTTPException(status_code=400, detail="El nombre es requerido")
    unit_uso = await _valid_measure(db, cid, data.unit_uso_id)
    unit_id  = await _valid_measure(db, cid, data.unit_id) or unit_uso
    agrupar  = await _valid_category(db, cid, data.category_id)
    id_item  = await next_id_item(db, cid)

    item = SupplyItem(company_id=cid, code=data.code or None, description=data.description,
                      id_grupo=DEFAULT_ID_GRUPO, id_item=id_item, posicion=id_item, agrupar=agrupar,
                      unit_id=unit_id, unit_uso_id=unit_uso,
                      stock_qty=float(data.stock_qty or 0),
                      control_stock=1 if data.control_stock is None else data.control_stock)
    for f in _SIMPLE:
        v = getattr(data, f)
        if v is not None and f != "control_stock":
            setattr(item, f, v)
    db.add(item)
    await db.flush()
    await upsert_stock_row(db, cid, item.id)      # mismo registro en stock actual (cantidad_actual = 0)
    await db.commit()
    await db.refresh(item)
    if item.control_stock and float(item.stock_qty) != 0:
        await _record_movement(db, item, "adjustment", float(item.stock_qty), 0, current_user.id, "Stock inicial")
        await db.commit()
    return _ser(item, await _measure_name(db, cid, item.unit_uso_id or item.unit_id))


@router.put("/{iid}")
async def update_supply_item(iid: int, data: SupplyIn, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = current_user.company_id
    item = await _get_item(db, cid, iid)
    sent = data.model_fields_set

    if "description" in sent:
        if not data.description:
            raise HTTPException(status_code=400, detail="El nombre es requerido")
        item.description = data.description
    if "code" in sent:
        item.code = data.code or None
    if "unit_uso_id" in sent:
        item.unit_uso_id = await _valid_measure(db, cid, data.unit_uso_id)
    if "unit_id" in sent:
        item.unit_id = await _valid_measure(db, cid, data.unit_id)
    if "category_id" in sent:
        item.agrupar = await _valid_category(db, cid, data.category_id)
    for f in _SIMPLE:
        if f in sent and (getattr(data, f) is not None or f == "fecha_vence"):
            setattr(item, f, getattr(data, f))
    if "stock_qty" in sent and data.stock_qty is not None:
        new_qty = float(data.stock_qty)
        old_qty = float(item.stock_qty or 0)
        if new_qty != old_qty:
            await _record_movement(db, item, "adjustment", new_qty - old_qty, old_qty, current_user.id,
                                   data.adjustment_notes or "Ajuste manual")
        item.stock_qty = new_qty
    if not item.id_item or not item.id_grupo:                  # insumos antiguos creados sin llaves
        if not item.id_item:
            item.id_item = await next_id_item(db, cid)
            item.posicion = item.id_item
        item.id_grupo = item.id_grupo or DEFAULT_ID_GRUPO
    item.synced = 0
    await db.flush()
    await upsert_stock_row(db, cid, item.id)
    await db.commit()
    await db.refresh(item)
    return _ser(item, await _measure_name(db, cid, item.unit_uso_id or item.unit_id))


@router.delete("/{iid}")
async def delete_supply_item(iid: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await _get_item(db, current_user.company_id, iid)
    item.is_active = 0
    item.synced = 0
    await db.commit()
    return {"ok": True}


# ─── Proveedores del insumo (insumos_proveedor) ───────────────────────────────

@router.get("/{iid}/proveedores")
async def get_proveedores_insumo(iid: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = current_user.company_id
    item = await _get_item(db, cid, iid)
    rows = (await db.execute(text("""
        SELECT ip.id_proveedor, s.name
        FROM insumos_proveedor ip
        LEFT JOIN suppliers s ON s.company_id = ip.company_id AND s.id_proveedor = ip.id_proveedor
        WHERE ip.company_id = :cid AND ip.id_insumo = :ins
        ORDER BY s.name
    """), {"cid": cid, "ins": item.id_item or -1})).mappings().all()
    return [dict(r) for r in rows]


@router.put("/{iid}/proveedores")
async def set_proveedores_insumo(iid: int, data: ProveedoresIn, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = current_user.company_id
    item = await _get_item(db, cid, iid)
    if not item.id_item:
        raise HTTPException(status_code=400, detail="Guarde el insumo antes de asignar proveedores")
    ids = sorted(set(data.ids))
    valid = {int(r[0]) for r in (await db.execute(text(
        "SELECT id_proveedor FROM suppliers WHERE company_id = :cid AND id_proveedor IS NOT NULL"
    ), {"cid": cid})).all()}
    if any(i not in valid for i in ids):
        raise HTTPException(status_code=400, detail="Proveedor no válido para esta empresa")

    current = {int(r[0]) for r in (await db.execute(text(
        "SELECT id_proveedor FROM insumos_proveedor WHERE company_id = :cid AND id_insumo = :ins"
    ), {"cid": cid, "ins": item.id_item})).all()}
    quitar = current - set(ids)
    if quitar:
        await db.execute(text(
            "DELETE FROM insumos_proveedor WHERE company_id = :cid AND id_insumo = :ins "
            "AND id_proveedor IN (" + ",".join(str(int(x)) for x in quitar) + ")"
        ), {"cid": cid, "ins": item.id_item})
    # Nuevos: como el escritorio — fecha de hoy, precio 0, forma de medida = unidad de uso
    mid = item.unit_uso_id or item.unit_id or 0
    mname = (await _measure_name(db, cid, mid)) or ""
    obs = "SE REGISTRO POR NUEVO INSUMO" if not current else "SE REGISTRO POR MODIFICACION INSUMO"
    for pid in set(ids) - current:
        await db.execute(text("""
            INSERT INTO insumos_proveedor
                (company_id, id_proveedor, id_insumo, fecha_inicial_negociacion, fecha_final_negociacion,
                 precio_pactado, id_forma_medida, nombre_forma_medida, observacion, enviada_mysql)
            VALUES (:cid, :pid, :ins, CURDATE(), CURDATE(), 0, :mid, :mname, :obs, 0)
        """), {"cid": cid, "pid": pid, "ins": item.id_item, "mid": mid, "mname": mname[:50], "obs": obs})
    await db.commit()
    return {"ok": True}


# ─── Formas de medida del insumo (insumos_forma_medida) ───────────────────────

@router.get("/{iid}/formas-medida")
async def get_formas_insumo(iid: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = current_user.company_id
    item = await _get_item(db, cid, iid)
    rows = (await db.execute(text("""
        SELECT fm.id_forma_medida, fm.cant_unidades_minimas, mf.name
        FROM insumos_forma_medida fm
        LEFT JOIN pos_measure_forms mf ON mf.company_id = fm.company_id AND mf.id = fm.id_forma_medida
        WHERE fm.company_id = :cid AND fm.id_insumo = :ins
        ORDER BY mf.name
    """), {"cid": cid, "ins": item.id_item or -1})).mappings().all()
    return [dict(r) for r in rows]


@router.put("/{iid}/formas-medida")
async def set_formas_insumo(iid: int, data: FormasMedidaIn, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cid = current_user.company_id
    item = await _get_item(db, cid, iid)
    if not item.id_item:
        raise HTTPException(status_code=400, detail="Guarde el insumo antes de asignar formas de medida")
    valid = {int(r[0]) for r in (await db.execute(text(
        "SELECT id FROM pos_measure_forms WHERE company_id = :cid"
    ), {"cid": cid})).all()}
    wanted = {it.id_forma_medida: it.cant_unidades_minimas for it in data.items}
    if any(m not in valid for m in wanted):
        raise HTTPException(status_code=400, detail="Forma de medida no válida para esta empresa")

    current = {int(r[0]) for r in (await db.execute(text(
        "SELECT id_forma_medida FROM insumos_forma_medida WHERE company_id = :cid AND id_insumo = :ins"
    ), {"cid": cid, "ins": item.id_item})).all()}
    quitar = current - set(wanted)
    if quitar:
        await db.execute(text(
            "DELETE FROM insumos_forma_medida WHERE company_id = :cid AND id_insumo = :ins "
            "AND id_forma_medida IN (" + ",".join(str(int(x)) for x in quitar) + ")"
        ), {"cid": cid, "ins": item.id_item})
    for mid, cant in wanted.items():
        await db.execute(text("""
            INSERT INTO insumos_forma_medida
                (company_id, id_insumo, id_forma_medida, cant_unidades_minimas, enviada_mysql)
            VALUES (:cid, :ins, :mid, :cant, 0)
            ON DUPLICATE KEY UPDATE cant_unidades_minimas = VALUES(cant_unidades_minimas),
                                    enviada_mysql = 0, updated_at = NOW()
        """), {"cid": cid, "ins": item.id_item, "mid": mid, "cant": cant})
    await db.commit()
    return {"ok": True}


# ─── Movimientos ──────────────────────────────────────────────────────────────

@router.get("/{iid}/movements")
async def get_movements(iid: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await _get_item(db, current_user.company_id, iid)
    result = await db.execute(select(StockMovement).where(StockMovement.supply_item_id == iid).order_by(StockMovement.created_at.desc()).limit(100))
    return [{"id": m.id, "type": m.movement_type, "qty": float(m.qty),
             "qty_before": float(m.qty_before), "qty_after": float(m.qty_after),
             "reference_type": m.reference_type, "reference_id": m.reference_id,
             "notes": m.notes, "created_at": m.created_at.isoformat() if m.created_at else None}
            for m in result.scalars().all()]
