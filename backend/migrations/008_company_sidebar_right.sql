-- ============================================================
-- 008_company_sidebar_right.sql
-- Agrega control de visibilidad del panel lateral derecho
-- (publicidad) por empresa.
-- DEFAULT 1 = visible (sin impacto en empresas existentes).
-- ============================================================

ALTER TABLE companies
    ADD COLUMN show_sidebar_right TINYINT(1) NOT NULL DEFAULT 1 AFTER ext_db_password;
