-- ================================================================
-- MIGRACIÓN: roles.name — unique global → unique por empresa
-- Ejecutar UNA sola vez en la BD MySQL
-- ================================================================

-- 1. Eliminar el índice único global sobre 'name'
ALTER TABLE roles DROP INDEX name;

-- 2. Crear índice único compuesto (name + company_id)
ALTER TABLE roles ADD UNIQUE KEY uq_role_name_company (name, company_id);
