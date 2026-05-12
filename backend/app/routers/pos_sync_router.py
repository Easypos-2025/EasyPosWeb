import os
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.database import get_db

router = APIRouter(prefix="/api/pos", tags=["POS Sync"])

POS_API_KEY = os.getenv("POS_API_KEY", "easypos-sync-key-2024")


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != POS_API_KEY:
        raise HTTPException(status_code=401, detail="API Key inválida")


@router.get("/test/users")
async def get_users(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    result = await db.execute(
        text("SELECT id, nombre, email, company_id, is_active FROM users ORDER BY id")
    )
    rows = result.mappings().all()
    return {
        "total": len(rows),
        "users": [dict(r) for r in rows]
    }
