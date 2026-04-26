from pydantic import BaseModel
from typing import Optional


class SystemConfigUpdate(BaseModel):
    config_value: str
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SystemConfigResponse(BaseModel):
    id: int
    config_key: str
    config_value: str
    description: Optional[str]
    config_type: str
    is_active: bool

    class Config:
        from_attributes = True
