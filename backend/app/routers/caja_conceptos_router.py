"""
Conceptos de Caja (conceptos / sub_conceptos del escritorio → pos_cash_concepts / pos_cash_subconcepts).

  GET  /api/caja/conceptos?tipo=&q=                 conceptos de la empresa (con # de subconceptos)
  POST /api/caja/conceptos                          crear  (Cod_Concepto = siguiente de la empresa)
  PUT  /api/caja/conceptos/{concept_id}             editar / activar / desactivar
  GET  /api/caja/conceptos/{concept_id}/sub         subconceptos
  POST /api/caja/conceptos/{concept_id}/sub         crear subconcepto
  PUT  /api/caja/conceptos/{concept_id}/sub/{sub}   editar / activar / desactivar

Tipo de concepto (tipo_concepto del escritorio): 1 Gastos · 2 Compras · 3 Otros Egresos · 4 Otros Ingresos.
Nunca se elimina: solo se desactiva. La empresa sale de la sesión (tenant).
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import Annotated

from app.auth.dependencies import get_current_user
from app.auth.tenant import tenant_guard
from app.database import get_db
from app.models.user_model import User

router = APIRouter(prefix="/api/caja/conceptos", tags=["Caja Conceptos"], dependencies=[Depends(tenant_guard)])

TIPOS = {1: "Gastos", 2: "Compras", 3: "Otros Egresos", 4: "Otros Ingresos"}
Desc = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]


class ConceptoIn(BaseModel):
    description: Desc
    concept_type: Annotated[int, Field(ge=1, le=4)]
    is_active: bool = True
    company_id: Optional[int] = None      # lo valida tenant_guard; no se usa


class SubconceptoIn(BaseModel):
    description: Desc
    is_active: bool = True
    company_id: Optional[int] = None


async def _concepto(db: AsyncSession, cid: int, concept_id: int) -> dict:
    row = (await db.execute(text(
        "SELECT concept_id, description, concept_type, is_active FROM pos_cash_concepts WHERE company_id = :c AND concept_id = :id"
    ), {"c": cid, "id": concept_id})).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Concepto no encontrado")
    return dict(row) | {"is_active": bool(row["is_active"])}


async def _duplicado(db: AsyncSession, sql: str, params: dict, msg: str) -> None:
    if (await db.execute(text(sql), params)).scalar():
        raise HTTPException(status_code=409, detail=msg)


@router.get("")
async def listar(
    tipo: Optional[Annotated[int, Field(ge=1, le=4)]] = Query(None),
    q: Optional[Annotated[str, StringConstraints(max_length=50)]] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    where, p = "c.company_id = :cid", {"cid": current_user.company_id}
    if tipo:
        where += " AND c.concept_type = :t"
        p["t"] = tipo
    if q and q.strip():
        where += " AND c.description LIKE :q"
        p["q"] = f"%{q.strip()}%"
    rows = (await db.execute(text(f"""
        SELECT c.concept_id, c.description, c.concept_type, c.is_active,
               (SELECT COUNT(*) FROM pos_cash_subconcepts s
                WHERE s.company_id = c.company_id AND s.concept_id = c.concept_id) AS subconceptos
        FROM pos_cash_concepts c
        WHERE {where}
        ORDER BY c.concept_type, c.description
    """), p)).mappings().all()
    return {"tipos": TIPOS, "conceptos": [dict(r) | {"is_active": bool(r["is_active"])} for r in rows]}


@router.post("")
async def crear(
    body: ConceptoIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cid = current_user.company_id
    desc = body.description.upper()
    await _duplicado(db, """SELECT 1 FROM pos_cash_concepts WHERE company_id = :c AND concept_type = :t
                            AND UPPER(description) = :d""", {"c": cid, "t": body.concept_type, "d": desc},
                     f'Ya existe el concepto "{desc}" en {TIPOS[body.concept_type]}')
    for _ in range(5):
        nuevo = int((await db.execute(text(
            "SELECT COALESCE(MAX(concept_id), 0) + 1 FROM pos_cash_concepts WHERE company_id = :c"
        ), {"c": cid})).scalar())
        try:
            await db.execute(text("""
                INSERT INTO pos_cash_concepts (company_id, concept_id, description, concept_type, is_active, synced)
                VALUES (:c, :id, :d, :t, :a, 0)
            """), {"c": cid, "id": nuevo, "d": desc, "t": body.concept_type, "a": int(body.is_active)})
            await db.commit()
            return await _concepto(db, cid, nuevo)
        except IntegrityError:
            await db.rollback()
    raise HTTPException(status_code=409, detail="No se pudo crear el concepto, intente nuevamente")


@router.put("/{concept_id}")
async def editar(
    concept_id: int,
    body: ConceptoIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cid = current_user.company_id
    await _concepto(db, cid, concept_id)
    desc = body.description.upper()
    await _duplicado(db, """SELECT 1 FROM pos_cash_concepts WHERE company_id = :c AND concept_type = :t
                            AND UPPER(description) = :d AND concept_id <> :id""",
                     {"c": cid, "t": body.concept_type, "d": desc, "id": concept_id},
                     f'Ya existe el concepto "{desc}" en {TIPOS[body.concept_type]}')
    await db.execute(text("""
        UPDATE pos_cash_concepts SET description = :d, concept_type = :t, is_active = :a, synced = 0
        WHERE company_id = :c AND concept_id = :id
    """), {"d": desc, "t": body.concept_type, "a": int(body.is_active), "c": cid, "id": concept_id})
    await db.commit()
    return await _concepto(db, cid, concept_id)


@router.get("/{concept_id}/sub")
async def listar_sub(
    concept_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cid = current_user.company_id
    concepto = await _concepto(db, cid, concept_id)
    rows = (await db.execute(text("""
        SELECT subconcept_id, description, is_active FROM pos_cash_subconcepts
        WHERE company_id = :c AND concept_id = :id ORDER BY description
    """), {"c": cid, "id": concept_id})).mappings().all()
    return {"concepto": concepto, "subconceptos": [dict(r) | {"is_active": bool(r["is_active"])} for r in rows]}


@router.post("/{concept_id}/sub")
async def crear_sub(
    concept_id: int,
    body: SubconceptoIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cid = current_user.company_id
    await _concepto(db, cid, concept_id)
    desc = body.description.upper()
    await _duplicado(db, """SELECT 1 FROM pos_cash_subconcepts WHERE company_id = :c AND concept_id = :id
                            AND UPPER(description) = :d""", {"c": cid, "id": concept_id, "d": desc},
                     f'Ya existe el subconcepto "{desc}"')
    for _ in range(5):
        nuevo = int((await db.execute(text(
            "SELECT COALESCE(MAX(subconcept_id), 0) + 1 FROM pos_cash_subconcepts WHERE company_id = :c AND concept_id = :id"
        ), {"c": cid, "id": concept_id})).scalar())
        try:
            await db.execute(text("""
                INSERT INTO pos_cash_subconcepts (company_id, concept_id, subconcept_id, description, is_active, synced)
                VALUES (:c, :id, :sid, :d, :a, 0)
            """), {"c": cid, "id": concept_id, "sid": nuevo, "d": desc, "a": int(body.is_active)})
            await db.commit()
            return {"subconcept_id": nuevo, "description": desc, "is_active": body.is_active}
        except IntegrityError:
            await db.rollback()
    raise HTTPException(status_code=409, detail="No se pudo crear el subconcepto, intente nuevamente")


@router.put("/{concept_id}/sub/{subconcept_id}")
async def editar_sub(
    concept_id: int,
    subconcept_id: int,
    body: SubconceptoIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cid = current_user.company_id
    await _concepto(db, cid, concept_id)
    existe = (await db.execute(text(
        "SELECT 1 FROM pos_cash_subconcepts WHERE company_id = :c AND concept_id = :id AND subconcept_id = :sid"
    ), {"c": cid, "id": concept_id, "sid": subconcept_id})).scalar()
    if not existe:
        raise HTTPException(status_code=404, detail="Subconcepto no encontrado")
    desc = body.description.upper()
    await _duplicado(db, """SELECT 1 FROM pos_cash_subconcepts WHERE company_id = :c AND concept_id = :id
                            AND UPPER(description) = :d AND subconcept_id <> :sid""",
                     {"c": cid, "id": concept_id, "d": desc, "sid": subconcept_id}, f'Ya existe el subconcepto "{desc}"')
    await db.execute(text("""
        UPDATE pos_cash_subconcepts SET description = :d, is_active = :a, synced = 0
        WHERE company_id = :c AND concept_id = :id AND subconcept_id = :sid
    """), {"d": desc, "a": int(body.is_active), "c": cid, "id": concept_id, "sid": subconcept_id})
    await db.commit()
    return {"subconcept_id": subconcept_id, "description": desc, "is_active": body.is_active}
