-- ═══════════════════════════════════════════════════════════════════════════
-- MIGRACIÓN: Sistema de Downgrade Automático por Plan
-- Fecha: 2026-05-14
-- ═══════════════════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────────────────
-- 1. NUEVOS LÍMITES EN plans (waiters + diarios de recibos y tareas)
-- ─────────────────────────────────────────────────────────────────────────
ALTER TABLE plans
    ADD COLUMN IF NOT EXISTS max_waiters         INT NOT NULL DEFAULT -1 COMMENT '-1 = ilimitado',
    ADD COLUMN IF NOT EXISTS max_daily_receipts  INT NOT NULL DEFAULT -1 COMMENT '-1 = ilimitado',
    ADD COLUMN IF NOT EXISTS max_daily_tasks     INT NOT NULL DEFAULT -1 COMMENT '-1 = ilimitado';

-- ─────────────────────────────────────────────────────────────────────────
-- 2. MISMOS CAMPOS EN company_plan_limits (snapshot por asociado)
-- ─────────────────────────────────────────────────────────────────────────
ALTER TABLE company_plan_limits
    ADD COLUMN IF NOT EXISTS max_waiters         INT NOT NULL DEFAULT -1,
    ADD COLUMN IF NOT EXISTS max_daily_receipts  INT NOT NULL DEFAULT -1,
    ADD COLUMN IF NOT EXISTS max_daily_tasks     INT NOT NULL DEFAULT -1;

-- ─────────────────────────────────────────────────────────────────────────
-- 3. plan_blocked EN TABLAS ORM (bloqueo por exceder límite de plan)
-- ─────────────────────────────────────────────────────────────────────────
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS plan_blocked    TINYINT  NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS plan_blocked_at DATETIME NULL;

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS plan_blocked    TINYINT  NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS plan_blocked_at DATETIME NULL;

ALTER TABLE product_categories
    ADD COLUMN IF NOT EXISTS plan_blocked    TINYINT  NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS plan_blocked_at DATETIME NULL;

ALTER TABLE workers
    ADD COLUMN IF NOT EXISTS plan_blocked    TINYINT  NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS plan_blocked_at DATETIME NULL;

ALTER TABLE clients
    ADD COLUMN IF NOT EXISTS plan_blocked    TINYINT  NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS plan_blocked_at DATETIME NULL;

ALTER TABLE bodega_items
    ADD COLUMN IF NOT EXISTS plan_blocked    TINYINT  NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS plan_blocked_at DATETIME NULL;

ALTER TABLE assets
    ADD COLUMN IF NOT EXISTS plan_blocked    TINYINT  NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS plan_blocked_at DATETIME NULL;

-- ─────────────────────────────────────────────────────────────────────────
-- 4. plan_blocked EN pos_waiters (tabla raw SQL del POS)
-- ─────────────────────────────────────────────────────────────────────────
ALTER TABLE pos_waiters
    ADD COLUMN IF NOT EXISTS plan_blocked    TINYINT  NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS plan_blocked_at DATETIME NULL;

-- ─────────────────────────────────────────────────────────────────────────
-- 5. ÍNDICES para queries de filtrado rápido
-- ─────────────────────────────────────────────────────────────────────────
ALTER TABLE users            ADD INDEX IF NOT EXISTS idx_users_plan_blocked    (company_id, plan_blocked);
ALTER TABLE products         ADD INDEX IF NOT EXISTS idx_products_plan_blocked (company_id, plan_blocked);
ALTER TABLE product_categories ADD INDEX IF NOT EXISTS idx_cats_plan_blocked   (company_id, plan_blocked);
ALTER TABLE workers          ADD INDEX IF NOT EXISTS idx_workers_plan_blocked  (company_id, plan_blocked);
ALTER TABLE clients          ADD INDEX IF NOT EXISTS idx_clients_plan_blocked  (company_id, plan_blocked);
ALTER TABLE bodega_items     ADD INDEX IF NOT EXISTS idx_bodega_plan_blocked   (company_id, plan_blocked);
ALTER TABLE assets           ADD INDEX IF NOT EXISTS idx_assets_plan_blocked   (company_id, plan_blocked);
ALTER TABLE pos_waiters      ADD INDEX IF NOT EXISTS idx_waiters_plan_blocked  (company_id, plan_blocked);
