-- ============================================================
-- MIGRACIÓN: Sistema de límites de plan por asociado
-- Ejecutar en orden sobre la BD de producción
-- ============================================================

-- 1. Nuevas columnas en tabla plans
ALTER TABLE plans
  ADD COLUMN max_workers        INT NOT NULL DEFAULT -1 AFTER max_categories,
  ADD COLUMN max_clients        INT NOT NULL DEFAULT -1 AFTER max_workers,
  ADD COLUMN max_bodega_items   INT NOT NULL DEFAULT -1 AFTER max_clients,
  ADD COLUMN max_tasks          INT NOT NULL DEFAULT -1 AFTER max_bodega_items,
  ADD COLUMN max_daily_invoices INT NOT NULL DEFAULT -1 AFTER max_tasks,
  ADD COLUMN max_assets         INT NOT NULL DEFAULT -1 AFTER max_daily_invoices;

-- 2. Ajustar valores de planes existentes (personaliza según tus planes reales)
-- Plan Free (id=1)
UPDATE plans SET
  max_workers=2, max_clients=20, max_bodega_items=5,
  max_tasks=5, max_daily_invoices=10, max_assets=1
WHERE name LIKE '%ree%' OR price = 0;

-- Plan Básico (busca por nombre)
UPDATE plans SET
  max_workers=5, max_clients=100, max_bodega_items=20,
  max_tasks=20, max_daily_invoices=50, max_assets=3
WHERE name LIKE '%sic%' OR name LIKE '%Basic%';

-- Plan Estándar
UPDATE plans SET
  max_workers=10, max_clients=300, max_bodega_items=50,
  max_tasks=60, max_daily_invoices=150, max_assets=10
WHERE name LIKE '%st%ndar%' OR name LIKE '%Standard%';

-- Plan Premium (ilimitado)
UPDATE plans SET
  max_workers=-1, max_clients=-1, max_bodega_items=-1,
  max_tasks=-1, max_daily_invoices=-1, max_assets=-1
WHERE name LIKE '%remium%' OR price = (SELECT MAX(price) FROM plans p2);

-- 3. Crear tabla company_plan_limits
CREATE TABLE IF NOT EXISTS company_plan_limits (
  id                 INT AUTO_INCREMENT PRIMARY KEY,
  company_id         INT NOT NULL UNIQUE,
  plan_id            INT NOT NULL,
  max_users          INT NOT NULL DEFAULT 1,
  max_products       INT NOT NULL DEFAULT -1,
  max_categories     INT NOT NULL DEFAULT -1,
  max_workers        INT NOT NULL DEFAULT -1,
  max_clients        INT NOT NULL DEFAULT -1,
  max_bodega_items   INT NOT NULL DEFAULT -1,
  max_tasks          INT NOT NULL DEFAULT -1,
  max_daily_invoices INT NOT NULL DEFAULT -1,
  max_assets         INT NOT NULL DEFAULT -1,
  is_custom          TINYINT(1) NOT NULL DEFAULT 0,
  notes              VARCHAR(500) NULL,
  created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_cpl_company FOREIGN KEY (company_id) REFERENCES companies(id_company) ON DELETE CASCADE,
  CONSTRAINT fk_cpl_plan    FOREIGN KEY (plan_id)    REFERENCES plans(id)
);

-- 4. Generar snapshots para todos los asociados que ya tienen plan activo
-- (los nuevos se generarán automáticamente al aprobar pagos)
INSERT IGNORE INTO company_plan_limits
  (company_id, plan_id, max_users, max_products, max_categories,
   max_workers, max_clients, max_bodega_items, max_tasks, max_daily_invoices, max_assets,
   is_custom)
SELECT
  cp.company_id,
  cp.plan_id,
  p.max_users, p.max_products, p.max_categories,
  p.max_workers, p.max_clients, p.max_bodega_items,
  p.max_tasks, p.max_daily_invoices, p.max_assets,
  0
FROM company_plans cp
JOIN plans p ON p.id = cp.plan_id
WHERE cp.is_active = 1;

-- 5. system_modules: vista plan_asociado (solo SYSADMIN)
INSERT IGNORE INTO system_modules (name, route, icon, parent_id, is_active, order_index, is_sysadmin)
VALUES ('Límites por Asociado', '/sysadmin/plan-asociado', 'bi-sliders', NULL, 1, 0, 1);
