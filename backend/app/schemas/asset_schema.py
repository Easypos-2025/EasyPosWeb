"""
========================================================
SCHEMA ASSET
========================================================
"""

from pydantic import BaseModel


# =====================================================
# CREATE
# =====================================================

class AssetCreate(BaseModel):

    name: str
    category_id: int
    description: str
    location: str


# =====================================================
# UPDATE
# =====================================================

class AssetUpdate(BaseModel):

    name: str
    category_id: int
    description: str
    location: str


# =====================================================
# RESPONSE
# =====================================================

class AssetResponse(BaseModel):

    id: int
    name: str
    category_id: int
    description: str
    location: str

    class Config:
        from_attributes = True
        
