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
from app.routers.invitation_router import router as invitation_router
from app.routers.landing_router import router as landing_router
from app.routers.register_router import router as register_router
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
        # ── MIGRACIONES SEGURAS: columnas nuevas en business_profiles ──
        for col_sql in [
            "ALTER TABLE business_profiles ADD COLUMN image_url VARCHAR(500) NULL",
            "ALTER TABLE business_profiles ADD COLUMN landing_description TEXT NULL",
            "ALTER TABLE business_profiles ADD COLUMN icon VARCHAR(100) DEFAULT 'bi-building'",
            "ALTER TABLE business_profiles ADD COLUMN color_accent VARCHAR(30) DEFAULT '#0d6efd'",
            "ALTER TABLE business_profiles ADD COLUMN show_in_landing TINYINT(1) DEFAULT 1",
        ]:
            try:
                db.execute(text(col_sql))
                db.commit()
            except Exception:
                db.rollback()

        # ── SEED: landing_sections ──────────────────────────────────────
        from app.models.landing_section_model import LandingSection
        seed_sections = [
            {
                "section_key": "hero",
                "title": "Tu negocio, en línea. Sin complicaciones.",
                "subtitle": "Vende, controla inventario y genera reportes desde cualquier dispositivo. Sin instalaciones, sin costos de mantenimiento. Empieza gratis hoy.",
                "cta_text": "Empezar Gratis",
                "cta_url": "/register",
                "image_url": "",
                "is_active": True,
                "order_index": 1,
                "section_type": "hero",
            },
            {
                "section_key": "profiles_intro",
                "title": "Un sistema para cada tipo de negocio",
                "subtitle": "EasyPosWeb se adapta al perfil de tu empresa. Conoce nuestras soluciones especializadas.",
                "cta_text": "",
                "cta_url": "",
                "image_url": "",
                "is_active": True,
                "order_index": 2,
                "section_type": "slider",
            },
            {
                "section_key": "features",
                "title": "Todo lo que necesitas para operar tu negocio",
                "subtitle": "EasyPosWeb no es un programa contable. Es una herramienta operativa para el control diario de ventas, inventarios y cuadres de caja.",
                "body_text": "Control Ventas POS Electrónico (DIAN opcional)|Control Ventas por Recibo (No DIAN)|Control de Clientes|Cuentas por Cobrar — Ventas a Crédito|Impresión Tirilla de Venta y Domiciliario|Pedidos de clientes con ajuste antes de facturar|Todas las formas de pago|Inventario de Productos|Costo y utilidad versus ventas|Reportes de Ventas por categorías a Excel|Cuadres de caja diario|Registro de Gastos, Compras y Vales|Control de usuarios y permisos|Productos por Categorías|Reporte de utilidad por periodo|Reporte por forma de pago por periodo|Asignación de Descuentos por tipificación o valor",
                "cta_text": "",
                "cta_url": "",
                "image_url": "",
                "is_active": True,
                "order_index": 3,
                "section_type": "features",
            },
            {
                "section_key": "free_plan",
                "title": "Comienza GRATIS. Sin tarjeta de crédito.",
                "subtitle": "TODO ESTO DE FORMA GRATUITA Y EN LÍNEA",
                "body_text": "Genera e Imprime tus Ventas|Controla tus inventarios por Categoría|Crea tu base de datos de clientes|Realiza tu cuadre de caja|Genera tus reportes a Excel",
                "cta_text": "Regístrate Gratis",
                "cta_url": "/register",
                "image_url": "",
                "is_active": True,
                "order_index": 4,
                "section_type": "cta",
            },
            {
                "section_key": "multidevice",
                "title": "Desde tu PC, celular o tablet",
                "subtitle": "¿No tienes computador? No te preocupes. Accede desde cualquier dispositivo con internet.",
                "body_text": "Desde tu PC, Celular o Tablet|Sin inversiones costosas en equipos|Sin instalaciones eléctricas adicionales|Sin ocupar espacio|Acceso 24/7 desde cualquier lugar",
                "cta_text": "Ir a easyposweb.com",
                "cta_url": "http://easyposweb.com",
                "image_url": "",
                "is_active": True,
                "order_index": 5,
                "section_type": "features",
            },
            {
                "section_key": "about",
                "title": "Notas Importantes",
                "subtitle": "",
                "body_text": "EasyPos no es un programa Contable — es operativo para ventas, inventarios y cuadres de caja.|No necesita internet para funcionar, excepto el módulo POS Electrónico.|Se paga anualmente con todos los módulos incluidos (excepto POS Electrónico).|Incluye soporte, capacitaciones y actualizaciones durante todo el año.|Las copias de seguridad están incluidas.|El valor de la licencia se conserva igual para el año siguiente.",
                "cta_text": "",
                "cta_url": "",
                "image_url": "",
                "is_active": True,
                "order_index": 6,
                "section_type": "about",
            },
            {
                "section_key": "contact",
                "title": "¿Tienes preguntas? Escríbenos",
                "subtitle": "Nuestro equipo te responde en menos de 24 horas.",
                "body_text": "",
                "cta_text": "",
                "cta_url": "",
                "image_url": "",
                "is_active": True,
                "order_index": 7,
                "section_type": "contact",
            },
        ]
        for s in seed_sections:
            if not db.query(LandingSection).filter(LandingSection.section_key == s["section_key"]).first():
                db.add(LandingSection(**s))
        db.commit()

        # ── SEED: iconos, colores e imágenes por tipo de perfil ───────
        from app.models.business_profile_model import BusinessProfile as BP
        profile_defaults = [
            # (keywords_en_nombre, icon, color, image_url, show_in_landing, landing_desc)
            (
                ["restaurante", "restaurant", "comida", "food"],
                "bi-shop-window", "#f59e0b",
                "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800&q=80",
                True,
                "Solución integral para restaurantes: ventas, mesas, domicilios, menú diario, recetas y control de caja."
            ),
            (
                ["fruver", "fruta", "verdura", "mercado"],
                "bi-basket2-fill", "#10b981",
                "https://images.unsplash.com/photo-1542838132-92c53300491e?w=800&q=80",
                True,
                "Control de ventas e inventario para fruterías y verduleras. Rápido, sencillo y desde cualquier dispositivo."
            ),
            (
                ["drogueria", "droguería", "farmacia", "pharmacy"],
                "bi-capsule", "#6366f1",
                "https://images.unsplash.com/photo-1585435557343-3b092031a831?w=800&q=80",
                True,
                "Gestión de ventas, inventario y clientes para droguerías y farmacias. Con o sin Pos Electrónico."
            ),
            (
                ["tarea", "task", "admon", "administrador", "obra", "proyecto"],
                "bi-clipboard-check-fill", "#2563eb",
                "https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=800&q=80",
                True,
                "Asignación, seguimiento y control de tareas por equipos. Evidencias, materiales y reportes en tiempo real."
            ),
            (
                ["sysadmin", "system", "admin"],
                "bi-shield-fill-check", "#ef4444",
                "",
                False,
                ""
            ),
        ]
        all_profiles = db.query(BP).all()
        for p in all_profiles:
            name_lower = p.name.lower()
            for keywords, icon, color, img, show, desc in profile_defaults:
                if any(k in name_lower for k in keywords):
                    if not p.icon or p.icon == "bi-building":
                        p.icon = icon
                    if not p.color_accent or p.color_accent == "#0d6efd":
                        p.color_accent = color
                    if not p.image_url and img:
                        p.image_url = img
                    if p.show_in_landing is None:
                        p.show_in_landing = show
                    elif any(k in name_lower for k in ["sysadmin", "system"]):
                        p.show_in_landing = False
                    if not p.landing_description and desc:
                        p.landing_description = desc
                    break
        db.commit()

        # ── SEED: plan_features ────────────────────────────────────────
        from app.models.plan_feature_model import PlanFeature
        if db.query(PlanFeature).count() == 0:
            seed_features = [
                # Módulos Básicos
                ("Módulos Básicos", "Administrativo",     "X",   "X",   "X",   "X",   1),
                ("Módulos Básicos", "Ventas / Recibo",    "X",   "X",   "X",   "X",   2),
                ("Módulos Básicos", "Registro Clientes",  "x",   "x",   "x",   "x",   3),
                ("Módulos Básicos", "Cierre Caja",        "x",   "x",   "x",   "x",   4),
                ("Módulos Básicos", "Reporte Ventas",     "x",   "x",   "x",   "x",   5),
                ("Módulos Básicos", "Categorías",         "5",   "10",  "Ilim","Ilim", 6),
                ("Módulos Básicos", "Productos",          "25",  "50",  "Ilim","Ilim", 7),
                ("Módulos Básicos", "Usuarios",           "1",   "5",   "10",  "Ilim", 8),
                ("Módulos Básicos", "Facturas x Mes",     "300", "200", "600", "Ilim", 9),
                # Módulos Avanzados
                ("Módulos Avanzados", "Inventarios",         None, "x", "x", "x", 1),
                ("Módulos Avanzados", "Receta Productos",    None, "x", "x", "x", 2),
                ("Módulos Avanzados", "Ingresos - Egresos",  None, "x", "x", "x", 3),
                ("Módulos Avanzados", "Reportes Varios",     None, "x", "x", "x", 4),
                ("Módulos Avanzados", "Gastos",              None, "x", "x", "x", 5),
                ("Módulos Avanzados", "Ventas x Periodo",    None, "x", "x", "x", 6),
                ("Módulos Avanzados", "Ventas x Vendedor",   None, "x", "x", "x", 7),
                ("Módulos Avanzados", "Cuentas x Cobrar",    None, "x", "x", "x", 8),
                ("Módulos Avanzados", "Armar Menú Diario",   None, "x", "x", "x", 9),
                ("Módulos Avanzados", "Registro Historia",   None, "x", "x", "x", 10),
                # Módulos Especiales
                ("Módulos Especiales", "Domicilios",         None, None, "x", "x", 1),
                ("Módulos Especiales", "Servicio a Mesa",    None, None, "x", "x", 2),
                ("Módulos Especiales", "Separados",          None, None, "x", "x", 3),
                ("Módulos Especiales", "Combos",             None, None, "x", "x", 4),
                ("Módulos Especiales", "Reporte Productos",  None, None, "x", "x", 5),
                ("Módulos Especiales", "Reporte Utilidad",   None, None, "x", "x", 6),
                ("Módulos Especiales", "Proveedores",        None, None, "x", "x", 7),
                ("Módulos Especiales", "Control Propinas",   None, None, "x", "x", 8),
                ("Módulos Especiales", "Cambio Productos",   None, None, "x", "x", 9),
                # Módulos Elite
                ("Módulos Elite", "Control Precios",     None, None, None, "x", 1),
                ("Módulos Elite", "POS Electrónico",     None, None, None, "x", 2),
                ("Módulos Elite", "Módulo Escritorio",   None, None, None, "x", 3),
                ("Módulos Elite", "Insumos Preparados",  None, None, None, "x", 4),
                ("Módulos Elite", "Factura / Recibo",    None, None, None, "x", 5),
            ]
            for cat, name, vf, vb, vs, vp, idx in seed_features:
                db.add(PlanFeature(
                    category=cat, feature_name=name,
                    val_free=vf, val_basic=vb, val_standard=vs, val_premium=vp,
                    order_index=idx, is_active=True
                ))
            db.commit()

        # ── SEED: system_config email_sender_landing ───────────────────
        if not db.query(SystemConfig).filter(SystemConfig.config_key == "email_sender_landing").first():
            db.add(SystemConfig(
                config_key="email_sender_landing",
                config_value="easypos.co@gmail.com",
                description="Email desde donde se envían los correos de contacto de la landing",
                config_type="string"
            ))
            db.commit()

        # ── SEED: módulo landing-manager en system_modules ─────────────
        from app.models.system_module_model import SystemModule
        if not db.query(SystemModule).filter(SystemModule.route == "/sysadmin/landing-manager").first():
            db.add(SystemModule(
                name="Gestión Landing Page",
                route="/sysadmin/landing-manager",
                icon="bi-layout-text-window-reverse",
                parent_id=None,
                is_active=True,
                order_index=0,
                is_sysadmin=True
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
(UPLOADS_DIR / "landing").mkdir(parents=True, exist_ok=True)
(UPLOADS_DIR / "profiles").mkdir(parents=True, exist_ok=True)
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
    invitation_router,
    landing_router,
    register_router,
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

