-- 048 — Pantalla "Productos" para comercio (/productos): guarda en pos_dishes, la tabla que vende el POS y usa
-- el escritorio. Reemplaza en los perfiles de comercio la opción "Productos" de /inventory/products, que es del
-- catálogo de vehículos (otra tabla, no se vende en el POS) y se queda solo en Servi-Cars.
--   Perfiles: 3 Droguerías, 7 Fruver, 8 Estancos, 11 Almacén Lujos Autos y Motos, 13 Mini-Market,
--             14 Almacén, 20 Ferreterías.
--   · Queda en el mismo lugar del menú (mismo padre y orden) que tenía la opción anterior en cada perfil.
--   · Los roles que tenían la opción anterior reciben la nueva con los mismos permisos.

INSERT INTO system_modules (name, route, icon, parent_id, is_active, order_index, is_sysadmin)
SELECT 'Productos', '/productos', 'bi-box-seam', NULL, 1, 0, 0
WHERE NOT EXISTS (SELECT 1 FROM system_modules WHERE route = '/productos');

INSERT INTO business_profile_modules (business_profile_id, module_id, parent_id, sort_order, display_name)
SELECT b.business_profile_id, n.id, b.parent_id, b.sort_order, NULL
FROM business_profile_modules b
JOIN system_modules v ON v.id = b.module_id AND v.route = '/inventory/products' AND v.name = 'Productos'
JOIN system_modules n ON n.route = '/productos'
WHERE b.business_profile_id IN (3, 7, 8, 11, 13, 14, 20)
  AND NOT EXISTS (SELECT 1 FROM business_profile_modules x
                  WHERE x.business_profile_id = b.business_profile_id AND x.module_id = n.id);

-- Perfiles de comercio que no tenían la opción anterior: la nueva va en la raíz del menú
INSERT INTO business_profile_modules (business_profile_id, module_id, parent_id, sort_order, display_name)
SELECT bp.id, n.id, NULL, 0, NULL
FROM business_profiles bp
JOIN system_modules n ON n.route = '/productos'
WHERE bp.id IN (3, 7, 8, 11, 13, 14, 20)
  AND NOT EXISTS (SELECT 1 FROM business_profile_modules x WHERE x.business_profile_id = bp.id AND x.module_id = n.id);

INSERT INTO role_modules (role_id, module_id, can_view, can_view_all, can_create, can_edit, can_delete)
SELECT rm.role_id, n.id, rm.can_view, rm.can_view_all, rm.can_create, rm.can_edit, rm.can_delete
FROM role_modules rm
JOIN system_modules v ON v.id = rm.module_id AND v.route = '/inventory/products' AND v.name = 'Productos'
JOIN system_modules n ON n.route = '/productos'
WHERE NOT EXISTS (SELECT 1 FROM role_modules x WHERE x.role_id = rm.role_id AND x.module_id = n.id);

-- La opción anterior sale de esos perfiles (sigue en Servi-Cars y en los demás que la usen)
DELETE b FROM business_profile_modules b
JOIN system_modules v ON v.id = b.module_id AND v.route = '/inventory/products' AND v.name = 'Productos'
WHERE b.business_profile_id IN (3, 7, 8, 11, 13, 14, 20);
