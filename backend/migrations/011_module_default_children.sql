-- ==========================================================
-- MIGRACIÓN 011: Módulos-Padre con Hijos por Defecto
-- ==========================================================
-- Permite definir qué hijos se asignan automáticamente cuando
-- un módulo padre se agrega a un perfil de negocio.
-- La propagación es NO DESTRUCTIVA: solo agrega, nunca elimina.
-- ==========================================================

ALTER TABLE system_modules
  ADD COLUMN is_default_child TINYINT(1) NOT NULL DEFAULT 0
  COMMENT 'Si 1, este hijo se asigna automaticamente cuando su padre se agrega a un perfil';

-- Vista SYSADMIN: Gestión de Defaults de Módulos
INSERT INTO system_modules (name, route, icon, parent_id, is_active, order_index, is_sysadmin)
VALUES ('Defaults Módulos', '/sysadmin/module-defaults', 'bi-diagram-3-fill', NULL, 1, 0, 1);
