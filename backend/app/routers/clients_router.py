from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

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
def list_clients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    clients = (
        db.query(Client)
        .filter(Client.company_id == current_user.company_id)
        .order_by(Client.name)
        .all()
    )
    return [_ser(c) for c in clients]


@router.post("")
def create_client(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
    db.commit()
    db.refresh(client)
    return _ser(client)


@router.put("/{client_id}")
def update_client(
    client_id: int,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.company_id == current_user.company_id
    ).first()
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

    db.commit()
    db.refresh(client)
    return _ser(client)


@router.delete("/{client_id}")
def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.company_id == current_user.company_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    db.delete(client)
    db.commit()
    return {"ok": True}
