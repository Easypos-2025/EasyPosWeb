import os
import time
import collections
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, func, text

from app.database import AsyncSessionLocal, init_db
from app import models

# ===============================
# IMPORT ROUTERS
# ===============================
from app.routers.asset_category_router import router as asset_category_router
from app.routers.assets_router import router as assets_router
from app.routers.asset_media_router import router as asset_media_router
from app.routers.public_asset_router import router as public_asset_router
from app.routers.asset_inquiries_router import router as asset_inquiries_router
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
from app.routers.help_router import router as help_router
from app.routers.asset_sector_router import router as asset_sector_router
from app.routers.company_asset_content_router import router as company_asset_content_router
from app.routers.register_router import router as register_router
from app.routers.payment_router import router as payment_router
from app.routers.task_collaborators_router import router as task_collaborators_router
from app.routers.user_notification_router import router as user_notification_router
from app.routers.unidades_medida_router import router as unidades_medida_router
from app.routers.conceptos_gastos_router import router as conceptos_gastos_router
from app.routers.conceptos_compras_router import router as conceptos_compras_router
from app.routers.task_purchases_router import router as task_purchases_router
from app.routers.external_collaborators_router import router as external_collaborators_router
from app.routers.bodega_items_router import router as bodega_items_router
from app.routers.loans_router import router as loans_router
from app.routers.qr_public_router import router as qr_public_router
from app.routers.suppliers_router import router as suppliers_router
from app.routers.supply_items_router import router as supply_items_router
from app.routers.product_categories_router import router as product_categories_router
from app.routers.products_router import router as products_router
from app.routers.price_lists_router import router as price_lists_router
from app.routers.purchase_orders_router import router as purchase_orders_router
from app.routers.pos_sync_router import router as pos_sync_router
from app.routers.pos_dashboard_router import router as pos_dashboard_router
from app.routers.pos_consultas_router import router as pos_consultas_router
from app.routers.pos_categorias_router import router as pos_categorias_router
from app.routers.pos_printers_router import router as pos_printers_router
from app.routers.pos_cajas_router import router as pos_cajas_router
from app.routers.pos_lista_precios_router import router as pos_lista_precios_router
from app.routers.pos_platos_router import router as pos_platos_router
from app.routers.pos_tables_router import router as pos_tables_router
from app.routers.plan_associate_limits_router import router as plan_associate_limits_router
from app.routers.advertisement_router import router as advertisement_router
from app.routers.welcome_steps_router import router as welcome_steps_router
from app import models  # asegura que plan_model se registre en Base

# ===============================
# PATHS
# ===============================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
ASSETS_DIR = FRONTEND_DIST / "assets"


# ===============================
# DB INIT DATA (async)
# ===============================
async def _init_db_data():
    from app.models.system_config_model import SystemConfig
    from app.models.topbar_menu_item_model import TopbarMenuItem

    async with AsyncSessionLocal() as db:
        # Agregar columna last_seen si no existe (migración segura)
        try:
            await db.execute(text("ALTER TABLE user_sessions ADD COLUMN last_seen DATETIME NULL"))
            await db.commit()
        except Exception:
            await db.rollback()

        # Agregar client_id en assets si no existe
        try:
            await db.execute(text("ALTER TABLE assets ADD COLUMN client_id INT NULL"))
            await db.commit()
        except Exception:
            await db.rollback()

        # ── ASSETS: campos extendidos (migración segura columna a columna) ─────
        _asset_cols = [
            "ALTER TABLE assets ADD COLUMN short_name VARCHAR(100) NULL",
            "ALTER TABLE assets ADD COLUMN address VARCHAR(300) NULL",
            "ALTER TABLE assets ADD COLUMN phone VARCHAR(20) NULL",
            "ALTER TABLE assets ADD COLUMN sector_id INT NULL",
            "ALTER TABLE assets ADD COLUMN owner_id INT NULL",
            "ALTER TABLE assets ADD COLUMN is_rented TINYINT(1) NOT NULL DEFAULT 0",
            "ALTER TABLE assets ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1",
            "ALTER TABLE assets ADD COLUMN has_sale_option TINYINT(1) NOT NULL DEFAULT 0",
            "ALTER TABLE assets ADD COLUMN canon_value DECIMAL(15,2) NULL",
            "ALTER TABLE assets ADD COLUMN cadastral_value DECIMAL(15,2) NULL",
            "ALTER TABLE assets ADD COLUMN commercial_value DECIMAL(15,2) NULL",
            "ALTER TABLE assets ADD COLUMN sale_price DECIMAL(15,2) NULL",
            "ALTER TABLE assets ADD COLUMN appraisal_year INT NULL",
            "ALTER TABLE assets ADD COLUMN acquisition_type VARCHAR(50) NULL",
            "ALTER TABLE assets ADD COLUMN registration VARCHAR(100) NULL",
            "ALTER TABLE assets ADD COLUMN property_number VARCHAR(100) NULL",
            "ALTER TABLE assets ADD COLUMN additional_reference VARCHAR(300) NULL",
            "ALTER TABLE assets ADD COLUMN list_code INT NULL",
            "ALTER TABLE assets ADD UNIQUE INDEX uq_assets_list_code (list_code)",
            "ALTER TABLE assets ADD COLUMN rental_requirements TEXT NULL",
            "ALTER TABLE assets ADD COLUMN general_observations TEXT NULL",
            "ALTER TABLE assets ADD COLUMN plan_blocked TINYINT(1) NOT NULL DEFAULT 0",
            "ALTER TABLE assets ADD COLUMN plan_blocked_at DATETIME NULL",
        ]
        for _sql in _asset_cols:
            try:
                await db.execute(text(_sql))
                await db.commit()
            except Exception:
                await db.rollback()

        # ── Migración: view_route en help_articles ────────────────────────────
        try:
            await db.execute(text(
                "ALTER TABLE help_articles ADD COLUMN view_route VARCHAR(200) NULL"
            ))
            await db.commit()
        except Exception:
            await db.rollback()

        # ── SYSTEM_MODULE: Consultas de Activos ───────────────────────────────
        try:
            from app.models.system_module_model import SystemModule as SM
            _existing = await db.execute(select(SM).where(SM.route == "/assets/inquiries"))
            if not _existing.scalars().first():
                db.add(SM(name="Consultas Activos", route="/assets/inquiries",
                          icon="bi-chat-dots", parent_id=None, is_active=True, order_index=0, is_sysadmin=False))
                await db.commit()
        except Exception:
            await db.rollback()

        # ── ASSET MEDIA y ASSET INQUIRIES ──────────────────────────────────────
        _asset_tables = [
            """CREATE TABLE IF NOT EXISTS asset_media (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                asset_id    INT NOT NULL,
                file_url    VARCHAR(500) NOT NULL,
                file_name   VARCHAR(200) NOT NULL,
                file_type   VARCHAR(10)  NOT NULL,
                file_size   INT NOT NULL DEFAULT 0,
                sort_order  SMALLINT NOT NULL DEFAULT 0,
                uploaded_by INT NOT NULL,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
                INDEX idx_am_asset (asset_id)
            )""",
            """CREATE TABLE IF NOT EXISTS asset_inquiries (
                id            INT AUTO_INCREMENT PRIMARY KEY,
                asset_id      INT NOT NULL,
                name          VARCHAR(100) NOT NULL,
                phone         VARCHAR(20)  NOT NULL,
                email         VARCHAR(150) NOT NULL,
                interest      VARCHAR(20)  NOT NULL,
                message       TEXT NULL,
                confirm_token VARCHAR(64)  NOT NULL,
                status        VARCHAR(20)  NOT NULL DEFAULT 'pending',
                ip_address    VARCHAR(45)  NULL,
                confirmed_at  TIMESTAMP NULL,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
                UNIQUE KEY uq_inquiry_asset_email (asset_id, email),
                UNIQUE KEY uq_inquiry_token (confirm_token),
                INDEX idx_ai_asset (asset_id)
            )""",
        ]
        for _sql in _asset_tables:
            try:
                await db.execute(text(_sql))
                await db.commit()
            except Exception:
                await db.rollback()

        # ── INVENTARIO: tablas base ────────────────────────────────────────────
        inventory_tables = [
            """CREATE TABLE IF NOT EXISTS suppliers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                company_id INT NOT NULL,
                name VARCHAR(200) NOT NULL,
                nit VARCHAR(50) NULL,
                contact_name VARCHAR(150) NULL,
                email VARCHAR(150) NULL,
                phone VARCHAR(30) NULL,
                address TEXT NULL,
                notes TEXT NULL,
                is_active TINYINT(1) NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_sup_company (company_id)
            )""",
            """CREATE TABLE IF NOT EXISTS supply_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                company_id INT NOT NULL,
                code VARCHAR(50) NULL,
                name VARCHAR(200) NOT NULL,
                description TEXT NULL,
                unit_id INT NULL,
                cost_price DECIMAL(14,4) NOT NULL DEFAULT 0,
                stock_qty DECIMAL(14,4) NOT NULL DEFAULT 0,
                min_stock DECIMAL(14,4) NOT NULL DEFAULT 0,
                waste_pct DECIMAL(5,2) NOT NULL DEFAULT 0,
                control_stock TINYINT(1) NOT NULL DEFAULT 1,
                is_active TINYINT(1) NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_si_company (company_id),
                INDEX idx_si_code (code)
            )""",
            """CREATE TABLE IF NOT EXISTS product_categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                company_id INT NOT NULL,
                name VARCHAR(150) NOT NULL,
                description VARCHAR(255) NULL,
                color VARCHAR(10) NULL,
                icon VARCHAR(50) NULL,
                is_active TINYINT(1) NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_pc_company (company_id)
            )""",
            """CREATE TABLE IF NOT EXISTS product_references (
                id INT AUTO_INCREMENT PRIMARY KEY,
                company_id INT NOT NULL,
                code VARCHAR(50) NOT NULL,
                name VARCHAR(200) NOT NULL,
                base_price DECIMAL(14,2) NOT NULL DEFAULT 0,
                base_cost DECIMAL(14,2) NOT NULL DEFAULT 0,
                is_active TINYINT(1) NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_pr_company (company_id)
            )""",
            """CREATE TABLE IF NOT EXISTS price_lists (
                id INT AUTO_INCREMENT PRIMARY KEY,
                company_id INT NOT NULL,
                name VARCHAR(150) NOT NULL,
                description VARCHAR(255) NULL,
                is_default TINYINT(1) NOT NULL DEFAULT 0,
                is_active TINYINT(1) NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_pl_company (company_id)
            )""",
            """CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                company_id INT NOT NULL,
                code VARCHAR(50) NULL,
                name VARCHAR(200) NOT NULL,
                description TEXT NULL,
                photo_url VARCHAR(500) NULL,
                category_id INT NULL,
                reference_id INT NULL,
                inventory_behavior VARCHAR(20) NOT NULL DEFAULT 'direct',
                base_price DECIMAL(14,2) NOT NULL DEFAULT 0,
                cost_price DECIMAL(14,2) NOT NULL DEFAULT 0,
                tax_rate DECIMAL(5,2) NOT NULL DEFAULT 0,
                min_stock DECIMAL(14,4) NOT NULL DEFAULT 0,
                ask_price TINYINT(1) NOT NULL DEFAULT 0,
                ask_description TINYINT(1) NOT NULL DEFAULT 0,
                is_active TINYINT(1) NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_prod_company (company_id),
                INDEX idx_prod_code (code)
            )""",
            """CREATE TABLE IF NOT EXISTS product_recipes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                product_id INT NOT NULL,
                supply_item_id INT NOT NULL,
                qty_required DECIMAL(14,4) NOT NULL DEFAULT 1,
                unit_id INT NULL,
                INDEX idx_recipe_product (product_id)
            )""",
            """CREATE TABLE IF NOT EXISTS product_presentations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                product_id INT NOT NULL,
                supply_item_id INT NULL,
                name VARCHAR(100) NOT NULL,
                factor DECIMAL(14,4) NOT NULL DEFAULT 1,
                barcode VARCHAR(100) NULL,
                price DECIMAL(14,2) NULL,
                is_active TINYINT(1) NOT NULL DEFAULT 1,
                INDEX idx_pp_product (product_id)
            )""",
            """CREATE TABLE IF NOT EXISTS serialized_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                product_id INT NOT NULL,
                serial_code VARCHAR(100) NOT NULL,
                supplier_id INT NULL,
                purchase_cost DECIMAL(14,2) NOT NULL DEFAULT 0,
                is_sold TINYINT(1) NOT NULL DEFAULT 0,
                sold_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_ser_product (product_id),
                INDEX idx_ser_serial (serial_code)
            )""",
            """CREATE TABLE IF NOT EXISTS price_list_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                price_list_id INT NOT NULL,
                product_id INT NOT NULL,
                presentation_id INT NULL,
                price DECIMAL(14,2) NOT NULL DEFAULT 0,
                is_active TINYINT(1) NOT NULL DEFAULT 1,
                INDEX idx_pli_list (price_list_id),
                INDEX idx_pli_product (product_id)
            )""",
            """CREATE TABLE IF NOT EXISTS purchase_orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                company_id INT NOT NULL,
                supplier_id INT NULL,
                invoice_no VARCHAR(100) NULL,
                order_date DATE NOT NULL,
                total_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
                notes TEXT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'draft',
                created_by INT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_po_company (company_id),
                INDEX idx_po_supplier (supplier_id)
            )""",
            """CREATE TABLE IF NOT EXISTS purchase_order_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                purchase_order_id INT NOT NULL,
                supply_item_id INT NOT NULL,
                qty DECIMAL(14,4) NOT NULL DEFAULT 0,
                unit_price DECIMAL(14,4) NOT NULL DEFAULT 0,
                subtotal DECIMAL(14,2) NOT NULL DEFAULT 0,
                presentation_name VARCHAR(100) NULL,
                INDEX idx_poi_order (purchase_order_id)
            )""",
            """CREATE TABLE IF NOT EXISTS stock_movements (
                id INT AUTO_INCREMENT PRIMARY KEY,
                company_id INT NOT NULL,
                supply_item_id INT NOT NULL,
                movement_type VARCHAR(20) NOT NULL,
                qty DECIMAL(14,4) NOT NULL,
                qty_before DECIMAL(14,4) NOT NULL DEFAULT 0,
                qty_after DECIMAL(14,4) NOT NULL DEFAULT 0,
                reference_type VARCHAR(30) NULL,
                reference_id INT NULL,
                notes TEXT NULL,
                created_by INT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_sm_company (company_id),
                INDEX idx_sm_item (supply_item_id)
            )""",
        ]
        for sql in inventory_tables:
            try:
                await db.execute(text(sql))
                await db.commit()
            except Exception:
                await db.rollback()

        # Agregar price_list_id a clients si no existe
        try:
            await db.execute(text("ALTER TABLE clients ADD COLUMN price_list_id INT NULL"))
            await db.commit()
        except Exception:
            await db.rollback()

        # Registrar módulo Clientes en system_modules si no existe
        from app.models.system_module_model import SystemModule
        result = await db.execute(select(SystemModule).where(SystemModule.route == "/configuration/clients"))
        if not result.scalars().first():
            db.add(SystemModule(
                name="Clientes", route="/configuration/clients",
                icon="bi-people", parent_id=None, is_active=True,
                order_index=0, is_sysadmin=False
            ))
            await db.commit()

        # Registrar módulo Completar Tareas en system_modules si no existe
        result = await db.execute(select(SystemModule).where(SystemModule.route == "/tasks/completar-info"))
        if not result.scalars().first():
            db.add(SystemModule(
                name="Completar Información Tareas", route="/tasks/completar-info",
                icon="bi-clipboard-check", parent_id=None, is_active=True,
                order_index=0, is_sysadmin=False
            ))
            await db.commit()

        # Registrar módulo Firma de Email en system_modules si no existe
        result = await db.execute(select(SystemModule).where(SystemModule.route == "/sysadmin/email-footer"))
        if not result.scalars().first():
            db.add(SystemModule(
                name="Firma de Email", route="/sysadmin/email-footer",
                icon="bi-envelope-paper", parent_id=None, is_active=True,
                order_index=0, is_sysadmin=True
            ))
            await db.commit()

        # Registrar módulo Gestión de Ayuda en system_modules si no existe
        result = await db.execute(select(SystemModule).where(SystemModule.route == "/sysadmin/help"))
        if not result.scalars().first():
            db.add(SystemModule(
                name="Gestión de Ayuda", route="/sysadmin/help",
                icon="bi-question-circle-fill", parent_id=None, is_active=True,
                order_index=0, is_sysadmin=True
            ))
            await db.commit()

        # ── Módulos de inventario ──────────────────────────────────────────────
        inventory_modules = [
            ("Proveedores",       "/inventory/suppliers",        "bi-truck"),
            ("Insumos",           "/inventory/supply-items",     "bi-box-seam"),
            ("Categorías Prod.",  "/inventory/categories",       "bi-tags"),
            ("Productos",         "/inventory/products",         "bi-grid"),
            ("Listas de Precios", "/inventory/price-lists",      "bi-currency-dollar"),
            ("Entradas Mercancía","/inventory/purchase-orders",  "bi-cart-plus"),
        ]
        for mod_name, mod_route, mod_icon in inventory_modules:
            result = await db.execute(select(SystemModule).where(SystemModule.route == mod_route))
            if not result.scalars().first():
                db.add(SystemModule(
                    name=mod_name, route=mod_route,
                    icon=mod_icon, parent_id=None, is_active=True,
                    order_index=0, is_sysadmin=False
                ))
        await db.commit()

        # Crear tabla user_notifications si no existe (migración segura)
        try:
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS user_notifications (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    sender_id INTEGER NOT NULL,
                    receiver_id INTEGER NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    message TEXT NOT NULL,
                    is_read TINYINT(1) NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_un_receiver (receiver_id),
                    INDEX idx_un_sender (sender_id)
                )
            """))
            await db.commit()
        except Exception:
            await db.rollback()

        # Registrar módulos inbox/outbox en system_modules
        result = await db.execute(select(SystemModule).where(SystemModule.route == "/notifications/inbox"))
        if not result.scalars().first():
            db.add(SystemModule(
                name="Bandeja de Entrada", route="/notifications/inbox",
                icon="bi-envelope-open", parent_id=None, is_active=True,
                order_index=0, is_sysadmin=False
            ))
            await db.commit()

        result = await db.execute(select(SystemModule).where(SystemModule.route == "/notifications/outbox"))
        if not result.scalars().first():
            db.add(SystemModule(
                name="Mensajes Enviados", route="/notifications/outbox",
                icon="bi-send", parent_id=None, is_active=True,
                order_index=0, is_sysadmin=False
            ))
            await db.commit()

        # Datos iniciales system_config
        defaults_config = [
            ("footer_ticker_interval_sec",      "45",    "Segundos entre cada asociado en el ticker del footer",                   "integer"),
            ("footer_new_associates_days",      "30",    "Días para considerar un asociado como nuevo",                           "integer"),
            ("footer_ticker_enabled",           "1",     "Habilitar ticker de nuevos asociados",                                  "boolean"),
            ("topbar_notif_interval_ms",        "60000", "Intervalo en ms para verificar notificaciones en el topbar (default 60s)", "integer"),
            ("topbar_heartbeat_interval_ms",    "180000","Intervalo en ms para heartbeat de sesión en el topbar (default 3min)",    "integer"),
            ("email_footer_legal_name",    "EasyPosWeb SAS",                              "Razón social que aparece en el pie de los emails",        "string"),
            ("email_footer_nit",           "900.123.456-7",                               "NIT de la empresa en el pie de los emails",               "string"),
            ("email_footer_tagline",       "Tu negocio, en línea. Sin complicaciones.",   "Slogan que aparece en el pie de los emails",              "string"),
            ("email_footer_website",       "https://easyposweb.com",                      "URL del sitio web en el pie de los emails",               "string"),
            ("email_footer_support_email", "soporte@easyposweb.com",                      "Email de soporte visible en el pie de los emails",        "string"),
            ("email_footer_phone",         "",                                             "Teléfono de contacto en el pie de los emails (opcional)", "string"),
            ("email_footer_address",       "Colombia",                                    "Dirección o país en el pie de los emails",                "string"),
        ]
        for key, value, desc, ctype in defaults_config:
            result = await db.execute(select(SystemConfig).where(SystemConfig.config_key == key))
            if not result.scalars().first():
                db.add(SystemConfig(config_key=key, config_value=value, description=desc, config_type=ctype))

        # Datos iniciales topbar_menu_items
        defaults_menu = [
            ("Registro Novedades",    "novedades",   "bi-exclamation-triangle", "/novedades",         True,  None, True, 1),
            ("Abrir Ticket Soporte",  "ticket",      "bi-ticket-detailed",      "/soporte/ticket",    True,  2,    True, 2),
            ("Ayuda",                 "ayuda",       "bi-question-circle",      None,                 False, None, True, 3),
            ("Solicitar Productos",   "productos",   "bi-bag-plus",             None,                 False, None, True, 4),
            ("Cláusulas Legales",     "clausulas",   "bi-shield-check",         "/clausulas-legales", False, None, True, 5),
            ("Guía de Inicio",        "bienvenida",  "bi-stars",                "/bienvenida",        False, None, True, 0),
        ]
        for name, key, icon, route, has_ev, min_plan, is_act, order in defaults_menu:
            result = await db.execute(select(TopbarMenuItem).where(TopbarMenuItem.key == key))
            if not result.scalars().first():
                db.add(TopbarMenuItem(
                    name=name, key=key, icon=icon, route=route,
                    has_evidence=has_ev, min_plan_id=min_plan,
                    is_active=is_act, order_index=order
                ))

        await db.commit()

        # ── TABLA profile_welcome_steps ───────────────────────────────────────
        try:
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS profile_welcome_steps (
                    id                  INT AUTO_INCREMENT PRIMARY KEY,
                    business_profile_id INT NOT NULL,
                    step_number         INT NOT NULL DEFAULT 0,
                    icon                VARCHAR(60)  NOT NULL DEFAULT 'bi-star',
                    title               VARCHAR(120) NOT NULL,
                    description         TEXT NOT NULL,
                    route_hint          VARCHAR(150) NULL,
                    is_active           TINYINT(1) NOT NULL DEFAULT 1,
                    FOREIGN KEY (business_profile_id) REFERENCES business_profiles(id),
                    INDEX idx_pws_profile (business_profile_id)
                )
            """))
            await db.commit()
        except Exception:
            await db.rollback()

        # ── SEED pasos bienvenida Perfil Administrativo (id=2) ───────────────
        from app.models.profile_welcome_step_model import ProfileWelcomeStep
        _existing_steps = (await db.execute(
            select(ProfileWelcomeStep).where(ProfileWelcomeStep.business_profile_id == 2)
        )).scalars().all()
        if not _existing_steps:
            _admin_steps = [
                (1, "bi-shield-lock",    "Configura tus roles",
                 "Define qué puede ver y hacer cada tipo de usuario en la plataforma. "
                 "Por ejemplo: un Administrador tiene acceso total, mientras que un Líder de Tareas solo ve las tareas que le asignan.",
                 "/configuration/roles"),
                (2, "bi-people-fill",    "Crea tus usuarios",
                 "Agrega a las personas de tu equipo para que puedan ingresar al sistema. "
                 "Cada usuario tendrá su propio correo y contraseña, y solo verá lo que su rol le permite.",
                 "/configuration/users"),
                (3, "bi-tags-fill",      "Define categorías de activos",
                 "Organiza tus propiedades o equipos por tipo: por ejemplo, Edificios, Vehículos o Maquinaria. "
                 "Esto te ayuda a filtrar y encontrar lo que necesitas más rápido.",
                 "/configuration/asset-categories"),
                (4, "bi-building-fill",  "Registra tus activos",
                 "Un activo es cualquier bien que administras: un apartamento, una bodega, un vehículo o un equipo. "
                 "Aquí los registras con todos sus datos, fotos y documentos.",
                 "/configuration/assets"),
                (5, "bi-person-badge",   "Agrega tus trabajadores",
                 "Los trabajadores son el personal de campo que ejecuta las tareas. "
                 "No necesitan acceso al sistema; el Líder de Tareas reporta por ellos.",
                 "/configuration/workers"),
                (6, "bi-clipboard2-check-fill", "Crea y asigna tareas",
                 "Una tarea es cualquier trabajo que se hace sobre un activo: mantenimiento, reparación, inspección, etc. "
                 "Asígnala a un Líder de Tareas y haz seguimiento del avance en tiempo real.",
                 "/configuration/tasks"),
            ]
            for num, icon, title, desc, route in _admin_steps:
                db.add(ProfileWelcomeStep(
                    business_profile_id=2, step_number=num,
                    icon=icon, title=title, description=desc,
                    route_hint=route, is_active=True
                ))
            await db.commit()

        # ── SYSTEM_MODULE: Bienvenida ─────────────────────────────────────────
        try:
            from app.models.system_module_model import SystemModule as SM
            _bv = await db.execute(select(SM).where(SM.route == "/bienvenida"))
            if not _bv.scalars().first():
                db.add(SM(name="Bienvenida", route="/bienvenida", icon="bi-stars",
                          parent_id=None, is_active=True, order_index=0, is_sysadmin=False))
                await db.commit()
        except Exception:
            await db.rollback()

        # ── MIGRACIONES SEGURAS: columnas nuevas en business_profiles ──
        for col_sql in [
            "ALTER TABLE business_profiles ADD COLUMN image_url VARCHAR(500) NULL",
            "ALTER TABLE business_profiles ADD COLUMN landing_description TEXT NULL",
            "ALTER TABLE business_profiles ADD COLUMN icon VARCHAR(100) DEFAULT 'bi-building'",
            "ALTER TABLE business_profiles ADD COLUMN color_accent VARCHAR(30) DEFAULT '#0d6efd'",
            "ALTER TABLE business_profiles ADD COLUMN show_in_landing TINYINT(1) DEFAULT 1",
        ]:
            try:
                await db.execute(text(col_sql))
                await db.commit()
            except Exception:
                await db.rollback()

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
            result = await db.execute(select(LandingSection).where(LandingSection.section_key == s["section_key"]))
            if not result.scalars().first():
                db.add(LandingSection(**s))
        await db.commit()

        # ── SEED: iconos, colores e imágenes por tipo de perfil ───────
        from app.models.business_profile_model import BusinessProfile as BP
        profile_defaults = [
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
        result = await db.execute(select(BP))
        all_profiles = result.scalars().all()
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
        await db.commit()

        # ── SEED: plan_features ────────────────────────────────────────
        from app.models.plan_feature_model import PlanFeature
        count_result = await db.execute(select(func.count()).select_from(PlanFeature))
        if count_result.scalar() == 0:
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
            await db.commit()

        # ── SEED: system_config email_sender_landing ───────────────────
        result = await db.execute(select(SystemConfig).where(SystemConfig.config_key == "email_sender_landing"))
        if not result.scalars().first():
            db.add(SystemConfig(
                config_key="email_sender_landing",
                config_value="easypos.co@gmail.com",
                description="Email desde donde se envían los correos de contacto de la landing",
                config_type="string"
            ))
            await db.commit()

        # ── SEED: módulo landing-manager en system_modules ─────────────
        result = await db.execute(select(SystemModule).where(SystemModule.route == "/sysadmin/landing-manager"))
        if not result.scalars().first():
            db.add(SystemModule(
                name="Gestión Landing Page",
                route="/sysadmin/landing-manager",
                icon="bi-layout-text-window-reverse",
                parent_id=None,
                is_active=True,
                order_index=0,
                is_sysadmin=True
            ))
            await db.commit()

        # ── MIGRACIÓN: columnas nuevas en companies ─────────────────────
        for col_sql in [
            "ALTER TABLE companies ADD COLUMN payment_status VARCHAR(30) NOT NULL DEFAULT 'active'",
            "ALTER TABLE companies ADD COLUMN upgrade_status VARCHAR(30) NULL DEFAULT NULL",
        ]:
            try:
                await db.execute(text(col_sql))
                await db.commit()
            except Exception:
                await db.rollback()

        # ── MIGRACIÓN: company_payments — todas las columnas del modelo ──
        for col_sql in [
            "ALTER TABLE company_payments ADD COLUMN payment_type VARCHAR(20) NOT NULL DEFAULT 'activation'",
            "ALTER TABLE company_payments ADD COLUMN currency_code VARCHAR(3) NOT NULL DEFAULT 'COP'",
            "ALTER TABLE company_payments ADD COLUMN previous_plan_id INT NULL",
            "ALTER TABLE company_payments ADD COLUMN receipt_url VARCHAR(500) NULL",
            "ALTER TABLE company_payments ADD COLUMN receipt_number VARCHAR(100) NULL",
            "ALTER TABLE company_payments ADD COLUMN bank_origin VARCHAR(100) NULL",
            "ALTER TABLE company_payments ADD COLUMN payment_date DATE NULL",
            "ALTER TABLE company_payments ADD COLUMN confirmed_amount FLOAT NULL",
            "ALTER TABLE company_payments ADD COLUMN review_description TEXT NULL",
            "ALTER TABLE company_payments ADD COLUMN review_evidence_url VARCHAR(500) NULL",
            "ALTER TABLE company_payments ADD COLUMN rejection_reason TEXT NULL",
            "ALTER TABLE company_payments ADD COLUMN submitted_at DATETIME NULL",
            "ALTER TABLE company_payments ADD COLUMN reviewed_at DATETIME NULL",
            "ALTER TABLE company_payments ADD COLUMN reviewed_by INT NULL",
            "ALTER TABLE company_payments ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE company_payments ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
        ]:
            try:
                await db.execute(text(col_sql))
                await db.commit()
            except Exception:
                await db.rollback()

        # ── MIGRACIÓN: renombrar tablas con nombres en español ─────────
        for old_name, new_name in [
            ("colaborador_tarea", "task_collaborators"),
            ("factura_domicilio",  "invoice_delivery_fees"),
            ("recibos_domicilio",  "receipt_delivery_fees"),
        ]:
            try:
                await db.execute(text(f"RENAME TABLE {old_name} TO {new_name}"))
                await db.commit()
            except Exception:
                await db.rollback()

        # ── MIGRACIÓN: tabla task_collaborators ─────────────────────────
        try:
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS task_collaborators (
                    id          INT AUTO_INCREMENT PRIMARY KEY,
                    task_id     INT NOT NULL,
                    user_id     INT NOT NULL,
                    assigned_by INT NULL,
                    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_task_user (task_id, user_id),
                    FOREIGN KEY (task_id)     REFERENCES tasks(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id)     REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (assigned_by) REFERENCES users(id) ON DELETE SET NULL
                )
            """))
            await db.commit()
        except Exception:
            await db.rollback()

        # ── MIGRACIÓN: tablas de domicilios (nombres en inglés) ─────────
        for ddl in [
            """CREATE TABLE IF NOT EXISTS invoice_delivery_fees (
                id             INT AUTO_INCREMENT PRIMARY KEY,
                invoice_number VARCHAR(20)  NOT NULL,
                company_id     INT          NOT NULL,
                amount         FLOAT        DEFAULT 0,
                date           DATE         NULL,
                order_number   VARCHAR(50)  NULL DEFAULT '',
                employee_id    INT          DEFAULT 0,
                customer_id    INT          DEFAULT 0,
                synced         TINYINT(1)   DEFAULT 0,
                updated_at     DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uq_inv_company (invoice_number, company_id)
            ) COLLATE=utf8mb4_general_ci""",
            """CREATE TABLE IF NOT EXISTS receipt_delivery_fees (
                id             INT AUTO_INCREMENT PRIMARY KEY,
                invoice_number VARCHAR(20)  NOT NULL,
                company_id     INT          NOT NULL,
                amount         FLOAT        DEFAULT 0,
                date           DATE         NULL,
                order_number   VARCHAR(50)  NULL DEFAULT '',
                employee_id    INT          DEFAULT 0,
                customer_id    INT          DEFAULT 0,
                synced         TINYINT(1)   DEFAULT 0,
                updated_at     DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uq_rec_company (invoice_number, company_id)
            ) COLLATE=utf8mb4_general_ci""",
        ]:
            try:
                await db.execute(text(ddl))
                await db.commit()
            except Exception:
                await db.rollback()

        # ── MIGRACIÓN: system_modules — columna is_sysadmin ─────────────
        for col_sql in [
            "ALTER TABLE system_modules ADD COLUMN is_sysadmin TINYINT(1) NOT NULL DEFAULT 0",
        ]:
            try:
                await db.execute(text(col_sql))
                await db.commit()
            except Exception:
                await db.rollback()

        # ── MIGRACIÓN: users — columnas de personalización ──────────────
        for col_sql in [
            "ALTER TABLE users ADD COLUMN topbar_color VARCHAR(20) NULL",
            "ALTER TABLE users ADD COLUMN sidebar_color VARCHAR(20) NULL",
            "ALTER TABLE users ADD COLUMN bg_color VARCHAR(20) NULL",
            "ALTER TABLE users ADD COLUMN logo VARCHAR(255) NULL",
        ]:
            try:
                await db.execute(text(col_sql))
                await db.commit()
            except Exception:
                await db.rollback()

        # ── MIGRACIÓN: companies — columna business_profile_id ──────────
        for col_sql in [
            "ALTER TABLE companies ADD COLUMN business_profile_id INT NULL",
        ]:
            try:
                await db.execute(text(col_sql))
                await db.commit()
            except Exception:
                await db.rollback()

        # ── MIGRACIÓN: tabla plan_prices (multi-moneda) ──────────────────
        try:
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS plan_prices (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    plan_id INT NOT NULL,
                    currency_code VARCHAR(3) NOT NULL,
                    amount FLOAT NOT NULL,
                    is_active TINYINT(1) DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_plan_currency (plan_id, currency_code),
                    FOREIGN KEY (plan_id) REFERENCES plans(id)
                )
            """))
            await db.commit()
        except Exception:
            await db.rollback()

        # ── SEED: módulos de pagos en system_modules ────────────────────
        for route, name, icon, is_sysadmin in [
            ("/sysadmin/payment-review",  "Revisión de Pagos",  "bi-credit-card-2-back", True),
            ("/sysadmin/payment-history", "Historial de Pagos", "bi-clock-history",      True),
            ("/payment-history",          "Historial de Pagos", "bi-clock-history",      False),
        ]:
            result = await db.execute(select(SystemModule).where(SystemModule.route == route))
            if not result.scalars().first():
                db.add(SystemModule(
                    name=name, route=route, icon=icon,
                    parent_id=None, is_active=True, order_index=0,
                    is_sysadmin=is_sysadmin
                ))
        await db.commit()

        # ── SEED: módulos préstamos/bodega ───────────────────────────────
        for route, name, icon in [
            ("/configuration/colaboradores-externos", "Colaboradores Externos", "bi-person-badge"),
            ("/configuration/bodega",                 "Bodega",                 "bi-archive"),
            ("/loans/prestamos",                      "Préstamos",              "bi-box-arrow-right"),
        ]:
            result = await db.execute(select(SystemModule).where(SystemModule.route == route))
            if not result.scalars().first():
                db.add(SystemModule(
                    name=name, route=route, icon=icon,
                    parent_id=None, is_active=True, order_index=0, is_sysadmin=False
                ))
        await db.commit()

        # ── SEED: módulos catálogo tareas ────────────────────────────────
        for route, name, icon in [
            ("/configuration/unidades-medida",  "Unidades de Medida","bi-rulers"),
            ("/configuration/conceptos-gastos", "Conceptos de Gasto","bi-receipt"),
            ("/configuration/conceptos-compras","Conceptos de Compra","bi-cart3"),
        ]:
            result = await db.execute(select(SystemModule).where(SystemModule.route == route))
            if not result.scalars().first():
                db.add(SystemModule(
                    name=name, route=route, icon=icon,
                    parent_id=None, is_active=True, order_index=0, is_sysadmin=False
                ))
        await db.commit()

        # ── PAUTAS PUBLICITARIAS: tablas ─────────────────────────────────
        ad_tables = [
            """CREATE TABLE IF NOT EXISTS advertisements (
                id                INT AUTO_INCREMENT PRIMARY KEY,
                company_id        INT NOT NULL,
                title             VARCHAR(200) NOT NULL,
                description       TEXT NULL,
                cta_url           VARCHAR(500) NULL,
                notes_to_admin    TEXT NULL,
                target_profile_id INT NULL,
                status            VARCHAR(20) NOT NULL DEFAULT 'pending',
                slot_position     SMALLINT NULL,
                priority          SMALLINT NOT NULL DEFAULT 0,
                start_date        DATE NULL,
                end_date          DATE NULL,
                rejection_reason  TEXT NULL,
                approved_by       INT NULL,
                approved_at       TIMESTAMP NULL,
                impressions       INT NOT NULL DEFAULT 0,
                created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_ad_company (company_id),
                INDEX idx_ad_status  (status),
                INDEX idx_ad_slot    (slot_position)
            )""",
            """CREATE TABLE IF NOT EXISTS ad_pieces (
                id               INT AUTO_INCREMENT PRIMARY KEY,
                advertisement_id INT NOT NULL,
                piece_type       VARCHAR(20) NOT NULL,
                media_url        VARCHAR(500) NULL,
                youtube_id       VARCHAR(20) NULL,
                text_content     TEXT NULL,
                order_index      SMALLINT NOT NULL DEFAULT 0,
                created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (advertisement_id) REFERENCES advertisements(id) ON DELETE CASCADE,
                INDEX idx_ap_ad (advertisement_id)
            )""",
            """CREATE TABLE IF NOT EXISTS ad_payments (
                id               INT AUTO_INCREMENT PRIMARY KEY,
                advertisement_id INT NOT NULL,
                company_id       INT NOT NULL,
                amount           FLOAT NULL,
                currency_code    VARCHAR(3) NOT NULL DEFAULT 'COP',
                receipt_url      VARCHAR(500) NULL,
                payment_date     DATE NULL,
                status           VARCHAR(20) NOT NULL DEFAULT 'pending',
                notes            TEXT NULL,
                verified_by      INT NULL,
                verified_at      TIMESTAMP NULL,
                created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (advertisement_id) REFERENCES advertisements(id) ON DELETE CASCADE,
                INDEX idx_apay_ad      (advertisement_id),
                INDEX idx_apay_company (company_id)
            )""",
        ]
        for sql in ad_tables:
            try:
                await db.execute(text(sql))
                await db.commit()
            except Exception:
                await db.rollback()

        # ── PAUTAS: migraciones de columnas nuevas ────────────────────
        ad_migrations = [
            "ALTER TABLE ad_pieces ADD COLUMN social_platform VARCHAR(20) NULL",
            "ALTER TABLE advertisements ADD COLUMN social_instagram VARCHAR(500) NULL",
            "ALTER TABLE advertisements ADD COLUMN social_tiktok VARCHAR(500) NULL",
            "ALTER TABLE advertisements ADD COLUMN social_facebook VARCHAR(500) NULL",
            "ALTER TABLE advertisements ADD COLUMN social_youtube_channel VARCHAR(500) NULL",
            "ALTER TABLE advertisements ADD COLUMN social_website VARCHAR(500) NULL",
        ]
        for sql in ad_migrations:
            try:
                await db.execute(text(sql))
                await db.commit()
            except Exception:
                await db.rollback()

        # ── SEED: precios de pautas en system_config ──────────────────
        for ad_key, ad_val, ad_desc in [
            ("ad_price_single_profile", "50000",  "Precio pauta dirigida a un perfil (COP)"),
            ("ad_price_all_profiles",   "80000",  "Precio pauta dirigida a todos los perfiles (COP)"),
        ]:
            r = await db.execute(select(SystemConfig).where(SystemConfig.config_key == ad_key))
            if not r.scalars().first():
                db.add(SystemConfig(config_key=ad_key, config_value=ad_val, description=ad_desc, config_type="integer"))
        await db.commit()

        # ── SEED: módulos de pautas en system_modules ──────────────────
        for route, name, icon, is_sysadmin in [
            ("/advertising/my-ads",   "Mis Pautas",         "bi-megaphone",       False),
            ("/sysadmin/advertising", "Gestión de Pautas",  "bi-megaphone-fill",  True),
        ]:
            result = await db.execute(select(SystemModule).where(SystemModule.route == route))
            if not result.scalars().first():
                db.add(SystemModule(
                    name=name, route=route, icon=icon,
                    parent_id=None, is_active=True, order_index=0,
                    is_sysadmin=is_sysadmin
                ))
        await db.commit()

        # ── PAUTAS: uploads dir ────────────────────────────────────────
        (UPLOADS_DIR / "ads").mkdir(parents=True, exist_ok=True)
        (UPLOADS_DIR / "ad_payments").mkdir(parents=True, exist_ok=True)

        # ── SEED: módulos Facturación (estructura padre/hijo) ────────────
        async def _get_or_create_module(name, route, icon, parent_id=None):
            r = await db.execute(select(SystemModule).where(SystemModule.route == route))
            m = r.scalars().first()
            if not m:
                m = SystemModule(
                    name=name, route=route, icon=icon,
                    parent_id=parent_id, is_active=True, order_index=0, is_sysadmin=False
                )
                db.add(m)
                await db.commit()
                await db.refresh(m)
            return m

        fact_root     = await _get_or_create_module("Facturación",   "/facturacion",                  "bi-receipt-cutoff")
        fact_ventas   = await _get_or_create_module("Ventas",        "/facturacion/ventas",            "bi-bag",                  fact_root.id)
        fact_reportes = await _get_or_create_module("Reportes",      "/facturacion/reportes",          "bi-bar-chart-line",       fact_root.id)
        await _get_or_create_module("Factura",  "/facturacion/ventas/factura",          "bi-file-earmark-text",    fact_ventas.id)
        await _get_or_create_module("Recibo",   "/facturacion/ventas/recibo",           "bi-receipt",              fact_ventas.id)
        await _get_or_create_module("Facturas", "/facturacion/reportes/facturas",       "bi-file-earmark-spreadsheet", fact_reportes.id)
        await _get_or_create_module("Recibos",  "/facturacion/reportes/recibos",        "bi-receipt-cutoff",       fact_reportes.id)
        await db.commit()

        # ── pos_printers: rediseño tipo conexión ──────────────────────────────────
        for _sql in [
            "ALTER TABLE pos_printers ADD COLUMN connection_type VARCHAR(20) NOT NULL DEFAULT 'network'",
            "ALTER TABLE pos_printers DROP COLUMN type",
            "ALTER TABLE pos_printers MODIFY COLUMN port INT NULL DEFAULT 9100",
            "ALTER TABLE pos_printers ADD COLUMN bluetooth_address VARCHAR(30) NULL",
            "ALTER TABLE pos_printers ADD COLUMN usb_device_id VARCHAR(200) NULL",
        ]:
            try:
                await db.execute(text(_sql))
                await db.commit()
            except Exception:
                await db.rollback()

        # ── asset_categories: agregar company_id (fix aislamiento multi-tenant) ─
        for _sql in [
            "ALTER TABLE asset_categories ADD COLUMN company_id INT NOT NULL DEFAULT 0",
            "ALTER TABLE asset_categories DROP INDEX name",
            "ALTER TABLE asset_categories ADD INDEX idx_ac_company (company_id)",
        ]:
            try:
                await db.execute(text(_sql))
                await db.commit()
            except Exception:
                await db.rollback()

        # ── POS CATÁLOGO: tablas del módulo restaurante ────────────────────────
        _pos_cat_tables = [
            """CREATE TABLE IF NOT EXISTS pos_item_categories (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                company_id  INT          NOT NULL,
                name        VARCHAR(100) NOT NULL,
                description VARCHAR(250) NULL,
                color       VARCHAR(10)  NOT NULL DEFAULT '#1d4ed8',
                icon        VARCHAR(50)  NOT NULL DEFAULT 'bi-tag',
                is_active   TINYINT      NOT NULL DEFAULT 1,
                created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_ic_company (company_id)
            )""",
            """CREATE TABLE IF NOT EXISTS pos_printers (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                company_id  INT          NOT NULL,
                name        VARCHAR(100) NOT NULL,
                ip          VARCHAR(50)  NULL,
                port        INT          NOT NULL DEFAULT 9100,
                type        VARCHAR(50)  NULL,
                is_active   TINYINT      NOT NULL DEFAULT 1,
                created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_printer_company (company_id)
            )""",
            """CREATE TABLE IF NOT EXISTS pos_cash_registers (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                company_id  INT          NOT NULL,
                name        VARCHAR(100) NOT NULL,
                type        ENUM('main','auxiliary') NOT NULL DEFAULT 'auxiliary',
                is_active   TINYINT      NOT NULL DEFAULT 1,
                created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_cr_company (company_id)
            )""",
            """CREATE TABLE IF NOT EXISTS pos_customer_price_list (
                id               BIGINT        AUTO_INCREMENT PRIMARY KEY,
                id_lista         INT           NOT NULL DEFAULT 0,
                id_cliente       INT           NOT NULL DEFAULT 0,
                id_producto      INT           NOT NULL,
                id_presentacion  INT           NULL DEFAULT NULL,
                precio_producto  DECIMAL(14,2) NOT NULL DEFAULT 0,
                fecha            DATE          NULL,
                activa           TINYINT       NOT NULL DEFAULT 1,
                company_id       INT           NOT NULL,
                created_at       DATETIME      DEFAULT CURRENT_TIMESTAMP,
                updated_at       DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uq_cpl_key (company_id, id_lista, id_cliente, id_producto, id_presentacion),
                INDEX idx_cpl_company  (company_id),
                INDEX idx_cpl_producto (company_id, id_producto),
                INDEX idx_cpl_lista    (company_id, id_lista)
            )""",
            """CREATE TABLE IF NOT EXISTS pos_item_printers (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                company_id  INT NOT NULL,
                item_id     INT NOT NULL,
                printer_id  INT NOT NULL,
                UNIQUE KEY uq_item_printer (company_id, item_id, printer_id),
                INDEX idx_ip_company (company_id, item_id)
            )""",
            """CREATE TABLE IF NOT EXISTS pos_item_modifiers (
                id            INT AUTO_INCREMENT PRIMARY KEY,
                company_id    INT          NOT NULL,
                item_id       INT          NOT NULL,
                name          VARCHAR(100) NOT NULL,
                is_required   TINYINT      NOT NULL DEFAULT 0,
                is_multiple   TINYINT      NOT NULL DEFAULT 0,
                min_selection INT          NOT NULL DEFAULT 0,
                max_selection INT          NOT NULL DEFAULT 1,
                sort_order    INT          NOT NULL DEFAULT 0,
                is_active     TINYINT      NOT NULL DEFAULT 1,
                INDEX idx_im_item (company_id, item_id)
            )""",
            """CREATE TABLE IF NOT EXISTS pos_item_modifier_options (
                id               INT AUTO_INCREMENT PRIMARY KEY,
                company_id       INT           NOT NULL,
                modifier_id      INT           NOT NULL,
                name             VARCHAR(100)  NOT NULL,
                extra_price      DECIMAL(14,2) NOT NULL DEFAULT 0,
                supply_item_id   INT           NULL,
                quantity         DECIMAL(14,4) NOT NULL DEFAULT 1,
                is_active        TINYINT       NOT NULL DEFAULT 1,
                sort_order       INT           NOT NULL DEFAULT 0,
                INDEX idx_imo_modifier (company_id, modifier_id)
            )""",
        ]
        for _sql in _pos_cat_tables:
            try:
                await db.execute(text(_sql))
                await db.commit()
            except Exception:
                await db.rollback()

        # ── POS: tablas zonas y mesas ─────────────────────────────────────────
        _pos_tables_sql = [
            """CREATE TABLE IF NOT EXISTS pos_zones (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                company_id  INT          NOT NULL,
                name        VARCHAR(100) NOT NULL,
                description VARCHAR(255) NULL,
                color       VARCHAR(10)  NOT NULL DEFAULT '#1d4ed8',
                icon        VARCHAR(50)  NOT NULL DEFAULT 'bi-grid',
                is_active   TINYINT      NOT NULL DEFAULT 1,
                order_index INT          NOT NULL DEFAULT 0,
                created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_pz_company (company_id)
            )""",
            """CREATE TABLE IF NOT EXISTS pos_tables (
                id               INT AUTO_INCREMENT PRIMARY KEY,
                company_id       INT         NOT NULL,
                zone_id          INT         NOT NULL,
                name             VARCHAR(50) NOT NULL,
                capacity         INT         NOT NULL DEFAULT 4,
                status           ENUM('free','occupied','bill_requested') NOT NULL DEFAULT 'free',
                current_order_id INT         NULL,
                is_active        TINYINT     NOT NULL DEFAULT 1,
                order_index      INT         NOT NULL DEFAULT 0,
                created_at       DATETIME    DEFAULT CURRENT_TIMESTAMP,
                updated_at       DATETIME    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_pt_company (company_id),
                INDEX idx_pt_zone    (company_id, zone_id)
            )""",
        ]
        for _sql in _pos_tables_sql:
            try:
                await db.execute(text(_sql))
                await db.commit()
            except Exception:
                await db.rollback()

        # ── POS CATÁLOGO: módulos en system_modules (grupo padre + hijos) ─────
        # ── Dashboard Restaurante ─────────────────────────────────────────────
        await _get_or_create_module("Restaurante", "/restaurante", "bi-shop-window")
        try:
            r = await db.execute(select(SystemModule).where(SystemModule.route == "/restaurante"))
            _dash = r.scalars().first()
            if _dash:
                _exists = await db.execute(text(
                    "SELECT 1 FROM business_profile_modules "
                    "WHERE business_profile_id=1 AND module_id=:mid LIMIT 1"
                ), {"mid": _dash.id})
                if not _exists.fetchone():
                    await db.execute(text(
                        "INSERT INTO business_profile_modules "
                        "(business_profile_id, module_id, parent_id, sort_order) "
                        "VALUES (1, :mid, NULL, 0)"
                    ), {"mid": _dash.id})
                    await db.commit()
        except Exception:
            await db.rollback()

        pos_parent = await _get_or_create_module(
            "Catálogo Restaurante", "/pos", "bi-grid-3x3"
        )
        _pos_modules = [
            ("Zonas",             "/pos/zonas",           "bi-grid-3x3-gap",    0),
            ("Mesas",             "/pos/mesas",           "bi-table",           1),
            ("Platos",            "/pos/platos",          "bi-egg-fried",       2),
            ("Categorías",        "/pos/categorias",      "bi-tags",            3),
            ("Impresoras",        "/pos/impresoras",      "bi-printer",         4),
            ("Listas de Precios", "/pos/listas-precios",  "bi-currency-dollar", 5),
            ("Cajas",             "/pos/cajas",           "bi-cash-stack",      6),
        ]
        for _name, _route, _icon, _order in _pos_modules:
            r = await db.execute(select(SystemModule).where(SystemModule.route == _route))
            if not r.scalars().first():
                _m = SystemModule(
                    name=_name, route=_route, icon=_icon,
                    parent_id=pos_parent.id, is_active=True,
                    order_index=_order, is_sysadmin=False
                )
                db.add(_m)
        await db.commit()

        # Asignar módulos POS catálogo al perfil Restaurante (business_profile_id=1)
        try:
            _pos_routes = ["/pos", "/pos/zonas", "/pos/mesas", "/pos/platos",
                           "/pos/categorias", "/pos/impresoras", "/pos/listas-precios", "/pos/cajas"]
            for _route in _pos_routes:
                r = await db.execute(select(SystemModule).where(SystemModule.route == _route))
                _mod = r.scalars().first()
                if _mod:
                    _exists = await db.execute(text(
                        "SELECT 1 FROM business_profile_modules "
                        "WHERE business_profile_id=1 AND module_id=:mid LIMIT 1"
                    ), {"mid": _mod.id})
                    if not _exists.fetchone():
                        await db.execute(text(
                            "INSERT INTO business_profile_modules "
                            "(business_profile_id, module_id, parent_id, sort_order) "
                            "VALUES (1, :mid, :pid, 0)"
                        ), {"mid": _mod.id, "pid": _mod.parent_id})
            await db.commit()
        except Exception:
            await db.rollback()


# ===============================
# RATE LIMITER (in-memory, single server)
# ===============================
_RATE_LIMITS: dict[str, tuple[int, int]] = {
    "/register/associate/": (5, 3600),
    "/payments/submit-receipt": (10, 3600),
    "/auth/login": (20, 900),
    "/auth/forgot-password": (5, 3600),
    "/qr/prestamo/": (15, 60),
    "/ads/": (30, 60),
}
_rate_store: dict[str, dict[str, collections.deque]] = collections.defaultdict(
    lambda: collections.defaultdict(collections.deque)
)


def _check_rate_limit(ip: str, path: str) -> bool:
    for route, (max_req, window) in _RATE_LIMITS.items():
        if path.startswith(route):
            now = time.time()
            dq = _rate_store[ip][route]
            while dq and dq[0] < now - window:
                dq.popleft()
            if len(dq) >= max_req:
                return False
            dq.append(now)
            return True
    return True


# ===============================
# APP
# ===============================
app = FastAPI(
    title="EasyPosWeb API",
    version="1.0"
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    ip = ip.split(",")[0].strip()
    if not _check_rate_limit(ip, request.url.path):
        return JSONResponse(
            status_code=429,
            content={"detail": "Demasiadas solicitudes. Intenta más tarde."}
        )
    return await call_next(request)


@app.on_event("startup")
async def startup():
    await init_db()
    await _init_db_data()


app.router.redirect_slashes = True

UPLOADS_DIR = BASE_DIR / "backend" / "app" / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
(UPLOADS_DIR / "landing").mkdir(parents=True, exist_ok=True)
(UPLOADS_DIR / "profiles").mkdir(parents=True, exist_ok=True)
(UPLOADS_DIR / "payments").mkdir(parents=True, exist_ok=True)
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
    help_router,
    asset_sector_router,
    company_asset_content_router,
    register_router,
    payment_router,
    task_collaborators_router,
    user_notification_router,
    unidades_medida_router,
    conceptos_gastos_router,
    conceptos_compras_router,
    task_purchases_router,
    external_collaborators_router,
    bodega_items_router,
    loans_router,
    qr_public_router,
    suppliers_router,
    supply_items_router,
    product_categories_router,
    products_router,
    price_lists_router,
    purchase_orders_router,
    asset_media_router,
    public_asset_router,
    asset_inquiries_router,
    pos_sync_router,
    pos_dashboard_router,
    pos_consultas_router,
    pos_categorias_router,
    pos_printers_router,
    pos_cajas_router,
    pos_lista_precios_router,
    pos_platos_router,
    pos_tables_router,
    plan_associate_limits_router,
    advertisement_router,
    welcome_steps_router,
]

for router in routers:
    app.include_router(router)

# STATIC FILES — registrado después de routers para que /assets/ API tenga prioridad
if ASSETS_DIR.exists() and os.getenv("SERVE_FRONTEND") == "true":
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

# ===============================
# SPA FRONTEND
# ===============================
_NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma":        "no-cache",
    "Expires":       "0",
}

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if full_path.startswith("api/"):
        return {"detail": "Not Found"}

    requested = FRONTEND_DIST / full_path

    if requested.exists() and requested.is_file():
        if requested.suffix in (".js", ".css") and requested.parent.name == "assets":
            return FileResponse(requested, headers={"Cache-Control": "public, max-age=31536000, immutable"})
        return FileResponse(requested, headers=_NO_CACHE_HEADERS)

    return FileResponse(FRONTEND_DIST / "index.html", headers=_NO_CACHE_HEADERS)
