-- 050 — Limpieza del menú (decisión del usuario 2026-10-13).
--   NO se toca: nada de SYSADMIN (perfil 4 ni módulos de sistema), Hipotecas / Cobros, Parqueadero ni Parking.
--
--   1. "Productos" (/inventory/products), "Entradas Mercancía", "Categorías Prod." y "Bodega" (/configuration/bodega)
--      son del catálogo de vehículos: salen de todos los perfiles menos Servi-Cars (15) y SYSADMIN (4). La opción
--      "Productos Parking" (misma ruta, otro módulo) no se toca.
--   2. Se borran (módulo, permisos y asignaciones) las opciones que ningún perfil usa:
--      "Configuracion Res." (/configurationRES), "Historial de Pagos" del asociado (/payment-history) y
--      "Reportes" de Facturación con sus hijos "Facturas" y "Recibos" (pantallas vacías "Módulo en desarrollo").
--   3. "Venta x Producto" y "Venta x Insumo" (pestañas de Consulta de Ventas) quedan en el menú junto a
--      "Consulta de Ventas", con el mismo padre, en cada perfil que la tiene; los roles con Consulta de Ventas
--      reciben los mismos permisos.

-- 1. Catálogo de vehículos fuera de los perfiles que no son Servi-Cars
DELETE b FROM business_profile_modules b
JOIN system_modules m ON m.id = b.module_id
WHERE b.business_profile_id NOT IN (4, 15)
  AND ((m.route = '/inventory/products' AND m.name = 'Productos')
       OR m.route IN ('/inventory/purchase-orders', '/inventory/categories', '/configuration/bodega'));

-- 2. Opciones sin uso (los hijos primero por la llave del padre)
DELETE rm FROM role_modules rm JOIN system_modules m ON m.id = rm.module_id
WHERE m.route IN ('/configurationRES', '/payment-history', '/facturacion/reportes',
                  '/facturacion/reportes/facturas', '/facturacion/reportes/recibos');
DELETE b FROM business_profile_modules b JOIN system_modules m ON m.id = b.module_id
WHERE m.route IN ('/configurationRES', '/payment-history', '/facturacion/reportes',
                  '/facturacion/reportes/facturas', '/facturacion/reportes/recibos');
UPDATE system_modules SET parent_id = NULL WHERE route = '/configurationRES';
DELETE FROM system_modules WHERE route IN ('/facturacion/reportes/facturas', '/facturacion/reportes/recibos');
DELETE FROM system_modules WHERE route IN ('/configurationRES', '/payment-history', '/facturacion/reportes');

-- 3. Venta x Producto y Venta x Insumo junto a Consulta de Ventas (Parqueadero, perfil 24, no se toca)
INSERT INTO business_profile_modules (business_profile_id, module_id, parent_id, sort_order, display_name)
SELECT b.business_profile_id, n.id, b.parent_id,
       b.sort_order + IF(n.route = '/pos/consultas/ventas-producto', 1, 2), NULL
FROM business_profile_modules b
JOIN system_modules c ON c.id = b.module_id AND c.route = '/pos/consultas/ventas'
JOIN system_modules n ON n.route IN ('/pos/consultas/ventas-producto', '/pos/consultas/ventas-insumo')
WHERE b.business_profile_id NOT IN (4, 24)
  AND NOT EXISTS (SELECT 1 FROM business_profile_modules x
                  WHERE x.business_profile_id = b.business_profile_id AND x.module_id = n.id);

INSERT INTO role_modules (role_id, module_id, can_view, can_view_all, can_create, can_edit, can_delete)
SELECT rm.role_id, n.id, rm.can_view, rm.can_view_all, rm.can_create, rm.can_edit, rm.can_delete
FROM role_modules rm
JOIN system_modules c ON c.id = rm.module_id AND c.route = '/pos/consultas/ventas'
JOIN system_modules n ON n.route IN ('/pos/consultas/ventas-producto', '/pos/consultas/ventas-insumo')
WHERE NOT EXISTS (SELECT 1 FROM role_modules x WHERE x.role_id = rm.role_id AND x.module_id = n.id);
