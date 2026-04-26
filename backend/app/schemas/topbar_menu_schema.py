from pydantic import BaseModel
from typing import Optional


class TopbarMenuItemCreate(BaseModel):
    name: str
    key: str
    icon: Optional[str] = "bi-grid"
    route: Optional[str] = None
    has_evidence: Optional[bool] = False
    min_plan_id: Optional[int] = None
    is_active: Optional[bool] = True
    order_index: Optional[int] = 0


class TopbarMenuItemUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    route: Optional[str] = None
    has_evidence: Optional[bool] = None
    min_plan_id: Optional[int] = None
    is_active: Optional[bool] = None
    order_index: Optional[int] = None


class TopbarMenuItemResponse(BaseModel):
    id: int
    name: str
    key: str
    icon: Optional[str]
    route: Optional[str]
    has_evidence: bool
    min_plan_id: Optional[int]
    is_active: bool
    order_index: int

    class Config:
        from_attributes = True
