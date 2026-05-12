-- ============================================================
-- MIGRACIÓN: Ajustes finales perfil Administrador de Tareas
-- Ejecutar en orden sobre la BD de producción
-- ============================================================

-- 1. loans: agregar task_leader_id, qr_signed_by; hacer external_collaborator_id nullable
ALTER TABLE loans
  ADD COLUMN task_leader_id INT NULL AFTER external_collaborator_id,
  ADD COLUMN qr_signed_by VARCHAR(20) NULL AFTER qr_token;

ALTER TABLE loans
  MODIFY COLUMN external_collaborator_id INT NULL;

ALTER TABLE loans
  ADD CONSTRAINT fk_loans_task_leader FOREIGN KEY (task_leader_id) REFERENCES users(id) ON DELETE SET NULL;

-- 2. asset_inquiries: agregar campo notified para control topbar
ALTER TABLE asset_inquiries
  ADD COLUMN notified TINYINT(1) NOT NULL DEFAULT 0 AFTER confirmed_at;

-- 3. system_modules: registrar vista de solicitudes de activos
INSERT IGNORE INTO system_modules (name, route, icon, parent_id, is_active, order_index, is_sysadmin)
VALUES ('Solicitudes de Activos', '/assets/inquiries', 'bi-envelope-check', NULL, 1, 0, 0);

-- 4. system_config: versión de la aplicación (cambiar el valor en cada deploy)
INSERT IGNORE INTO system_config (config_key, config_value, description, config_type, is_active)
VALUES ('app_version', '1.1.0', 'Versión actual del frontend. Cambiar en cada deploy para notificar a usuarios activos.', 'string', 1);
