-- ============================================================
-- 007_company_ext_db.sql
-- Agrega configuración de base de datos externa por empresa.
-- Permite que cada empresa apunte a una DB diferente (mismo
-- servidor u otro) sin afectar las empresas actuales (NULL = default).
-- ============================================================

ALTER TABLE companies
    ADD COLUMN ext_db_host     VARCHAR(150) NULL     AFTER updated_at,
    ADD COLUMN ext_db_port     SMALLINT     NOT NULL DEFAULT 3306 AFTER ext_db_host,
    ADD COLUMN ext_db_name     VARCHAR(100) NULL     AFTER ext_db_port,
    ADD COLUMN ext_db_user     VARCHAR(100) NULL     AFTER ext_db_name,
    ADD COLUMN ext_db_password VARCHAR(255) NULL     AFTER ext_db_user;
