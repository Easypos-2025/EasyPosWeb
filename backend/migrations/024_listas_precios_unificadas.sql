-- 024 — Una sola vista "Listas de Precios" (módulo 214, /pos/listas-precios-cliente,
--       tablas lista_precios_cliente del escritorio). Se eliminan:
--         · módulo 80  /inventory/price-lists  (tablas genéricas price_lists / price_list_items)
--         · módulo 119 /pos/listas-precios     (editor de la antigua lista general Id_Lista = 0)
--       En los menús de cada perfil, la posición que tenían pasa a la vista nueva.

-- Los módulos se ubican por ruta (los ids pueden variar entre bases)
SET @nuevo = (SELECT id FROM system_modules WHERE route = '/pos/listas-precios-cliente' LIMIT 1);
SET @gen   = (SELECT id FROM system_modules WHERE route = '/inventory/price-lists' LIMIT 1);
SET @gral  = (SELECT id FROM system_modules WHERE route = '/pos/listas-precios' LIMIT 1);

-- ── 1. Menús por perfil ─────────────────────────────────────────────────────
-- Si el perfil ya tiene la 214, se quitan las viejas
DELETE b FROM business_profile_modules b
WHERE b.module_id IN (@gen, @gral)
  AND EXISTS (SELECT 1 FROM (SELECT business_profile_id FROM business_profile_modules WHERE module_id = @nuevo) x
              WHERE x.business_profile_id = b.business_profile_id);
-- Si tiene las dos viejas, se conserva la posición de la 119 (Catálogo) y se quita la 80
DELETE b FROM business_profile_modules b
WHERE b.module_id = @gen
  AND EXISTS (SELECT 1 FROM (SELECT business_profile_id FROM business_profile_modules WHERE module_id = @gral) x
              WHERE x.business_profile_id = b.business_profile_id);
-- La que queda pasa a ser la vista nueva, en la misma posición
UPDATE business_profile_modules SET module_id = @nuevo WHERE module_id IN (@gen, @gral);

-- ── 2. Permisos por rol: quien veía una vista vieja ve la nueva ─────────────
INSERT INTO role_modules (role_id, module_id, can_view, can_create, can_edit, can_delete, can_view_all)
SELECT rm.role_id, @nuevo, MAX(rm.can_view), MAX(rm.can_create), MAX(rm.can_edit), MAX(rm.can_delete), MAX(rm.can_view_all)
FROM role_modules rm
WHERE rm.module_id IN (@gen, @gral)
  AND NOT EXISTS (SELECT 1 FROM (SELECT role_id FROM role_modules WHERE module_id = @nuevo) x WHERE x.role_id = rm.role_id)
GROUP BY rm.role_id;
DELETE FROM role_modules WHERE module_id IN (@gen, @gral);

-- ── 3. Módulos ──────────────────────────────────────────────────────────────
UPDATE system_modules SET name = 'Listas de Precios', icon = 'bi-currency-dollar' WHERE id = @nuevo;
UPDATE system_modules SET parent_id = NULL WHERE parent_id IN (@gen, @gral);
DELETE FROM system_modules WHERE id IN (@gen, @gral);

-- ── 4. Tablas genéricas de listas (sin uso) ─────────────────────────────────
ALTER TABLE clients DROP COLUMN IF EXISTS price_list_id;
DROP TABLE IF EXISTS price_list_items;
DROP TABLE IF EXISTS price_lists;
