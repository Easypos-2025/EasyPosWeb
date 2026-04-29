from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.business_profile_module import BusinessProfileModule

router = APIRouter(prefix="/business-profile-module", tags=["BusinessProfileModule"])


@router.put("/reorder/")
def reorder_modules(data: list[dict], db: Session = Depends(get_db)):
    if not data:
        return {"message": "Sin datos"}

    # Detectar profile_id desde el primer registro para eliminar huérfanos
    first = db.query(BusinessProfileModule).filter(
        BusinessProfileModule.id == data[0]["id"]
    ).first()

    if first:
        keep_ids = [item["id"] for item in data]
        # Eliminar registros del perfil que ya no están en el payload
        db.query(BusinessProfileModule).filter(
            BusinessProfileModule.business_profile_id == first.business_profile_id,
            BusinessProfileModule.id.notin_(keep_ids)
        ).delete(synchronize_session=False)

    for item in data:
        module = db.query(BusinessProfileModule).filter(
            BusinessProfileModule.id == item["id"]
        ).first()
        if module:
            module.sort_order = item["sort_order"]
            module.parent_id = int(item["parent_id"]) if item.get("parent_id") is not None else None

    db.commit()
    return {"message": "Orden actualizado correctamente"}

