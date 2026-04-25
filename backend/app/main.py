import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine
from app import models

# ===============================
# IMPORT ROUTERS
# ===============================
from app.routers.asset_category_router import router as asset_category_router
from app.routers.assets_router import router as assets_router
from app.routers.worker_router import router as worker_router
from app.routers.profession_router import router as profession_router
from app.routers.task_router import router as task_router
from app.routers.task_status_router import router as task_status_router
from app.routers.auth_router import router as auth_router
from app.routers.menu_router import router as menu_router
from app.routers import profile_router
from app.routers.company_router import router as company_router
from app.routers.company_theme_router import router as company_theme_router
from app.routers.user_router import router as user_router
from app.routers.role_router import router as role_router
from app.routers.system_module_router import router as system_module_router
from app.routers.business_profile_router import router as business_profile_router
from app.routers.business_profile_module import router as bpm_router
from app.routers.language_router import router as language_router
from app.routers.country_router import router as country_router
from app.routers.department_router import router as department_router
from app.routers.municipality_router import router as municipality_router
from app.routers.type_currency_router import router as type_currency_router
from app.routers.dashboard_router import router as dashboard_router
from app.routers.plan_router import router as plan_router
from app.routers.company_plan_router import router as company_plan_router
from app.routers.task_evidence_router import router as task_evidence_router
from app.routers.task_materials_router import router as task_materials_router
from app.routers.task_materials_router import expenses_router as task_expenses_router
from app.routers.task_comment_router import router as task_comment_router
from app.routers.task_progress_router import router as task_progress_router
from app.routers.task_progress_router import asset_history_router
from app import models  # asegura que plan_model se registre en Base

# ===============================
# PATHS
# ===============================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
ASSETS_DIR = FRONTEND_DIST / "assets"

# ===============================
# DB
# ===============================
Base.metadata.create_all(bind=engine)

# ===============================
# APP
# ===============================
app = FastAPI(
    title="EasyPosWeb API",
    version="1.0"
)

app.router.redirect_slashes = True

# ===============================
# STATIC FILES
# ===============================
if ASSETS_DIR.exists() and os.getenv("SERVE_FRONTEND") == "true":
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

UPLOADS_DIR = BASE_DIR / "backend" / "app" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# ===============================
# CORS
# ===============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_origin_regex=r"http://192\.168\.\d+\.\d+:5173",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# ROUTERS
# ===============================
routers = [
    asset_category_router,
    assets_router,
    worker_router,
    profession_router,
    task_router,
    task_status_router,
    auth_router,
    menu_router,
    profile_router.router,
    company_router,
    company_theme_router,
    user_router,
    role_router,
    system_module_router,
    business_profile_router,
    bpm_router,
    language_router,
    country_router,
    department_router,
    municipality_router,
    type_currency_router,
    dashboard_router,
    plan_router,
    company_plan_router,
    task_evidence_router,
    task_materials_router,
    task_expenses_router,
    task_comment_router,
    task_progress_router,
    asset_history_router,
]

for router in routers:
    app.include_router(router)

# ===============================
# SPA FRONTEND
# ===============================
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):

    # 🔥 SI ES API → NO tocar (dejar que FastAPI responda)
    if full_path.startswith("api/"):
        return {"detail": "Not Found"}

    requested = FRONTEND_DIST / full_path

    if requested.exists() and requested.is_file():
        return FileResponse(requested)

    return FileResponse(FRONTEND_DIST / "index.html")

