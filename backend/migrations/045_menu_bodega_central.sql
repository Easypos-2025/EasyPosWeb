-- 045 — Menú "Bodega Central": padre con una pantalla (hijo) por opción
--
-- El módulo /bodega-central pasa a ser el PADRE y cada opción es un hijo con su ruta, para poder dar o quitar
-- permisos por opción a cada rol (un ayudante puede tener Productos y Movimientos sin Usuarios). El padre y sus
-- hijos solo se muestran en empresas con company_configs.has_bodega_central = 1 (filtro del menú lateral, como
-- POS electrónico, Parking y TV Cocina).
--   · Los hijos se agregan a cada perfil que ya tiene el padre (debajo de él).
--   · Cada rol que ya tiene el padre recibe los hijos con los mismos permisos (nadie pierde acceso).
-- Actualizar valores y Traslados se agregan cuando se construyan.

INSERT INTO system_modules (name, route, icon, parent_id, is_active, order_index, is_sysadmin)
SELECT h.nombre, h.ruta, h.icono, p.id, 1, h.orden, 0
FROM system_modules p
JOIN (SELECT 'Productos' AS nombre, '/bodega-central/productos' AS ruta, 'bi-box-seam' AS icono, 1 AS orden
      UNION ALL SELECT 'Importar de sedes', '/bodega-central/importar', 'bi-cloud-download', 2
      UNION ALL SELECT 'Enviar a sedes', '/bodega-central/enviar', 'bi-send', 3
      UNION ALL SELECT 'Usuarios del grupo', '/bodega-central/usuarios', 'bi-people', 6
      UNION ALL SELECT 'Movimientos', '/bodega-central/movimientos', 'bi-journal-text', 7) h
WHERE p.route = '/bodega-central'
  AND NOT EXISTS (SELECT 1 FROM system_modules x WHERE x.route = h.ruta);

INSERT INTO business_profile_modules (business_profile_id, module_id, parent_id, sort_order)
SELECT bp.business_profile_id, c.id, bp.id, c.order_index
FROM business_profile_modules bp
JOIN system_modules p ON p.id = bp.module_id AND p.route = '/bodega-central'
JOIN system_modules c ON c.parent_id = p.id
WHERE NOT EXISTS (SELECT 1 FROM business_profile_modules x
                  WHERE x.business_profile_id = bp.business_profile_id AND x.module_id = c.id);

INSERT INTO role_modules (role_id, module_id, can_view, can_view_all, can_create, can_edit, can_delete)
SELECT rm.role_id, c.id, rm.can_view, rm.can_view_all, rm.can_create, rm.can_edit, rm.can_delete
FROM role_modules rm
JOIN system_modules p ON p.id = rm.module_id AND p.route = '/bodega-central'
JOIN system_modules c ON c.parent_id = p.id
WHERE NOT EXISTS (SELECT 1 FROM role_modules x WHERE x.role_id = rm.role_id AND x.module_id = c.id);
