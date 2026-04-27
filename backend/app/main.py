import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine, SessionLocal
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
from app.routers.novelty_router import router as novelty_router
from app.routers.support_ticket_router import router as support_ticket_router
from app.routers.topbar_menu_router import router as topbar_menu_router
from app.routers.system_config_router import router as system_config_router
from app.routers.footer_router import router as footer_router
from app.routers.clients_router import router as clients_router
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


def _init_db_data():
    from sqlalchemy import text
    from app.models.system_config_model import SystemConfig
    from app.models.topbar_menu_item_model import TopbarMenuItem

    db = SessionLocal()
    try:
        # Agregar columna last_seen si no existe (migración segura)
        try:
            db.execute(text("ALTER TABLE user_sessions ADD COLUMN last_seen DATETIME NULL"))
            db.commit()
        except Exception:
            db.rollback()

        # Agregar client_id en assets si no existe
        try:
            db.execute(text("ALTER TABLE assets ADD COLUMN client_id INT NULL"))
            db.commit()
        except Exception:
            db.rollback()

        # Registrar módulo Clientes en system_modules si no existe
        from app.models.system_module_model import SystemModule
        if not db.query(SystemModule).filter(SystemModule.route == "/configuration/clients").first():
            db.add(SystemModule(
                name="Clientes", route="/configuration/clients",
                icon="bi-people", parent_id=None, is_active=True,
                order_index=0, is_sysadmin=False
            ))
            db.commit()

        # Registrar módulo Completar Tareas en system_modules si no existe
        if not db.query(SystemModule).filter(SystemModule.route == "/tasks/completar-info").first():
            db.add(SystemModule(
                name="Completar Información Tareas", route="/tasks/completar-info",
                icon="bi-clipboard-check", parent_id=None, is_active=True,
                order_index=0, is_sysadmin=False
            ))
            db.commit()

        # Datos iniciales system_config
        defaults_config = [
            ("footer_ticker_interval_sec", "45", "Segundos entre cada asociado en el ticker del footer", "integer"),
            ("footer_new_associates_days", "30", "Días para considerar un asociado como nuevo",          "integer"),
            ("footer_ticker_enabled",      "1",  "Habilitar ticker de nuevos asociados",                 "boolean"),
        ]
        for key, value, desc, ctype in defaults_config:
            if not db.query(SystemConfig).filter(SystemConfig.config_key == key).first():
                db.add(SystemConfig(config_key=key, config_value=value, description=desc, config_type=ctype))

        # Datos iniciales topbar_menu_items
        defaults_menu = [
            ("Registro Novedades",    "novedades", "bi-exclamation-triangle", "/novedades",         True,  None, True, 1),
            ("Abrir Ticket Soporte",  "ticket",    "bi-ticket-detailed",      "/soporte/ticket",    True,  2,    True, 2),
            ("Ayuda",                 "ayuda",     "bi-question-circle",      None,                 False, None, True, 3),
            ("Solicitar Productos",   "productos", "bi-bag-plus",             None,                 False, None, True, 4),
            ("Cláusulas Legales",     "clausulas", "bi-shield-check",         "/clausulas-legales", False, None, True, 5),
        ]
        for name, key, icon, route, has_ev, min_plan, is_act, order in defaults_menu:
            if not db.query(TopbarMenuItem).filter(TopbarMenuItem.key == key).first():
                db.add(TopbarMenuItem(
                    name=name, key=key, icon=icon, route=route,
                    has_evidence=has_ev, min_plan_id=min_plan,
                    is_active=is_act, order_index=order
                ))

        db.commit()
    finally:
        db.close()

# ===============================
# APP
# ===============================
app = FastAPI(
    title="EasyPosWeb API",
    version="1.0"
)

_init_db_data()

app.router.redirect_slashes = True

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
        "http://127.0.0.1:5173",
        "https://easyposweb.com",
        "https://www.easyposweb.com",
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
    novelty_router,
    support_ticket_router,
    topbar_menu_router,
    system_config_router,
    footer_router,
    clients_router,
]

for router in routers:
    app.include_router(router)

# STATIC FILES — registrado después de routers para que /assets/ API tenga prioridad
if ASSETS_DIR.exists() and os.getenv("SERVE_FRONTEND") == "true":
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

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

