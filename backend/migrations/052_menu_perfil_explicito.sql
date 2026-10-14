-- 052 — El menú de cada perfil queda EXPLÍCITO (lo que se ve en "Menú del Cliente" es exactamente lo que ve el cliente).
--   Antes, una opción sin padre en el perfil (parent_id NULL) se metía sola bajo su padre del catálogo si ese padre
--   estaba en el perfil: escoger "Raíz" no la dejaba en la raíz. Desde ahora "Raíz" es raíz.
--   Para que ningún cliente vea un cambio, ese padre implícito se guarda en la fila (mismo lugar donde ya se veía).
UPDATE business_profile_modules b
JOIN system_modules sm ON sm.id = b.module_id
JOIN business_profile_modules p ON p.business_profile_id = b.business_profile_id AND p.module_id = sm.parent_id
SET b.parent_id = p.id
WHERE b.parent_id IS NULL AND p.id <> b.id;

-- La pantalla "Gestion Orden Sidebar" pasa a ser la vista previa del menú del cliente por perfil
UPDATE system_modules SET name = 'Menú del Cliente (Vista previa)' WHERE route = '/companies/sysadmin';
