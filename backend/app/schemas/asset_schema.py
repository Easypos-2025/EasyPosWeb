"""
========================================================
SCHEMA ASSET
========================================================
"""

from typing import Optional
from pydantic import BaseModel


# =====================================================
# CREATE
# =====================================================

class AssetCreate(BaseModel):

    name: str
    category_id: int
    client_id: Optional[int] = None
    description: Optional[str] = ""
    location: Optional[str] = ""


# =====================================================
# UPDATE
# =====================================================

class AssetUpdate(BaseModel):

    name: str
    category_id: int
    client_id: Optional[int] = None
    description: Optional[str] = ""
    location: Optional[str] = ""


# =====================================================
# RESPONSE
# =====================================================

class AssetResponse(BaseModel):

    id: int
    name: str
    category_id: int
    client_id: Optional[int] = None
    description: Optional[str] = ""
    location: Optional[str] = ""

    class Config:
        from_attributes = True
