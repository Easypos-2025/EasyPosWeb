"""
Clientes (espejo de `clientes` del escritorio) — lógica compartida por la comanda,
las listas de precios por cliente y, más adelante, el Registro de Recibo.

  id_cliente = 1 → Consumidor Final (cédula 222222222222), se crea bajo demanda.
  Todo pedido nace con id_cliente = 1.
"""
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

CONSUMIDOR_FINAL_ID = 1
CONSUMIDOR_FINAL_CEDULA = "222222222222"
CONSUMIDOR_FINAL_NOMBRE = "Consumidor Final"


def _clean(v: Optional[str], n: int) -> Optional[str]:
    v = (v or "").strip()
    return v[:n] or None


async def ensure_consumidor_final(db: AsyncSession, cid: int) -> None:
    """Crea el cliente 1 (Consumidor Final) si la empresa aún no lo tiene."""
    await db.execute(text("""
        INSERT IGNORE INTO clientes (company_id, id_cliente, cedula, nombres, enviada_mysql)
        VALUES (:cid, :id, :ced, :nom, 0)
    """), {"cid": cid, "id": CONSUMIDOR_FINAL_ID, "ced": CONSUMIDOR_FINAL_CEDULA, "nom": CONSUMIDOR_FINAL_NOMBRE})


async def next_id_cliente(db: AsyncSession, cid: int) -> int:
    # Punto único de numeración de clientes creados en la web (ver nota en el informe de la Fase 5)
    mx = (await db.execute(text(
        "SELECT COALESCE(MAX(id_cliente), 1) FROM clientes WHERE company_id = :cid FOR UPDATE"
    ), {"cid": cid})).scalar() or 1
    return int(mx) + 1


def serialize(r) -> dict:
    nombre = " ".join(p for p in [(r["nombres"] or "").strip(), (r["apellidos"] or "").strip()] if p)
    return {"id_cliente": int(r["id_cliente"]), "cedula": r["cedula"], "nombre": nombre or f"Cliente {r['id_cliente']}",
            "telefono": r["telefono"], "direccion": r["direccion"], "mail": r["mail"]}


async def get_cliente(db: AsyncSession, cid: int, id_cliente: int) -> dict:
    if int(id_cliente) == CONSUMIDOR_FINAL_ID:
        await ensure_consumidor_final(db, cid)
    r = (await db.execute(text("""
        SELECT id_cliente, cedula, nombres, apellidos, telefono, direccion, mail
        FROM clientes WHERE company_id = :cid AND id_cliente = :id
    """), {"cid": cid, "id": int(id_cliente)})).mappings().first()
    if not r:
        raise HTTPException(status_code=400, detail="Cliente no válido para esta empresa")
    return serialize(r)


async def buscar(db: AsyncSession, cid: int, q: Optional[str], limit: int = 30) -> list:
    await ensure_consumidor_final(db, cid)
    sql = """
        SELECT id_cliente, cedula, nombres, apellidos, telefono, direccion, mail
        FROM clientes WHERE company_id = :cid
    """
    params: dict = {"cid": cid, "lim": limit}
    term = (q or "").strip()[:60]
    if term:
        term = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        sql += " AND (cedula LIKE :q OR nombres LIKE :q OR apellidos LIKE :q OR telefono LIKE :q)"
        params["q"] = f"%{term}%"
    sql += " ORDER BY (id_cliente = 1) DESC, nombres LIMIT :lim"
    return [serialize(r) for r in (await db.execute(text(sql), params)).mappings().all()]


async def crear(db: AsyncSession, cid: int, nombres: str, cedula: Optional[str], telefono: Optional[str],
                direccion: Optional[str], mail: Optional[str]) -> dict:
    nombres = _clean(nombres, 150)
    if not nombres:
        raise HTTPException(status_code=400, detail="El nombre del cliente es obligatorio")
    cedula = _clean(cedula, 50)
    if cedula:
        dup = (await db.execute(text(
            "SELECT id_cliente FROM clientes WHERE company_id = :cid AND cedula = :ced LIMIT 1"
        ), {"cid": cid, "ced": cedula})).scalar()
        if dup:
            raise HTTPException(status_code=409, detail=f"Ya existe un cliente con la cédula/NIT {cedula}")
    await ensure_consumidor_final(db, cid)
    nid = await next_id_cliente(db, cid)
    await db.execute(text("""
        INSERT INTO clientes (company_id, id_cliente, cedula, nombres, telefono, direccion, mail, enviada_mysql)
        VALUES (:cid, :id, :ced, :nom, :tel, :dir, :mail, 0)
    """), {"cid": cid, "id": nid, "ced": cedula, "nom": nombres, "tel": _clean(telefono, 250),
           "dir": _clean(direccion, 255), "mail": _clean(mail, 150)})
    return {"id_cliente": nid, "cedula": cedula, "nombre": nombres, "telefono": _clean(telefono, 250),
            "direccion": _clean(direccion, 255), "mail": _clean(mail, 150)}
