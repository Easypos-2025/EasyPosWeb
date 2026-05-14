-- ============================================================
-- MIGRACIÓN: landing_contacts + fix system_modules duplicados
-- ============================================================

-- 1. landing_contacts: agregar company_id, asset_id, list_code
ALTER TABLE landing_contacts
  ADD COLUMN company_id INT NULL AFTER id,
  ADD COLUMN asset_id   INT NULL AFTER company_id,
  ADD COLUMN list_code  INT NULL AFTER asset_id;

-- 2. Limpiar TODOS los duplicados de system_modules por ruta
--    Conserva solo el registro más antiguo (menor id) por cada ruta
DELETE sm FROM system_modules sm
INNER JOIN (
    SELECT route, MIN(id) AS min_id
    FROM system_modules
    GROUP BY route
    HAVING COUNT(*) > 1
) dups ON sm.route = dups.route AND sm.id != dups.min_id;

-- 3. Agregar constraint UNIQUE en route para evitar futuros duplicados
ALTER TABLE system_modules ADD UNIQUE INDEX uq_system_modules_route (route);
