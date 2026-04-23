"""
========================================================
SYSTEM MODULE SCHEMA
========================================================

Esquemas para crear, actualizar y responder módulos del sistema.
"""

# =====================================================
# IMPORTS
# =====================================================

from pydantic import BaseModel
from typing import List, Optional


# =====================================================
# BASE
# =====================================================

class SystemModuleBase(BaseModel):
    name: str
    route: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = True
    order_index: Optional[int] = None

# =====================================================
# CREATE
# =====================================================

class SystemModuleCreate(SystemModuleBase):
    pass


# =====================================================
# UPDATE
# =====================================================

class SystemModuleUpdate(BaseModel):
    name: Optional[str] = None
    route: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None
    order_index: Optional[int] = None


# =====================================================
# RESPONSE (🔥 CON CHILDREN)
# =====================================================

class SystemModuleOut(SystemModuleBase):
    id: int
    children: Optional[List["SystemModuleOut"]] = []


    class Config:
        from_attributes = True


# 🔥 NECESARIO PARA RELACIÓN RECURSIVA

SystemModuleOut.model_rebuild()