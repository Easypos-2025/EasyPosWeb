from pydantic import BaseModel

from typing import Optional

class ProfileUpdate(BaseModel):
    topbar_color: str
    sidebar_color: str
    bg_color: str
    logo: Optional[str] = None
    font_size: Optional[int] = None
    font_color: Optional[str] = None
    
        