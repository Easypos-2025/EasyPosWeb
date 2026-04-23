"""
========================================================
SCHEMA ASSET CATEGORY
========================================================
"""

from pydantic import BaseModel


# =====================================================
# CREATE
# =====================================================

class AssetCategoryCreate(BaseModel):

    name: str
    description: str


# =====================================================
# UPDATE
# =====================================================

class AssetCategoryUpdate(BaseModel):

    name: str
    description: str


# =====================================================
# RESPONSE
# =====================================================

class AssetCategoryResponse(BaseModel):

    id: int
    name: str
    description: str

    class Config:
        from_attributes = True
        
