-- 022 — Vista "Categorías de Productos" (CRUD de categoria_productos / pos_product_categories)
-- parent_id NULL: se ubica en el menú desde SidebarMenuManager. Idempotente.
INSERT INTO system_modules (name, route, icon, parent_id, is_active, order_index, is_sysadmin)
SELECT 'Categorías de Productos', '/pos/categorias-productos', 'bi-diagram-3', NULL, 1, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_modules WHERE route = '/pos/categorias-productos');
