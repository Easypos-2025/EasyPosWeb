from typing import Optional
from decimal import Decimal
from pydantic import BaseModel


class AssetCreate(BaseModel):
    name:                 str
    category_id:          Optional[int]     = None
    short_name:           Optional[str]     = None
    client_id:            Optional[int]     = None
    owner_id:             Optional[int]     = None
    description:          Optional[str]     = None
    location:             Optional[str]     = None
    address:              Optional[str]     = None
    phone:                Optional[str]     = None
    sector_id:            Optional[int]     = None
    is_rented:            Optional[int]     = 0
    is_active:            Optional[int]     = 1
    has_sale_option:      Optional[int]     = 0
    canon_value:          Optional[Decimal] = None
    cadastral_value:      Optional[Decimal] = None
    commercial_value:     Optional[Decimal] = None
    sale_price:           Optional[Decimal] = None
    appraisal_year:       Optional[int]     = None
    acquisition_type:     Optional[str]     = None
    registration:         Optional[str]     = None
    property_number:      Optional[str]     = None
    additional_reference: Optional[str]     = None
    list_code:            Optional[int]     = None
    rental_requirements:  Optional[str]     = None
    general_observations: Optional[str]     = None


class AssetUpdate(AssetCreate):
    pass


class AssetResponse(BaseModel):
    id:                   int
    name:                 str
    short_name:           Optional[str]     = None
    category_id:          int
    category_name:        Optional[str]     = None
    client_id:            Optional[int]     = None
    client_name:          Optional[str]     = None
    owner_id:             Optional[int]     = None
    owner_name:           Optional[str]     = None
    description:          Optional[str]     = None
    location:             Optional[str]     = None
    address:              Optional[str]     = None
    phone:                Optional[str]     = None
    sector_id:            Optional[int]     = None
    is_rented:            int               = 0
    is_active:            int               = 1
    has_sale_option:      int               = 0
    canon_value:          Optional[Decimal] = None
    cadastral_value:      Optional[Decimal] = None
    commercial_value:     Optional[Decimal] = None
    sale_price:           Optional[Decimal] = None
    appraisal_year:       Optional[int]     = None
    acquisition_type:     Optional[str]     = None
    registration:         Optional[str]     = None
    property_number:      Optional[str]     = None
    additional_reference: Optional[str]     = None
    list_code:            Optional[int]     = None
    rental_requirements:  Optional[str]     = None
    general_observations: Optional[str]     = None

    class Config:
        from_attributes = True
