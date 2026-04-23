"""
========================================================
WORKER ROUTER
========================================================

Profesionales o trabajadores que ejecutan tareas.
"""

# =====================================================
# IMPORTS
# =====================================================

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.worker_model import Worker

# =====================================================
# ROUTER
# =====================================================

router = APIRouter(
    prefix="/workers",
    tags=["Workers"]
)

# =====================================================
# GET ALL WORKERS
# =====================================================

@router.get("/")
def get_workers(db: Session = Depends(get_db)):

    workers = db.query(Worker).all()

    return workers


# =====================================================
# GET WORKER BY ID
# =====================================================

@router.get("/{worker_id}")
def get_worker(worker_id: int, db: Session = Depends(get_db)):

    worker = db.query(Worker).filter(
        Worker.id == worker_id
    ).first()

    if not worker:
        return {"error": "Worker not found"}

    return worker

