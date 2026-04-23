"""
========================================================
TASK STATUS ROUTER
========================================================

CRUD para los estados de las tareas
"""

# =====================================================
# IMPORTS
# =====================================================

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.task_status_model import TaskStatus

# =====================================================
# ROUTER
# =====================================================

router = APIRouter(
    prefix="/task-status",
    tags=["Task Status"]
)

# =====================================================
# CREATE STATUS
# =====================================================

@router.post("/")
def create_status(
    name: str,
    description: str,
    db: Session = Depends(get_db)
):

    new_status = TaskStatus(
        name=name,
        description=description
    )

    db.add(new_status)
    db.commit()
    db.refresh(new_status)

    return new_status


# =====================================================
# GET ALL STATUS
# =====================================================

@router.get("/")
def get_status_list(db: Session = Depends(get_db)):

    statuses = db.query(TaskStatus).all()

    return statuses


# =====================================================
# GET STATUS BY ID
# =====================================================

@router.get("/{status_id}")
def get_status(status_id: int, db: Session = Depends(get_db)):

    status = db.query(TaskStatus).filter(
        TaskStatus.id == status_id
    ).first()

    if not status:
        return {"error": "Status not found"}

    return status


# =====================================================
# UPDATE STATUS
# =====================================================

@router.put("/{status_id}")
def update_status(
    status_id: int,
    name: str,
    description: str,
    db: Session = Depends(get_db)
):

    status = db.query(TaskStatus).filter(
        TaskStatus.id == status_id
    ).first()

    if not status:
        return {"error": "Status not found"}

    status.name = name
    status.description = description

    db.commit()

    return status


# =====================================================
# DELETE STATUS
# =====================================================

@router.delete("/{status_id}")
def delete_status(status_id: int, db: Session = Depends(get_db)):

    status = db.query(TaskStatus).filter(
        TaskStatus.id == status_id
    ).first()

    if not status:
        return {"error": "Status not found"}

    db.delete(status)
    db.commit()

    return {"message": "Status deleted"}
