"""
========================================================
TASK ROUTER
========================================================

Endpoints relacionados con las tareas del sistema.
"""

# =====================================================
# IMPORTS
# =====================================================

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.task_model import Task

# =====================================================
# ROUTER
# =====================================================

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"]
)

# =====================================================
# GET ALL TASKS
# =====================================================

@router.get("/")
def get_tasks(db: Session = Depends(get_db)):

    tasks = db.query(Task).all()

    return tasks


# =====================================================
# GET TASK BY ID
# =====================================================

@router.get("/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):

    task = db.query(Task).filter(
        Task.id == task_id
    ).first()

    if not task:
        return {"error": "Task not found"}

    return task