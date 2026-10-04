-- 030 — Servi-Cars alineado con Cuadre de Caja e Id_Caja (como Restaurante)
--
-- · Liquidación de Operarios = Otro Egreso (concepto "Pagos", subconcepto "Pago Operarios") en el
--   Id_Caja abierto; worker_liquidaciones guarda el Id_Caja y el Otro Egreso. Se anula, no se borra.
-- · Menú Transaccional (Cuadre, Gastos, Compras, Otros Ingresos/Egresos, Vales, Abono Vales) en el perfil
--   Servi-Cars (15).
-- · El viejo "Cierre de Caja" (/talleres/caja) y su tabla caja_egresos (vacía) se eliminan.

ALTER TABLE worker_liquidaciones
  ADD COLUMN IF NOT EXISTS register_id      BIGINT       NULL,
  ADD COLUMN IF NOT EXISTS other_expense_id BIGINT       NULL,
  ADD COLUMN IF NOT EXISTS voided           TINYINT      NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS void_reason      VARCHAR(255) NULL,
  ADD COLUMN IF NOT EXISTS voided_by        INT          NULL,
  ADD COLUMN IF NOT EXISTS voided_at        DATETIME     NULL;
CREATE INDEX IF NOT EXISTS ix_wl_oexp ON worker_liquidaciones (company_id, other_expense_id);

-- ── Menú Transaccional en Servi-Cars (perfil 15) ──
SET @padre = (SELECT parent_id FROM system_modules WHERE route = '/caja/cuadre' LIMIT 1);
INSERT INTO business_profile_modules (business_profile_id, module_id, parent_id, sort_order)
SELECT 15, @padre, NULL, 3 FROM DUAL
WHERE @padre IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM business_profile_modules WHERE business_profile_id = 15 AND module_id = @padre);
SET @bpm_padre = (SELECT id FROM business_profile_modules WHERE business_profile_id = 15 AND module_id = @padre LIMIT 1);
INSERT INTO business_profile_modules (business_profile_id, module_id, parent_id, sort_order)
SELECT 15, s.id, @bpm_padre, s.order_index
FROM system_modules s
WHERE s.parent_id = @padre AND @bpm_padre IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM business_profile_modules b WHERE b.business_profile_id = 15 AND b.module_id = s.id);

-- Permiso de ver para los roles de las empresas Servi-Cars
INSERT INTO role_modules (role_id, module_id, can_view, can_create, can_edit, can_delete)
SELECT DISTINCT r.id, s.id, 1, 1, 1, 0
FROM roles r
JOIN companies c ON c.id_company = r.company_id AND c.business_profile_id = 15
JOIN system_modules s ON s.id = @padre OR s.parent_id = @padre
WHERE NOT EXISTS (SELECT 1 FROM role_modules rm WHERE rm.role_id = r.id AND rm.module_id = s.id);

-- Conceptos de Caja (Configuración) para los Admin de Servi-Cars
INSERT INTO business_profile_modules (business_profile_id, module_id, parent_id, sort_order)
SELECT 15, s.id, (SELECT b.parent_id FROM business_profile_modules b JOIN system_modules m ON m.id = b.module_id
                  WHERE b.business_profile_id = 15 AND m.route = '/payment-types' LIMIT 1), 12
FROM system_modules s
WHERE s.route = '/configuration/conceptos-caja'
  AND NOT EXISTS (SELECT 1 FROM business_profile_modules b WHERE b.business_profile_id = 15 AND b.module_id = s.id);
INSERT INTO role_modules (role_id, module_id, can_view, can_create, can_edit, can_delete)
SELECT DISTINCT r.id, s.id, 1, 1, 1, 0
FROM roles r
JOIN companies c ON c.id_company = r.company_id AND c.business_profile_id = 15
JOIN system_modules s ON s.route = '/configuration/conceptos-caja'
WHERE UPPER(r.name) LIKE '%ADMIN%'
  AND NOT EXISTS (SELECT 1 FROM role_modules rm WHERE rm.role_id = r.id AND rm.module_id = s.id);

-- ── Eliminar el viejo Cierre de Caja (/talleres/caja) ──
SET @viejo = (SELECT id FROM system_modules WHERE route = '/talleres/caja' LIMIT 1);
DELETE FROM role_modules WHERE module_id = @viejo;
DELETE FROM business_profile_modules WHERE module_id = @viejo;
DELETE FROM topbar_menu_items WHERE route = '/talleres/caja';
UPDATE system_modules SET parent_id = NULL WHERE parent_id = @viejo;
DELETE FROM system_modules WHERE id = @viejo;
DROP TABLE IF EXISTS caja_egresos;
