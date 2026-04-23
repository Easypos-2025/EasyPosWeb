"""
========================================================
ROUTERS PACKAGE
========================================================

Este módulo centraliza todos los routers del sistema
para facilitar las importaciones.
"""

from .asset_category_router import router as asset_category_router
from .assets_router import router as assets_router
from .worker_router import router as worker_router
from .task_router import router as task_router
from .task_status_router import router as task_status_router

__all__ = [
    "asset_category_router",
    "assets_router",
    "worker_router",
    "task_router",
    "task_status_router"
]