from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.business_profile_module import BusinessProfileModule

router = APIRouter(prefix="/business-profile-module", tags=["BusinessProfileModule"])


@router.put("/reorder/")
def reorder_modules(data: list[dict], db: Session = Depends(get_db)):

    for item in data:
        print("ITEM:", item)
        
        module = db.query(BusinessProfileModule).filter(
            BusinessProfileModule.id == item["id"]
        ).first()
        print("FOUND:", module)  # 👈 AGREGA ESTO
        
        if module:
            module.sort_order = item["sort_order"]
            setattr(module, "parent_id", int(item["parent_id"]) if item.get("parent_id") is not None else None)
            
    db.commit()

    return {"message": "Orden actualizado correctamente"}

