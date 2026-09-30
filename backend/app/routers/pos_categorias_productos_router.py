"""
Categorías de Productos — CRUD de categoria_productos del escritorio (pos_product_categories).

  Cod_Categoria            → id (por empresa; el siguiente número al crear)
  Nombre                   → name
  Porcentaje (reciclado)   → percentage: 1 = categoría de ARMADO, 0 = normal
  Activa                   → is_active
  Exgir_Seleccion          → require_selection
  Imprimir_Armar_Solo_Cambio → print_assembly_changes_only

Se usa para agrupar insumos (inventario_porciones.Agrupar), para las categorías de armado de
los platos (plato_armar) y para el menú del día. No se borra: se desactiva (la usan platos,
insumos y menús). La empresa sale de la sesión (empresa del topbar validada por tenant).
"""
import re
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, StringConstraints
from typing_extensions import Annotated
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.tenant import tenant_guard
from app.models.user_model import User

router = APIRouter(prefix="/api/pos-catalogo/categorias-productos", tags=["Categorías de Productos"],
                   dependencies=[Depends(tenant_guard)])

_CTRL = re.compile(r"[\x00-\x1f\x7f<>]")
Nombre = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class CategoriaIn(BaseModel):
    name: Nombre
    is_assembly: bool = False                 # Porcentaje = 1
    is_active: bool = True
    require_selection: bool = False
    print_assembly_changes_only: bool = False
    company_id: Optional[int] = None          # lo valida tenant_guard; no se usa


def _limpio(nombre: str) -> str:
    n = _CTRL.sub("", nombre).strip()
    if not n:
        raise HTTPException(status_code=422, detail="El nombre no es válido")
    return n.upper()


def _fila(r) -> dict:
    return {
        "id": int(r["id"]), "name": r["name"] or "",
        "is_assembly": float(r["percentage"] or 0) == 1,
        "is_active": bool(r["is_active"]),
        "require_selection": bool(r["require_selection"]),
        "print_assembly_changes_only": bool(r["print_assembly_changes_only"]),
        "insumos": int(r["insumos"] or 0), "insumos_armado": int(r["insumos_armado"] or 0),
        "platos": int(r["platos"] or 0),
    }


_SELECT = """
    SELECT pc.id, pc.name, pc.percentage, pc.is_active, pc.require_selection, pc.print_assembly_changes_only,
           (SELECT COUNT(*) FROM supply_items si
             WHERE si.company_id = pc.company_id AND si.agrupar = pc.id AND si.is_active = 1) AS insumos,
           (SELECT COUNT(*) FROM supply_items si
             WHERE si.company_id = pc.company_id AND si.agrupar = pc.id AND si.is_active = 1
               AND si.armar_plato = 1) AS insumos_armado,
           (SELECT COUNT(DISTINCT da.dish_id) FROM pos_dish_assembly da
             WHERE da.company_id = pc.company_id AND da.category_code = pc.id) AS platos
    FROM pos_product_categories pc
    WHERE pc.company_id = :cid
"""


async def _nombre_libre(db: AsyncSession, cid: int, nombre: str, excluir: Optional[int] = None) -> None:
    dup = (await db.execute(text(
        "SELECT 1 FROM pos_product_categories WHERE company_id=:cid AND UPPER(TRIM(name))=:n"
        + (" AND id<>:id" if excluir is not None else "")
    ), {"cid": cid, "n": nombre, "id": excluir})).scalar()
    if dup:
        raise HTTPException(status_code=409, detail="Ya existe una categoría con ese nombre")


@router.get("")
async def listar(
    tipo: Literal["todas", "armado", "normal"] = "todas",
    q: Optional[str] = Query(None, max_length=60),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sql, params = _SELECT, {"cid": current_user.company_id}
    if tipo == "armado":
        sql += " AND pc.percentage = 1"
    elif tipo == "normal":
        sql += " AND COALESCE(pc.percentage, 0) <> 1"
    term = (q or "").strip()
    if term:
        term = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        sql += " AND pc.name LIKE :q"
        params["q"] = f"%{term}%"
    sql += " ORDER BY pc.is_active DESC, pc.name"
    return [_fila(r) for r in (await db.execute(text(sql), params)).mappings().all()]


@router.post("", status_code=201)
async def crear(data: CategoriaIn, db: AsyncSession = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    cid = current_user.company_id
    nombre = _limpio(data.name)
    await _nombre_libre(db, cid, nombre)
    nuevo_id = int((await db.execute(text(
        "SELECT COALESCE(MAX(id), 0) + 1 FROM pos_product_categories WHERE company_id=:cid"
    ), {"cid": cid})).scalar())
    await db.execute(text("""
        INSERT INTO pos_product_categories
            (id, company_id, name, percentage, is_active, require_selection, print_assembly_changes_only, synced)
        VALUES (:id, :cid, :name, :pct, :act, :req, :poc, 0)
    """), {"id": nuevo_id, "cid": cid, "name": nombre, "pct": 1 if data.is_assembly else 0,
           "act": int(data.is_active), "req": int(data.require_selection),
           "poc": int(data.print_assembly_changes_only)})
    await db.commit()
    row = (await db.execute(text(_SELECT + " AND pc.id = :id"), {"cid": cid, "id": nuevo_id})).mappings().first()
    return _fila(row)


@router.put("/{cat_id}")
async def actualizar(cat_id: int, data: CategoriaIn, db: AsyncSession = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    cid = current_user.company_id
    nombre = _limpio(data.name)
    await _nombre_libre(db, cid, nombre, excluir=cat_id)
    r = await db.execute(text("""
        UPDATE pos_product_categories
        SET name=:name, percentage=:pct, is_active=:act, require_selection=:req,
            print_assembly_changes_only=:poc, synced=0
        WHERE id=:id AND company_id=:cid
    """), {"id": cat_id, "cid": cid, "name": nombre, "pct": 1 if data.is_assembly else 0,
           "act": int(data.is_active), "req": int(data.require_selection),
           "poc": int(data.print_assembly_changes_only)})
    if not r.rowcount:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    await db.commit()
    row = (await db.execute(text(_SELECT + " AND pc.id = :id"), {"cid": cid, "id": cat_id})).mappings().first()
    return _fila(row)


@router.delete("/{cat_id}")
async def desactivar(cat_id: int, db: AsyncSession = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    """No se borra (la usan insumos, platos y menús): se desactiva."""
    r = await db.execute(text(
        "UPDATE pos_product_categories SET is_active=0, synced=0 WHERE id=:id AND company_id=:cid"
    ), {"id": cat_id, "cid": current_user.company_id})
    if not r.rowcount:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    await db.commit()
    return {"ok": True}


@router.get("/{cat_id}/insumos")
async def insumos_de_categoria(cat_id: int, db: AsyncSession = Depends(get_db),
                               current_user: User = Depends(get_current_user)):
    """Insumos de la categoría (inventario_porciones.Agrupar = Cod_Categoria), informativo.
    Qué insumos se ofrecen en cada plato se define en el plato (plato_armar_detalle)."""
    cid = current_user.company_id
    existe = (await db.execute(text(
        "SELECT 1 FROM pos_product_categories WHERE company_id=:cid AND id=:id"
    ), {"cid": cid, "id": cat_id})).scalar()
    if not existe:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    rows = (await db.execute(text("""
        SELECT id_item, description, COALESCE(armar_plato, 0) AS armar_plato, is_active
        FROM supply_items
        WHERE company_id = :cid AND agrupar = :id
        ORDER BY is_active DESC, description
    """), {"cid": cid, "id": cat_id})).mappings().all()
    return [{"id_item": int(r["id_item"]), "description": r["description"] or f"Insumo {r['id_item']}",
             "armar_plato": bool(r["armar_plato"]), "is_active": bool(r["is_active"])} for r in rows]
