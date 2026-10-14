-- 051 — Corrige la 049: "Factura de Proveedor" quedó con parent_id = id del MÓDULO "Transaccional" en lugar del
-- id de la FILA de "Transaccional" del mismo perfil (business_profile_modules.parent_id apunta a filas del perfil).
UPDATE business_profile_modules b
JOIN system_modules m ON m.id = b.module_id AND m.route = '/compras/factura-proveedor'
JOIN system_modules tm ON tm.name = 'Transaccional' AND tm.route IS NULL
JOIN business_profile_modules t ON t.business_profile_id = b.business_profile_id AND t.module_id = tm.id
SET b.parent_id = t.id
WHERE NOT (b.parent_id <=> t.id);
