-- 046 — Menú "Bodega Central": opción "Actualizar valores" (precio de venta, mínimo, costo, IVA, stock mínimo y
-- listas de precios por cliente, enviados de la bodega a las sedes). Igual que 045: se agrega a los perfiles que
-- tienen el padre y a los roles que lo tienen, con sus mismos permisos.

INSERT INTO system_modules (name, route, icon, parent_id, is_active, order_index, is_sysadmin)
SELECT 'Actualizar valores', '/bodega-central/valores', 'bi-currency-exchange', p.id, 1, 4, 0
FROM system_modules p
WHERE p.route = '/bodega-central'
  AND NOT EXISTS (SELECT 1 FROM system_modules x WHERE x.route = '/bodega-central/valores');

INSERT INTO business_profile_modules (business_profile_id, module_id, parent_id, sort_order)
SELECT bp.business_profile_id, c.id, bp.id, c.order_index
FROM business_profile_modules bp
JOIN system_modules p ON p.id = bp.module_id AND p.route = '/bodega-central'
JOIN system_modules c ON c.parent_id = p.id AND c.route = '/bodega-central/valores'
WHERE NOT EXISTS (SELECT 1 FROM business_profile_modules x
                  WHERE x.business_profile_id = bp.business_profile_id AND x.module_id = c.id);

INSERT INTO role_modules (role_id, module_id, can_view, can_view_all, can_create, can_edit, can_delete)
SELECT rm.role_id, c.id, rm.can_view, rm.can_view_all, rm.can_create, rm.can_edit, rm.can_delete
FROM role_modules rm
JOIN system_modules p ON p.id = rm.module_id AND p.route = '/bodega-central'
JOIN system_modules c ON c.parent_id = p.id AND c.route = '/bodega-central/valores'
WHERE NOT EXISTS (SELECT 1 FROM role_modules x WHERE x.role_id = rm.role_id AND x.module_id = c.id);
