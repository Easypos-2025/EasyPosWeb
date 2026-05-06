from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.client_model import Client
from app.auth.dependencies import get_current_user
from app.models.user_model import User

router = APIRouter(prefix="/clients", tags=["Clients"])


def _ser(c: Client) -> dict:
    return {
        "id":              c.id,
        "company_id":      c.company_id,
        "name":            c.name,
        "document_type":   c.document_type,
        "document_number": c.document_number,
        "email":           c.email,
        "phone":           c.phone,
        "address":         c.address,
        "is_active":       c.is_active,
        "created_at":      c.created_at.isoformat() if c.created_at else None,
    }


@router.get("")
async def list_clients(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Client).where(Client.company_id == current_user.company_id).order_by(Client.name)
    )
    return [_ser(c) for c in result.scalars().all()]


@router.post("")
async def create_client(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre del cliente es obligatorio")

    client = Client(
        company_id=current_user.company_id,
        name=name,
        document_type=data.get("document_type") or None,
        document_number=(data.get("document_number") or "").strip() or None,
        email=(data.get("email") or "").strip() or None,
        phone=(data.get("phone") or "").strip() or None,
        address=(data.get("address") or "").strip() or None,
        is_active=1,
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return _ser(client)


@router.put("/{client_id}")
async def update_client(
    client_id: int,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.company_id == current_user.company_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre del cliente es obligatorio")

    client.name            = name
    client.document_type   = data.get("document_type") or None
    client.document_number = (data.get("document_number") or "").strip() or None
    client.email           = (data.get("email") or "").strip() or None
    client.phone           = (data.get("phone") or "").strip() or None
    client.address         = (data.get("address") or "").strip() or None
    if "is_active" in data:
        client.is_active   = int(bool(data["is_active"]))

    await db.commit()
    await db.refresh(client)
    return _ser(client)


@router.delete("/{client_id}")
async def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.company_id == current_user.company_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    await db.delete(client)
    await db.commit()
    return {"ok": True}
