-- ============================================================
-- FIX: Completar renombrado de tablas + agregar company_id
-- Estado actual: purchase_concepts y expense_concepts YA existen
-- Faltan: supplies, measurement_units, task_collaborators
-- ============================================================

-- Desactivar FK checks para poder renombrar sin conflictos
SET FOREIGN_KEY_CHECKS = 0;

-- 1. Eliminar tablas vacías creadas por create_all (si existen)
DROP TABLE IF EXISTS supplies;
DROP TABLE IF EXISTS measurement_units;
DROP TABLE IF EXISTS task_collaborators;

-- 2. Eliminar tablas viejas vacías (los datos ya están en purchase_concepts/expense_concepts)
DROP TABLE IF EXISTS conceptos_compras;
DROP TABLE IF EXISTS conceptos_gastos;

-- 3. Renombrar las 3 que faltaron
RENAME TABLE insumos           TO supplies;
RENAME TABLE unidades_medida   TO measurement_units;
RENAME TABLE colaborador_tarea TO task_collaborators;

-- 4. Reactivar FK checks
SET FOREIGN_KEY_CHECKS = 1;

-- 5. Agregar company_id a workers (nullable para datos existentes)
ALTER TABLE workers
  ADD COLUMN company_id INT NULL AFTER id;

-- 6. Agregar company_id a assets (si no se hizo en la migración anterior)
ALTER TABLE assets
  ADD COLUMN IF NOT EXISTS company_id INT NULL AFTER id;

-- 7. Agregar campos nuevos a assets (si no existen)
ALTER TABLE assets
  ADD COLUMN IF NOT EXISTS rental_requirements  TEXT NULL AFTER additional_reference,
  ADD COLUMN IF NOT EXISTS general_observations TEXT NULL AFTER rental_requirements;

-- ============================================================
-- VERIFICACIÓN: ejecuta esto al final para confirmar
-- ============================================================
-- SHOW TABLES LIKE 'supplies';
-- SHOW TABLES LIKE 'measurement_units';
-- SHOW TABLES LIKE 'task_collaborators';
-- SHOW COLUMNS FROM workers LIKE 'company_id';
